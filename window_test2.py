import sys
import pygame
import time
from scripts.player import PhysicalEntity
from scripts.utils import load_image, load_images
from pytmx.util_pygame import load_pygame
from scripts.tilemaps import Tile
from scripts.level import TMXMapLoader
from scripts.Agents.npc import NPCController
from scripts.Agents.ai_npc_bridge import TMXAIBridge
from scripts.Agents.npc_status_handler import NPCStatusSystem
from scripts.Agents.dialogue_system import DialogueSystem
from scripts.Agents.npc_manager import NPCManager
from scripts.Agents.schedule_templates import npc1_schedule, npc2_schedule
from scripts.Agents.npc_target_indicator import NPCTargetIndicator


class game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Project")  # window title  

        self.screen = pygame.display.set_mode((1280, 720))
        
        self.clock = pygame.time.Clock()  # clock control variable to control the frame rate

        self.dialogue_system = DialogueSystem(self)

        # 创建NPC对话系统
        from scripts.Agents.npc_dialogue_system import NPCDialogueSystem
        self.npc_dialogue_system = NPCDialogueSystem(self)

        # 确保已经创建agents目录及复制两个agent文件
        import os
        if not os.path.exists("scripts/Agents/agents"):
            os.makedirs("scripts/Agents/agents")
            
        # 检查agent文件是否存在，如果不存在则创建默认文件
        for agent_name in ["Lisa", "Lila"]:
            agent_file = os.path.join("scripts/Agents/agents", f"{agent_name}.agent.json")
            if not os.path.exists(agent_file):
                with open(agent_file, "w", encoding="utf-8") as f:
                    if agent_name == "Lisa":
                        f.write('{"type":"TinyPerson","persona":{"name":"Lisa","style":"活泼开朗，喜欢聊天，性格外向"}}')
                    else:
                        f.write('{"type":"TinyPerson","persona":{"name":"Lila","style":"温和内敛，善于倾听，偶尔幽默"}}')
        
        # Add game time system
        self.game_time = {
            "minute": 0,
            "hour": 13,    # Start at 8 AM
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
            'npc1': load_image('entities/npc1.png'),
            'npc2': load_image('entities/npc2.png'),
            'player': load_image('entities/player.png')
        }  # load the image
        
        self.player = PhysicalEntity(self, 'player', (150, 200), (32, 32))  # Set tile size as 32x32
        
        self.npc_controller = None  # Will be initialized after loading the map
        
        # Load the map before initializing NPC controller
        self.map_loader = TMXMapLoader(self)
        self.tmx_data = self.map_loader.load_map('art/image/tiles/tiles/tmx/new.tmx')

        # Initialize NPC controller
        self.npc_controller = NPCController(self)
        
        # 創建第一個NPC
        self.npc = self.npc_controller.create_npc("npc1", "npc2", (200, 220), (32, 32))

        # Add a variable to store user input command
        self.command_input = ""
        self.command_active = False
        
        # **直接創建AI Bridge，但不立即启动**
        print("正在初始化NPC1的AI系统...")
        self.ai_bridge = TMXAIBridge(self, "npc1")
        self.ai_bridge.initialize_agent("NPC Assistant 1")

        # 創建第二個NPC
        print("正在创建NPC2...")
        self.npc2 = self.npc_controller.create_npc("npc2", "npc2", (250, 250), (32, 32))

        # 創建NPC2的AI系統
        print("正在初始化NPC2的AI系统...")
        self.ai_bridge2 = TMXAIBridge(self, "npc2")
        self.ai_bridge2.initialize_agent("NPC Assistant 2")

        # **CRITICAL: 确保每个agent都有正确的npc_id**
        # 这一步非常重要，确保AI agent知道自己的身份
        if hasattr(self.ai_bridge, 'agent'):
            self.ai_bridge.agent.npc_id = "npc1"
            print(f"设置 NPC1 的 agent.npc_id = {self.ai_bridge.agent.npc_id}")

        if hasattr(self.ai_bridge2, 'agent'):
            self.ai_bridge2.agent.npc_id = "npc2"
            print(f"设置 NPC2 的 agent.npc_id = {self.ai_bridge2.agent.npc_id}")

        # 設置第二個agent的不同日程（帶偏移）- 移除这部分，因为现在用npc_id来区分
        # 重新生成两个NPC的日程表，确保使用正确的npc_id
        print("重新生成NPC1的日程表...")
        if hasattr(self.ai_bridge.agent, '_generate_dynamic_schedule'):
            self.ai_bridge.agent.planning.daily_schedule = {}  # 清空现有日程
            self.ai_bridge.agent._generate_dynamic_schedule()

        print("重新生成NPC2的日程表...")
        if hasattr(self.ai_bridge2.agent, '_generate_dynamic_schedule'):
            self.ai_bridge2.agent.planning.daily_schedule = {}  # 清空现有日程
            self.ai_bridge2.agent._generate_dynamic_schedule()

        # **创建共享的交互效果配置**
        print("正在准备交互效果配置...")
        self.shared_interaction_effects = self._create_shared_interaction_effects()
        
        # 註冊交互效果 - 使用共享配置
        print("正在注册交互效果...")
        self._register_interaction_effects_for_npc(self.ai_bridge, "NPC1")
        self._register_interaction_effects_for_npc(self.ai_bridge2, "NPC2")

        # Display status and command history
        self.status_messages = []
        # Add status update cooldown system
        self.status_update_cooldown = {
            "npc1": 0,
            "npc2": 0
        }
        self.status_update_interval = 30  # In seconds
        self.last_status_update_time = {
            "npc1": 0,
            "npc2": 0
        }
        self.movement_status_cooldown = {
            "npc1": 0,
            "npc2": 0
        }
        self.movement_status_interval = 5  # In seconds
        self.max_status_messages = 5
        self.ai_enabled = False
        self.last_command_time = 0
        
        # 创建NPC目标指示器
        self.npc_target_indicator = NPCTargetIndicator(self)

        # 由于你的系统完美支持emoji，设置为emoji模式
        self.npc_target_indicator.set_display_mode('emoji')
        
        # 可选：添加自定义图标映射
        # self.npc_target_indicator.add_custom_target_icon("piano", "🎹")
        # self.npc_target_indicator.add_custom_activity_icon("弹钢琴", "🎹")
        # self.npc_target_indicator.add_custom_target_icon("garden", "🌱")
        # self.npc_target_indicator.add_custom_activity_icon("浇花", "🌱")
        
        print("NPC表符已初始化!")
        print("初始化完成!")
        
    # 在window_test2.py文件中修改register_all_interaction_effects方法

    def _create_shared_interaction_effects(self):
        """创建共享的交互效果配置"""
        return {
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
            
        }

    def _register_interaction_effects_for_npc(self, ai_bridge, npc_name):
        """为指定NPC注册交互效果"""
        if not ai_bridge:
            print(f"Warning: AI Bridge for {npc_name} not initialized")
            return
        
        effects_registered = 0
        for obj_type, (status_changes, description) in self.shared_interaction_effects.items():
            ai_bridge.register_interaction_effect(obj_type, status_changes, description)
            effects_registered += 1
            
        print(f"为 {npc_name} 注册了 {effects_registered} 个交互效果")
        
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Ensure AI thread is stopped before exiting
                    if self.ai_bridge and self.ai_enabled:
                        self.ai_bridge.stop_ai_loop()
                    pygame.quit()
                    sys.exit()  # exit the program
                if hasattr(self, 'npc_dialogue_system'):
                    if self.npc_dialogue_system.handle_scroll_event(event):
                        continue  # 如果對話系統處理了事件，跳過後續處理               
                # First check if dialogue system should handle this event
                if hasattr(self, 'dialogue_system') and self.dialogue_system.handle_input_event(event):
                    # If dialogue system handled the event, skip further processing
                    continue

                # Handle command input mode toggle
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:  # Enter key
                        if self.command_active:  # If command mode is active
                            self.process_command(self.command_input)
                            self.command_input = ""
                            self.command_active = False
                        else:
                            self.command_active = True
                    
                    elif event.key == pygame.K_ESCAPE:  # ESC key to exit command mode
                        self.command_input = ""
                        self.command_active = False
                    
                    
                    # Add key to enable/disable AI control
                    elif event.key == pygame.K_F1:  # F1 key to toggle AI control
                        self.toggle_ai_control()
                    
                    # Add time control hotkeys
                    elif event.key == pygame.K_F2:  # F2 key to pause/resume time
                        self.toggle_time_pause()
                    elif event.key == pygame.K_F3:  # F3 key to slow down time
                        new_scale = max(0.5, self.game_time["time_scale"] - 0.5)
                        self.set_time_scale(new_scale)
                    elif event.key == pygame.K_F4:  # F4 key to speed up time
                        new_scale = min(5.0, self.game_time["time_scale"] + 0.5)
                        self.set_time_scale(new_scale)
                    elif event.key == pygame.K_F5:  # F5 key to reset time speed
                        self.set_time_scale(1.0)
                    
                    elif self.command_active:  # If command mode is active, collect input
                        if event.key == pygame.K_BACKSPACE:
                            self.command_input = self.command_input[:-1]
                        else:
                            self.command_input += event.unicode
                    
                    # Regular movement controls, only when not in command mode AND not in dialogue
                    elif not self.command_active and not self.dialogue_system.active:
                        if event.key == pygame.K_w:
                            self.movements[0] = True
                        elif event.key == pygame.K_s:
                            self.movements[1] = True
                        elif event.key == pygame.K_a:
                            self.movements[2] = True
                        elif event.key == pygame.K_d:
                            self.movements[3] = True

                elif event.type == pygame.KEYUP and not self.command_active and not self.dialogue_system.active:
                    if event.key == pygame.K_w:
                        self.movements[0] = False
                    elif event.key == pygame.K_s:
                        self.movements[1] = False
                    elif event.key == pygame.K_a:
                        self.movements[2] = False
                    elif event.key == pygame.K_d:
                        self.movements[3] = False

            # Update game time
            self.update_game_time()
            
            self.screen.fill((50, 50, 50))  # background color and clear the screen
            
            # 處理 AI 命令
            if self.ai_enabled:
                if hasattr(self, 'npc_manager'):
                    # 使用 NPCManager 統一處理
                    self.npc_manager.update_all()
                else:
                    # 原有的分別處理方式
                    if self.ai_bridge and time.time() - self.last_command_time > 0.5:
                        if self.ai_bridge.process_next_command():
                            self.last_command_time = time.time()
                            # ... 現有的命令處理邏輯
                    
                    # 處理 NPC2
                    if hasattr(self, 'ai_bridge2') and self.ai_bridge2:
                        if time.time() - self.last_command_time > 0.5:
                            if self.ai_bridge2.process_next_command():
                                # NPC2 的命令處理
                                pass
            
            # 在 run() 方法的 AI 處理部分
            if self.ai_enabled and self.ai_bridge:
                if time.time() - self.last_command_time > 0.5:
                    if self.ai_bridge.process_next_command():
                        self.last_command_time = time.time()
                        # ... NPC1的命令處理

            # **添加這部分來處理NPC2**
            if self.ai_enabled and hasattr(self, 'ai_bridge2') and self.ai_bridge2:
                if time.time() - self.last_command_time > 0.5:
                    if self.ai_bridge2.process_next_command():
                        # 處理NPC2的命令
                        if self.ai_bridge2.commands_queue:
                            cmd = self.ai_bridge2.commands_queue[0]
                            if cmd and len(cmd) > 0:
                                cmd_type = cmd[0]
                                cmd_param = cmd[1] if len(cmd) > 1 and cmd[1] is not None else ""
                                self.add_status_message(f"NPC2 next command: {cmd_type} {cmd_param}")
            
            # Update player movement - convert to vertical and horizontal movement values
            vertical_movement = self.movements[1] - self.movements[0]  # Down - Up
            horizontal_movement = self.movements[3] - self.movements[2]  # Right - Left
            self.player.update((vertical_movement, horizontal_movement))
            
            # **CRITICAL FIX: Add NPC controller update**
            # This is what was missing - NPCs weren't updating their positions
            if self.npc_controller:
                self.npc_controller.update_all()
            
            # Drawing the tilemap
            self.sprite_group.draw(self.screen)  # Draw all tiles and objects
            self.player.render(self.screen)  # Draw the player
            
            # 渲染NPC目标指示器
            if hasattr(self, 'npc_target_indicator'):
                self.npc_target_indicator.render_npc_targets()

            # If command mode is active, display command input box
            if self.command_active:
                # Create a command input box
                font = pygame.font.SysFont(None, 24)
                command_surface = font.render(f"> {self.command_input}", True, (255, 255, 255))
                self.screen.blit(command_surface, (10, 10))

            # Render game time
            self.render_game_time()
            
            # Display status and AI control status
            self.render_status()
            
            if hasattr(self, 'npc_dialogue_system'):
                self.npc_dialogue_system.update()
                self.npc_dialogue_system.render()

            # Add this at the end, after all other rendering
            if hasattr(self, 'dialogue_system'):
                self.dialogue_system.render()

            # Update the screen
            pygame.display.update()
            self.clock.tick(60)  # 60 frames per second
            
    def update_game_time(self):
        """Update game time"""
        if self.game_time["paused"]:
            return
            
        current_time = time.time()
        elapsed_real_seconds = current_time - self.game_time["last_update"]
        self.game_time["last_update"] = current_time
        
        # Calculate elapsed game minutes
        real_minutes_per_game_hour = self.game_time["real_minutes_per_game_hour"]
        real_seconds_per_game_minute = (real_minutes_per_game_hour * 60) / 60
        
        game_minutes_passed = elapsed_real_seconds / real_seconds_per_game_minute
        game_minutes_passed *= self.game_time["time_scale"]  # Apply time multiplier
        
        # Update game minutes
        self.game_time["minute"] += game_minutes_passed
        
        # Handle minute overflow
        while self.game_time["minute"] >= 60:
            self.game_time["minute"] -= 60
            self.game_time["hour"] += 1
            
            # Trigger hourly events
            self.on_hour_change()
            
            # Handle hour overflow
            if self.game_time["hour"] >= 24:
                self.game_time["hour"] -= 24
                
                # Trigger day change events
                self.on_day_change()
        
        # 每30分钟更新NPC状态，但添加独立的计时器和冷却系统
        current_time = time.time()
        if self.npc_controller and hasattr(self.npc_controller, 'npcs'):
            # Get current minute for display purposes only
            hour = self.game_time["hour"]
            minute = int(self.game_time["minute"])
            
            # Only update status at the specified interval and when not paused
            if not self.game_time["paused"]:
                # Update NPC1 if cooldown has expired
                if hasattr(self.ai_bridge, 'agent') and self.ai_bridge.agent:
                    if current_time - self.last_status_update_time.get("npc1", 0) >= self.status_update_interval:
                        old_mood1 = self.ai_bridge.agent.profile.status.get("mood", 0)
                        old_health1 = self.ai_bridge.agent.profile.status.get("health", 0)
                        
                        # Decrease mood at appropriate rate
                        self.ai_bridge.agent.profile.update_status("mood", -1)
                        
                        # If nighttime, mood decreases faster
                        if 0 <= hour < 6:
                            self.ai_bridge.agent.profile.update_status("mood", -1)
                            
                        # If mood too low, reduce health
                        if self.ai_bridge.agent.profile.status["mood"] < 20:
                            self.ai_bridge.agent.profile.update_status("health", -1)
                        
                        # Update timestamp for next cooldown
                        self.last_status_update_time["npc1"] = current_time
                        
                        # Display updated status
                        self.add_status_message(f"NPC1 Time-based status update: [Hour: {hour:02d}:{minute:02d}]")
                        self.add_status_message(f"NPC1 Mood: {old_mood1} -> {self.ai_bridge.agent.profile.status['mood']}")
                        self.add_status_message(f"NPC1 Health: {old_health1} -> {self.ai_bridge.agent.profile.status['health']}")
                
                # Update NPC2 if cooldown has expired
                if hasattr(self, 'ai_bridge2') and hasattr(self.ai_bridge2, 'agent') and self.ai_bridge2.agent:
                    if current_time - self.last_status_update_time.get("npc2", 0) >= self.status_update_interval:
                        old_mood2 = self.ai_bridge2.agent.profile.status.get("mood", 0)
                        old_health2 = self.ai_bridge2.agent.profile.status.get("health", 0)
                        
                        # Decrease mood at appropriate rate
                        self.ai_bridge2.agent.profile.update_status("mood", -1)
                        
                        # If nighttime, mood decreases faster
                        if 0 <= hour < 6:
                            self.ai_bridge2.agent.profile.update_status("mood", -1)
                            
                        # If mood too low, reduce health
                        if self.ai_bridge2.agent.profile.status["mood"] < 20:
                            self.ai_bridge2.agent.profile.update_status("health", -1)
                        
                        # Update timestamp for next cooldown
                        self.last_status_update_time["npc2"] = current_time
                        
                        # Display updated status
                        self.add_status_message(f"NPC2 Time-based status update: [Hour: {hour:02d}:{minute:02d}]")
                        self.add_status_message(f"NPC2 Mood: {old_mood2} -> {self.ai_bridge2.agent.profile.status['mood']}")
                        self.add_status_message(f"NPC2 Health: {old_health2} -> {self.ai_bridge2.agent.profile.status['health']}")
    
    def on_hour_change(self):
        """Events triggered when hour changes"""
        # Here you can add NPC behavior changes, environmental changes, etc.
        hour = self.game_time["hour"]
        
        # Add to status messages
        self.add_status_message(f"Time: {hour:02d}:00")
        
        # Trigger specific behavior based on time period
        if 7 <= hour <= 9:
            # Morning period
            pass
        elif 12 <= hour <= 14:
            # Noon period
            pass
        elif 18 <= hour <= 20:
            # Evening period
            pass
        elif 22 <= hour <= 23 or 0 <= hour <= 5:
            # Night period
            pass
    
    def on_day_change(self):
        """Events triggered when day changes"""
        self.add_status_message("Date changed to next day")
    
    def format_game_time(self):
        """Format game time as a string"""
        h = self.game_time["hour"]
        m = int(self.game_time["minute"])
        return f"{h:02d}:{m:02d}"
    
    def set_time_scale(self, scale):
        """Set time flow speed"""
        if scale >= 0:
            self.game_time["time_scale"] = scale
            status = "Normal" if scale == 1.0 else ("Slow" if scale < 1.0 else "Fast")
            self.add_status_message(f"Time speed set to {scale}x ({status})")
    
    def toggle_time_pause(self):
        """Toggle time pause state"""
        self.game_time["paused"] = not self.game_time["paused"]
        state = "Paused" if self.game_time["paused"] else "Resumed"
        self.add_status_message(f"Time {state}")
    
    def render_game_time(self):
        """Render game time on screen"""
        font = pygame.font.SysFont(None, 24)
        time_text = self.format_game_time()
        
        # Add time flow indicator
        if self.game_time["paused"]:
            time_text += " [Paused]"
        elif self.game_time["time_scale"] != 1.0:
            time_text += f" [x{self.game_time['time_scale']}]"
            
        time_surface = font.render(time_text, True, (255, 255, 255))
        self.screen.blit(time_surface, (650, 10))
    
    def process_command(self, command):
        """Process user input command"""
        self.add_status_message(f"Command: {command}")
        
        if not command:
            return
        
        # Split command string
        parts = command.strip().split()
        
        # Command needs at least one parameter
        if len(parts) < 1:
            self.add_status_message("Invalid command")
            return
        
        # AI control related commands
        if parts[0].lower() == "ai":
            if len(parts) >= 2:
                if parts[1].lower() == "on":
                    self.enable_ai_control()
                elif parts[1].lower() == "off":
                    self.disable_ai_control()
                elif parts[1].lower() == "status":
                    self.add_status_message(f"AI Control: {'Enabled' if self.ai_enabled else 'Disabled'}")
                    # Process AI commands
                    if self.ai_enabled and self.ai_bridge:
                        if time.time() - self.last_command_time > 0.5:  # Limit command processing frequency
                            if self.ai_bridge.process_next_command():
                                self.last_command_time = time.time()
                                if self.ai_bridge.commands_queue:
                                    cmd = self.ai_bridge.commands_queue[0]
                                    cmd_type = cmd[0] if cmd and len(cmd) > 0 else "unknown"
                                    cmd_param = cmd[1] if cmd and len(cmd) > 1 and cmd[1] is not None else ""
                                    self.add_status_message(f"Next command: {cmd_type} {cmd_param}")
                else:
                    self.add_status_message(f"Unknown AI command: {parts[1]}")
            else:
                self.add_status_message("Usage: ai [on|off|status]")
        
        # Time control commands
        elif parts[0].lower() == "time":
            if len(parts) >= 2:
                if parts[1].lower() == "pause" or parts[1].lower() == "p":
                    self.toggle_time_pause()
                elif parts[1].lower() == "scale" and len(parts) >= 3:
                    try:
                        scale = float(parts[2])
                        self.set_time_scale(scale)
                    except ValueError:
                        self.add_status_message("Invalid time scale")
                elif parts[1].lower() == "set" and len(parts) >= 4:
                    try:
                        hour = int(parts[2])
                        minute = int(parts[3])
                        if 0 <= hour < 24 and 0 <= minute < 60:
                            self.game_time["hour"] = hour
                            self.game_time["minute"] = minute
                            self.add_status_message(f"Time set to {hour:02d}:{minute:02d}")
                        else:
                            self.add_status_message("Invalid time")
                    except ValueError:
                        self.add_status_message("Invalid time format")
                elif parts[1].lower() == "help":
                    self.add_status_message("Time commands: pause/p, scale <value>, set <hour> <minute>")
                    self.add_status_message("Hotkeys: F2=Pause, F3=Slow, F4=Fast, F5=Normal speed")
                else:
                    self.add_status_message("Current game time: " + self.format_game_time())
            else:
                self.add_status_message("Current game time: " + self.format_game_time())
        
        # 修改 "goto" 命令，支援指定 NPC
        elif parts[0].lower() == "goto" and len(parts) >= 2:
            # 檢查是否指定了 NPC ID
            if len(parts) >= 3 and parts[1].lower() in ["npc1", "npc2"]:
                npc_id = parts[1].lower()
                object_name = " ".join(parts[2:])
            else:
                npc_id = "npc1"  # 默認使用 npc1
                object_name = " ".join(parts[1:])
                
            success = self.npc_controller.move_npc_to_object(npc_id, object_name)
            self.add_status_message(f"{npc_id} going to {object_name}: {'Success' if success else 'Failed'}")

        
        # Process "goto_tile" command
        elif parts[0].lower() == "goto_tile" and len(parts) >= 4:
            layer_name = parts[1]
            try:
                tile_x = int(parts[2])
                tile_y = int(parts[3])
                success = self.npc_controller.move_npc_to_tile("npc1", layer_name, tile_x, tile_y)
                self.add_status_message(f"Going to tile {layer_name}({tile_x},{tile_y}): {'Success' if success else 'Failed'}")
            except ValueError:
                self.add_status_message("Invalid coordinates")
        
        # 修改 "interact" 命令，支援指定 NPC
        elif parts[0].lower() == "interact":
            if len(parts) >= 2:
                # 檢查是否指定了 NPC ID
                if len(parts) >= 3 and parts[1].lower() in ["npc1", "npc2"]:
                    npc_id = parts[1].lower()
                    object_name = " ".join(parts[2:])
                else:
                    npc_id = "npc1"  # 默認使用 npc1
                    object_name = " ".join(parts[1:])
                    
                success = self.npc_controller.npc_interact_with(npc_id, object_name)
                self.add_status_message(f"{npc_id} interacting with {object_name}: {'Success' if success else 'Failed'}")
            else:
                # 如果沒有指定對象，對所有 NPC 執行互動
                success1 = self.npc_controller.npc_interact("npc1")
                success2 = self.npc_controller.npc_interact("npc2") if hasattr(self, 'npc2') else False
                self.add_status_message(f"NPC1 interact: {'Success' if success1 else 'Failed'}")
                if hasattr(self, 'npc2'):
                    self.add_status_message(f"NPC2 interact: {'Success' if success2 else 'Failed'}")
        
        # Process "list" command - list map objects
        elif parts[0].lower() == "list":
            if self.ai_bridge:
                nearby = self.ai_bridge.get_nearby_objects()
                if nearby:
                    self.add_status_message(f"Nearby objects: {', '.join(nearby)}")
                else:
                    self.add_status_message("No nearby objects")
            else:
                self.add_status_message("AI Bridge not initialized")
        
        # Process "status" command - show NPC status
        elif parts[0].lower() == "status":
            if self.ai_bridge and hasattr(self.ai_bridge, 'agent'):
                agent = self.ai_bridge.agent
                status = agent.profile.status
                self.add_status_message(f"NPC Status: Mood={status['mood']}, Health={status['health']}")
            else:
                self.add_status_message("AI agent not initialized")
        
        # Process "help" command
        elif parts[0].lower() == "help":
            self.print_help()
            
        # Add "debug" command
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
                        
                        # Check nearby objects - only check four directions
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
        """Toggle AI control state for all NPCs"""
        if self.ai_enabled:
            self.disable_ai_control()
        else:
            self.enable_ai_control()
    
    def enable_ai_control(self):
        """Enable AI control for all NPCs"""
        if not self.ai_enabled:
            self.ai_enabled = True
            # 啟動所有AI
            if hasattr(self, 'ai_bridge') and self.ai_bridge:
                self.ai_bridge.start_ai_loop()
            if hasattr(self, 'ai_bridge2') and self.ai_bridge2:
                self.ai_bridge2.start_ai_loop()
            self.add_status_message("AI Control Enabled for all NPCs")

    def disable_ai_control(self):
        """Disable AI control for all NPCs"""
        if self.ai_enabled:
            self.ai_enabled = False
            # 停止所有AI
            if hasattr(self, 'ai_bridge') and self.ai_bridge:
                self.ai_bridge.stop_ai_loop()
            if hasattr(self, 'ai_bridge2') and self.ai_bridge2:
                self.ai_bridge2.stop_ai_loop()
            self.add_status_message("AI Control Disabled for all NPCs")
    
    def add_status_message(self, message):
        """Add status message, control output"""
        # Filter output content, only keep important info
        # Check if it's a key message that should be output
        important_keywords = ["AI Decision", "Pathfinding Debug", "Plan", "Reached Target", "Time is"]
        should_print = any(keyword in message for keyword in important_keywords)
        
        # Skip processing detail output
        skip_keywords = ["Processing", "Found", "Objects at", "Nearby objects", "No nearby objects"]
        if any(keyword in message for keyword in skip_keywords):
            return
        
        # Only add important messages to status list
        if should_print:
            self.status_messages.append(message)
            if len(self.status_messages) > self.max_status_messages:
                self.status_messages.pop(0)
            print(message)  # Also output to console
            
    
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

         # Display NPC status
        if hasattr(self.ai_bridge, 'agent') and self.ai_bridge.agent:
            npc1_status = self.ai_bridge.agent.profile.status
            npc1_text = f"NPC1 Status: Mood={npc1_status['mood']}, Health={npc1_status['health']}"
            npc1_surface = font.render(npc1_text, True, (255, 255, 200))
            self.screen.blit(npc1_surface, (10, 570))
        
        if hasattr(self, 'ai_bridge2') and hasattr(self.ai_bridge2, 'agent') and self.ai_bridge2.agent:
            npc2_status = self.ai_bridge2.agent.profile.status
            npc2_text = f"NPC2 Status: Mood={npc2_status['mood']}, Health={npc2_status['health']}"
            npc2_surface = font.render(npc2_text, True, (255, 255, 200))
            self.screen.blit(npc2_surface, (10, 590))
            
        # Display controls help
        controls_text = "Controls: WASD=Move, E=Talk to NPC, Enter=Command, Tab=Toggle Status"
        controls_surface = font.render(controls_text, True, (180, 180, 220))
        self.screen.blit(controls_surface, (10, 610))
    
    def print_help(self):
        """Display all available commands help"""
        help_text = [
            "--- Command Help ---",
            "ai on|off|status - Control AI agent",
            "time pause|scale <value>|set <hour> <minute> - Control game time",
            "goto [npc1|npc2] <object> - Go to specified object",
            "goto_tile <layer> <x> <y> - Go to specified position",
            "interact [npc1|npc2] [object] - Interact with object",
            "list - List nearby objects",
            "status - Show NPC status",
            "help - Show this help"
        ]
        
        for text in help_text:
            self.add_status_message(text)
        
        self.add_status_message("--- Hotkeys ---")
        self.add_status_message("F1=Toggle AI, F2=Pause time")
        self.add_status_message("F3=Slow time, F4=Speed up time, F5=Normal speed")
        self.add_status_message("Tab=Toggle status display, E=Talk to NPC when nearby")


game().run()