import os
import time
import random
from typing import List, Dict

# 從同目錄導入其他 AI 元件
from scripts.Agents.profile import Profile
from scripts.Agents.memory import Memory
from scripts.Agents.planning import Planning
from scripts.Agents.action import Action

class AIAgent:
    """主 AI 代理人類，整合所有模組。"""
    
    def __init__(self, name: str = "代理人", game_instance=None, schedule_offset=0, npc_id=None):
        """
        初始化 AI 代理人。
        
        參數:
            name: 代理人的名稱
            game_instance: 遊戲實例，包含TMX地圖
            schedule_offset: 日程表時間偏移（以分鐘為單位）
            npc_id: NPC的唯一標識符
        """
        # 存儲NPC ID
        self.npc_id = npc_id or name  # 如果沒有提供ID，使用名稱作為ID
        
        # 初始化個人資料
        self.profile = Profile(
            name=name,
            traits={
                "外向性": random.uniform(0.4, 0.8),
                "冒險性": random.uniform(0.5, 0.9),
                "盡責性": random.uniform(0.6, 0.9),
                "創造力": random.uniform(0.4, 0.8)
            },
            occupation="虛擬探索者",
            interests=["探索", "學習", "互動", "解謎"],
            background="我是一個居住在虛擬世界中的智能代理人，充滿好奇心和學習的渴望。"
        )
        
        # 初始化其他模組
        self.memory = Memory()
        self.game = game_instance
        self.planning = Planning(self.profile)
        self.action = Action(self.profile, self.memory, self.planning, self.game)
        
        # 存儲偏移量
        self.schedule_offset = schedule_offset
        
        # 創建更動態和靈活的日程安排
        self._generate_dynamic_schedule()
        
        # 添加更多樣化和具體的目標
        self._set_diverse_goals()
        
        # 初始化狀態追蹤
        self.run_count = 0
        self.consecutive_same_actions = 0
        self.last_action_type = None
    
    
    # In scripts/Agents/ai_agent.py
# Modify the _generate_dynamic_schedule method

        # 在scripts/Agents/ai_agent.py文件中
    def _generate_dynamic_schedule(self):
        """生成基于固定模式的日程表，每30分钟轮流去冰箱、沙发和床，并在特定时间段安排互相聊天"""
        # 检查是否已经生成过日程表
        if self.planning.daily_schedule:
            print(f"日程表已存在，跳过重复生成 for {getattr(self, 'npc_id', 'unknown')}")
            return
            
        # 清空现有日程安排
        self.planning.daily_schedule = {}
        
        # 从早上8點開始到晚上22點，每30分鐘輪流安排三種活動
        current_hour = 8
        current_minute = 0
        
        # 根据NPC ID设置完全不同的活动序列
        if hasattr(self, 'npc_id') and self.npc_id == "npc2":
            # NPC2的活动序列：床上休息 -> 沙发放松 -> 桌子工作
            activities = [
                "去床上休息",
                "去沙发上放松", 
                "在桌子旁工作"
            ]
            print(f"为 {self.npc_id} 设置特殊活动序列：床上休息 -> 沙发放松 -> 桌子工作")
        else:
            # NPC1的默认活动序列：冰箱互动 -> 床上休息 -> 沙发放松
            activities = [
                "去冰箱拿东西",
                "去床上休息",
                "去沙发上放松"
            ]
            print(f"为 {getattr(self, 'npc_id', 'npc1')} 设置默认活动序列：冰箱互动 -> 床上休息 -> 沙发放松")
        
        activity_index = 0
        
        # 生成循环日程表，直到22:00
        while current_hour < 22 or (current_hour == 22 and current_minute == 0):
            
            # 格式化时间字符串
            time_str = f"{current_hour:02d}:{current_minute:02d}"
            
            # 在13:00到18:00之间，根据NPC ID安排不同的聊天行为
            if 13 <= current_hour < 18:
                if hasattr(self, 'npc_id') and self.npc_id == "npc2":
                    self.planning.daily_schedule[time_str] = "在沙发上与NPC1聊天"
                else:
                    self.planning.daily_schedule[time_str] = "在沙发上与NPC2聊天"
            else:
                # 其他时间使用对应NPC的活动序列
                self.planning.daily_schedule[time_str] = activities[activity_index]
                # 更新活动索引，循环使用三种活动
                activity_index = (activity_index + 1) % len(activities)
            
            # 增加30分钟
            current_minute += 30
            if current_minute >= 60:
                current_minute -= 60
                current_hour += 1
        
        # 計算睡覺時間（22:00）
        sleep_hour = 22
        sleep_minute = 0
        
        # 添加晚上22:00的睡觉活动
        self.planning.daily_schedule[f"{sleep_hour:02d}:{sleep_minute:02d}"] = "去床上睡觉"
        
        # 添加深夜和凌晨的睡觉活动
        for hour in range(23, 24):
            self.planning.daily_schedule[f"{hour:02d}:00"] = "在床上睡觉"
            self.planning.daily_schedule[f"{hour:02d}:30"] = "在床上睡觉"
        
        for hour in range(0, 8):
            self.planning.daily_schedule[f"{hour:02d}:00"] = "在床上睡觉"
            self.planning.daily_schedule[f"{hour:02d}:30"] = "在床上睡觉"
        
        # 初始化時立即創建計劃，避免"無計劃"狀態
        self._create_initial_plan()
        
        # 根据NPC显示不同的日程表信息
        if hasattr(self, 'npc_id') and self.npc_id == "npc2":
            activity_sequence = "床上休息 -> 沙发放松 -> 桌子工作"
        else:
            activity_sequence = "冰箱互动 -> 床上休息 -> 沙发放松"
        
        print(f"已生成循环日程表 for {getattr(self, 'npc_id', 'npc1')}: {activity_sequence}，每30分钟轮换一次，13:00-18:00聊天时间，晚上{sleep_hour:02d}:{sleep_minute:02d}-早上08:00睡觉")
        
    def set_custom_schedule(self, schedule_config):
        """設置自定義日程表"""
        self.planning.daily_schedule = {}
        
        activities = schedule_config['activities']
        duration = schedule_config['activity_duration']
        start_hour = schedule_config['start_hour']
        end_hour = schedule_config['end_hour']
        sleep_hour = schedule_config['sleep_hour']
        
        # 應用偏移量
        if hasattr(self, 'schedule_offset'):
            start_hour = (start_hour + self.schedule_offset // 60) % 24
            end_hour = (end_hour + self.schedule_offset // 60) % 24
            sleep_hour = (sleep_hour + self.schedule_offset // 60) % 24
        
        current_hour = start_hour
        current_minute = self.schedule_offset % 60 if hasattr(self, 'schedule_offset') else 0
        activity_index = 0
        
        # 生成日程表
        while current_hour < end_hour or (current_hour == end_hour and current_minute == 0):
            time_str = f"{current_hour:02d}:{current_minute:02d}"
            self.planning.daily_schedule[time_str] = activities[activity_index]
            
            activity_index = (activity_index + 1) % len(activities)
            current_minute += duration
            
            if current_minute >= 60:
                current_minute -= 60
                current_hour += 1
        
        # 添加睡覺時間
        self.planning.daily_schedule[f"{sleep_hour:02d}:{current_minute:02d}"] = "去床上睡觉"
        
        # 初始創建計劃
        self._create_initial_plan()
    
    def _adjust_time(self, time_str: str, minutes: int) -> str:
        """調整時間"""
        hours, mins = map(int, time_str.split(':'))
        total_mins = hours * 60 + mins + minutes
        new_hours = (total_mins // 60) % 24
        new_mins = total_mins % 60
        return f"{new_hours:02d}:{new_mins:02d}"
    
    def _extract_location(self, activity):
        """从活动描述中提取位置信息"""
        if "冰箱" in activity:
            return "冰箱"
        elif "桌子" in activity or "工作" in activity:
            return "桌子"
        elif "沙发" in activity or "聊天" in activity:
            return "沙发"
        elif "床" in activity:
            return "床"
        return None

    def _create_initial_plan(self):
        """改进：创建初始计划，根据当前时间匹配日程表"""
        # 获取当前游戏时间
        current_time = None
        if hasattr(self.game, 'game_time'):
            hour = self.game.game_time["hour"]
            minute = int(self.game.game_time["minute"])
            current_time = f"{hour:02d}:{minute:02d}"
        
        if not current_time:
            # 如果无法获取当前时间，根据NPC ID创建默认计划
            if hasattr(self, 'npc_id') and self.npc_id == "npc2":
                default_plan = [
                    {"action": "去床上休息", "status": "pending"},
                    {"action": "去沙发上放松", "status": "pending"},
                    {"action": "在桌子旁工作", "status": "pending"}
                ]
            else:
                default_plan = [
                    {"action": "去冰箱拿东西", "status": "pending"},
                    {"action": "去床上休息", "status": "pending"},
                    {"action": "去沙发上放松", "status": "pending"}
                ]
            self.planning.current_plan = default_plan
            return
        
        # 找到当前时间段对应的活动
        current_activity = None
        next_activity = None
        next_time = None
        
        # 将日程表转为排序列表，便于查找
        schedule_items = sorted(self.planning.daily_schedule.items())
        
        # 找出当前活动和下一个活动
        for i, (time_str, activity) in enumerate(schedule_items):
            if time_str <= current_time:
                current_activity = activity
                # 查找下一个活动
                if i + 1 < len(schedule_items):
                    next_time, next_activity = schedule_items[i + 1]
        
        if current_activity:
            # 根据当前活动和下一个活动创建计划
            plan = [{"action": f"{current_activity}", "status": "pending"}]
            
            # 如果有下一个活动，预先计划
            if next_activity:
                # 提取当前活动和下一个活动的位置信息
                current_location = self._extract_location(current_activity)
                next_location = self._extract_location(next_activity)
                
                # 如果当前活动和下一个活动在不同位置，添加移动计划
                if current_location != next_location and next_location:
                    plan.append({"action": f"前往{next_location}", "status": "pending"})
                
                plan.append({"action": f"{next_activity}", "status": "pending"})
            
            self.planning.current_plan = plan
            
            # 添加调试信息
            print(f"[{getattr(self, 'npc_id', 'unknown')}] 创建计划基于当前活动: {current_activity}")
            
        else:
            # 根据NPC ID创建不同的默认计划
            if hasattr(self, 'npc_id') and self.npc_id == "npc2":
                default_plan = [
                    {"action": "去床上休息", "status": "pending"},
                    {"action": "去沙发上放松", "status": "pending"},
                    {"action": "在桌子旁工作", "status": "pending"}
                ]
            else:
                default_plan = [
                    {"action": "去冰箱拿东西", "status": "pending"},
                    {"action": "去床上休息", "status": "pending"},
                    {"action": "去沙发上放松", "status": "pending"}
                ]
            self.planning.current_plan = default_plan
            print(f"[{getattr(self, 'npc_id', 'unknown')}] 使用默认计划")
    
    def _set_diverse_goals(self):
        """修改：设置更具体和针对性的目标"""
        # 设置具体的、针对现有物体的目标，无探索相关目标
        goal_types = [
            ("short_term", [
                "完成玩家的任务",
                "建立日常生活规律"
            ]),
            ("medium_term", [
                "建立每日生活规律",
                "保持合理作息时间"
            ]),
            ("long_term", [
                "保持健康",
                "规律的生活节奏"
            ])
        ]
        
        # 使用固定优先级而非随机优先级
        for term, goals in goal_types:
            priority = 4  # 使用固定的高优先级
            for goal in goals:
                self.planning.add_goal(goal, term, priority)
        
    def run_step(self) -> str:
        """改进：运行代理人决策过程的单个步骤，确保计划与时间匹配"""
        # 增加运行计数
        self.run_count += 1
        
        # 根据当前时间更新计划
        self._update_plan_based_on_time()
        
        # 检查是否需要添加多样性
        if self.consecutive_same_actions > 3:
            self._inject_diversity()
        
        # 确保始终有计划
        if not self.planning.current_plan:
            self._create_initial_plan()
        
        # 决定采取什么动作
        action_type, parameters = self.action.decide_next_action()
        # 檢查是否在聊天時間段內
        in_chat_time = False
        if hasattr(self.game, 'game_time'):
            hour = self.game.game_time["hour"]
            if 13 <= hour < 18:
                in_chat_time = True
        
        # 如果在聊天時間內，且設定為NPC2，強制進行聊天行為
        if in_chat_time and self.npc_id == "npc2":
            # 創建一個固定的聊天行為計劃
            chat_plan = [{"action": "在沙发上聊天", "status": "pending"}]
            self.planning.current_plan = chat_plan
            # 跳過普通的決策過程
            return "NPC2在沙发上进行聊天"
        
        # 追踪连续相同动作
        if action_type == self.last_action_type:
            self.consecutive_same_actions += 1
        else:
            self.consecutive_same_actions = 0
        
        self.last_action_type = action_type
        
        # 获取代理人状态
        status = "站立"
        if action_type == "rest":
            status = "休息中"
        elif action_type == "eat":
            status = "进食中"
        
        # 显示当前计划 - 始终有计划可显示
        current_plan = "按日程活动"
        if self.planning.current_plan:
            next_step = next((step for step in self.planning.current_plan if step["status"] == "pending"), None)
            if next_step:
                current_plan = f"计划：{next_step['action']}"
        
        # 执行动作
        success, message = self.action.execute_action(action_type, parameters)
        
        # 根据动作更新代理人的状态
        self._update_status_from_action(action_type)
        
        # 如果动作成功且与当前计划相关，标记计划步骤为完成
        if success and self.planning.current_plan:
            self._update_plan_after_action(action_type, parameters, message)
        
        # 根据动作结果生成响应 - 简化输出
        response = f"{self.profile.name}【{status}】{current_plan} 决定{self._translate_action_type(action_type)}，{message}"
        return response
        

    def _update_plan_after_action(self, action_type, parameters, message):
        """根据执行的动作更新计划状态"""
        if not self.planning.current_plan:
            return
        
        next_step = next((step for step in self.planning.current_plan if step["status"] == "pending"), None)
        if not next_step:
            return
        
        # 检查动作是否完成了当前计划步骤
        action_completed_step = False
        
        # 吃饭动作可能完成"吃早餐/午餐/晚餐"计划
        if action_type == "eat" and ("吃" in next_step["action"]):
            action_completed_step = True
        
        # 移动动作可能完成"前往"计划
        elif action_type in ["goto", "move", "random_move"] and "前往" in next_step["action"]:
            location = self._extract_location(next_step["action"])
            if location and location.lower() in message.lower():
                action_completed_step = True
        
        # 互动动作可能完成特定互动计划
        elif action_type in ["interact", "interact_with"] and any(keyword in next_step["action"] for keyword in ["使用", "互动", "整理", "准备", "学习"]):
            action_completed_step = True
        
        # 休息动作可能完成"睡觉"计划
        elif action_type == "rest" and "睡" in next_step["action"]:
            action_completed_step = True
        
        # 如果动作完成了计划步骤，标记为完成并添加调试信息
        if action_completed_step:
            next_step["status"] = "completed"
            
            # 添加调试信息
            if hasattr(self.game, 'add_status_message'):
                self.game.add_status_message(f"完成计划：{next_step['action']}")
            
            # 如果所有计划步骤都完成，创建新计划
            if all(step["status"] == "completed" for step in self.planning.current_plan):
                self._create_initial_plan()

    def _inject_diversity(self):
        """注入行為多樣性，但移除探索相关行为"""
        # 隨機執行一些特殊動作或調整目標
        diversity_actions = [
            self._adjust_goals,
            self._reflect_on_experience
        ]
        # 隨機選擇一個多樣性方法
        random.choice(diversity_actions)()
    
    def _randomize_schedule(self):
        """隨機調整日程表"""
        current_schedule = self.planning.daily_schedule.copy()
        for time in list(current_schedule.keys()):
            if random.random() < 0.4:  # 40%概率調整
                new_activity = random.choice([
                    "探索", "思考", "休息", "學習", "互動", "創造"
                ])
                current_schedule[time] = new_activity
        
        self.planning.set_daily_schedule(current_schedule)
    
    def _adjust_goals(self):
        """調整或添加新目標，移除探索相关目标"""
        goal_types = ["short_term", "medium_term", "long_term"]
        goal_type = random.choice(goal_types)
        
        new_goals = [
            "制定更合理的饮食计划",
            "调整作息时间",
            "优化室内活动安排",
            "规划休息时间",
            "改善居家生活质量"
        ]
        
        new_goal = random.choice(new_goals)
        priority = random.randint(2, 5)
        
        self.planning.add_goal(new_goal, goal_type, priority)
    
    def _reflect_on_experience(self):
        """基於當前記憶進行反思"""
        recent_memories = self.memory.retrieve_relevant("最近經歷", limit=5)
        if recent_memories:
            reflection_topics = [
                "我的學習進展如何",
                "我遇到了哪些挑戰",
                "我如何改進我的探索策略"
            ]
            query = random.choice(reflection_topics)
            reflection = self.action._think(query)
            self.memory.add_memory(f"反思：{reflection}", 0.8)
    
    def _translate_action_type(self, action_type: str) -> str:
        """將動作類型翻譯成中文描述"""
        action_map = {
            "move": "移動",
            "interact": "互動",
            "examine": "觀察環境",
            "use_item": "使用物品",
            "rest": "休息",
            "eat": "進食",
            "think": "思考"
        }
        return action_map.get(action_type, action_type)
    
    def _update_status_from_action(self, action_type: str) -> None:
        """根據動作類型更新代理人的狀態"""
        # 不同的動作對狀態有不同的影響
        if action_type == "move":
            self.profile.update_status("mood", 5)
            
        elif action_type == "interact":
            self.profile.update_status("mood", 5)
            
        elif action_type == "think":
            self.profile.update_status("mood", 5)

    def _update_plan_based_on_time(self):
        """根据当前时间更新计划"""
        # 获取当前游戏时间
        if not hasattr(self.game, 'game_time'):
            return
        
        hour = self.game.game_time["hour"]
        minute = int(self.game.game_time["minute"])
        current_time = f"{hour:02d}:{minute:02d}"
        
        # 检查当前计划是否与时间匹配
        current_activity = None
        best_time = "00:00"
        
        # 查找最接近当前时间的活动
        for time_str, activity in sorted(self.planning.daily_schedule.items()):
            if time_str <= current_time and time_str >= best_time:
                best_time = time_str
                current_activity = activity
        
        # 检查当前计划是否需要更新
        should_update_plan = False
        
        if not self.planning.current_plan:
            should_update_plan = True
        else:
            # 检查当前计划中是否有匹配当前时间的活动
            current_plan_matches = False
            for step in self.planning.current_plan:
                if step["status"] == "pending" and step["action"] == current_activity:
                    current_plan_matches = True
                    break
            
            if not current_plan_matches:
                should_update_plan = True
        
        # 如果需要更新计划，创建新计划
        if should_update_plan and current_activity:
            self.planning.current_plan = [{"action": current_activity, "status": "pending"}]
            
            # 添加调试信息，显示NPC ID和更新后的计划
            npc_info = getattr(self, 'npc_id', 'unknown')
            print(f"[{npc_info}] 更新计划为：{current_activity} (时间: {current_time})")
            
            # 添加到游戏状态消息中
            if hasattr(self.game, 'add_status_message'):
                self.game.add_status_message(f"[{npc_info}] 更新计划为：{current_activity}")
        
        # 特殊处理聊天时间
        if (self.planning.current_plan and 
            any(step["action"] in ["在沙发上与NPC1聊天", "在沙发上与NPC2聊天", "在沙发上聊天"] 
                for step in self.planning.current_plan if step["status"] == "pending")):
            hour = self.game.game_time["hour"]
            if 13 <= hour < 18:
                # 保持当前聊天计划不变
                return
    
    def _force_update_plan_based_on_time(self):
        """强制根据当前时间更新计划"""
        # # 获取当前游戏时间
        # if not hasattr(self.game, 'game_time'):
        #     return
        
        # hour = self.game.game_time["hour"]
        # minute = int(self.game.game_time["minute"])
        # current_time = f"{hour:02d}:{minute:02d}"
        
        # # 直接按小时查找计划
        # hour_str = f"{hour:02d}:00"
        
        # # 查找最近的时间点
        # current_activity = None
        # best_time = "00:00"
        
        # for time_str, activity in sorted(self.planning.daily_schedule.items()):
        #     if time_str <= current_time and time_str >= best_time:
        #         best_time = time_str
        #         current_activity = activity
        
        # # 如果找到了当前时间的活动，强制更新计划
        # if current_activity:
        #     # 创建新计划，替换当前计划
        #     self.planning.current_plan = [{"action": current_activity, "status": "pending"}]
            
        #     # 添加调试信息
        #     if hasattr(self.game, 'add_status_message'):
        #         self.game.add_status_message(f"强制更新计划为：{current_activity}")
        

    def run_simulation(self, steps: int = 10, delay: float = 20.0) -> List[str]:
        """
        運行指定步數的模擬。
        
        參數:
            steps: 要運行的模擬步數
            delay: 步驟之間的延遲秒數
            
        返回:
            步驟描述的列表
        """
        results = []
        for _ in range(steps):
            result = self.run_step()
            results.append(result)
            print(result)
            
            # 每次行動後匯出記憶以便查看
            self.memory.export_memory("memory_export.json")
            
            time.sleep(delay)
        return results
    
    def save_state(self, directory: str = "agent_state") -> None:
        """
        將整個代理人狀態保存到文件。
        
        參數:
            directory: 保存狀態文件的目錄
        """
        # 如果目錄不存在則創建
        os.makedirs(directory, exist_ok=True)
        
        # 保存每個模組的狀態
        self.profile.save(os.path.join(directory, "profile.json"))
        self.memory.save(os.path.join(directory, "memory.json"))
        self.planning.save(os.path.join(directory, "planning.json"))
        self.action.save(os.path.join(directory, "action.json"))
        
        # 另外匯出記憶以便查看
        self.memory.export_memory(os.path.join(directory, "memory_export.json"))
        
        print(f"代理人狀態已保存到 {directory}")
    
    def load_state(self, directory: str = "agent_state") -> bool:
        """
        從文件加載整個代理人狀態。
        
        參數:
            directory: 包含狀態文件的目錄
            
        返回:
            成功則為 True，否則為 False
        """
        # 檢查目錄是否存在
        if not os.path.isdir(directory):
            print(f"目錄 {directory} 未找到。")
            return False
            
        try:
            # 加載每個模組的狀態
            self.profile = Profile.load(os.path.join(directory, "profile.json"))
            self.memory.load(os.path.join(directory, "memory.json"))
            self.planning.load(os.path.join(directory, "planning.json"))
            self.action.load(os.path.join(directory, "action.json"))
            
            # 重新連接模組
            self.planning.profile = self.profile
            self.action.profile = self.profile
            self.action.memory = self.memory
            self.action.planning = self.planning
            self.action.game = self.game
            
            print(f"已從 {directory} 加載代理人狀態")
            return True
            
        except Exception as e:
            print(f"加載代理人狀態時出錯: {e}")
            return False