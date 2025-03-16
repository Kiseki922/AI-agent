import json
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Set

# 常量
MAP_SIZE = 20

class Map:
    """地圖模組，將代理人的環境表示為二維網格。"""
    
    # 單元格類型常量
    EMPTY = 0
    WALL = 1
    CHAIR = 2
    DOOR_CLOSED = 3
    DOOR_OPEN = 4
    TABLE = 5
    BED = 6
    
    # 單元格類型名稱，用於顯示
    CELL_NAMES = {
        EMPTY: "空地",
        WALL: "牆壁",
        CHAIR: "椅子",
        DOOR_CLOSED: "門（關閉）",
        DOOR_OPEN: "門（開啟）",
        TABLE: "桌子",
        BED: "床"
    }
    
    # 地圖顯示字符
    DISPLAY_CHARS = {
        EMPTY: "·",
        WALL: "█",
        CHAIR: "椅",
        DOOR_CLOSED: "門",
        DOOR_OPEN: "╱",
        TABLE: "桌",
        BED: "床"
    }
    
    def __init__(self, size: int = MAP_SIZE):
        """
        初始化地圖。
        
        參數:
            size: 正方形網格的大小
        """
        self.size = size
        self.grid = np.zeros((size, size), dtype=int)
        self.agent_pos = (size // 2, size // 2)  # 從中間開始
        self.room_names = {}  # 將區域映射到房間名稱
    
    def set_cell(self, x: int, y: int, cell_type: int) -> bool:
        """
        將單元格設置為特定類型。
        
        參數:
            x, y: 單元格坐標
            cell_type: 要設置的單元格類型
            
        返回:
            如果成功則為 True，如果坐標無效則為 False
        """
        if 0 <= x < self.size and 0 <= y < self.size:
            self.grid[y, x] = cell_type
            return True
        return False
    
    def get_cell(self, x: int, y: int) -> int:
        """
        獲取單元格的類型。
        
        參數:
            x, y: 單元格坐標
            
        返回:
            單元格類型，如果坐標無效則為 -1
        """
        if 0 <= x < self.size and 0 <= y < self.size:
            return self.grid[y, x]
        return -1
    
    def is_walkable(self, x: int, y: int) -> bool:
        """檢查代理人是否可以走到特定單元格。"""
        cell_type = self.get_cell(x, y)
        return cell_type not in [self.WALL, self.DOOR_CLOSED, -1]
    
    def interact_with_cell(self, x: int, y: int) -> Tuple[bool, str]:
        """
        與給定坐標的單元格互動。
        
        參數:
            x, y: 單元格坐標
            
        返回:
            (成功, 消息) 的元組
        """
        cell_type = self.get_cell(x, y)
        
        if cell_type == self.DOOR_CLOSED:
            self.grid[y, x] = self.DOOR_OPEN
            return True, "你打開了門。"
            
        elif cell_type == self.DOOR_OPEN:
            self.grid[y, x] = self.DOOR_CLOSED
            return True, "你關上了門。"
            
        elif cell_type == self.CHAIR:
            return True, "你坐在椅子上。"
            
        elif cell_type == self.TABLE:
            return True, "你查看了桌子。"
            
        elif cell_type == self.BED:
            return True, "你在床上休息。"
            
        else:
            return False, "這裡沒有什麼有趣的互動物件。"
    
    def move_agent(self, direction: str) -> Tuple[bool, str]:
        """
        將代理人向某個方向移動。
        
        參數:
            direction: "north" (北), "south" (南), "east" (東), 或 "west" (西)
            
        返回:
            (成功, 消息) 的元組
        """
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
            
        new_x, new_y = new_pos
        
        if not (0 <= new_x < self.size and 0 <= new_y < self.size):
            return False, "你不能移動到地圖外。"
            
        if not self.is_walkable(new_x, new_y):
            cell_type = self.get_cell(new_x, new_y)
            if cell_type == self.DOOR_CLOSED:
                return False, "門是關著的。你需要先開門。"
            else:
                return False, "你不能走到那裡。"
                
        self.agent_pos = new_pos
        return True, f"你向{self._translate_direction(direction)}移動了。"
    
    def _translate_direction(self, direction: str) -> str:
        """將英文方向轉換為中文"""
        direction_map = {
            "north": "北",
            "south": "南",
            "east": "東",
            "west": "西"
        }
        return direction_map.get(direction, direction)
    
    def get_surroundings(self) -> str:
        """
        獲取代理人周圍環境的描述。
        
        返回:
            代理人周圍環境的文本描述
        """
        x, y = self.agent_pos
        surroundings = []
        
        # 檢查所有相鄰單元格
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                # 跳過中心單元格（代理人的位置）
                if dx == 0 and dy == 0:
                    continue
                    
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.size and 0 <= ny < self.size:
                    cell_type = self.grid[ny, nx]
                    if cell_type != self.EMPTY:
                        direction = self._get_direction_text(dx, dy)
                        surroundings.append(f"在{direction}方向有一個{self.CELL_NAMES[cell_type]}。")
        
        # 找出代理人所在的房間
        room_name = "未知區域"
        for region, name in self.room_names.items():
            if self._is_in_region(self.agent_pos, region):
                room_name = name
                break
                
        if not surroundings:
            return f"你位於{room_name}中。周圍沒有值得注意的東西。"
        else:
            return f"你位於{room_name}中。" + " ".join(surroundings)
    
    def _get_direction_text(self, dx: int, dy: int) -> str:
        """基於坐標變化獲取方向文本"""
        direction = ""
        if dy == -1:
            direction = "北"
        elif dy == 1:
            direction = "南"
            
        if dx == -1:
            direction += "西"
        elif dx == 1:
            direction += "東"
            
        return direction or "附近"
    
    def _is_in_region(self, pos: Tuple[int, int], region: Tuple[int, int, int, int]) -> bool:
        """檢查位置是否在由 (x1, y1, x2, y2) 定義的區域內。"""
        x, y = pos
        x1, y1, x2, y2 = region
        return x1 <= x <= x2 and y1 <= y <= y2
    
    def set_room(self, x1: int, y1: int, x2: int, y2: int, name: str) -> None:
        """
        在地圖上定義一個命名的房間區域。
        
        參數:
            x1, y1: 左上角坐標
            x2, y2: 右下角坐標
            name: 房間名稱
        """
        self.room_names[(x1, y1, x2, y2)] = name
    
    def create_house(self) -> None:
        """在地圖上創建一個預定義的房屋佈局。"""
        # 清除地圖
        self.grid.fill(self.EMPTY)
        
        # 建造外牆
        for x in range(self.size):
            self.set_cell(x, 0, self.WALL)  # 上牆
            self.set_cell(x, self.size-1, self.WALL)  # 下牆
            
        for y in range(self.size):
            self.set_cell(0, y, self.WALL)  # 左牆
            self.set_cell(self.size-1, y, self.WALL)  # 右牆
            
        # 建造內牆
        # 水平分隔
        for x in range(self.size):
            if x != self.size // 2:
                self.set_cell(x, self.size // 2, self.WALL)
            else:
                self.set_cell(x, self.size // 2, self.DOOR_CLOSED)
                
        # 上半部分的垂直分隔
        for y in range(0, self.size // 2):
            if y != self.size // 4:
                self.set_cell(self.size // 2, y, self.WALL)
            else:
                self.set_cell(self.size // 2, y, self.DOOR_CLOSED)
                
        # 定義房間
        self.set_room(1, 1, self.size//2-1, self.size//2-1, "臥室")
        self.set_room(self.size//2+1, 1, self.size-2, self.size//2-1, "浴室")
        self.set_room(1, self.size//2+1, self.size-2, self.size-2, "客廳")
        
        # 添加家具
        # 臥室
        self.set_cell(3, 3, self.BED)
        self.set_cell(5, 3, self.TABLE)
        
        # 浴室
        self.set_cell(self.size-4, 3, self.CHAIR)
        
        # 客廳
        self.set_cell(5, self.size-4, self.TABLE)
        self.set_cell(6, self.size-4, self.CHAIR)
        self.set_cell(4, self.size-4, self.CHAIR)
        self.set_cell(5, self.size-5, self.CHAIR)
        
        # 設置代理人位置
        self.agent_pos = (5, self.size-4)
    
    def display(self) -> str:
        """
        生成地圖的字符串表示。
        
        返回:
            帶有地圖可視化的字符串
        """
        display = ""
        for y in range(self.size):
            row = ""
            for x in range(self.size):
                if (x, y) == self.agent_pos:
                    row += "人"
                else:
                    cell_type = self.grid[y, x]
                    row += self.DISPLAY_CHARS.get(cell_type, "?")
            display += row + "\n"
        return display
    
    def to_dict(self) -> Dict:
        """將地圖轉換為字典以便存儲。"""
        return {
            "size": self.size,
            "grid": self.grid.tolist(),
            "agent_pos": self.agent_pos,
            "room_names": {str(k): v for k, v in self.room_names.items()}
        }
    
    def from_dict(self, data: Dict) -> None:
        """從字典數據加載地圖。"""
        self.size = data.get("size", MAP_SIZE)
        self.grid = np.array(data.get("grid", [[self.EMPTY] * self.size] * self.size))
        self.agent_pos = tuple(data.get("agent_pos", (self.size // 2, self.size // 2)))
        
        # 將房間名稱從字符串鍵轉換回元組鍵
        self.room_names = {}
        for k, v in data.get("room_names", {}).items():
            # 將元組的字符串表示轉換回實際元組
            # 例如: "(1, 2, 3, 4)" -> (1, 2, 3, 4)
            tuple_key = tuple(map(int, k.strip("()").split(", ")))
            self.room_names[tuple_key] = v
    
    def save(self, filename: str = "map.json") -> None:
        """將地圖保存到 JSON 文件。"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            
    def load(self, filename: str = "map.json") -> None:
        """從 JSON 文件加載地圖。"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.from_dict(data)
        except FileNotFoundError:
            print(f"地圖文件 {filename} 未找到。創建默認地圖。")
            self.create_house()