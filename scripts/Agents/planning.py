import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any

from profile import Profile

class Planning:
    """規劃模組，用於代理人的計劃活動和目標。"""
    
    def __init__(self, agent_profile: Profile):
        """
        初始化規劃模組。
        
        參數:
            agent_profile: 代理人的個人資料實例
        """
        self.profile = agent_profile
        self.daily_schedule = {}  # 基於時間的計劃表
        self.current_plan = []    # 當前的動作序列
        self.goals = {            # 帶有優先級的長期目標
            "short_term": [],     # 短期可實現的目標
            "medium_term": [],    # 數天/週內可實現的目標
            "long_term": []       # 數月/年內可實現的目標
        }
        
    def set_daily_schedule(self, schedule: Dict[str, str]) -> None:
        """
        設置基於時間的日常計劃表。
        
        參數:
            schedule: 將時間字符串映射到活動的字典
                     例如，{"09:00": "早餐", "10:00": "學習"}
        """
        self.daily_schedule = schedule
    
    def add_goal(self, goal: str, timeframe: str, priority: int = 1) -> None:
        """
        向規劃系統添加新目標。
        
        參數:
            goal: 目標描述
            timeframe: "short_term", "medium_term", 或 "long_term"
            priority: 目標優先級 (1-5, 5 為最高)
        """
        if timeframe in self.goals:
            self.goals[timeframe].append({
                "description": goal,
                "priority": priority,
                "status": "pending",
                "created": datetime.now().isoformat()
            })
            
            # 按優先級排序目標
            self.goals[timeframe].sort(key=lambda x: x["priority"], reverse=True)
    
    def create_plan(self, goal: str) -> List[Dict]:
        """
        將目標分解為一系列動作。
        
        參數:
            goal: 要計劃的目標
            
        返回:
            計劃步驟的列表
        """
        # 為大語言模型創建提示以生成計劃
        prompt = f"""
        目標: {goal}
        
        創建一個達成這個目標的逐步計劃。將其分解為可執行的步驟。
        對於每個步驟，提供:
        1. 動作的簡要描述
        2. 需要的任何先決條件
        3. 如何驗證完成情況
        
        按以下格式提供每個步驟: 步驟編號. 動作描述 | 先決條件 | 驗證
        """
        
        try:
            # 使用 DeepSeek API 生成計劃
            plan_text = self._generate_text(prompt)
            
            # 解析生成的計劃
            plan_steps = []
            for line in plan_text.strip().split('\n'):
                if not line.strip() or '步驟' not in line.lower():
                    continue
                    
                parts = line.split('|')
                if len(parts) >= 1:
                    step = {
                        "action": parts[0].strip().split('.', 1)[-1].strip(),
                        "prerequisites": parts[1].strip() if len(parts) > 1 else "",
                        "verification": parts[2].strip() if len(parts) > 2 else "",
                        "status": "pending"
                    }
                    plan_steps.append(step)
            
            self.current_plan = plan_steps
            return plan_steps
            
        except Exception as e:
            print(f"生成計劃失敗: {e}")
            # 備用方案: 創建一個簡單的三步計劃
            fallback_plan = [
                {"action": f"研究關於 {goal}", "status": "pending"},
                {"action": f"收集 {goal} 的資源", "status": "pending"},
                {"action": f"執行 {goal}", "status": "pending"}
            ]
            self.current_plan = fallback_plan
            return fallback_plan
    
    def get_current_activity(self) -> Optional[str]:
        """
        獲取當前時間安排的活動。
        
        返回:
            當前安排的活動或者如果沒有安排則返回 None
        """
        if not self.daily_schedule:
            return None
            
        current_time = datetime.now().strftime("%H:%M")
        
        # 找到最近安排的活動
        scheduled_times = sorted(self.daily_schedule.keys())
        current_activity = None
        
        for time_str in scheduled_times:
            if time_str <= current_time:
                current_activity = self.daily_schedule[time_str]
            else:
                break
                
        return current_activity
    
    def adjust_plan(self, unexpected_event: str) -> None:
        """
        當出現意外事件時調整當前計劃。
        
        參數:
            unexpected_event: 意外事件的描述
        """
        if not self.current_plan:
            return
            
        # 為大語言模型生成一個提示以調整計劃
        current_plan_text = "\n".join([f"- {step['action']} ({step['status']})" 
                                     for step in self.current_plan])
        
        prompt = f"""
        當前計劃:
        {current_plan_text}
        
        意外事件: {unexpected_event}
        
        應該如何調整計劃以應對這個意外事件？
        提供一個修訂的逐步計劃。
        """
        
        try:
            # 使用 DeepSeek API 生成調整後的計劃
            adjusted_plan_text = self._generate_text(prompt)
            
            # 解析調整後的計劃
            adjusted_steps = []
            for line in adjusted_plan_text.strip().split('\n'):
                if line.strip() and ('-' in line or '.' in line):
                    # 從行中提取動作
                    action = line.split('-', 1)[-1].strip() if '-' in line else line.split('.', 1)[-1].strip()
                    adjusted_steps.append({
                        "action": action,
                        "status": "pending"
                    })
            
            # 更新當前計劃
            self.current_plan = adjusted_steps
            
        except Exception as e:
            print(f"調整計劃失敗: {e}")
            # 添加一個處理意外事件的步驟
            self.current_plan.insert(0, {
                "action": f"處理意外事件: {unexpected_event}",
                "status": "pending"
            })
    
    def mark_step_complete(self, step_index: int) -> None:
        """將當前計劃中的一個步驟標記為完成。"""
        if 0 <= step_index < len(self.current_plan):
            self.current_plan[step_index]["status"] = "completed"
    
    def _generate_text(self, prompt: str) -> str:
        """使用 DeepSeek API 生成文本。"""
        payload = {
            "model": "deepseek-r1-distill-qwen-7b",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post("http://127.0.0.1:1234/v1/chat/completions", json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"API 請求失敗: {e}")
            return "目前無法生成計劃。"
    
    def to_dict(self) -> Dict:
        """將規劃數據轉換為字典以便存儲。"""
        return {
            "daily_schedule": self.daily_schedule,
            "current_plan": self.current_plan,
            "goals": self.goals
        }
    
    def from_dict(self, data: Dict) -> None:
        """從字典加載規劃數據。"""
        self.daily_schedule = data.get("daily_schedule", {})
        self.current_plan = data.get("current_plan", [])
        self.goals = data.get("goals", {
            "short_term": [],
            "medium_term": [],
            "long_term": []
        })
    
    def save(self, filename: str = "planning.json") -> None:
        """將規劃數據保存到 JSON 文件。"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            
    def load(self, filename: str = "planning.json") -> None:
        """從 JSON 文件加載規劃數據。"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.from_dict(data)
        except FileNotFoundError:
            print(f"規劃文件 {filename} 未找到。從空規劃開始。")