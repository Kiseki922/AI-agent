import os
import time
from typing import List, Dict

from profile import Profile
from memory import Memory
from planning import Planning
from map import Map
from action import Action

class AIAgent:
    """主 AI 代理人類，整合所有模組。"""
    
    def __init__(self, name: str = "代理人"):
        """
        初始化 AI 代理人。
        
        參數:
            name: 代理人的名稱
        """
        # 初始化個人資料
        self.profile = Profile(
            name=name,
            traits={"外向性": 0.6, "冒險性": 0.7, "盡責性": 0.8},
            occupation="學生",
            interests=["閱讀", "編程", "音樂"],
            background="我是一個居住在虛擬世界中的 AI 代理人。我很好奇並且渴望學習。"
        )
        
        # 初始化其他模組
        self.memory = Memory()
        self.map = Map()
        self.planning = Planning(self.profile)
        self.action = Action(self.profile, self.memory, self.planning, self.map)
        
        # 創建默認房屋地圖
        self.map.create_house()
        
        # 創建默認日程安排
        self.planning.set_daily_schedule({
            "08:00": "起床準備",
            "09:00": "吃早餐",
            "10:00": "學習編程",
            "12:00": "吃午餐",
            "13:00": "鍛煉",
            "15:00": "閱讀書籍",
            "18:00": "吃晚餐",
            "20:00": "自由時間",
            "22:00": "準備睡覺",
            "23:00": "睡覺"
        })
        
        # 添加一些初始目標
        self.planning.add_goal("學習更多關於 AI 的知識", "short_term", 3)
        self.planning.add_goal("提高編程技能", "medium_term", 4)
        self.planning.add_goal("開發個人項目", "long_term", 5)
    
    def run_step(self) -> str:
        """
        運行代理人決策過程的單個步驟。
        
        返回:
            描述代理人做了什麼的字符串
        """
        # 決定採取什麼動作
        action_type, parameters = self.action.decide_next_action()
        
        # 執行動作
        success, message = self.action.execute_action(action_type, parameters)
        
        # 根據動作更新代理人的狀態
        self._update_status_from_action(action_type)
        
        # 根據動作結果生成回應
        return f"{self.profile.name}決定{self._translate_action_type(action_type)}，{message}"
    
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
    
    def run_simulation(self, steps: int = 10, delay: float = 1.0) -> List[str]:
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
            print(self.map.display())
            
            # 每次行動後匯出記憶以便查看
            self.memory.export_memory("memory_export.json")
            
            time.sleep(delay)
        return results
    
    def _update_status_from_action(self, action_type: str) -> None:
        """根據動作類型更新代理人的狀態。"""
        # 不同的動作對狀態有不同的影響
        if action_type == "move":
            self.profile.update_status("energy", -2)
            self.profile.update_status("hunger", 1)
            
        elif action_type == "interact":
            self.profile.update_status("energy", -1)
            
        elif action_type == "examine":
            self.profile.update_status("energy", -1)
            
        elif action_type == "think":
            self.profile.update_status("energy", -3)
            self.profile.update_status("hunger", 1)
    
    def save_state(self, directory: str = "agent_state") -> None:
        """
        將整個代理人狀態保存到文件。
        
        參數:
            directory: 保存狀態文件的目錄
        """
        import os
        
        # 如果目錄不存在則創建
        os.makedirs(directory, exist_ok=True)
        
        # 保存每個模組的狀態
        self.profile.save(os.path.join(directory, "profile.json"))
        self.memory.save(os.path.join(directory, "memory.json"))
        self.planning.save(os.path.join(directory, "planning.json"))
        self.map.save(os.path.join(directory, "map.json"))
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
        import os
        
        # 檢查目錄是否存在
        if not os.path.isdir(directory):
            print(f"目錄 {directory} 未找到。")
            return False
            
        try:
            # 加載每個模組的狀態
            self.profile = Profile.load(os.path.join(directory, "profile.json"))
            self.memory.load(os.path.join(directory, "memory.json"))
            self.planning.load(os.path.join(directory, "planning.json"))
            self.map.load(os.path.join(directory, "map.json"))
            self.action.load(os.path.join(directory, "action.json"))
            
            # 重新連接模組
            self.planning.profile = self.profile
            self.action.profile = self.profile
            self.action.memory = self.memory
            self.action.planning = self.planning
            self.action.map = self.map
            
            print(f"已從 {directory} 加載代理人狀態")
            return True
            
        except Exception as e:
            print(f"加載代理人狀態時出錯: {e}")
            return False


if __name__ == "__main__":
    # 創建一個代理人
    agent = AIAgent("小明")
    
    # 運行模擬
    print("開始模擬...")
    agent.run_simulation(steps=10, delay=0.5)
    
    # 保存代理人的狀態
    agent.save_state()