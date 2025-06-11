import sys
import pygame
import time
from scripts.player import PhysicalEntity
from scripts.utils import load_image, load_images
from pytmx.util_pygame import load_pygame
from scripts.tilemaps import Tile
from scripts.level import TMXMapLoader
from scripts.Agents.npc import NPCController
from scripts.Agents.ai_npc_bridge import TMXAIBridge  # 導入TMX橋接類


class game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Project")  # window title  

        self.screen = pygame.display.set_mode((1280, 720))
        
        self.clock = pygame.time.Clock()  # clock control variable to control the frame rate

        self.dialogue_system = DialogueSystem(self)
        
        # Add game time system
        self.game_time = {
            "minute": 0,
            "hour": 8,    # Start at 8 AM
            "real_minutes_per_game_hour": 0.5,  # Real 2 minutes = Game 1 hour
            "last_update": time.time(),
            "time_scale": 1.0,  # Time flow rate, adjustable
            "paused": False     # Whether time is paused
        }
        
        self.movements = [False, False, False, False]  # Up, Down, Left, Right
        
        self.sprite_group = pygame.sprite.Group()  # group to store the sprites
        
        self.collision_sprites = pygame.sprite.Group()  # Group for collision tiles
        # assets
        self.assets = {
            'npc': load_image('entities/npc.png'),
            'player': load_image('entities/player.png')
        }  # load the image
        
        self.player = PhysicalEntity(self, 'player', (150, 200), (32, 32))  # Set tile size as 32x32
        
        self.npc_controller = None  # Will be initialized after loading the map
        
        # Load the map before initializing NPC controller
        self.map_loader = TMXMapLoader(self)
        self.tmx_data = self.map_loader.load_map('art/image/tiles/tiles/tmx/new.tmx')

        # Initialize NPC controller
        self.npc_controller = NPCController(self)
        
        # 創建第一個NPC（使用原有方式，保持兼容性）
        self.npc = self.npc_controller.create_npc("npc1", "npc", (200, 220), (32, 32))

        # Add a variable to store user input command
        self.command_input = ""
        self.command_active = False
        
        # 初始化NPC管理器（新增）
        from scripts.npc_manager import NPCManager
        from scripts.schedule_templates import npc1_schedule, npc2_schedule
        
        self.npc_manager = NPCManager(self)
        
        # 創建NPC1的AI系統
        self.ai_bridge = self.npc_manager.create_npc("npc1", "NPC Assistant 1", npc1_schedule())
        
        # 創建第二個NPC
        self.npc2 = self.npc_controller.create_npc("npc2", "npc", (250, 250), (32, 32))
        
        # 創建NPC2的AI系統（使用不同的日程表）
        self.ai_bridge2 = self.npc_manager.create_npc("npc2", "NPC Assistant 2", npc2_schedule())
        
        # 為NPC2設置時間偏移（可選）
        self.ai_bridge2.agent.schedule_offset = 30  # 30分鐘偏移
        self.ai_bridge2.agent.set_custom_schedule(npc2_schedule())

        # Display status and command history
        self.status_messages = []
        self.max_status_messages = 5
        self.ai_enabled = False
        self.last_command_time = 0
            
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # 确保在退出前停止AI线程
                    if self.ai_bridge and self.ai_enabled:
                        self.ai_bridge.stop_ai_loop()
                    pygame.quit()
                    sys.exit()  # exit the program

                # 处理命令输入模式的开关
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:  # Enter键
                        if self.command_active:  # 如果命令模式是活跃的
                            self.process_command(self.command_input)
                            self.command_input = ""
                            self.command_active = False
                        else:
                            self.command_active = True
                    
                    elif event.key == pygame.K_ESCAPE:  # ESC键退出命令模式
                        self.command_input = ""
                        self.command_active = False
                    
                    # 添加按键来启用/禁用AI控制
                    elif event.key == pygame.K_F1:  # F1键来切换AI控制
                        self.toggle_ai_control()
                    
                    # 添加时间控制快捷键
                    elif event.key == pygame.K_F2:  # F2键暂停/恢复时间
                        self.toggle_time_pause()
                    elif event.key == pygame.K_F3:  # F3键减慢时间
                        new_scale = max(0.5, self.game_time["time_scale"] - 0.5)
                        self.set_time_scale(new_scale)
                    elif event.key == pygame.K_F4:  # F4键加快时间
                        new_scale = min(5.0, self.game_time["time_scale"] + 0.5)
                        self.set_time_scale(new_scale)
                    elif event.key == pygame.K_F5:  # F5键重置时间速度
                        self.set_time_scale(1.0)
                    
                    elif self.command_active:  # 如果命令模式是活跃的，收集输入
                        if event.key == pygame.K_BACKSPACE:
                            self.command_input = self.command_input[:-1]
                        else:
                            self.command_input += event.unicode
                    
                    # 常规移动控制，仅在非命令模式下
                    elif not self.command_active:
                        if event.key == pygame.K_w:
                            self.movements[0] = True
                        elif event.key == pygame.K_s:
                            self.movements[1] = True
                        elif event.key == pygame.K_a:
                            self.movements[2] = True
                        elif event.key == pygame.K_d:
                            self.movements[3] = True

                elif event.type == pygame.KEYUP and not self.command_active:
                    if event.key == pygame.K_w:
                        self.movements[0] = False
                    elif event.key == pygame.K_s:
                        self.movements[1] = False
                    elif event.key == pygame.K_a:
                        self.movements[2] = False
                    elif event.key == pygame.K_d:
                        self.movements[3] = False

            # 更新游戏时间
            self.update_game_time()
            
            self.screen.fill((50, 50, 50))  # background color and clear the screen
            
            # 更新NPC
            if self.npc_controller:
                self.npc_controller.update_all()
            
            # 處理AI命令
            if self.ai_enabled and self.ai_bridge:
                if time.time() - self.last_command_time > 0.5:  # 限制命令處理頻率
                    if self.ai_bridge.process_next_command():
                        self.last_command_time = time.time()
                        if self.ai_bridge.commands_queue:
                            cmd = self.ai_bridge.commands_queue[0]
                            if cmd and len(cmd) > 0:
                                cmd_type = cmd[0]
                                # 獲取命令參數，如果不存在則使用空字符串
                                cmd_param = cmd[1] if len(cmd) > 1 and cmd[1] is not None else ""
                                self.add_status_message(f"Next command: {cmd_type} {cmd_param}")
            
            # 更新玩家移動 - 轉換為垂直和水平方向的移動值
            vertical_movement = self.movements[1] - self.movements[0]  # 下 - 上
            horizontal_movement = self.movements[3] - self.movements[2]  # 右 - 左
            self.player.update((vertical_movement, horizontal_movement))
            
            # Drawing the tilemap
            self.sprite_group.draw(self.screen)  # Draw all tiles and objects
            self.player.render(self.screen)  # Draw the player

            # 如果命令模式是活跃的，显示命令输入框
            if self.command_active:
                # 创建一个命令输入框
                font = pygame.font.SysFont(None, 24)
                command_surface = font.render(f"> {self.command_input}", True, (255, 255, 255))
                self.screen.blit(command_surface, (10, 10))

            # 渲染游戏时间
            self.render_game_time()
            
            # 显示状态和AI控制状态
            self.render_status()

            # Update the screen by drawing the 'display' surface onto the screen
            pygame.display.update()  # Update the screen
            self.clock.tick(60)  # 60 frames

    def update_game_time(self):
        """更新游戏内时间"""
        if self.game_time["paused"]:
            return
            
        current_time = time.time()
        elapsed_real_seconds = current_time - self.game_time["last_update"]
        self.game_time["last_update"] = current_time
        
        # 计算经过的游戏分钟
        real_minutes_per_game_hour = self.game_time["real_minutes_per_game_hour"]
        real_seconds_per_game_minute = (real_minutes_per_game_hour * 60) / 60
        
        game_minutes_passed = elapsed_real_seconds / real_seconds_per_game_minute
        game_minutes_passed *= self.game_time["time_scale"]  # 应用时间倍率
        
        # 更新游戏分钟
        self.game_time["minute"] += game_minutes_passed
        
        # 处理分钟溢出
        while self.game_time["minute"] >= 60:
            self.game_time["minute"] -= 60
            self.game_time["hour"] += 1
            
            # 触发整点事件
            self.on_hour_change()
            
            # 处理小时溢出
            if self.game_time["hour"] >= 24:
                self.game_time["hour"] -= 24
                self.game_time["day"] += 1
                
                # 触发天数变化事件
                self.on_day_change()
                
                # 简单处理月份
                if self.game_time["day"] > 30:
                    self.game_time["day"] = 1
                    self.game_time["month"] += 1
                    
                    if self.game_time["month"] > 12:
                        self.game_time["month"] = 1
                        self.game_time["year"] += 1
        
        # 每分钟更新一次NPC状态
        if self.npc_controller and hasattr(self.npc_controller, 'npcs'):
            # 获取主要NPC
            npc = self.npc_controller.npcs.get("npc1")
            if npc:
                # 根据时间更新NPC状态
                hour = self.game_time["hour"]
                
                # 深夜和清晨降低NPC能量
                if 0 <= hour < 6:
                    # 如果NPC在深夜还活动，逐渐降低能量
                    if self.ai_enabled and not npc.interacting:
                        if hasattr(self.ai_bridge, 'agent') and self.ai_bridge.agent:
                            # 降低能量
                            self.ai_bridge.agent.profile.update_status("energy", -1)
                            
                            # 如果能量过低，强制休息
                            if self.ai_bridge.agent.profile.status["energy"] < 20:
                                self.add_status_message("NPC能量不足，需要休息")
                                self.ai_bridge.commands_queue.insert(0, ("rest", None))
    
    def on_hour_change(self):
        """每小时变化时触发的事件"""
        # 这里可以添加NPC行为变化、环境变化等
        hour = self.game_time["hour"]
        
        # 添加到状态消息
        self.add_status_message(f"现在是 {hour:02d}:00")
        
        # 根据时间段执行特定行为
        if 7 <= hour <= 9:
            # 早上时段，可以触发早餐行为等
            pass
        elif 12 <= hour <= 14:
            # 中午时段
            pass
        elif 18 <= hour <= 20:
            # 晚上时段
            pass
        elif 22 <= hour <= 23 or 0 <= hour <= 5:
            # 夜间时段
            pass
    
    def on_day_change(self):
        """每天变化时触发的事件"""
        day = self.game_time["day"]
        month = self.game_time["month"]
        self.add_status_message(f"日期变为 {month}月{day}日")
    
    def format_game_time(self):
        """格式化游戏时间为字符串"""
        h = self.game_time["hour"]
        m = int(self.game_time["minute"])
        d = self.game_time["day"]
        mon = self.game_time["month"]
        y = self.game_time["year"]
        
        return f"{y}/{mon:02d}/{d:02d} {h:02d}:{m:02d}"
    
    def set_time_scale(self, scale):
        """设置时间流速"""
        if scale >= 0:
            self.game_time["time_scale"] = scale
            status = "正常" if scale == 1.0 else ("慢" if scale < 1.0 else "快")
            self.add_status_message(f"时间流速设为 {scale}x ({status})")
    
    def toggle_time_pause(self):
        """切换时间暂停状态"""
        self.game_time["paused"] = not self.game_time["paused"]
        state = "暂停" if self.game_time["paused"] else "恢复"
        self.add_status_message(f"时间已{state}")
    
    def render_game_time(self):
        """在屏幕上渲染游戏时间"""
        font = pygame.font.SysFont(None, 24)
        time_text = self.format_game_time()
        
        # 添加时间流速指示器
        if self.game_time["paused"]:
            time_text += " [暂停]"
        elif self.game_time["time_scale"] != 1.0:
            time_text += f" [x{self.game_time['time_scale']}]"
            
        time_surface = font.render(time_text, True, (255, 255, 255))
        self.screen.blit(time_surface, (650, 10))

    def process_command(self, command):
        """处理用户输入的命令"""
        self.add_status_message(f"命令: {command}")
        
        if not command:
            return
        
        # 分割命令字符串
        parts = command.strip().split()
        
        # 命令需要至少有一个参数
        if len(parts) < 1:
            self.add_status_message("無效命令")
            return
        
        # AI控制相关命令
        if parts[0].lower() == "ai":
            if len(parts) >= 2:
                if parts[1].lower() == "on":
                    self.enable_ai_control()
                elif parts[1].lower() == "off":
                    self.disable_ai_control()
                elif parts[1].lower() == "status":
                    self.add_status_message(f"AI控制: {'啟用' if self.ai_enabled else '禁用'}")
                    # 處理AI命令
                    if self.ai_enabled and self.ai_bridge:
                        if time.time() - self.last_command_time > 0.5:  # 限制命令處理頻率
                            if self.ai_bridge.process_next_command():
                                self.last_command_time = time.time()
                                if self.ai_bridge.commands_queue:
                                    cmd = self.ai_bridge.commands_queue[0]
                                    cmd_type = cmd[0] if cmd and len(cmd) > 0 else "unknown"
                                    cmd_param = cmd[1] if cmd and len(cmd) > 1 and cmd[1] is not None else ""
                                    self.add_status_message(f"Next command: {cmd_type} {cmd_param}")
                else:
                    self.add_status_message(f"未知AI命令: {parts[1]}")
            else:
                self.add_status_message("用法: ai [on|off|status]")
        
        # 时间控制命令
        elif parts[0].lower() == "time":
            if len(parts) >= 2:
                if parts[1].lower() == "pause" or parts[1].lower() == "p":
                    self.toggle_time_pause()
                elif parts[1].lower() == "scale" and len(parts) >= 3:
                    try:
                        scale = float(parts[2])
                        self.set_time_scale(scale)
                    except ValueError:
                        self.add_status_message("无效的时间比例")
                elif parts[1].lower() == "set" and len(parts) >= 4:
                    try:
                        hour = int(parts[2])
                        minute = int(parts[3])
                        if 0 <= hour < 24 and 0 <= minute < 60:
                            self.game_time["hour"] = hour
                            self.game_time["minute"] = minute
                            self.add_status_message(f"时间设置为 {hour:02d}:{minute:02d}")
                        else:
                            self.add_status_message("无效的时间")
                    except ValueError:
                        self.add_status_message("无效的时间格式")
                elif parts[1].lower() == "help":
                    self.add_status_message("时间命令: pause/p, scale <数值>, set <时> <分>")
                    self.add_status_message("快捷键: F2=暂停, F3=减速, F4=加速, F5=正常速度")
                else:
                    self.add_status_message("当前游戏时间: " + self.format_game_time())
            else:
                self.add_status_message("当前游戏时间: " + self.format_game_time())
        
        # 处理 "goto" 命令
        elif parts[0].lower() == "goto" and len(parts) >= 2:
            object_name = " ".join(parts[1:])  # 合并可能包含空格的对象名称
            success = self.npc_controller.move_npc_to_object("npc1", object_name)
            self.add_status_message(f"前往物件 {object_name}: {'成功' if success else '失敗'}")
        
        # 处理 "goto_tile" 命令
        elif parts[0].lower() == "goto_tile" and len(parts) >= 4:
            layer_name = parts[1]
            try:
                tile_x = int(parts[2])
                tile_y = int(parts[3])
                success = self.npc_controller.move_npc_to_tile("npc1", layer_name, tile_x, tile_y)
                self.add_status_message(f"前往瓦片 {layer_name}({tile_x},{tile_y}): {'成功' if success else '失敗'}")
            except ValueError:
                self.add_status_message("無效的坐標值")
        

        # 处理 "interact" 命令
        elif parts[0].lower() == "interact":
            if len(parts) >= 2:
                object_name = " ".join(parts[1:])
                success = self.npc_controller.npc_interact_with("npc1", object_name)
                self.add_status_message(f"Interacting with {object_name}: {'Success' if success else 'Failed'}")
            else:
                success = self.npc_controller.npc_interact("npc1")
                self.add_status_message(f"Attempting interaction: {'Success' if success else 'Failed'}")
        
        # 处理 "list" 命令 - 列出地图对象
        elif parts[0].lower() == "list":
            if self.ai_bridge:
                nearby = self.ai_bridge.get_nearby_objects()
                if nearby:
                    self.add_status_message(f"附近物件: {', '.join(nearby)}")
                else:
                    self.add_status_message("附近沒有物件")
            else:
                self.add_status_message("AI橋接未初始化")
        
        # 处理 "status" 命令 - 显示NPC状态
        elif parts[0].lower() == "status":
            if self.ai_bridge and hasattr(self.ai_bridge, 'agent'):
                agent = self.ai_bridge.agent
                status = agent.profile.status
                self.add_status_message(f"NPC状态: 能量={status['energy']}, 饥饿={status['hunger']}, 心情={status['mood']}")
            else:
                self.add_status_message("AI代理未初始化")
        
        # 处理 "help" 命令
        elif parts[0].lower() == "help":
            self.print_help()
        # 在 process_command 方法中添加以下代碼段
        # 添加 "debug" 命令
        elif parts[0].lower() == "debug":
            if len(parts) >= 2:
                if parts[1].lower() == "objects":
                    npc = self.npc_controller.npcs.get("npc1")
                    if npc:
                        current_x = npc.grid_pos[0]
                        current_y = npc.grid_pos[1]
                        self.add_status_message(f"NPC position: ({current_x}, {current_y})")
                        
                        # Check objects at NPC position
                        objects = npc._get_objects_at_position(current_x, current_y)
                        if objects:
                            self.add_status_message(f"Objects at current position: {', '.join(objects)}")
                        else:
                            self.add_status_message("No objects at current position")
                        
                        # Check nearby objects - 只檢查四個方向
                        nearby = []
                        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            objects = npc._get_objects_at_position(current_x + dx, current_y + dy)
                            if objects:
                                nearby.extend(objects)
                        
                        if nearby:
                            self.add_status_message(f"Nearby objects: {', '.join(nearby)}")
                        else:
                            self.add_status_message("No nearby objects")
                            
                        # Check interaction target
                        if npc.interaction_target:
                            self.add_status_message(f"Current interaction target: {npc.interaction_target}")
                        else:
                            self.add_status_message("No interaction target set")
                    else:
                        self.add_status_message("NPC not found")
                else:
                    self.add_status_message(f"Unknown debug command: {parts[1]}")
            else:
                self.add_status_message("Usage: debug [objects]")

    def toggle_ai_control(self):
        """切换AI控制状态"""
        if self.ai_enabled:
            self.disable_ai_control()
        else:
            self.enable_ai_control()
    
    def enable_ai_control(self):
        """启用AI控制"""
        if not self.ai_enabled:
            self.ai_enabled = True
            self.ai_bridge.start_ai_loop()
            self.add_status_message("已啟用AI控制")
    
    def disable_ai_control(self):
        """禁用AI控制"""
        if self.ai_enabled:
            self.ai_enabled = False
            self.ai_bridge.stop_ai_loop()
            self.add_status_message("已禁用AI控制")
    
    def add_status_message(self, message):
        """添加状态消息"""
        self.status_messages.append(message)
        if len(self.status_messages) > self.max_status_messages:
            self.status_messages.pop(0)
        print(message)  # 同时在控制台输出
    
    def render_status(self):
        """Render status information"""
        font = pygame.font.SysFont(None, 20)
        
        # Display AI control status
        ai_status = f"AI Control: {'Enabled' if self.ai_enabled else 'Disabled'} (F1 to toggle)"
        status_surface = font.render(ai_status, True, (255, 255, 0))
        self.screen.blit(status_surface, (10, 550))
        
        # Display game time status
        time_status = f"Game time: {self.format_game_time()} (F2=pause, F3=slow, F4=fast)"
        time_surface = font.render(time_status, True, (255, 255, 0))
        self.screen.blit(time_surface, (10, 530))
        
        # Display command history
        y_offset = 480
        for msg in self.status_messages:
            msg_surface = font.render(msg, True, (200, 200, 200))
            self.screen.blit(msg_surface, (10, y_offset))
            y_offset += 20
    
    def print_help(self):
        """显示所有可用命令的帮助信息"""
        help_text = [
            "--- 命令帮助 ---",
            "ai on|off|status - 控制AI代理",
            "time pause|scale <值>|set <时> <分> - 控制游戏时间",
            "goto <对象名> - 前往指定对象",
            "goto_tile <图层> <x> <y> - 前往指定位置",
            "interact [对象名] - 与对象互动",
            "list - 列出附近物体",
            "status - 显示NPC状态",
            "help - 显示此帮助"
        ]
        
        for text in help_text:
            self.add_status_message(text)
        
        self.add_status_message("--- 快捷键 ---")
        self.add_status_message("F1=切换AI控制, F2=暂停时间")
        self.add_status_message("F3=减速时间, F4=加速时间, F5=正常速度")


if __name__ == "__main__":
    game().run()