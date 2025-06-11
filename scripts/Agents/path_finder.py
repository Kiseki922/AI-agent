import heapq
import random
from collections import deque

class EnhancedPathfinding:
    def __init__(self, grid):
        self.grid = grid
        self.width = len(grid[0])
        self.height = len(grid)
        # 只保留四向移動，移除對角線方向
        self.directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # 只有上下左右

    def is_valid(self, x, y):
        """檢查座標是否在網格範圍內且可通行"""
        return 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] == 0

    def get_neighbors(self, pos):
        """獲取指定位置的鄰居節點 - 只允許四向移動"""
        x, y = pos
        neighbors = []
        
        for dx, dy in self.directions:
            nx, ny = x + dx, y + dy
            if self.is_valid(nx, ny):
                neighbors.append((nx, ny))
        
        return neighbors

    def heuristic(self, a, b):
        """計算兩點之間的曼哈頓距離 - 適合四向移動"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def dfs(self, start, end, max_depth=1000):
        """使用深度優先搜索找尋路徑"""
        if not (self.is_valid(start[0], start[1]) and self.is_valid(end[0], end[1])):
            return []
            
        stack = [(start, [start])]
        visited = set([start])
        depth_count = 0
        
        while stack and depth_count < max_depth:
            (node, path) = stack.pop()
            depth_count += 1
            
            if node == end:
                return path
                
            # 獲取所有鄰居並按與目標的距離排序（啟發式改進）
            neighbors = self.get_neighbors(node)
            neighbors.sort(key=lambda n: self.heuristic(n, end))
            
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = path + [neighbor]
                    stack.append((neighbor, new_path))
                    
        # 如果DFS失敗，返回空路徑
        return []

    def bfs(self, start, end):
        """使用廣度優先搜索找尋最短路徑（Lee算法）"""
        if not (self.is_valid(start[0], start[1]) and self.is_valid(end[0], end[1])):
            return []
            
        queue = deque([(start, [start])])
        visited = set([start])
        
        while queue:
            (node, path) = queue.popleft()
            
            if node == end:
                return path
                
            for neighbor in self.get_neighbors(node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = path + [neighbor]
                    queue.append((neighbor, new_path))
                    
        # 如果BFS失敗，返回空路徑
        return []

    def bidirectional_bfs(self, start, end):
        """使用雙向BFS尋找路徑，從起點和終點同時開始搜索"""
        if not (self.is_valid(start[0], start[1]) and self.is_valid(end[0], end[1])):
            return []
            
        # 從起點開始的BFS
        start_queue = deque([start])
        start_visited = {start: None}  # 節點 -> 前一個節點
        
        # 從終點開始的BFS
        end_queue = deque([end])
        end_visited = {end: None}  # 節點 -> 前一個節點
        
        # 兩個BFS交會的點
        meeting_point = None
        
        while start_queue and end_queue and not meeting_point:
            # 從起點BFS擴展一步
            current = start_queue.popleft()
            for neighbor in self.get_neighbors(current):
                if neighbor not in start_visited:
                    start_visited[neighbor] = current
                    start_queue.append(neighbor)
                    
                    # 檢查是否與終點BFS相遇
                    if neighbor in end_visited:
                        meeting_point = neighbor
                        break
                        
            if meeting_point:
                break
                
            # 從終點BFS擴展一步
            current = end_queue.popleft()
            for neighbor in self.get_neighbors(current):
                if neighbor not in end_visited:
                    end_visited[neighbor] = current
                    end_queue.append(neighbor)
                    
                    # 檢查是否與起點BFS相遇
                    if neighbor in start_visited:
                        meeting_point = neighbor
                        break
        
        # 如果找到交會點，構建完整路徑
        if meeting_point:
            # 構建從起點到交會點的路徑
            path1 = []
            current = meeting_point
            while current:
                path1.append(current)
                current = start_visited[current]
            path1.reverse()
            
            # 構建從交會點到終點的路徑
            path2 = []
            current = end_visited[meeting_point]
            while current:
                path2.append(current)
                current = end_visited[current]
                
            # 合併路徑（不重複包含交會點）
            return path1 + path2
            
        return []

    def bfs_around_target(self, start, end, radius=2):
        """尋找終點周圍可達的點，而不是直接尋找終點"""
        if not (self.is_valid(start[0], start[1])):
            return []
            
        # 找出終點附近的所有有效點 - 只考慮四個方向
        target_area = []
        for dx, dy in self.directions:
            for i in range(1, radius + 1):
                nx, ny = end[0] + dx * i, end[1] + dy * i
                if self.is_valid(nx, ny):
                    target_area.append((nx, ny))
                    
        if not target_area:
            return []
            
        # 按照到終點的距離排序
        target_area.sort(key=lambda pos: self.heuristic(pos, end))
        
        # 嘗試尋找到最近的可達點的路徑
        for target in target_area:
            path = self.bfs(start, target)
            if path:
                return path
                
        return []

    def random_walk(self, start, end, max_attempts=1000):
        """使用隨機游走算法尋路，適合處理迷宮中的死路"""
        if not (self.is_valid(start[0], start[1]) and self.is_valid(end[0], end[1])):
            return []
            
        current = start
        path = [current]
        visited = set([current])
        attempts = 0
        
        while current != end and attempts < max_attempts:
            neighbors = self.get_neighbors(current)
            # 過濾掉已訪問的鄰居
            unvisited = [n for n in neighbors if n not in visited]
            
            if unvisited:
                # 根據與目標的距離為鄰居分配權重
                weights = [1.0 / (self.heuristic(n, end) + 1) for n in unvisited]
                total = sum(weights)
                weights = [w / total for w in weights]
                
                # 根據權重隨機選擇下一個節點
                next_node = random.choices(unvisited, weights=weights, k=1)[0]
                current = next_node
                path.append(current)
                visited.add(current)
            else:
                # 如果被卡住，回溯一步
                if len(path) > 1:
                    path.pop()
                    current = path[-1]
                    
            attempts += 1
            
        return path if current == end else []

    def find_path(self, start, end, method="auto"):
        """根據不同場景選擇最合適的路徑尋找方法"""
        # 檢查起點和終點是否合法
        if not (self.is_valid(start[0], start[1]) and self.is_valid(end[0], end[1])):
            return []
            
        # 計算起點和終點的曼哈頓距離
        distance = self.heuristic(start, end)
        
        # 根據距離選擇不同的方法
        if method == "auto":
            if distance < 10:  # 短距離使用BFS
                return self.bfs(start, end)
            elif distance < 20:  # 中等距離使用雙向BFS
                return self.bidirectional_bfs(start, end)
            else:  # 長距離使用BFS - 確保只用四向移動
                return self.bfs(start, end)
        elif method == "dfs":
            return self.dfs(start, end)
        elif method == "bfs":
            return self.bfs(start, end)
        elif method == "bidirectional":
            return self.bidirectional_bfs(start, end)
        elif method == "around_target":
            return self.bfs_around_target(start, end)
        elif method == "random_walk":
            return self.random_walk(start, end)
        else:
            return self.bfs(start, end)  # 默認使用BFS
        
    def debug_path_finding(self, start, end):
        """详细调试寻路过程"""
        print(f"寻路调试: 起点 {start}, 终点 {end}")
        
        # 检查起点和终点的有效性
        print(f"起点 {start} 是否可通行: {self.is_valid(start[0], start[1])}")
        print(f"终点 {end} 是否可通行: {self.is_valid(end[0], end[1])}")
        
        # 打印周围格子的状态
        print("起点周围格子:")
        for dx, dy in self.directions:
            nx, ny = start[0] + dx, start[1] + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                print(f"({nx},{ny}): {self.grid[ny][nx]}", end=" ")
        print()
        
        print("终点周围格子:")
        for dx, dy in self.directions:
            nx, ny = end[0] + dx, end[1] + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                print(f"({nx},{ny}): {self.grid[ny][nx]}", end=" ")
        print()
        
        # 尝试使用不同的寻路方法
        methods = [
            "bfs", 
            "bidirectional", 
            "around_target", 
            "random_walk"
        ]
        
        for method in methods:
            path = self.find_path(start, end, method)
            print(f"{method.upper()} 方法寻路结果长度: {len(path)}")