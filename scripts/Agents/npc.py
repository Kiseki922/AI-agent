import pygame
import time
from scripts.Agents.path_finder import EnhancedPathfinding

class NPC(pygame.sprite.Sprite):
    def __init__(self, game, entity_type, position, size, speed=1):
        super().__init__(game.sprite_group)
        self.game = game
        self.entity_type = entity_type
        
        # 設置 NPC 圖像和位置
        self.image = game.assets[entity_type]
        
        # 計算網格位置
        self.grid_size = size
        self.grid_pos = [position[0] // size[0], position[1] // size[1]]
        self.pos = [self.grid_pos[0] * size[0], self.grid_pos[1] * size[1]]
        
        self.rect = self.image.get_rect(topleft=self.pos)
        self.hitbox = self.rect.copy().inflate((-30, -30))  # 碰撞箱略小於圖像
        
        self.size = size
        self.speed = speed  # 此處的速度表示每次更新移動的格子數，應該保持為1
        
        # 設置尋路系統
        self.pathfinder = None  # 將在遊戲加載地圖後初始化
        self.path = []  # 存儲 NPC 將要遵循的路徑
        self.current_target = None
        self.moving = False
        self.stuck_counter = 0  # 用於檢測NPC是否卡住
        
        # 移動方向枚舉 - 只允許四個方向
        self.DIRECTION_UP = 0
        self.DIRECTION_DOWN = 1
        self.DIRECTION_LEFT = 2
        self.DIRECTION_RIGHT = 3
        
        # 當前移動方向
        self.direction = 'down'  # 預設方向
        
        # 移動冷卻時間
        self.move_cooldown = 0
        self.move_cooldown_time = 15  # 移動間隔的幀數
        
        # 動畫相關
        self.animation_timer = 0
        self.animation_speed = 0.1  # 動畫幀率調整
        
        # 互動狀態
        self.interacting = False
        self.interaction_target = None
        self.interaction_timer = 0
        self.interaction_duration = 2.0  # 互動持續時間（秒）
        
        # 上次執行動作的時間戳
        self.last_action_time = time.time()
        self.action_cooldown = 1.0  # 動作冷卻時間（秒）

        # 添加步数跟踪变量
        self.steps_taken = 0
        self.steps_threshold = 5  # 每走5步触发一次状态变化
        self.last_position = self.grid_pos.copy()  # 记录上一次位置
    
    def initialize_pathfinder(self, grid):
        """初始化尋路系統，需要在地圖加載後調用"""
        self.pathfinder = EnhancedPathfinding(grid)
    
    def set_target_by_name(self, object_name):
        """Set target position by object name"""
        # 檢查 object_name 是否為有效值
        if not object_name:  # 如果是 None 或空字符串
            print("Cannot find target: empty object name")
            return False
            
        # 在 TMX 資料中尋找指定名稱的對象
        target_pos = None
        found_objects = []
        
        # 先記錄要找的物件名稱
        print(f"Searching for object named: '{object_name}'")
        
        # 首先檢查 AI bridge 中的已知物件
        if hasattr(self.game, 'ai_bridge') and self.game.ai_bridge:
            for group_name, objects in self.game.ai_bridge.map_objects.items():
                for obj in objects:
                    if obj["name"].lower() == object_name.lower():
                        found_objects.append((obj["x"], obj["y"]))
                        print(f"Found object in AI bridge mapping: {obj['name']} at ({obj['x']},{obj['y']})")
                    
            if found_objects:
                # 找到目標物體列表後，選擇最近的一個
                current_x = self.grid_pos[0]
                current_y = self.grid_pos[1]
                closest_obj = min(found_objects, 
                                key=lambda pos: ((pos[0]-current_x)**2 + (pos[1]-current_y)**2))
                target_pos = closest_obj
                print(f"Selected nearest object position: {target_pos}")
        
        # 如果在 AI bridge 中沒找到，再直接從 TMX 資料中尋找
        if not target_pos:
            # 首先尝试找到名称匹配的对象组
            for obj_group in self.game.tmx_data.objectgroups:
                if obj_group.name and obj_group.name.lower() == object_name.lower():
                    # 找到匹配的对象组，遍历其中的对象
                    print(f"Found matching object group: {obj_group.name}")
                    idx = 0
                    for obj in obj_group:  # 直接遍历对象组
                        # 转换为网格坐标
                        grid_x = int(obj.x / self.size[0])
                        grid_y = int(obj.y / self.size[1])
                        obj_name = getattr(obj, 'name', f"{obj_group.name}_{idx}")
                        found_objects.append((grid_x, grid_y))
                        print(f"Found object in group: {obj_name} at ({grid_x},{grid_y})")
                        idx += 1
                        
                    if found_objects:
                        # 找到目標物體列表後，選擇最近的一個
                        current_x = self.grid_pos[0]
                        current_y = self.grid_pos[1]
                        closest_obj = min(found_objects, 
                                        key=lambda pos: ((pos[0]-current_x)**2 + (pos[1]-current_y)**2))
                        target_pos = closest_obj
                        print(f"Selected nearest object position: {target_pos}")
                    break
        
        # 如果沒找到匹配的對象組，尝试在所有对象中查找匹配名称的对象
        if not target_pos:
            for obj_group in self.game.tmx_data.objectgroups:
                idx = 0
                for obj in obj_group:
                    # 获取或生成物体名称
                    if hasattr(obj, 'name') and obj.name:
                        obj_name = obj.name
                    else:
                        obj_name = f"{obj_group.name}_{idx}"
                        idx += 1
                        
                    if obj_name.lower() == object_name.lower():
                        # 转换为网格坐标
                        grid_x = int(obj.x / self.size[0])
                        grid_y = int(obj.y / self.size[1])
                        target_pos = (grid_x, grid_y)
                        print(f"Found object by name: {obj_name} at ({grid_x},{grid_y})")
                        break
                if target_pos:
                    break
        
        if target_pos:
            self.set_target(target_pos)
            # 設置互動目標
            self.interaction_target = object_name
            return True
            
        print(f"Could not find object named '{object_name}'")
        return False
    
    def set_target_by_tile(self, layer_name, tile_x, tile_y):
        """根據圖層名稱和瓦片座標設置目標位置"""
        # 確認該層和座標存在
        for layer in self.game.tmx_data.visible_layers:
            if hasattr(layer, 'data') and layer.name.lower() == layer_name.lower():
                if 0 <= tile_x < layer.width and 0 <= tile_y < layer.height:
                    # 確認目標是有效的，然後設定目標
                    self.set_target((tile_x, tile_y))
                    return True
        return False
    
    def set_target(self, target_pos):
        if not self.pathfinder:
            print("Error: Pathfinder not initialized")
            return
        
        # 如果當前正在互動，則終止互動
        self.stop_interaction()
        
        # 檢查是否冷卻中
        current_time = time.time()
        if current_time - self.last_action_time < self.action_cooldown:
            return
        
        self.last_action_time = current_time
        self.current_target = target_pos
        current_x = self.grid_pos[0]
        current_y = self.grid_pos[1]
        current_pos = (current_x, current_y)
        
        # 添加调试信息
        self.pathfinder.debug_path_finding(current_pos, target_pos)
        
        # 修改為僅使用四向路徑
        self.path = self.pathfinder.find_path(current_pos, target_pos, method="bfs")
        self.moving = bool(self.path)
        self.stuck_counter = 0
    
    def stop_interaction(self):
        """停止當前互動"""
        if self.interacting:
            self.interacting = False
            self.interaction_target = None
            self.interaction_timer = 0
    
    def interact_with_current_target(self):
        """Interact with current target"""
        # 檢查是否有交互目標，如果沒有則使用當前位置
        if not self.interaction_target:
            # 使用當前位置作為交互目標
            current_x = self.grid_pos[0]
            current_y = self.grid_pos[1]
            self.interaction_target = f"position_{current_x}_{current_y}"
            print(f"No interaction target set, using current position: {self.interaction_target}")
        
        # 檢查是否已到達目標附近
        current_x = self.grid_pos[0]
        current_y = self.grid_pos[1]
        
        # 檢查附近是否有交互目標 (如果目標是位置標記，則跳過此檢查)
        found_target = False
        if not self.interaction_target.startswith("position_"):
            # 只檢查上下左右四個相鄰格子
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            for dx, dy in directions:
                objects = self._get_objects_at_position(current_x + dx, current_y + dy)
                if objects and self.interaction_target in objects:
                    found_target = True
                    break
        else:
            # 如果是位置標記，則直接認為已找到目標
            found_target = True
        
        # 如果未到達目標附近，嘗試移動到目標
        if not found_target and not self.interaction_target.startswith("position_"):
            # 先尝试通过名称设置目标 (只對非位置標記類型的目標)
            result = self.set_target_by_name(self.interaction_target)
            if result:
                print(f"NPC not near {self.interaction_target}, attempting to move to target")
            else:
                print(f"Cannot find path to {self.interaction_target}")
            return False
            
        print(f"NPC starts interacting with {self.interaction_target}")
        self.interacting = True
        self.interaction_timer = time.time()
        
        # 如果游戏中有时间系统，添加交互状态消息
        if hasattr(self.game, 'add_status_message'):
            current_time = ""
            if hasattr(self.game, 'game_time'):
                h = self.game.game_time["hour"]
                m = int(self.game.game_time["minute"])
                current_time = f"[{h:02d}:{m:02d}] "
            
            self.game.add_status_message(f"{current_time}NPC is interacting with {self.interaction_target}...")
        
        return True
    
    def try_move(self, direction):
        # 设置移动冷却
        self.move_cooldown = self.move_cooldown_time
        
        # 保存当前网格位置
        old_grid_pos = self.grid_pos.copy()
        
        # 根据方向计算新的网格位置
        if direction == self.DIRECTION_UP:
            new_grid_pos = [self.grid_pos[0], self.grid_pos[1] - 1]
        elif direction == self.DIRECTION_DOWN:
            new_grid_pos = [self.grid_pos[0], self.grid_pos[1] + 1]
        elif direction == self.DIRECTION_LEFT:
            new_grid_pos = [self.grid_pos[0] - 1, self.grid_pos[1]]
        elif direction == self.DIRECTION_RIGHT:
            new_grid_pos = [self.grid_pos[0] + 1, self.grid_pos[1]]
        else:
            return False
            
        # 更新方向
        self.current_direction = direction
        
        # 计算新的像素位置
        new_pos = [new_grid_pos[0] * self.size[0], new_grid_pos[1] * self.size[1]]
        
        # 暂时更新位置和碰撞盒
        self.grid_pos = new_grid_pos
        self.pos = new_pos
        self.hitbox.topleft = self.pos
        self.rect.topleft = self.pos
        
        # 检查碰撞
        if self.check_collision():
            # 如果碰撞，恢复原位置
            self.grid_pos = old_grid_pos
            self.pos = [old_grid_pos[0] * self.size[0], old_grid_pos[1] * self.size[1]]
            self.hitbox.topleft = self.pos
            self.rect.topleft = self.pos
            return False
        
        # 如果成功移动，增加步数计数器
        self.steps_taken += 1
        
        # 检查是否达到步数阈值，每走5步触发一次状态变化
        if self.steps_taken >= self.steps_threshold:
            self.steps_taken = 0  # 重置步数计数器
            
            # 更新NPC状态 - 通过ai_bridge访问agent的profile
            if hasattr(self.game, 'ai_bridge') and self.game.ai_bridge and hasattr(self.game.ai_bridge, 'agent'):
                agent = self.game.ai_bridge.agent
                if hasattr(agent, 'profile'):
                    # 每走5格，健康-1，心情-0.5
                    agent.profile.update_status("health", -1)
                    agent.profile.update_status("mood", -1)  # 因为mood只能是整数，所以这里用-1代替-0.5
                    
                    # 添加状态消息
                    if hasattr(self.game, 'add_status_message'):
                        self.game.add_status_message("NPC走动中: 健康-1, 心情-1")
        
        return True

    def _get_objects_at_position(self, grid_x, grid_y):
        """Get objects at the specified grid position"""
        objects = []
        if hasattr(self.game, 'tmx_data'):
            for obj_group in self.game.tmx_data.objectgroups:
                group_name = obj_group.name  # 保存组名
                obj_index = 0  # 添加索引计数器
                
                for obj in obj_group:
                    obj_x = int(obj.x / 32)
                    obj_y = int(obj.y / 32)
                    # 考虑物体大小
                    width = max(1, int(getattr(obj, 'width', 32) / 32))
                    height = max(1, int(getattr(obj, 'height', 32) / 32))
                    
                    # 检查物体是否覆盖指定位置
                    if obj_x <= grid_x < obj_x + width and obj_y <= grid_y < obj_y + height:
                        # 使用 name 属性，如果没有则使用组名+索引
                        if hasattr(obj, 'name') and obj.name:
                            obj_name = obj.name
                        else:
                            obj_name = f"{group_name}_{obj_index}"
                        
                        objects.append(obj_name)
                    obj_index += 1
        
        return objects
    
    def update_direction(self, dx, dy):
        """根據移動方向更新NPC的朝向 - 只允許四个基本方向"""
        if dx > 0:
            self.direction = 'right'
        elif dx < 0:
            self.direction = 'left'
        elif dy > 0:
            self.direction = 'down'
        elif dy < 0:
            self.direction = 'up'
    
    def update(self):
        """更新 NPC 的位置和互動狀態"""
        # 檢查是否正在互動
        if self.interacting:
            # 如果互動時間已超過持續時間，結束互動
            if time.time() - self.interaction_timer > self.interaction_duration:
                self.interacting = False
                self.interaction_target = None
                print("NPC 完成互動")
            return
        
        # 如果未移動則無需更新
        if not self.moving or not self.path:
            return
            
        # 減少移動冷卻計時器
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
            return
        
        # 檢查是否卡住
        if self.stuck_counter > 5:  # 降低卡住檢測閾值
            print("NPC 可能卡住了，嘗試重新計算路徑")
            self.recalculate_path()
            self.stuck_counter = 0
            return
            
        # 沿著路徑移動 - 一次只移動一格
        if self.path:
            next_node = self.path[0]
            
            # 計算移動方向 (只水平或垂直移動)
            dx = next_node[0] - self.grid_pos[0]
            dy = next_node[1] - self.grid_pos[1]
            
            # 確保一次只移動一格
            if dx != 0 and dy != 0:
                # 如果是對角線移動，優先水平移動
                dy = 0
            
            # 限制每次只移動一格
            if dx > 0: dx = 1
            elif dx < 0: dx = -1
            if dy > 0: dy = 1
            elif dy < 0: dy = -1
            
            # 更新方向
            self.update_direction(dx, dy)
            
            # 儲存舊位置以檢測碰撞
            old_grid_pos = self.grid_pos.copy()
            
            # 設置移動冷卻
            self.move_cooldown = self.move_cooldown_time
            
            # 更新網格位置
            self.grid_pos[0] += dx
            self.grid_pos[1] += dy
            
            # 更新像素位置
            self.pos[0] = self.grid_pos[0] * self.size[0]
            self.pos[1] = self.grid_pos[1] * self.size[1]
            
            # 更新碰撞箱和矩形位置
            self.hitbox.topleft = self.pos
            self.rect.topleft = self.pos
            
            # 如果成功移动，增加步数计数器
            self.steps_taken += 1
            
            # 检查是否达到步数阈值，并且冷却时间已过期
            current_time = time.time()
            npc_id = None
            
            # 确定当前NPC的ID
            for id, npc in self.game.npc_controller.npcs.items():
                if npc == self:
                    npc_id = id
                    break
            
            if npc_id and self.steps_taken >= self.steps_threshold:
                # 检查移动状态更新的冷却时间
                if current_time - self.game.movement_status_cooldown.get(npc_id, 0) >= self.game.movement_status_interval:
                    self.steps_taken = 0  # 重置步数计数器
                    
                    # 确定正确的AI Bridge
                    ai_bridge = None
                    if npc_id == "npc1" and hasattr(self.game, 'ai_bridge'):
                        ai_bridge = self.game.ai_bridge
                    elif npc_id == "npc2" and hasattr(self.game, 'ai_bridge2'):
                        ai_bridge = self.game.ai_bridge2
                    
                    # 更新NPC状态
                    if ai_bridge and hasattr(ai_bridge, 'agent') and hasattr(ai_bridge.agent, 'profile'):
                        agent = ai_bridge.agent
                        old_health = agent.profile.status.get("health", 0)
                        old_mood = agent.profile.status.get("mood", 0)
                        
                        # 每走5格，健康-1，心情-1，但不超过最小值
                        if old_health > 10:  # 保证健康不低于10
                            agent.profile.update_status("health", -1)
                        if old_mood > 10:     # 保证心情不低于10
                            agent.profile.update_status("mood", -1)
                        
                        # 更新冷却时间
                        self.game.movement_status_cooldown[npc_id] = current_time
                        
                        # 添加状态消息
                        if hasattr(self.game, 'add_status_message'):
                            new_health = agent.profile.status.get("health", 0)
                            new_mood = agent.profile.status.get("mood", 0)
                            self.game.add_status_message(f"{npc_id}走动: 健康: {old_health}->{new_health}, 心情: {old_mood}->{new_mood}")

            # 檢查碰撞
            if self.check_collision():
                # 如果碰撞，恢復原位置
                self.grid_pos = old_grid_pos.copy()
                self.pos[0] = self.grid_pos[0] * self.size[0]
                self.pos[1] = self.grid_pos[1] * self.size[1]
                self.hitbox.topleft = self.pos
                self.rect.topleft = self.pos
                
                # 增加卡住計數器
                self.stuck_counter += 1
                return
            
            # 檢查是否到達目標節點
            if self.grid_pos[0] == next_node[0] and self.grid_pos[1] == next_node[1]:
                # 移除已到達的節點
                self.path.pop(0)
                print(f"到達路徑點 {next_node}，剩餘路徑點: {len(self.path)}")
                
                # 如果路徑結束，停止移動
                if not self.path:
                    self.moving = False
                    print("已到達目標位置")
                    # 如果有互動目標，則開始互動
                    if self.interaction_target:
                        self.interact_with_current_target()
    
    def check_collision(self):
        """檢查碰撞並返回是否發生碰撞"""
        for sprite in self.game.collision_sprites:
            if self.hitbox.colliderect(sprite.rect):
                return True
        return False
    
    def recalculate_path(self):
        """當碰到障礙物或卡住時重新計算路徑"""
        if not self.current_target or not self.pathfinder:
            self.moving = False
            return
        
        # 獲取當前網格位置
        current_pos = (self.grid_pos[0], self.grid_pos[1])
        
        # 重新計算路徑 - 強制使用BFS而不使用對角線移動
        new_path = self.pathfinder.bfs(current_pos, self.current_target)
            
        if not new_path:
            # 如果找不到新的路徑，則停止移動
            self.moving = False
            print("重新計算路徑失敗，無法到達目標位置")
        else:
            self.path = new_path
            print(f"重新計算路徑成功，新路徑長度：{len(self.path)}")


class NPCController:
    def __init__(self, game):
        self.game = game
        self.npcs = {}  # 存儲所有的 NPC
        
        # 初始化網格數據
        self.initialize_grid()
        
    def initialize_grid(self):
        """Initialize grid for pathfinding"""
        # From TMX data create a basic grid
        # 1 represents obstacles, 0 represents passable
        tmx_data = self.game.tmx_data
        self.grid = []
        
        # Get map size
        map_width = tmx_data.width
        map_height = tmx_data.height
        
        # Initialize the entire grid as passable
        for y in range(map_height):
            row = [0] * map_width
            self.grid.append(row)
        
        # Mark walls and collision objects as obstacles
        collision_margin = 0.25  # Collision detection margin (between 0-1)
        
        for sprite in self.game.collision_sprites:
            # Convert pixel position to grid coordinates
            grid_x = int(sprite.rect.centerx / 32)
            grid_y = int(sprite.rect.centery / 32)
            
            # Get object size
            width_cells = max(1, int(sprite.rect.width / 32))
            height_cells = max(1, int(sprite.rect.height / 32))
            
            # Mark grid based on object size
            for y_offset in range(-1, height_cells + 1):  # Extend boundary by 1
                for x_offset in range(-1, width_cells + 1):  # Extend boundary by 1
                    nx, ny = grid_x + x_offset, grid_y + y_offset
                    
                    # Ensure coordinates are within grid range
                    if 0 <= nx < map_width and 0 <= ny < map_height:
                        # Calculate overlap between grid cell and obstacle
                        grid_rect = pygame.Rect(nx * 32, ny * 32, 32, 32)
                        overlap_area = grid_rect.clip(sprite.rect).width * grid_rect.clip(sprite.rect).height
                        overlap_ratio = overlap_area / (32 * 32)
                        
                        # If overlap exceeds threshold, mark as obstacle
                        if overlap_ratio > collision_margin:
                            self.grid[ny][nx] = 1
        
        # Output grid debug info
        obstacle_count = sum(row.count(1) for row in self.grid)
        print(f"Grid initialized: {map_width}x{map_height}, obstacles: {obstacle_count}")
        
        # Visualize grid (for debugging)
        self.print_grid()

    def optimize_grid(self):
        """Keep original grid, no optimization needed"""
        # Since grid generation is already precise, no further optimization needed
        pass
    
    def print_grid(self):
        """Print grid for debugging"""
        print("Grid map: (1=wall, 0=passable)")
        for row in self.grid[:10]:  # Only print first 10 rows to save space
            print("".join(str(cell) for cell in row[:40]))  # Only print first 40 columns
        print("...")  # Indicates truncated content
    
    def create_npc(self, npc_id, entity_type, position, size=(32, 32), speed=1):
        """Create a new NPC and add to controller"""
        npc = NPC(self.game, entity_type, position, size, speed)
        npc.initialize_pathfinder(self.grid)
        self.npcs[npc_id] = npc
        print(f"Created NPC: {npc_id}, position: {position}")
        return npc
    
    def get_npc(self, npc_id):
        """Get NPC by ID"""
        return self.npcs.get(npc_id)
    
    def move_npc_to_object(self, npc_id, object_name):
        """Command NPC to move to object"""
        npc = self.get_npc(npc_id)
        if npc:
            success = npc.set_target_by_name(object_name)
            if success:
                print(f"NPC {npc_id} commanded to move to object: {object_name}")
            else:
                print(f"Cannot find object: {object_name}")
            return success
        print(f"NPC not found: {npc_id}")
        return False
    
    def move_npc_to_tile(self, npc_id, layer_name, tile_x, tile_y):
        """Command NPC to move to tile position"""
        npc = self.get_npc(npc_id)
        if npc:
            success = npc.set_target_by_tile(layer_name, tile_x, tile_y)
            if success:
                print(f"NPC {npc_id} commanded to move to tile: {layer_name} ({tile_x}, {tile_y})")
            else:
                print(f"Invalid tile coordinates or layer: {layer_name} ({tile_x}, {tile_y})")
            return success
        print(f"NPC not found: {npc_id}")
        return False
    
    def update_all(self):
        """Update all NPCs"""
        for npc in self.npcs.values():
            npc.update()
    
    def stop_npc(self, npc_id):
        """Stop NPC movement"""
        npc = self.get_npc(npc_id)
        if npc:
            npc.moving = False
            npc.path = []
            print(f"Stopped NPC {npc_id} movement")
            return True
        print(f"NPC not found: {npc_id}")
        return False
    
    def set_npc_speed(self, npc_id, speed):
        """Set NPC movement speed"""
        npc = self.get_npc(npc_id)
        if npc and speed > 0:
            npc.speed = speed
            print(f"Set NPC {npc_id} speed to {speed}")
            return True
        print(f"NPC not found: {npc_id} or invalid speed parameter")
        return False
        
    def npc_interact(self, npc_id):
        """Command NPC to interact with current position"""
        npc = self.get_npc(npc_id)
        if npc:
            success = npc.interact_with_current_target()
            if success:
                print(f"NPC {npc_id} begins interaction")
            else:
                print(f"NPC {npc_id} cannot interact, no valid target")
            return success
        print(f"NPC not found: {npc_id}")
        return False
    
    def npc_interact_with(self, npc_id, object_name):
        """Command NPC to interact with specific object"""
        npc = self.get_npc(npc_id)
        if npc:
            # Set interaction target first
            npc.interaction_target = object_name
            # Then attempt interaction
            success = npc.interact_with_current_target()
            if success:
                print(f"NPC {npc_id} begins interaction with {object_name}")
            else:
                print(f"NPC {npc_id} cannot interact with {object_name}")
            return success
        print(f"NPC not found: {npc_id}")
        return False