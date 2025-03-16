import json
import random
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

from profile import Profile
from memory import Memory
from planning import Planning
from map import Map

class Action:
    """動作模組，用於代理人與環境的互動。"""
    
    def __init__(self, profile: Profile, memory: Memory, planning: Planning, map_system: Map):
        """
        初始化動作模組。
        
        參數:
            profile: 個人資料模組實例
            memory: 記憶模組實例
            planning: 規劃模組實例
            map_system: 地圖模組實例
        """
        self.profile = profile
        self.memory = memory
        self.planning = planning
        self.map = map_system
        self.last_action_time = datetime.now()
        self.action_history = []
    
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
        
        # 記錄動作時間
        current_time = datetime.now()
        time_since_last = (current_time - self.last_action_time).total_seconds()
        self.last_action_time = current_time
        
        # 根據類型執行動作
        if action_type == "move":
            direction = parameters.get("direction", "north")
            success, message = self.map.move_agent(direction)
            
        elif action_type == "interact":
            x, y = self.map.agent_pos
            dx = parameters.get("dx", 0)
            dy = parameters.get("dy", 0)
            success, message = self.map.interact_with_cell(x + dx, y + dy)
            
        elif action_type == "examine":
            message = self.map.get_surroundings()
            success = True
            
        elif action_type == "use_item":
            item = parameters.get("item", "")
            success, message = self._use_item(item)
            
        elif action_type == "rest":
            duration = parameters.get("duration", 30)  # 以分鐘為單位
            self.profile.update_status("energy", min(duration // 10, 20))
            message = f"你休息了 {duration} 分鐘，感覺精神煥發。"
            success = True
            
        elif action_type == "eat":
            food = parameters.get("food", "食物")
            self.profile.update_status("hunger", -30)
            message = f"你吃了一些 {food}，感覺不那麼餓了。"
            success = True
            
        elif action_type == "think":
            query = parameters.get("query", "")
            result = self._think(query)
            message = f"你思考了關於 {query} 的問題，得出結論：{result}"
            success = True
            
        else:
            message = f"未知的動作類型：{action_type}"
            success = False
        
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
    
    def _use_item(self, item: str) -> Tuple[bool, str]:
        """模擬使用物品。"""
        # 這是一個佔位符 - 在實際實現中，你會有一個物品庫存系統
        return True, f"你使用了 {item}。"
    
    def _think(self, query: str) -> str:
        """
        模擬代理人思考一個問題。
        
        參數:
            query: 要思考的問題
            
        返回:
            思考的結果
        """
        # 獲取相關記憶
        relevant_memories = self.memory.retrieve_relevant(query)
        memory_texts = [f"- {m['content']}" for m in relevant_memories]
        
        # 根據代理人的個人資料和記憶創建提示
        prompt = f"""
        你是 {self.profile.name}，一名 {self.profile.occupation}。
        你的個性特徵是：{self.profile.traits}
        你的興趣是：{self.profile.interests}
        
        你正在思考：{query}
        
        你的相關記憶是：
        {memory_texts if memory_texts else "你沒有與此相關的特定記憶。"}
        
        基於你的個性、興趣和記憶，你對此有什麼看法？
        """
        
        # 使用 DeepSeek API 生成回應
        try:
            payload = {
                "model": "deepseek-r1-distill-qwen-7b",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            response = requests.post("http://127.0.0.1:1234/v1/chat/completions", json=payload)
            response.raise_for_status()
            thought = response.json()["choices"][0]["message"]["content"]
            return thought
            
        except Exception as e:
            print(f"API 請求失敗：{e}")
            return f"我現在不確定對 {query} 有什麼想法。"
    
    def decide_next_action(self) -> Tuple[str, Dict]:
        """
        根據代理人的狀態決定下一個動作。
        
        返回:
            (動作類型, 參數) 的元組
        """
        # 檢查是否應該遵循當前計劃
        if self.planning.current_plan:
            next_step = next((step for step in self.planning.current_plan if step["status"] == "pending"), None)
            
            if next_step:
                # 解析下一步以確定動作
                action = next_step["action"]
                
                if "移動" in action or "走" in action or "去" in action:
                    directions = ["north", "south", "east", "west"]
                    for direction in directions:
                        dir_zh = {"north": "北", "south": "南", "east": "東", "west": "西"}[direction]
                        if dir_zh in action:
                            return "move", {"direction": direction}
                    
                    # 如果沒有特定方向，隨機移動
                    return "move", {"direction": random.choice(directions)}
                    
                elif "互動" in action or "使用" in action or "開" in action or "關" in action:
                    return "interact", {"dx": 0, "dy": 0}  # 與當前單元格互動
                    
                elif "檢查" in action or "查看" in action or "看" in action:
                    return "examine", {}
                    
                elif "休息" in action or "睡覺" in action:
                    return "rest", {"duration": 30}
                    
                elif "吃" in action or "食物" in action:
                    return "eat", {"food": "食物"}
                    
                else:
                    # 默認是思考該動作
                    return "think", {"query": action}
        
        # 如果沒有計劃或無法解析下一步，根據需求做出決定
        # 檢查緊急需求
        if self.profile.status["hunger"] > 70:
            return "eat", {"food": "食物"}
            
        if self.profile.status["energy"] < 30:
            return "rest", {"duration": 60}
            
        # 檢查計劃活動
        current_activity = self.planning.get_current_activity()
        if current_activity:
            # 將活動轉換為動作
            if "吃" in current_activity:
                return "eat", {"food": "食物"}
                
            if "休息" in current_activity or "睡覺" in current_activity:
                return "rest", {"duration": 60}
                
            # 默認是思考該活動
            return "think", {"query": current_activity}
        
        # 如果沒有緊急或計劃的事項，探索或思考
        if random.random() < 0.7:  # 70% 的機率探索
            return "move", {"direction": random.choice(["north", "south", "east", "west"])}
        else:
            topics = ["未來計劃", "最近事件", "有趣想法", "個人目標"]
            return "think", {"query": random.choice(topics)}
    
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