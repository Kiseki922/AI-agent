import json
import os
import time
import random
from typing import Dict, List, Tuple, Optional, Any
from threading import Thread

# 從同目錄導入 AI 代理元件
from scripts.Agents.profile import Profile
from scripts.Agents.memory import Memory
from scripts.Agents.planning import Planning
from scripts.Agents.ai_agent import AIAgent

# 從 scripts 目錄導入 level 相關類
from scripts.level import TMXMapLoader

class TMXAIBridge:
    """將AI代理人系統與基於TMX地圖的遊戲連接的橋接類"""
    
    def __init__(self, game_instance=None, npc_id="npc1"):
        """
        Initialize AI-TMX bridge
        
        Args:
            game_instance: Game instance with TMX map and NPC controller
            npc_id: ID of the NPC this bridge controls (default: "npc1")
        """
        self.game = game_instance
        self.npc_id = npc_id  # 添加這行
        self.agent = None
        self.running = False
        self.ai_thread = None
        self.commands_queue = []  # Queue for AI-generated commands
        self.last_command_time = 0
        self.command_cooldown = 2.0  # Command execution cooldown (seconds)
        self.map_objects = {}  # Store map object information
        self.command_success_count = 0  # Count of successfully executed commands
        self.command_failure_count = 0  # Count of failed command executions
        self.debug_output = False  # New: control debug info output
        
        # NPC status interaction effect configuration - IMPROVED VALUES
        self.interaction_effects = {
            # Rest objects - improve mood significantly
            "bed": ({"mood": 70, "health": 50}, "Sleep in bed"),
            "sofa": ({"mood": 65, "health": 45}, "Relax on sofa"),
            "chair": ({"mood": 60, "health": 52}, "Sit on chair"),
            "chair_in_fornt_of_desk": ({"mood": 60, "health": 52}, "Sit at desk"),
            "sofa in fornt of TV": ({"mood": 70, "health": 58}, "Relax on sofa in front of TV"),
            
            # Food related objects - improve health significantly
            "refrigerator": ({"mood": 65, "health": 70}, "Get food from refrigerator"),
            "ref": ({"mood": 65, "health": 70}, "Get food from refrigerator"),
            "food": ({"mood": 60, "health": 70}, "Eat food"),
            "kitchen": ({"mood": 60, "health": 70}, "Cook in kitchen"),
            
            # Entertainment objects - significantly improve mood
            "tv": ({"mood": 80, "health": -5}, "Watch TV"),
            "bookshelf": ({"mood": 75, "health": 55}, "Read books"),
            "computer": ({"mood": 75, "health": -10}, "Use computer"),
            "game": ({"mood": 85, "health": -15}, "Play games"),
            
            # Functional objects - improve health
            "toilet": ({"health": 65, "mood": 55}, "Use toilet"),
            "shower": ({"health": 75, "mood": 65}, "Take shower"),
            "window": ({"mood": 60, "health": 0}, "Look out window"),
            "door": ({"mood": 55, "health": 0}, "Open/close door"),
            
            # Default interaction
            "default": ({"mood": 55, "health": 0}, "Inspect item")
        }
        
        # Status history
        self.status_history = []  # Store status change history
        self.max_history_items = 10  # Maximum history items
        
    def initialize_agent(self, name="AI助手"):
        """初始化AI代理人"""
        # 直接傳入遊戲實例和NPC ID給AIAgent
        self.agent = AIAgent(name, self.game, npc_id=self.npc_id)

        # 直接傳入遊戲實例給AIAgent
        self.agent = AIAgent(name, self.game)
        
        # 自定义代理人特性
        self.agent.profile.traits = {
            "外向性": 0.7,
            "冒险性": 0.8,
            "好奇心": 0.9,
            "创造力": 0.6
        }
        self.agent.profile.occupation = "居家生活助手"  # 修改职业
        self.agent.profile.interests = ["家务", "休息", "用餐", "生活规律"]  # 修改兴趣
        
        # 设置一些初始目标，移除探索相关目标
        self.agent.planning.add_goal("维持生活规律", "short_term", 5)
        self.agent.planning.add_goal("按时进餐", "short_term", 4)
        self.agent.planning.add_goal("保持休息", "medium_term", 3)
        
        # 初始化记忆，添加地图信息
        self.agent.memory.add_memory("这是我的家，我很熟悉这里的一切。", 0.8)
        
        # 添加关于时间的初始记忆
        if hasattr(self.game, 'game_time'):
            current_time = f"{self.game.game_time['hour']:02d}:{int(self.game.game_time['minute']):02d}"
            self.agent.memory.add_memory(f"现在的时间是 {current_time}，我应该根据时间安排我的活动。", 0.7)
        
        # 收集地图对象信息
        self._initialize_map_knowledge()
        
        print(f"AI代理人 {name} 已初始化（控制 NPC: {self.npc_id}）")  # 修改這行
    
    def _initialize_map_knowledge(self):
        """收集地图对象信息到内部映射，并传递给AI - 使用共享地图知识"""
        if not self.game or not hasattr(self.game, 'tmx_data'):
            return
            
        # 检查是否已经有共享的地图对象缓存
        if hasattr(self.game, '_shared_map_objects') and self.game._shared_map_objects:
            print(f"使用共享地图知识 for {self.npc_id}...")
            # 直接使用已缓存的地图对象
            self.map_objects = self.game._shared_map_objects.copy()
            
            # 只添加少量个人化记忆
            self.agent.memory.add_memory("这是我的家，我很熟悉这里的一切。", 0.8)
            self.agent.memory.add_memory("日常生活中，我需要在合适的时间去合适的地点。", 0.8)
            
            # 添加重要物品记忆（简化版）
            important_objects = []
            for group_name, objects in self.map_objects.items():
                for obj in objects[:2]:  # 每个组只取前2个物体
                    if "name" in obj and obj["name"]:
                        important_objects.append(obj["name"])
            
            if important_objects:
                object_memory = f"我家里有这些重要物品: {', '.join(important_objects[:10])}。"
                self.agent.memory.add_memory(object_memory, 0.9)
            
            print(f"地图知识初始化完成 for {self.npc_id} (使用共享缓存)")
            return
        
        # 第一次初始化 - 创建共享缓存
        print(f"首次初始化地图知识，创建共享缓存...")
        tmx_data = self.game.tmx_data
        
        # 清除当前的对象映射
        self.map_objects = {}
        
        # 限制处理的对象数量，避免过度处理
        max_objects_per_group = 50
        total_objects = 0
        
        # 收集所有地图物体信息
        for obj_group in tmx_data.objectgroups:
            group_name = obj_group.name.lower()
            self.map_objects[group_name] = []
            
            idx = 0
            objects_in_group = 0
            
            for obj in obj_group:
                # 限制每个组的对象数量
                if objects_in_group >= max_objects_per_group:
                    break
                    
                # 计算网格坐标
                grid_x = int(obj.x / 32)
                grid_y = int(obj.y / 32)
                
                # 获取或生成物体名称
                if hasattr(obj, 'name') and obj.name:
                    obj_name = obj.name
                else:
                    obj_name = f"{group_name}_{idx}"
                    idx += 1
                
                # 存储对象信息
                obj_info = {
                    "name": obj_name,
                    "x": grid_x,
                    "y": grid_y,
                    "type": group_name
                }
                self.map_objects[group_name].append(obj_info)
                
                objects_in_group += 1
                total_objects += 1
            
            print(f"处理对象组 {group_name}: {objects_in_group} 个对象")
        
        # 保存共享缓存到游戏实例
        self.game._shared_map_objects = self.map_objects.copy()
        
        # 添加基本记忆
        self.agent.memory.add_memory("这是我的家，我很熟悉这里的一切。", 0.8)
        self.agent.memory.add_memory("日常生活中，我需要在合适的时间去合适的地点。", 0.8)
        
        # 創建物體列表的記憶 - 只包含重要物体
        if self.map_objects:
            important_objects = []
            for group_name, objects in self.map_objects.items():
                # 只添加前5个物体到记忆中
                for obj in objects[:5]:
                    if "name" in obj and obj["name"]:
                        important_objects.append(obj["name"])
                    else:
                        important_objects.append(f"{group_name}_{len(important_objects)}")
            
            if important_objects:
                object_memory = f"我家里有这些重要物品: {', '.join(important_objects[:20])}。"  # 最多20个
                self.agent.memory.add_memory(object_memory, 0.9)
        
        print(f"地图知识初始化完成，创建共享缓存，总共处理 {total_objects} 个对象")
        
        # 添加互動指南的記憶
        self.agent.memory.add_memory("日常生活中，我需要在合适的时间去合适的地点。", 0.8)
        
        # 創建物體列表的記憶 - 只包含重要物体
        if self.map_objects:
            important_objects = []
            for group_name, objects in self.map_objects.items():
                # 只添加前5个物体到记忆中
                for obj in objects[:5]:
                    if "name" in obj and obj["name"]:
                        important_objects.append(obj["name"])
                    else:
                        important_objects.append(f"{group_name}_{len(important_objects)}")
            
            if important_objects:
                object_memory = f"我家里有这些重要物品: {', '.join(important_objects[:20])}。"  # 最多20个
                self.agent.memory.add_memory(object_memory, 0.9)
        
        print(f"地图知识初始化完成 for {self.npc_id}, 总共处理 {total_objects} 个对象")
    
    def start_ai_loop(self):
        """在后台线程启动AI决策循环"""
        if self.running or self.ai_thread is not None:
            return
            
        print(f"准备启动AI决策循环 for {self.npc_id}...")
        self.running = True
        self.ai_thread = Thread(target=self._ai_decision_loop)
        self.ai_thread.daemon = True  # 设为守护线程，主线程结束时会自动终止
        self.ai_thread.start()
        print(f"AI决策循环已启动 for {self.npc_id}")
    
    def stop_ai_loop(self):
        """停止AI决策循环"""
        self.running = False
        if self.ai_thread:
            self.ai_thread.join(timeout=1.0)  # 等待线程结束，最多1秒
            self.ai_thread = None
        print("AI决策循环已停止")
    
    def _ai_decision_loop(self):
        """AI决策主循环，在单独线程中运行"""
        if not self.agent:
            print("错误：未初始化AI代理人")
            self.running = False
            return
            
        while self.running:
            try:
                # 更新AI代理的时间感知
                self._update_agent_time_awareness()
                
                # 运行一步AI决策
                result = self.agent.run_step()
                print(f"AI决策: {result}")  # 只保留这一行输出
                
                # 从决策结果中提取命令
                command = self._extract_command_from_decision(result)
                if command:
                    self.commands_queue.append(command)
                
                # 等待一段时间再进行下一次决策
                time.sleep(3.0)  # 决策间隔时间
                
            except Exception as e:
                print(f"AI决策循环中出错: {e}")
                time.sleep(5.0)  # 错误发生后等待更长时间
    
    def _update_agent_time_awareness(self):
        """更新AI代理的时间感知"""
        if not self.game or not hasattr(self.game, 'game_time') or not self.agent:
            return
            
        game_time = self.game.game_time
        hour = game_time["hour"]
        minute = int(game_time["minute"])
        
        # 每小时更新一次时间记忆
        if minute < 5:  # 每小时开始时更新
            time_str = f"{hour:02d}:{minute:02d}"
            
            # 根据时间段添加不同的记忆
            if 6 <= hour <= 8:
                self.agent.memory.add_memory(f"现在是早晨 {time_str}，是早餐时间。", 0.6)
            elif 11 <= hour <= 13:
                self.agent.memory.add_memory(f"现在是中午 {time_str}，是午餐时间。", 0.6)
            elif 17 <= hour <= 19:
                self.agent.memory.add_memory(f"现在是傍晚 {time_str}，是晚餐时间。", 0.6)
            elif 21 <= hour <= 23:
                self.agent.memory.add_memory(f"现在是晚上 {time_str}，应该准备休息了。", 0.6)
            elif 0 <= hour <= 5:
                self.agent.memory.add_memory(f"现在是深夜 {time_str}，应该在睡觉。", 0.6)
            else:
                self.agent.memory.add_memory(f"现在是 {time_str}。", 0.5)
    
    def _extract_command_from_decision(self, decision_text):
        """從AI決策文本中提取遊戲命令並進行預處理驗證"""
        # 檢查是否提到冰箱相關行為
        if "冰箱" in decision_text:
            return ("goto", "ref")
        
        # 檢查是否提到沙發相關行為
        if "沙发" in decision_text or "沙發" in decision_text:
            return ("goto", "sofa in fornt of TV")
        
        # 檢查是否提到床相關行為
        if "床" in decision_text:
            # 區分是睡覺還是休息
            if "睡覺" in decision_text or "睡觉" in decision_text:
                # 先去床的位置
                return ("goto", "bed")
            else:
                # 一般休息
                return ("goto", "bed")
        
        # 檢查是否提到桌子相關行為 - 新增
        if "桌子" in decision_text or "工作" in decision_text:
            return ("goto", "chair_in_fornt_of_desk")
        
        # 檢查互動行為
        if "互動" in decision_text or "交互" in decision_text or "互动" in decision_text:
            # 檢查是否提到特定物件
            if "冰箱" in decision_text:
                return ("interact_with", "ref")
            elif "沙发" in decision_text or "沙發" in decision_text:
                return ("interact_with", "sofa in fornt of TV")
            elif "床" in decision_text:
                return ("interact_with", "bed")
            elif "桌子" in decision_text:
                return ("interact_with", "chair_in_fornt_of_desk")
        
        # 檢查休息行為
        if "休息" in decision_text:
            return ("rest", None)
        
        # 檢查睡覺行為
        if "睡覺" in decision_text or "睡觉" in decision_text:
            # 先確保去床位置，然後與床互動，最後休息
            # 注意：這裡返回的只是一個命令，真正的睡覺行為需要多個連續命令
            # 這將在 trigger_time_based_behavior 中處理
            return ("rest", None)
        
        # 移除基於方向的移動命令，改為直接使用goto命令
        if "移動" in decision_text or "走" in decision_text:
            # 直接构建随机移动命令
            return ("random_move", None)
        
        # 檢查是否提到聊天相關行為
        if "聊天" in decision_text or "交谈" in decision_text or "社交" in decision_text:
            # 当时间在13:00-18:00之间时，保持不动
            if hasattr(self.game, 'game_time'):
                hour = self.game.game_time["hour"]
                if 13 <= hour < 18:
                    # 已经在沙发上，保持不动
                    return ("rest", None)
            # 否则去沙发
            return ("goto", "sofa in fornt of TV")
        
        # 原有的處理邏輯保持不變...
        # 這裡可以保留原代碼中其他的命令解析邏輯
        
        return None
    
    def return_to_player(self, npc_id=None):
        """Command the NPC to return to the player's location"""
        # 如果沒有指定 npc_id，使用 self.npc_id
        npc_id = npc_id or self.npc_id
        
        if not npc_id:
            print("Error: No NPC ID specified for return_to_player")
            return False
            
        if not self.game or not hasattr(self.game, 'player') or not hasattr(self.game, 'npc_controller'):
            return False
            
        player = self.game.player
        npc = self.game.npc_controller.get_npc(npc_id)
        
        if not npc:
            return False
            
        # Get player's grid position
        player_grid_x = player.grid_pos[0]
        player_grid_y = player.grid_pos[1]
        
        # Find a nearby position to stand (one of the 8 surrounding cells)
        directions = [
            (0, 1), (1, 0), (0, -1), (-1, 0),  # Cardinal directions
            (1, 1), (-1, -1), (1, -1), (-1, 1)  # Diagonal directions
        ]
        
        # Try each direction to find a valid spot
        for dx, dy in directions:
            target_x = player_grid_x + dx
            target_y = player_grid_y + dy
            
            # Check if the position is valid (not a wall)
            if self.game.npc_controller.move_npc_to_tile(npc_id, "floor", target_x, target_y):
                # Mark the task as completed
                self.task_completed = True
                
                if hasattr(self.game, 'dialogue_system'):
                    self.game.dialogue_system.task_completed = True
                    
                if hasattr(self.game, 'add_status_message'):
                    self.game.add_status_message("NPC已返回玩家身边，任务完成")
                    
                return True
            
        return self.game.npc_controller.move_npc_to_tile(npc_id, "floor", player_grid_x, player_grid_y)

    def process_next_command(self):
        """處理隊列中的下一個命令，添加智能失敗處理"""
        # 首先檢查是否有基於時間的行為需要觸發
        if self.agent and hasattr(self.game, 'game_time') and not self.game.game_time["paused"]:
            # 每小時整點檢查一次
            hour = self.game.game_time["hour"]
            minute = int(self.game.game_time["minute"])
            
            # 提前添加日程行為，使NPC能提前準備
            if minute >= 55 and not self.commands_queue:
                next_hour = (hour + 1) % 24
                # 臨時修改遊戲時間以觸發下一個小時的行為
                original_hour = self.game.game_time["hour"]
                self.game.game_time["hour"] = next_hour
                self.game.game_time["minute"] = 0
                triggered = self.trigger_time_based_behavior()
                # 恢復原始時間
                self.game.game_time["hour"] = original_hour
                self.game.game_time["minute"] = minute
                
                if triggered and hasattr(self.game, 'add_status_message') and self.debug_output:
                    self.game.add_status_message(f"提前準備{next_hour}點活動")
                    return True
            
            # 在整點或接近整點時觸發時間行為
            if 0 <= minute <= 2:
                # 嘗試觸發時間相關行為
                if self.trigger_time_based_behavior():
                    return True  # 如果成功觸發了時間行為，則本次處理結束
        
        # 如果命令隊列為空或上一個命令執行失敗太多次，添加隨機移動命令
        if not self.commands_queue or self.command_failure_count > 3:
            # 重置失敗計數
            self.command_failure_count = 0
            
            # 添加隨機移動命令到隊列
            self.commands_queue.append(("random_move", None))
            
            # 如果是特定時間，也添加去對應位置的命令
            if self.agent and hasattr(self.game, 'game_time'):
                hour = self.game.game_time["hour"]
                
                if 7 <= hour < 9 or 12 <= hour < 14 or 17 <= hour < 19:
                    # 用餐時間段，嘗試去冰箱或桌子
                    for group_name in ["ref", "chair_in_fornt_of_desk"]:
                        if group_name in self.map_objects:
                            self.commands_queue.append(("goto", group_name))
                            break
                elif 9 <= hour < 12 or 14 <= hour < 17:
                    # 日常活動時間段，嘗試去桌子
                    if "chair_in_fornt_of_desk" in self.map_objects:
                        self.commands_queue.append(("goto", "chair_in_fornt_of_desk"))
                elif 22 <= hour or hour < 6:
                    # 睡覺時間段，嘗試去床
                    if "bed" in self.map_objects:
                        self.commands_queue.append(("goto", "bed"))
        
        # 處理正常的命令隊列
        current_time = time.time()
        if current_time - self.last_command_time < self.command_cooldown:
            return False
        
        # 處理命令冷卻時間
        if current_time - self.last_command_time < self.command_cooldown:
            return False

        # 獲取並移除隊列中的第一個命令
        if not self.commands_queue:
            return False
            
        command = self.commands_queue.pop(0)
        self.last_command_time = current_time
        
        if not command or not self.game or not self.game.npc_controller:
            return False
            
        cmd_type, cmd_param = command

        # 執行命令並記錄結果
        command_success = False

        # 首先檢查命令隊列是否為空
        if not self.commands_queue:
            # 如果命令隊列為空，檢查是否有基於時間的行為需要觸發
            if self.agent and hasattr(self.game, 'game_time') and not self.game.game_time["paused"]:
                # 檢查是否有玩家任務標誌
                has_player_task = False
                if hasattr(self.game, 'dialogue_system'):
                    has_player_task = hasattr(self.game.dialogue_system, 'task_assigned') and self.game.dialogue_system.task_assigned
                
                # 只有在沒有玩家任務的情況下才觸發時間行為
                if not has_player_task:
                    # 提前添加日程行為，使NPC能提前準備
                    hour = self.game.game_time["hour"]
                    minute = int(self.game.game_time["minute"])
                    
                    # 在整點或接近整點時觸發時間行為
                    if 0 <= minute <= 2:
                        # 嘗試觸發時間相關行為
                        if self.trigger_time_based_behavior():
                            return True  # 如果成功觸發了時間行為，則本次處理結束
        
        # 執行命令
        if cmd_type == "random_move":
            # 隨機移動到周圍位置
            npc = self.game.npc_controller.npcs.get(self.npc_id)
            if npc:
                current_x = npc.grid_pos[0]
                current_y = npc.grid_pos[1]
                
                # 隨機選擇一個相鄰位置
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
                
                # 確保至少有一個方向移動
                if dx == 0 and dy == 0:
                    dx = random.choice([-1, 1])
                
                # 計算新位置
                new_x = current_x + dx
                new_y = current_y + dy
                
                # 移動NPC到新位置
                command_success = self.game.npc_controller.move_npc_to_tile(self.npc_id, "floor", new_x, new_y)
            else:
                command_success = False
                
        elif cmd_type == "move":
            # 不再使用方向，而是直接通過坐標移動
            # 獲取當前NPC位置
            npc = self.game.npc_controller.npcs.get(self.npc_id)
            if npc:
                current_x = npc.grid_pos[0]
                current_y = npc.grid_pos[1]
                
                # 不再使用東南西北方向而是使用相對坐標偏移
                # 將指令參數轉換為坐標偏移
                dx, dy = 0, 0
                
                # 如果仍然使用舊的方向格式，進行轉換
                if cmd_param == "north":
                    dy = -1
                elif cmd_param == "south":
                    dy = 1
                elif cmd_param == "east":
                    dx = 1
                elif cmd_param == "west":
                    dx = -1
                elif isinstance(cmd_param, tuple) and len(cmd_param) == 2:
                    # 如果已經是坐標偏移格式
                    dx, dy = cmd_param
                
                # 計算新位置
                new_x = current_x + dx
                new_y = current_y + dy
                
                # 移動NPC到新位置
                command_success = self.game.npc_controller.move_npc_to_tile(self.npc_id, "floor", new_x, new_y)
            else:
                command_success = False
                
        elif cmd_type == "goto":
            # 前往特定物體
            object_name = cmd_param
            if object_name:  # 確保有效的目標名稱
                npc = self.game.npc_controller.npcs.get(self.npc_id)
                if npc and self.debug_output:
                    print(f"尋路調試: 起點 {npc.grid_pos}, 終點 {object_name}")
                command_success = self.game.npc_controller.move_npc_to_object(self.npc_id, object_name)
                
                # 如果移動失敗並且是聊天時間，再次嘗試
                if not command_success and hasattr(self.game, 'game_time'):
                    hour = self.game.game_time["hour"]
                    if 13 <= hour < 18 and "sofa" in object_name:
                        # 添加到命令隊列前端，以便立即重試
                        self.commands_queue.insert(0, (cmd_type, cmd_param))
                        print(f"移動到沙發失敗，重新嘗試...")
                        return False
                
        elif cmd_type == "interact_with" and cmd_param:
            # 與特定對象交互
            command_success = self.game.npc_controller.npc_interact_with(self.npc_id, cmd_param)
            
            # 如果交互成功，處理狀態變化
            if command_success:
                self.handle_interaction(self.npc_id, cmd_param)
                
        elif cmd_type == "interact":
            # 改進交互命令處理
            npc = self.game.npc_controller.npcs.get(self.npc_id)
            if npc:
                # 獲取當前位置
                current_x = npc.grid_pos[0]
                current_y = npc.grid_pos[1]
                nearby_objects = []
                
                # 從地圖對象中查找附近的可交互對象
                for group_name, objects in self.map_objects.items():
                    for obj in objects:
                        # 檢查是否在附近 (1格範圍內)
                        obj_x = obj['x']
                        obj_y = obj['y']
                        dist = abs(obj_x - current_x) + abs(obj_y - current_y)
                        if dist <= 1:  # 如果在相鄰格子
                            nearby_objects.append(obj['name'])
                
                # 檢查周圍的格子
                if not nearby_objects:
                    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # 四個方向
                    for dx, dy in directions:
                        objects = npc._get_objects_at_position(current_x + dx, current_y + dy)
                        if objects:
                            nearby_objects.extend(objects)
                
                if nearby_objects:
                    # 有附近對象，設置交互目標並嘗試交互
                    target_obj = nearby_objects[0]  # 使用第一個找到的物體
                    # 先設置互動目標
                    npc.interaction_target = target_obj
                    # 然後執行互動
                    command_success = npc.interact_with_current_target()
                    
                    # 如果互動成功，處理狀態變化
                    if command_success:
                        self.handle_interaction(self.npc_id, target_obj)
                else:
                    # 添加隨機移動命令到隊列前端
                    self.commands_queue.insert(0, ("random_move", None))
                    command_success = True  # 認為命令成功但改為移動
            else:
                command_success = False
                
        elif cmd_type == "eat":
            # 簡單實現進食行為，移除hunger和energy
            if self.agent:
                # 顯示狀態變化，只更新mood和health
                self.handle_status_change(self.npc_id, "food", {"mood": 55, "health": 55})
                if hasattr(self.game, 'add_status_message') and self.debug_output:
                    self.game.add_status_message("NPC吃了一些食物")
                command_success = True
            else:
                command_success = False
                
        elif cmd_type == "rest":
            # 簡單實現休息行為，移除energy
            if self.agent:
                # 顯示狀態變化，只更新mood和health
                self.handle_status_change(self.npc_id, "rest", {"mood": 55, "health": 55})
                if hasattr(self.game, 'add_status_message') and self.debug_output:
                    self.game.add_status_message("NPC休息了一會兒")
                command_success = True
            else:
                command_success = False
                
        elif cmd_type == "return_to_player":
            # Return to player command
            command_success = self.return_to_player()
        else:
            command_success = False
        
        # 命令執行完畢後，檢查是否完成了玩家任務
        if command_success and cmd_type == "return_to_player":
            # 如果剛剛完成了"返回玩家"命令，重置任務狀態
            if hasattr(self.game, 'dialogue_system'):
                self.game.dialogue_system.task_assigned = False
                self.game.dialogue_system.task_completed = True
            
                # 添加狀態消息
                if hasattr(self.game, 'add_status_message'):
                    self.game.add_status_message("玩家任務已完成，恢復日程表執行")

                # 強制更新計劃，恢復日程表
                if self.agent and hasattr(self.agent, '_update_plan_based_on_time'):
                    self.agent._update_plan_based_on_time()

            # 新增：完成任務後提升心情
            if self.agent and hasattr(self.agent, 'profile'):
                old_mood = self.agent.profile.status.get("mood", 0)
                self.agent.profile.update_status("mood", 55)  # 完成任務，心情+5
                new_mood = self.agent.profile.status.get("mood", 0)
            
                # 添加狀態消息
                if hasattr(self.game, 'add_status_message'):
                    self.game.add_status_message(f"NPC完成任務: 心情+5 ({old_mood}->{new_mood})")
                    
                # 強制更新計劃，恢復日程表
                if self.agent and hasattr(self.agent, '_update_plan_based_on_time'):
                    self.agent._update_plan_based_on_time()
        
        return command_success
    
    def display_current_status(self):
        """顯示NPC當前狀態"""
        if not self.agent or not hasattr(self.agent, 'profile'):
            return
            
        status = self.agent.profile.status
        print(f"NPC當前狀態: 心情={status['mood']}, 健康={status['health']}")
        
        # 檢查是否有關鍵狀態需要提醒
        alerts = []
        if status['mood'] < 30:
            alerts.append("心情低")
        if status['health'] < 50:
            alerts.append("健康風險")
        
        if alerts:
            print(f"狀態警告: {', '.join(alerts)}")
    
    def handle_interaction(self, npc_id: str, object_name: str) -> bool:
        """
        Handle NPC interaction with objects and update status
        
        Args:
            npc_id: NPC's ID
            object_name: Interaction object name
                
        Returns:
            True if interaction was successfully processed, False otherwise
        """
        # Determine object type
        object_type = self._determine_object_type(object_name)
        
        # Get interaction effect
        if object_type in self.interaction_effects:
            status_changes, description = self.interaction_effects[object_type]
        else:
            # Use default effect
            status_changes, description = self.interaction_effects["default"]
        
        # Restrict the frequency of interaction effects
        current_time = time.time()
        last_interaction_time = getattr(self, 'last_interaction_times', {}).get(object_name, 0)
        interaction_cooldown = 2.0  # 2 seconds cooldown between same-object interactions

        # Initialize last_interaction_times if it doesn't exist
        if not hasattr(self, 'last_interaction_times'):
            self.last_interaction_times = {}

        # If the object was recently interacted with, don't apply the changes again
        if current_time - last_interaction_time < interaction_cooldown:
            print(f"Interaction with {object_name} is on cooldown. Skipping status updates.")
            return True

        # Initialize status_diff
        status_diff = {}
            
        # Modified status change processing
        if self.agent and hasattr(self.agent, 'profile'):
            # Record current status to calculate changes
            old_status = {key: value for key, value in self.agent.profile.status.items()}
            
            # Apply status changes - make sure to actually apply the changes!
            for status_type, change in status_changes.items():
                if status_type in self.agent.profile.status:
                    # Important: Actually modify the status!
                    # Special check for mood and health to not go below 20 or above 100
                    current_value = self.agent.profile.status[status_type]
                    
                    # If it's a negative change, don't let it go below 20
                    if change < 0 and current_value + change < 20:
                        new_value = 20
                        actual_change = 20 - current_value
                    # If it's a positive change, don't let it go above 100
                    elif change > 0 and current_value + change > 100:
                        new_value = 100
                        actual_change = 100 - current_value
                    else:
                        new_value = current_value + change
                        actual_change = change
                    
                    # Only update if there's a change
                    if actual_change != 0:
                        self.agent.profile.status[status_type] = new_value
                        print(f"Updated {status_type} by {actual_change}, new value: {new_value}")
            
            # Record this interaction time
            self.last_interaction_times[object_name] = current_time
            
            # Calculate status change difference
            for key in old_status:
                diff = self.agent.profile.status[key] - old_status[key]
                if diff != 0:
                    status_diff[key] = diff
            
            # Display status change
            self.handle_status_change(npc_id, object_name, status_diff, description)
            
            return True
        
        return False
    
    def handle_status_change(self, npc_id: str, object_name: str, status_diff: Dict[str, int], description: str = None) -> None:
        """
        處理並顯示狀態變化
        
        參數:
            npc_id: NPC的ID
            object_name: 互動物件名稱
            status_diff: 狀態變化字典 {"energy": +10, "hunger": -5, ...}
            description: 互動描述
        """
        if not description:
            description = f"與{object_name}互動"
            
        # 生成更改文本
        changes_text = []
        for status_type, change in status_diff.items():
            prefix = "+" if change > 0 else ""
            changes_text.append(f"{status_type}: {prefix}{change}")
        
        # 獲取當前狀態
        current_status = {}
        if self.agent and hasattr(self.agent, 'profile'):
            current_status = self.agent.profile.status
        
        # 簡潔方式顯示在控制台（與遊戲輸出風格匹配）
        print(f"NPC與{object_name}互動: {description}")
        print(f"狀態變化: {', '.join(changes_text)}")
        print(f"當前狀態: 心情={current_status.get('mood', 0)}, 健康={current_status.get('health', 0)}")
        
        # 記錄狀態變化歷史
        self._record_status_change(npc_id, object_name, status_diff)
        
        # 添加到遊戲狀態消息中（如果可用）
        if hasattr(self.game, 'add_status_message'):
            # 獲取當前遊戲時間
            time_str = ""
            if hasattr(self.game, 'game_time'):
                hour = self.game.game_time["hour"]
                minute = int(self.game.game_time["minute"])
                time_str = f"[{hour:02d}:{minute:02d}] "
            
            self.game.add_status_message(f"{time_str}NPC與{object_name}互動: {description}")
            self.game.add_status_message(f"狀態變化: {', '.join(changes_text)}")
            self.game.add_status_message(f"當前狀態: 心情={current_status.get('mood', 0)}")
    
    def _record_status_change(self, npc_id: str, object_name: str, status_diff: Dict[str, int]) -> None:
        """記錄狀態變化到歷史記錄"""
        # 創建狀態變化記錄
        timestamp = time.time()
        time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
        
        # 生成記錄文本
        changes_text = []
        for status_type, change in status_diff.items():
            prefix = "+" if change > 0 else ""
            changes_text.append(f"{status_type}: {prefix}{change}")
        
        record = f"[{time_str}] 與 {object_name} 互動: {', '.join(changes_text)}"
        
        # 添加到歷史記錄
        self.status_history.append(record)
        
        # 保持歷史記錄不超過最大數量
        if len(self.status_history) > self.max_history_items:
            self.status_history.pop(0)
    
    def _determine_object_type(self, object_name: str) -> str:
        """
        根據物件名稱確定其類型
        
        參數:
            object_name: 物件名稱
            
        返回:
            物件類型字符串
        """
        # 首先檢查是否直接匹配已知類型
        if object_name in self.interaction_effects:
            return object_name
        
        # 檢查TMX對象組
        if hasattr(self.game, 'tmx_data'):
            for obj_group in self.game.tmx_data.objectgroups:
                # 檢查組名匹配
                if obj_group.name.lower() == object_name.lower():
                    return obj_group.name.lower()
                
                # 檢查對象名匹配
                for obj in obj_group:
                    if hasattr(obj, 'name') and obj.name and obj.name.lower() == object_name.lower():
                        return obj_group.name.lower()
        
        # 根據名稱中的關鍵詞確定類型
        lower_name = object_name.lower()
        if "bed" in lower_name:
            return "bed"
        elif "sofa" in lower_name or "couch" in lower_name:
            return "sofa"
        elif "chair" in lower_name:
            return "chair"
        elif "refrigerator" in lower_name or "fridge" in lower_name or "ref" in lower_name:
            return "refrigerator"
        elif "food" in lower_name:
            return "food"
        elif "tv" in lower_name:
            return "tv"
        elif "book" in lower_name:
            return "bookshelf"
        elif "toilet" in lower_name:
            return "toilet"
        elif "shower" in lower_name:
            return "shower"
        elif "window" in lower_name:
            return "window"
        elif "door" in lower_name:
            return "door"
        
        # 默認類型
        return "default"
    
    def get_status_history(self, limit: int = None) -> List[str]:
        """
        獲取狀態變化歷史
        
        參數:
            limit: 返回的歷史記錄數量，None表示全部
            
        返回:
            狀態變化歷史的文本列表
        """
        if limit is not None:
            return self.status_history[-limit:]
        return self.status_history
    
    def register_interaction_effect(self, object_type: str, status_changes: Dict[str, int], description: str) -> None:
        """
        註冊新的互動效果
        
        參數:
            object_type: 物件類型
            status_changes: 狀態變化字典 {"energy": 10, "hunger": -5, ...}
            description: 互動效果描述
        """
        self.interaction_effects[object_type] = (status_changes, description)
        
    def trigger_time_based_behavior(self):
        """根據當前遊戲時間觸發特定行為，實現連貫的日程行為，考虑个体时间偏移"""
        if not self.game or not hasattr(self.game, 'game_time') or not self.agent:
            return False
                
        # 获取基础游戏时间
        base_hour = self.game.game_time["hour"]
        base_minute = int(self.game.game_time["minute"])
        
        # 应用个体时间偏移
        effective_hour = base_hour
        effective_minute = base_minute
        
        if hasattr(self.agent, 'schedule_offset') and self.agent.schedule_offset != 0:
            # 计算有效时间（加上偏移）
            total_minutes = base_hour * 60 + base_minute + self.agent.schedule_offset
            effective_hour = (total_minutes // 60) % 24
            effective_minute = total_minutes % 60
            
            # 调试输出偏移信息
            if hasattr(self.game, 'add_status_message') and self.debug_output:
                self.game.add_status_message(f"{self.npc_id}: 基础时间 {base_hour:02d}:{base_minute:02d}, 有效时间 {effective_hour:02d}:{effective_minute:02d} (偏移 {self.agent.schedule_offset}分钟)")

        has_player_task = False
        if hasattr(self.game, 'dialogue_system'):
            has_player_task = hasattr(self.game.dialogue_system, 'task_assigned') and self.game.dialogue_system.task_assigned
        
        # 如果有玩家任務，不觸發時間行為
        if has_player_task:
            if hasattr(self.game, 'add_status_message') and self.debug_output:
                self.game.add_status_message("存在玩家任務，跳過日程行為觸發")
            return False
        
        # 使用有效时间进行行为判断
        hour = effective_hour
        minute = effective_minute
        
        # 早上起床時間 (6點)
        if hour == 6:
            # 添加記憶
            self.agent.memory.add_memory("現在是早上6點，該起床開始新的一天了。", 0.7)
            
            # 按照日程表，預先計劃7點要去冰箱拿早餐
            for group_name, objects in self.map_objects.items():
                if group_name.lower() in ["bed", "bedroom", "床", "卧室"]:
                    self.commands_queue.append(("interact_with", group_name))  # 先與床互動（起床）
                    break
            
            if hasattr(self.game, 'add_status_message'):
                self.game.add_status_message(f"{self.npc_id}: 6点起床行为触发")
            
            return True
                
        # 早餐時間 (7點)
        elif hour == 7 and minute < 30:
            # 清空現有命令隊列
            self.commands_queue.clear()
            # 修改為使用冰箱拿食物
            self.agent.memory.add_memory("現在是早上7點，該準備早餐了。", 0.7)
            fridge_found = False
            table_found = False
            
            # 第一步：查找冰箱
            for group_name, objects in self.map_objects.items():
                if group_name.lower() in ["ref", "冰箱"]:
                    fridge_found = True
                    fridge_name = group_name
                    break
            
            # 第二步：查找桌子
            for group_name, objects in self.map_objects.items():
                if group_name.lower() in ["chair_in_fornt_of_desk", "chair", "椅子"]:
                    table_found = True
                    table_name = group_name
                    break
            
            # 構建完整行為序列：先去冰箱，拿食物，再去桌子
            if fridge_found:
                # 添加多個相同命令以提高優先級
                for _ in range(3):  # 添加三次相同命令以確保執行
                    self.commands_queue.append(("goto", fridge_name))
                self.commands_queue.append(("interact_with", fridge_name))
                
                # 如果找到了桌子，添加去桌子的指令（為8點做準備）
                if table_found:
                    self.commands_queue.append(("goto", table_name))
            elif table_found:
                # 如果沒找到冰箱但找到桌子，直接去桌子
                self.commands_queue.append(("goto", table_name))
            
            if hasattr(self.game, 'add_status_message'):
                self.game.add_status_message(f"{self.npc_id}: 7点早餐准备行为触发")
                
            return True
        
        # 早餐就餐時間 (8點)
        elif hour == 8:
            self.agent.memory.add_memory("現在是早上8點，該在桌子旁吃早餐了。", 0.7)
            table_found = False
            
            # 查找桌子
            for group_name, objects in self.map_objects.items():
                if group_name.lower() in ["chair_in_fornt_of_desk", "chair", "椅子"]:
                    table_found = True
                    self.commands_queue.append(("goto", group_name))
                    break
            
            # 無論是否找到桌子，都添加吃飯命令
            self.commands_queue.append(("eat", None))
            
            if hasattr(self.game, 'add_status_message'):
                self.game.add_status_message(f"{self.npc_id}: 8点早餐时间行为触发")
            
            return True
                
        # 日常活動時間 (10點)
        elif hour == 10:
            self.agent.memory.add_memory("現在是上午10點，應該在桌子旁活動。", 0.7)
            table_found = False
            
            # 查找桌子
            for group_name, objects in self.map_objects.items():
                if group_name.lower() in ["chair_in_fornt_of_desk", "chair", "椅子"]:
                    table_found = True
                    # 去桌子
                    self.commands_queue.append(("goto", group_name))
                    # 與桌子互動
                    self.commands_queue.append(("interact_with", group_name))
                    break
            
            if not table_found:
                # 如果沒找到桌子，添加隨機移動命令
                self.commands_queue.append(("random_move", None))
            
            if hasattr(self.game, 'add_status_message'):
                self.game.add_status_message(f"{self.npc_id}: 10点日常活动行为触发")
                
            return True
                
        # 午餐時間 (12點)
        elif hour == 12:
            self.agent.memory.add_memory("現在是中午12點，該準備午餐了。", 0.7)
            fridge_found = False
            table_found = False
            
            # 第一步：查找冰箱
            for group_name, objects in self.map_objects.items():
                if group_name.lower() in ["ref", "冰箱"]:
                    fridge_found = True
                    fridge_name = group_name
                    break
            
            # 第二步：查找桌子
            for group_name, objects in self.map_objects.items():
                if group_name.lower() in ["chair_in_fornt_of_desk", "chair", "椅子"]:
                    table_found = True
                    table_name = group_name
                    break
            
            # 構建完整行為序列
            if fridge_found:
                self.commands_queue.append(("goto", fridge_name))
                self.commands_queue.append(("interact_with", fridge_name))
                
                # 如果找到了桌子，添加去桌子的指令（為13點做準備）
                if table_found:
                    self.commands_queue.append(("goto", table_name))
            elif table_found:
                # 如果沒找到冰箱但找到桌子，直接去桌子
                self.commands_queue.append(("goto", table_name))
            
            if hasattr(self.game, 'add_status_message'):
                self.game.add_status_message(f"{self.npc_id}: 12点午餐准备行为触发")
            
            return True
                
        # 下午聊天時間 (13點-18點) - 关键修改
        elif 13 <= hour < 18:
            # 清空現有命令隊列，確保執行新命令
            self.commands_queue.clear()
            
            # 將優先級標記設置得非常高
            self.agent.memory.add_memory(f"現在是下午{hour}點，我必須去沙發上與其他NPC聊天，這非常重要。", 0.95)
            
            # 強制清除所有其他計劃
            if hasattr(self.agent, 'planning'):
                self.agent.planning.current_plan = []
            
            # 固定使用這個沙發名稱
            sofa_name = "sofa in fornt of TV"
            
            # 为不同的NPC分配不同的沙发位置
            if self.npc_id == "npc1":
                # NPC1去沙发的左侧位置
                self.commands_queue.append(("goto", sofa_name))
                # 到达后在附近位置休息，避免重复寻路
                for _ in range(3):
                    self.commands_queue.append(("rest", None))
            elif self.npc_id == "npc2":
                # NPC2去沙发，但添加延迟和不同的行为
                self.commands_queue.append(("goto", sofa_name))
                # 与沙发互动
                self.commands_queue.append(("interact_with", sofa_name))
                # 然后休息
                for _ in range(3):
                    self.commands_queue.append(("rest", None))
            
            if hasattr(self.game, 'add_status_message'):
                self.game.add_status_message(f"{self.npc_id}: {hour}点聊天时间行为触发 (有效时间)")
                
            return True
        
        # 其余时间段的处理保持原样，但都使用有效时间 hour 和 minute...
        # 晚餐就餐時間 (18點)
        elif hour == 18:
            self.agent.memory.add_memory("現在是晚上6點，該在桌子旁吃晚餐了。", 0.7)
            table_found = False
            
            # 查找桌子
            for group_name, objects in self.map_objects.items():
                if group_name.lower() in ["chair_in_fornt_of_desk", "chair", "椅子"]:
                    table_found = True
                    self.commands_queue.append(("goto", group_name))
                    break
            
            # 無論是否找到桌子，都添加吃飯命令
            self.commands_queue.append(("eat", None))
            
            if hasattr(self.game, 'add_status_message'):
                self.game.add_status_message(f"{self.npc_id}: 18点晚餐时间行为触发")
            
            return True
                
        # 睡覺時間 (22點)
        elif hour == 22:
            self.agent.memory.add_memory("現在是晚上10點，該去床上睡覺了。", 0.7)
            # 尋找床鋪
            bed_found = False
            for group_name, objects in self.map_objects.items():
                if group_name.lower() in ["bed", "bedroom", "床", "卧室"]:
                    bed_found = True
                    # 添加多個相同命令以提高優先級
                    for _ in range(3):  # 添加三次相同命令以確保執行
                        self.commands_queue.append(("goto", group_name))
                    # 與床互動
                    self.commands_queue.append(("interact_with", group_name))
                    # 休息
                    self.commands_queue.append(("rest", None))
                    break
            
            if not bed_found:
                # 如果沒找到床，隨機移動
                self.commands_queue.append(("random_move", None))
                
            if hasattr(self.game, 'add_status_message'):
                self.game.add_status_message(f"{self.npc_id}: 22点睡觉时间行为触发")
            
            return True
                
        # 睡眠狀態 (23點到早上7點)
        elif (23 <= hour or hour < 7):
            self.agent.memory.add_memory(f"現在是{hour}點，應該繼續睡覺。", 0.7)
            # 只添加休息命令，保持睡眠狀態
            self.commands_queue.append(("rest", None))
            
            if hasattr(self.game, 'add_status_message') and self.debug_output:
                self.game.add_status_message(f"{self.npc_id}: {hour}点睡眠状态")
            
            return True
                
        return False

    def get_nearby_objects(self):
        """获取NPC附近的物体列表，用于显示在UI上"""
        if not self.game or not self.game.npc_controller or self.npc_id not in self.game.npc_controller.npcs:
            return []
            
        npc = self.game.npc_controller.npcs[self.npc_id]  # 使用 self.npc_id
        grid_x = npc.grid_pos[0]
        grid_y = npc.grid_pos[1]
        
        nearby = []
        for group_name, objects in self.map_objects.items():
            for obj in objects:
                dist = abs(obj["x"] - grid_x) + abs(obj["y"] - grid_y)
                if dist < 8:  # 视线范围
                    obj_name = obj.get("name", group_name)
                    if not obj_name:  # 如果名称为None，使用默认名称
                        obj_name = f"{group_name}_{len(nearby)}"
                    direction = self._get_direction(grid_x, grid_y, obj["x"], obj["y"])
                    nearby.append(f"{obj_name}({direction})")
        
        return nearby
        
    def _get_direction(self, from_x, from_y, to_x, to_y):
        """获取从一点到另一点的方向描述"""
        dx = to_x - from_x
        dy = to_y - from_y
        
        if abs(dx) > abs(dy):
            return "东" if dx > 0 else "西"
        else:
            return "南" if dy > 0 else "北"