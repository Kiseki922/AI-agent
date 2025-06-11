import json
import random
import time
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

# 從同目錄導入其他 AI 元件
from scripts.Agents.profile import Profile
from scripts.Agents.memory import Memory
from scripts.Agents.planning import Planning

# 導入 level 而非 map
from scripts.level import TMXMapLoader

class Action:
    """動作模組，用於代理人與環境的互動。"""
    
    def __init__(self, profile: Profile, memory: Memory, planning: Planning, game_instance):
        """
        初始化動作模組。
        
        參數:
            profile: 個人資料模組實例
            memory: 記憶模組實例
            planning: 規劃模組實例
            game_instance: 遊戲實例，包含地圖資訊
        """
        self.profile = profile
        self.memory = memory
        self.planning = planning
        self.game = game_instance
        self.last_action_time = datetime.now()
        self.action_history = []
        
        # 追蹤最近的動作類型，避免重複
        self.recent_actions = []
        self.MAX_RECENT_ACTIONS = 3
        
        # 初始化地圖位置相關變數
        self.agent_pos = (0, 0)  # 代理人位置，將會從遊戲中獲取更新
        
        # 動作權重和冷卻
        self.action_weights = {
            "move": 0.3,
            "interact": 0.2,
            "examine": 0.2,
            "use_item": 0.1,
            "rest": 0.1,
            "eat": 0.1,
            "think": 0.1
        }
        self.action_cooldowns = {
            "eat": 30 * 60,  # 30分鐘只能吃一次
            "rest": 60 * 60,  # 1小時只能休息一次
            "use_item": 10 * 60  # 10分鐘只能使用一次道具
        }
        self.last_action_times = {}
    
    def _check_action_cooldown(self, action_type: str) -> bool:
        """檢查動作是否在冷卻中"""
        current_time = time.time()
        if action_type in self.action_cooldowns:
            last_time = self.last_action_times.get(action_type, 0)
            return current_time - last_time > self.action_cooldowns[action_type]
        return True
    
    def _update_action_weights(self):
        """根据代理人状态和时间动态调整动作权重"""
        # 重置权重
        self.action_weights = {
            "move": 0.3,
            "interact": 0.2,
            "examine": 0.2,
            "use_item": 0.1,
            "rest": 0.1,
            "eat": 0.1,
            "think": 0.1
        }
        
        # 根据飢餓度调整吃东西的权重
        # if self.profile.status["hunger"] > 70:
        #     self.action_weights["eat"] = 0.5
        #     self.action_weights["move"] = 0.1
        
        # # 根据精力调整休息的权重
        # if self.profile.status["energy"] < 30:
        #     self.action_weights["rest"] = 0.5
        #     self.action_weights["move"] = 0.1
        # 根据心情调整权重
        if self.profile.status["mood"] < 30:
            self.action_weights["rest"] = 0.4
            self.action_weights["move"] = 0.1
        
        # 根据游戏时间调整行为
        if self.game and hasattr(self.game, 'game_time'):
            hour = self.game.game_time["hour"]
            
            # 早上时段 (6-9点)：增加移动和探索权重
            if 6 <= hour < 9:
                self.action_weights["move"] *= 1.5
                self.action_weights["examine"] *= 0
                self.action_weights["eat"] *= 1.2  # 早餐时间
            
            # 中午时段 (11-14点)：增加互动和用餐权重
            elif 11 <= hour < 14:
                self.action_weights["interact"] *= 1.5
                self.action_weights["eat"] *= 1.5  # 午餐时间
            
            # 下午时段 (14-17点)：平衡行为
            elif 14 <= hour < 17:
                self.action_weights["move"] *= 1.2
                self.action_weights["interact"] *= 1.2
            
            # 晚上时段 (17-21点)：增加互动和思考权重
            elif 17 <= hour < 21:
                self.action_weights["interact"] *= 1.4
                self.action_weights["think"] *= 1.5
                self.action_weights["eat"] *= 1.3  # 晚餐时间
            
            # 夜晚时段 (21-23点)：增加休息权重，降低移动权重
            elif 21 <= hour < 23:
                self.action_weights["rest"] *= 2.0
                self.action_weights["move"] *= 0.6
                self.action_weights["think"] *= 1.3
            
            # 深夜时段 (23-6点)：大幅增加休息权重，大幅降低其他活动
            else:  # 23-6点
                self.action_weights["rest"] *= 3.0
                self.action_weights["move"] *= 0.3
                self.action_weights["interact"] *= 0.4
                self.action_weights["examine"] *= 0
        
        # 避免最近做过的动作
        for action in self.recent_actions:
            if action in self.action_weights:
                self.action_weights[action] *= 0.5
    
    def execute_action(self, action_type: str, parameters: Dict = None) -> Tuple[bool, str]:
        """
        執行指定類型的動作。
        
        參數:
            action_type: 要執行的動作類型
            parameters: 動作的可選參數
            
        返回:
            (成功, 結果消息) 的元組
        """
        parameters = parameters or {}
        
        # 檢查冷卻時間
        if not self._check_action_cooldown(action_type):
            return False, f"{action_type} 動作正在冷卻中"
        
        # 記錄動作時間
        current_time = datetime.now()
        time_since_last = (current_time - self.last_action_time).total_seconds()
        self.last_action_time = current_time
        
        # 更新代理人位置
        self._update_agent_position()
        
        # 更新最近動作列表
        self.recent_actions.append(action_type)
        if len(self.recent_actions) > self.MAX_RECENT_ACTIONS:
            self.recent_actions.pop(0)
        
        # 根據類型執行動作
        success, message = self._execute_specific_action(action_type, parameters)
        
        # 更新最後執行時間
        if success:
            self.last_action_times[action_type] = time.time()
        
        # 將動作記錄到歷史中
        action_record = {
            "type": action_type,
            "parameters": parameters,
            "success": success,
            "result": message,
            "timestamp": datetime.now().isoformat(),
            "time_since_last": time_since_last
        }
        self.action_history.append(action_record)
        
        # 添加到記憶中，重要性基於成功與否和新穎性
        importance = 0.7 if success else 0.3
        self.memory.add_memory(f"動作：{action_type} - {message}", importance)
        
        return success, message
    
    def _execute_specific_action(self, action_type: str, parameters: Dict) -> Tuple[bool, str]:
        """執行具體的動作類型"""
        if action_type == "move":
            direction = parameters.get("direction", "north")
            return self._move_agent(direction)
        
        elif action_type == "goto":
            # 处理goto命令
            object_name = parameters.get("object", "")
            if object_name:
                # 如果有游戏控制器，使用它移动NPC到目标物体
                if self.game and hasattr(self.game, 'npc_controller'):
                    success = self.game.npc_controller.move_npc_to_object("npc1", object_name)
                    if success:
                        return True, f"前往 {object_name}。"
                    else:
                        return False, f"无法前往 {object_name}。"
                else:
                    return False, "游戏控制器未初始化，无法前往目标。"
            else:
                return False, "未指定目标对象。"
            
        elif action_type == "interact":
            x, y = self.agent_pos
            dx = parameters.get("dx", 0)
            dy = parameters.get("dy", 0)
            return self._interact_with_cell(x + dx, y + dy)
            
        elif action_type == "examine":
            message = self._get_surroundings()
            return True, message
            
        elif action_type == "use_item":
            item = parameters.get("item", "")
            return self._use_item(item)
            
        elif action_type == "rest":
            duration = parameters.get("duration", 30)  # 以分鐘為單位
            return self._rest(duration)
            
        elif action_type == "eat":
            food = parameters.get("food", "食物")
            return self._eat(food)
            
        elif action_type == "think":
            query = parameters.get("query", "")
            result = self._think(query)
            return True, f"思考結果：{result}"
            
        else:
            return False, f"未知的動作類型：{action_type}"
    
    def _rest(self, duration: int) -> Tuple[bool, str]:
        """休息動作"""
        # 檢查是否真的需要休息
        if self.profile.status["energy"] > 70:
            return False, "你現在精力充沛，不需要休息。"
        
        energy_gained = min(duration // 10, 30)
        self.profile.update_status("energy", energy_gained)
        message = f"你休息了 {duration} 分鐘，恢復了 {energy_gained} 點精力。"
        return True, message
    
    def _eat(self, food: str) -> Tuple[bool, str]:
        """吃東西動作"""
        # 檢查當前飢餓程度
        if self.profile.status["hunger"] < 30:
            return False, "你現在並不餓，不需要吃東西。"
        
        hunger_reduction = random.randint(20, 40)
        self.profile.update_status("hunger", -hunger_reduction)
        message = f"你吃了一些 {food}，感覺飢餓感減輕了 {hunger_reduction} 點。"
        return True, message
    
    def decide_next_action(self) -> Tuple[str, Dict]:
        """
        根據代理人的狀態和環境決定下一個動作。
        
        返回:
            (動作類型, 參數) 的元組
        """
        # 更新動作權重
        self._update_action_weights()
        
        # 檢查是否有現有計劃
        if self.planning.current_plan:
            next_step = next((step for step in self.planning.current_plan if step["status"] == "pending"), None)
            if next_step:
                return self._parse_plan_step(next_step)
        
        # 根據權重和狀態選擇動作
        actions = list(self.action_weights.keys())
        weights = list(self.action_weights.values())
        chosen_action = random.choices(actions, weights=weights)[0]
        
        # 特殊狀態處理
        # if self.profile.status["hunger"] > 70:
        #     return "eat", {"food": "食物"}
        
        # if self.profile.status["energy"] < 30:
        #     return "rest", {"duration": 60}
        
        # 根據選擇的動作生成參數
        if chosen_action == "move":
            return chosen_action, {"direction": random.choice(["north", "south", "east", "west"])}
        elif chosen_action == "interact":
            return chosen_action, {"dx": random.choice([-1, 0, 1]), "dy": random.choice([-1, 0, 1])}
        elif chosen_action == "think":
            topics = ["未來計劃", "最近事件", "有趣想法", "個人目標"]
            return chosen_action, {"query": random.choice(topics)}
        else:
            return chosen_action, {}
    
    def _parse_plan_step(self, step: Dict) -> Tuple[str, Dict]:
        """將計劃步驟轉換為動作"""
        action = step["action"]

        # 冰箱相關的動作
        if "冰箱" in action:
            return "goto", {"object": "ref"}
        
        # 沙發相關的動作
        elif "沙发" in action:
            return "goto", {"object": "sofa in fornt of TV"}
        
        # 床相關的動作
        elif "床" in action:
            # 區分睡覺和休息
            if "睡覺" in action or "睡觉" in action:
                return "goto", {"object": "bed"}
            else:  # 普通休息
                return "goto", {"object": "bed"}
        
        # 桌子相關的動作 - 新增
        elif "桌子" in action or "工作" in action:
            return "goto", {"object": "chair_in_fornt_of_desk"}
        
        # 其他移動相關的動作
        elif "移動" in action or "走" in action or "去" in action:
            # 嘗試從動作文本中提取目標物件
            if "冰箱" in action:
                return "goto", {"object": "ref"}
            elif "沙发" in action:
                return "goto", {"object": "sofa in fornt of TV"}
            elif "床" in action:
                return "goto", {"object": "bed"}
            elif "桌子" in action or "工作" in action:
                return "goto", {"object": "chair_in_fornt_of_desk"}
            else:
                # 默認隨機移動
                return "move", {"direction": "random"}

        # 互動相關的動作
        elif "互動" in action or "使用" in action or "開" in action or "關" in action:
            # 從動作文本中嘗試提取互動目標
            if "冰箱" in action:
                return "interact_with", {"object": "ref"}
            elif "沙发" in action:
                return "interact_with", {"object": "sofa in fornt of TV"}
            elif "床" in action:
                return "interact_with", {"object": "bed"}
            elif "桌子" in action:
                return "interact_with", {"object": "chair_in_fornt_of_desk"}
            else:
                # 默認互動當前位置
                return "interact", {}
        
        # 休息相關的動作
        elif "休息" in action or "睡覺" in action or "睡觉" in action:
            return "rest", {"duration": 60}  # 增加休息時間
        
        # 吃東西相關的動作
        elif "吃" in action or "食物" in action:
            return "eat", {"food": "食物"}
        
        # 聊天相關的動作 - 新增
        elif "聊天" in action or "交談" in action:
            return "goto", {"object": "sofa in fornt of TV"}
        
        # 思考相關的動作或其他未匹配的動作
        else:
            return "think", {"query": action}

    def _update_agent_position(self):
        """從遊戲中更新代理人位置"""
        if self.game and hasattr(self.game, 'npc_controller') and "npc1" in self.game.npc_controller.npcs:
            npc = self.game.npc_controller.npcs["npc1"]
            grid_x = int(npc.pos[0] / 32)
            grid_y = int(npc.pos[1] / 32)
            self.agent_pos = (grid_x, grid_y)
    
    def _move_agent(self, direction: str) -> Tuple[bool, str]:
        """移動代理人"""
        if not self.game or not hasattr(self.game, 'npc_controller'):
            return False, "無法移動，遊戲控制器未初始化"
            
        # 從當前位置計算目標位置
        x, y = self.agent_pos
        if direction == "north":
            new_pos = (x, y-1)
        elif direction == "south":
            new_pos = (x, y+1)
        elif direction == "east":
            new_pos = (x+1, y)
        elif direction == "west":
            new_pos = (x-1, y)
        else:
            return False, f"未知方向: {direction}"
            
        # 使用NPC控制器移動
        success = self.game.npc_controller.move_npc_to_tile("npc1", "floor", new_pos[0], new_pos[1])
        if success:
            return True, f"你向{self._translate_direction(direction)}移動了。"
        else:
            return False, f"無法向{self._translate_direction(direction)}移動。"
    
    def _translate_direction(self, direction: str) -> str:
        """將英文方向轉換為中文"""
        direction_map = {
            "north": "北",
            "south": "南",
            "east": "東",
            "west": "西"
        }
        return direction_map.get(direction, direction)
    
    def _interact_with_cell(self, x: int, y: int) -> Tuple[bool, str]:
        """與指定位置的單元格互動"""
        if not self.game or not hasattr(self.game, 'npc_controller'):
            return False, "無法互動，遊戲控制器未初始化"
            
        # 嘗試獲取當前位置的對象
        objects_at_position = self._get_objects_at_position(x, y)
        if objects_at_position:
            # 使用第一個找到的對象互動
            object_name = objects_at_position[0]
            # 使用 npc_interact_with 而非 npc_interact
            success = self.game.npc_controller.npc_interact_with("npc1", object_name)
            return success, f"你與{object_name}互動了。"
        else:
            return False, "這裡沒有可互動的物體。"
    
    def _get_objects_at_position(self, x: int, y: int) -> List[str]:
        """獲取指定位置的對象列表"""
        objects = []
        if self.game and hasattr(self.game, 'tmx_data'):
            for obj_group in self.game.tmx_data.objectgroups:
                for obj in obj_group:
                    grid_x = int(obj.x / 32)
                    grid_y = int(obj.y / 32)
                    if grid_x == x and grid_y == y:
                        obj_name = getattr(obj, 'name', obj_group.name)
                        objects.append(obj_name)
        return objects
    
    def _get_surroundings(self) -> str:
        """獲取代理人周圍環境的描述"""
        surroundings = []
        
        # 檢查周圍的對象
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx == 0 and dy == 0:
                    continue  # 跳過代理人自己的位置
                    
                objects = self._get_objects_at_position(self.agent_pos[0] + dx, self.agent_pos[1] + dy)
                if objects:
                    direction = self._get_direction_text(dx, dy)
                    for obj in objects:
                        surroundings.append(f"在{direction}方向有一個{obj}。")
        
        # 找出代理人所在的區域
        room_name = self._get_current_room_name()
        
        if not surroundings:
            return f"你位於{room_name}。周圍沒有值得注意的東西。"
        else:
            return f"你位於{room_name}。" + " ".join(surroundings)
    
    def _get_direction_text(self, dx: int, dy: int) -> str:
        """基於坐標變化獲取方向文本"""
        direction = ""
        if dy < 0:
            direction = "北"
        elif dy > 0:
            direction = "南"
            
        if dx < 0:
            direction += "西"
        elif dx > 0:
            direction += "東"
            
        return direction or "附近"
    
    def _get_current_room_name(self) -> str:
        """獲取代理人當前所在的房間名稱"""
        # 嘗試從TMX地圖中識別區域
        room_name = "未知區域"
        if self.game and hasattr(self.game, 'tmx_data'):
            # 搜索房間物件組
            for obj_group in self.game.tmx_data.objectgroups:
                if obj_group.name.lower() == "rooms":
                    for obj in obj_group:
                        x1 = int(obj.x / 32)
                        y1 = int(obj.y / 32)
                        x2 = int((obj.x + obj.width) / 32)
                        y2 = int((obj.y + obj.height) / 32)
                        
                        if (x1 <= self.agent_pos[0] <= x2 and y1 <= self.agent_pos[1] <= y2):
                            room_name = getattr(obj, 'name', "房間")
                            break
        
        return room_name
    
    def _use_item(self, item: str) -> Tuple[bool, str]:
        """模擬使用物品。"""
        # 這是一個佔位符 - 在實際實現中，你會有一個物品庫存系統
        return True, f"你使用了 {item}。"

    def _think(self, query: str) -> str:
        """
        模擬代理人思考一個問題，並分段輸出結果。
        
        參數:
            query: 要思考的問題
            
        返回:
            思考的結果
        """
        # 獲取相關記憶
        relevant_memories = self.memory.retrieve_relevant(query)
        memory_texts = [f"- {m['content']}" for m in relevant_memories]
        
        # 使用換行符號連接記憶文本
        memories_str = ""
        if memory_texts:
            memories_str = "\n".join(memory_texts)
        else:
            memories_str = "你沒有與此相關的特定記憶。"
        
        # 根據代理人的個人資料和記憶創建提示
        prompt = f"""
        你是 {self.profile.name}，一名 {self.profile.occupation}。
        你的個性特徵是：{self.profile.traits}
        你的興趣是：{self.profile.interests}
        
        你正在思考：{query}
        
        你的相關記憶是：
        {memories_str}
        
        基於你的個性、興趣和記憶，你對此有什麼看法？
        請將你的想法分成3-5個段落，每個段落代表一個清晰的思路或觀點。
        每個段落之間空一行，讓內容更易於閱讀。
        """
        
        # 使用本地 API 生成回應
        try:
            payload = {
                "model": "deepseek-r1-distill-qwen-7b",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = requests.post("http://127.0.0.1:1234/v1/chat/completions", json=payload)
            response.raise_for_status()
            thought = response.json()["choices"][0]["message"]["content"]
            return thought
            
        except Exception as e:
            print(f"API 請求失敗：{e}")
            return f"我現在不確定對 {query} 有什麼想法。"

    def to_dict(self) -> Dict:
        """將動作數據轉換為字典以便存儲。"""
        return {
            "action_history": self.action_history,
            "last_action_time": self.last_action_time.isoformat()
        }
    
    def from_dict(self, data: Dict) -> None:
        """從字典加載動作數據。"""
        self.action_history = data.get("action_history", [])
        last_action_time = data.get("last_action_time")
        if last_action_time:
            self.last_action_time = datetime.fromisoformat(last_action_time)
            print("----------------------------------------------------------")
            print("get it")
    
    def save(self, filename: str = "action.json") -> None:
        """將動作數據保存到 JSON 文件。"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            
    def load(self, filename: str = "action.json") -> None:
        """從 JSON 文件加載動作數據。"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.from_dict(data)
        except FileNotFoundError:
            print(f"動作文件 {filename} 未找到。從空動作歷史開始。")