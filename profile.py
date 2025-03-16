import json
from typing import Dict, List, Optional

class Profile:
    """個人資料模組，負責存儲 AI 代理人的基本信息和個性特徵。"""
    
    def __init__(self, name: str, traits: Dict[str, float], occupation: str, 
                 interests: List[str], background: str, friends: List[Dict] = None):
        """
        初始化代理人的個人資料。
        
        參數:
            name: 代理人的名稱
            traits: 個性特徵的字典 (例如, {'外向性': 0.7})
            occupation: 代理人的職業或角色
            interests: 代理人的興趣列表
            background: 代理人的背景故事/歷史
            friends: 包含朋友信息的字典列表
        """
        self.name = name
        self.traits = traits
        self.occupation = occupation
        self.interests = interests
        self.background = background
        self.friends = friends or []
        self.status = {
            "hunger": 0,  # 0-100, 100 表示非常飢餓
            "energy": 100,  # 0-100, 0 表示精疲力竭
            "mood": 50,  # 0-100, 0 表示非常悲傷, 100 表示非常開心
            "health": 100  # 0-100, 0 表示非常生病
        }
        
    def update_status(self, status_type: str, value: int) -> None:
        """更新代理人的狀態值。"""
        if status_type in self.status:
            self.status[status_type] = max(0, min(100, self.status[status_type] + value))
    
    def get_personality_response(self, situation: str) -> float:
        """
        根據個性計算代理人對某種情況的反應。
        返回 0 到 1 之間的分數，表示積極回應的可能性。
        """
        # 基於個性的簡單決策制定
        # 較高的外向性意味著更可能參與社交場合
        if "社交" in situation or "聊天" in situation or "交談" in situation:
            return self.traits.get("外向性", 0.5)
        
        # 較高的冒險性意味著更可能嘗試新事物
        if "新" in situation or "風險" in situation or "冒險" in situation:
            return self.traits.get("冒險性", 0.5)
        
        # 默認為中性反應
        return 0.5
        
    def compatible_with_interest(self, activity: str) -> float:
        """檢查活動是否符合代理人的興趣。"""
        for interest in self.interests:
            if interest in activity:
                return 0.8
        return 0.2
    
    def to_dict(self) -> Dict:
        """將個人資料轉換為字典以便存儲。"""
        return {
            "name": self.name,
            "traits": self.traits,
            "occupation": self.occupation,
            "interests": self.interests,
            "background": self.background,
            "friends": self.friends,
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Profile':
        """從字典數據創建 Profile 實例。"""
        profile = cls(
            name=data["name"],
            traits=data["traits"],
            occupation=data["occupation"],
            interests=data["interests"],
            background=data["background"],
            friends=data.get("friends", [])
        )
        profile.status = data.get("status", profile.status)
        return profile
    
    def save(self, filename: str = "profile.json") -> None:
        """將個人資料保存到 JSON 文件。"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            
    @classmethod
    def load(cls, filename: str = "profile.json") -> 'Profile':
        """從 JSON 文件加載個人資料。"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except FileNotFoundError:
            print(f"個人資料文件 {filename} 未找到。創建新的個人資料。")
            return cls("代理人", {"外向性": 0.5, "冒險性": 0.5}, 
                      "學生", ["閱讀"], "默認背景")