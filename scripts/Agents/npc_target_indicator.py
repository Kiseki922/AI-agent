import pygame
import time
import os

class NPCTargetIndicator:
    """
    NPC目标指示器 - 在NPC头部上方显示其当前目标的图标
    修复版本：使用文字图标替代emoji，确保在pygame中正确显示
    """
    
    def __init__(self, game):
        """
        初始化目标指示器
        
        Args:
            game: 游戏实例
        """
        self.game = game
        self.font = pygame.font.SysFont(None, 20)
        self.icon_font = pygame.font.SysFont(None, 28)  # 稍大一些显示图标
        
        # 尝试加载支持emoji的字体
        self.emoji_font = self._load_emoji_font()
        
        # 目标对象到图标的映射 - 使用文字图标作为备选
        self.target_icons = {
            # 家具类
            "bed": {"emoji": "🛏️", "text": "BED", "color": (255, 200, 100)},
            "sofa": {"emoji": "🛋️", "text": "SOFA", "color": (150, 200, 255)}, 
            "sofa in fornt of TV": {"emoji": "📺", "text": "TV", "color": (255, 150, 150)},
            "chair": {"emoji": "🪑", "text": "CHAIR", "color": (200, 150, 100)},
            "chair_in_fornt_of_desk": {"emoji": "🪑", "text": "DESK", "color": (100, 200, 150)},
            
            # 电器类
            "ref": {"emoji": "🧊", "text": "FRIDGE", "color": (100, 150, 255)},
            "refrigerator": {"emoji": "🧊", "text": "FRIDGE", "color": (100, 150, 255)}, 
            "tv": {"emoji": "📺", "text": "TV", "color": (255, 100, 100)},
            "computer": {"emoji": "💻", "text": "PC", "color": (150, 150, 255)},
            
            # 房间设施
            "toilet": {"emoji": "🚽", "text": "WC", "color": (200, 200, 200)},
            "shower": {"emoji": "🚿", "text": "SHOWER", "color": (100, 200, 255)},
            "window": {"emoji": "🪟", "text": "WINDOW", "color": (200, 255, 200)},
            "door": {"emoji": "🚪", "text": "DOOR", "color": (150, 100, 50)},
            
            # 其他物品
            "bookshelf": {"emoji": "📚", "text": "BOOK", "color": (255, 200, 150)},
            "food": {"emoji": "🍽️", "text": "FOOD", "color": (255, 150, 100)},
            "kitchen": {"emoji": "🍳", "text": "COOK", "color": (255, 200, 100)},
            
            # 默认图标和状态
            "default": {"emoji": "❓", "text": "?", "color": (200, 200, 200)},
            "resting": {"emoji": "😴", "text": "REST", "color": (200, 200, 255)},
            "chatting": {"emoji": "💬", "text": "CHAT", "color": (255, 200, 255)}
        }
        
        # 活动状态到图标的映射
        self.activity_icons = {
            "去冰箱拿东西": "ref",
            "去沙发上放松": "sofa",
            "去床上休息": "bed",
            "去床上睡觉": "resting",
            "在桌子旁工作": "table",
            "在沙发上聊天": "chatting",
            "在沙发上与NPC1聊天": "chatting",
            "在沙发上与NPC2聊天": "chatting",
            "看电视": "tv",
            "在卧室休息": "bed",
            "休息": "resting",
            "睡觉": "resting",
            "聊天": "chatting"
        }
        
        # 图标显示配置
        self.icon_offset_y = -45  # 图标在NPC头部上方的距离
        self.background_size = (60, 30)  # 图标背景框大小
        
        # 动画效果
        self.bounce_amplitude = 3  # 跳动幅度
        self.bounce_speed = 3  # 跳动速度
        
        # 显示模式：'emoji', 'text', 'auto'
        self.display_mode = 'auto'  # 自动选择最佳显示方式
    
    def _load_emoji_font(self):
        """尝试加载支持emoji的字体"""
        emoji_fonts = [
            # Windows emoji字体
            "seguiemj.ttf",
            "C:/Windows/Fonts/seguiemj.ttf",
            # macOS emoji字体
            "/System/Library/Fonts/Apple Color Emoji.ttc",
            # Linux emoji字体
            "/usr/share/fonts/truetype/noto-color-emoji/NotoColorEmoji.ttf",
            # 备选字体
            "NotoColorEmoji.ttf",
            "arial.ttf"
        ]
        
        for font_path in emoji_fonts:
            try:
                if os.path.exists(font_path):
                    return pygame.font.Font(font_path, 24)
            except:
                continue
        
        # 如果都失败了，返回系统默认字体
        return pygame.font.SysFont(['segoeuiemoji', 'applesymbols', 'symbola'], 24)
    
    def _can_display_emoji(self, emoji_text):
        """测试是否能正确显示emoji"""
        try:
            if self.emoji_font:
                surface = self.emoji_font.render(emoji_text, True, (255, 255, 255))
                return surface.get_width() > 5  # 如果宽度太小，说明字符没有正确渲染
        except:
            pass
        return False
    
    def get_npc_target_icon(self, npc_id):
        """
        获取NPC当前目标的图标
        
        Args:
            npc_id: NPC的ID (如 "npc1", "npc2")
            
        Returns:
            tuple: (图标信息字典, 是否显示)
        """
        # 首先检查AI Bridge中的当前计划
        ai_bridge = None
        if npc_id == "npc1" and hasattr(self.game, 'ai_bridge'):
            ai_bridge = self.game.ai_bridge
        elif npc_id == "npc2" and hasattr(self.game, 'ai_bridge2'):
            ai_bridge = self.game.ai_bridge2
        
        # 从AI Bridge获取当前计划
        if ai_bridge and hasattr(ai_bridge, 'agent'):
            agent = ai_bridge.agent
            if hasattr(agent, 'planning') and agent.planning.current_plan:
                # 获取当前正在进行的计划步骤
                current_step = None
                for step in agent.planning.current_plan:
                    if step.get("status") == "pending":
                        current_step = step
                        break
                
                if current_step:
                    action = current_step.get("action", "")
                    # 从活动描述中找到对应的图标
                    for activity, icon_key in self.activity_icons.items():
                        if activity in action:
                            return self.target_icons.get(icon_key, self.target_icons["default"]), True
        
        # 检查NPC控制器中的移动目标
        if hasattr(self.game, 'npc_controller') and self.game.npc_controller:
            npc = self.game.npc_controller.get_npc(npc_id)
            if npc:
                # 检查是否正在移动到目标
                if npc.moving and npc.current_target:
                    return self.target_icons.get("moving"), True
                
                # 检查交互目标
                if hasattr(npc, 'interaction_target') and npc.interaction_target:
                    target_name = npc.interaction_target.lower()
                    for obj_name in self.target_icons:
                        if obj_name.lower() in target_name:
                            return self.target_icons[obj_name], True
                
                # 检查是否正在与某个对象交互
                if hasattr(npc, 'interacting') and npc.interacting:
                    return self.target_icons.get("resting"), True
        
        # 检查命令队列中的下一个命令
        if ai_bridge and hasattr(ai_bridge, 'commands_queue') and ai_bridge.commands_queue:
            next_command = ai_bridge.commands_queue[0]
            if len(next_command) >= 2:
                cmd_type, cmd_param = next_command[0], next_command[1]
                
                if cmd_type == "goto" and cmd_param:
                    return self.target_icons.get(cmd_param, self.target_icons["default"]), True
                elif cmd_type == "interact_with" and cmd_param:
                    return self.target_icons.get(cmd_param, self.target_icons["default"]), True
                elif cmd_type == "rest":
                    return self.target_icons.get("resting"), True
                elif cmd_type == "eat":
                    return self.target_icons.get("food"), True
        
        # 检查是否在聊天时间
        if hasattr(self.game, 'game_time'):
            hour = self.game.game_time["hour"]
            if 13 <= hour < 18:
                return self.target_icons.get("chatting"), True
        
        # 默认不显示图标
        return None, False
    
    def render_npc_targets(self):
        """
        渲染所有NPC的目标指示器
        """
        if not hasattr(self.game, 'npc_controller') or not self.game.npc_controller:
            return
        
        current_time = time.time()
        
        # 遍历所有NPC
        for npc_id, npc in self.game.npc_controller.npcs.items():
            # 获取目标图标
            icon_info, should_show = self.get_npc_target_icon(npc_id)
            
            if should_show and icon_info:
                # 计算NPC头部位置
                npc_center_x = npc.rect.centerx
                npc_top_y = npc.rect.top
                
                # 计算图标位置（带跳动动画）
                bounce_offset = int(self.bounce_amplitude * 
                                  abs(pygame.math.Vector2(0, 1).rotate(current_time * 100 * self.bounce_speed).y))
                
                icon_x = npc_center_x
                icon_y = npc_top_y + self.icon_offset_y - bounce_offset
                
                # 绘制图标
                self._draw_target_icon(icon_info, icon_x, icon_y, npc_id)
    
    def _draw_target_icon(self, icon_info, x, y, npc_id):
        """
        绘制单个目标图标
        
        Args:
            icon_info: 图标信息字典
            x, y: 图标位置
            npc_id: NPC的ID（用于颜色区分）
        """
        if not icon_info:
            return
            
        bg_width, bg_height = self.background_size
        
        # 创建背景
        bg_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        
        # 根据NPC ID选择不同的背景颜色
        if npc_id == "npc1":
            bg_color = (50, 100, 150, 200)  # 蓝色
        elif npc_id == "npc2":
            bg_color = (150, 50, 100, 200)  # 粉色
        else:
            bg_color = (100, 100, 100, 200)  # 灰色
        
        bg_surface.fill(bg_color)
        
        # 添加边框
        pygame.draw.rect(bg_surface, (255, 255, 255, 150), 
                        (0, 0, bg_width, bg_height), 2)
        
        # 计算居中位置
        bg_x = x - bg_width // 2
        bg_y = y - bg_height // 2
        
        # 绘制背景
        self.game.screen.blit(bg_surface, (bg_x, bg_y))
        
        # 尝试绘制emoji，如果失败则使用文字
        icon_rendered = False
        
        if self.display_mode in ['emoji', 'auto']:
            emoji_text = icon_info.get("emoji", "")
            if emoji_text and self._can_display_emoji(emoji_text):
                try:
                    icon_surface = self.emoji_font.render(emoji_text, True, (255, 255, 255))
                    if icon_surface.get_width() > 5:  # 确保正确渲染
                        icon_rect = icon_surface.get_rect()
                        icon_x = bg_x + (bg_width - icon_rect.width) // 2
                        icon_y = bg_y + (bg_height - icon_rect.height) // 2
                        self.game.screen.blit(icon_surface, (icon_x, icon_y))
                        icon_rendered = True
                except:
                    pass
        
        # 如果emoji渲染失败，使用文字图标
        if not icon_rendered:
            text = icon_info.get("text", "?")
            color = icon_info.get("color", (255, 255, 255))
            
            # 根据文字长度选择字体大小
            if len(text) <= 2:
                font = self.icon_font
            else:
                font = pygame.font.SysFont(None, 18)
            
            text_surface = font.render(text, True, color)
            text_rect = text_surface.get_rect()
            
            # 居中绘制文字
            text_x = bg_x + (bg_width - text_rect.width) // 2
            text_y = bg_y + (bg_height - text_rect.height) // 2
            self.game.screen.blit(text_surface, (text_x, text_y))
        
        # 可选：添加NPC ID标识（小文字）
        if hasattr(self, 'show_npc_id') and self.show_npc_id:
            id_text = self.font.render(npc_id[-1], True, (255, 255, 255))
            id_x = bg_x + bg_width - 12
            id_y = bg_y - 8
            self.game.screen.blit(id_text, (id_x, id_y))
    
    def add_custom_target_icon(self, target_name, emoji, text, color):
        """
        添加自定义目标图标映射
        
        Args:
            target_name: 目标名称
            emoji: emoji字符串
            text: 文字替代
            color: 文字颜色 (R, G, B)
        """
        self.target_icons[target_name] = {
            "emoji": emoji,
            "text": text,
            "color": color
        }
    
    def add_custom_activity_icon(self, activity_name, target_key):
        """
        添加自定义活动图标映射
        
        Args:
            activity_name: 活动名称
            target_key: 对应的目标键值
        """
        self.activity_icons[activity_name] = target_key
    
    def set_display_mode(self, mode):
        """
        设置显示模式
        
        Args:
            mode: 'emoji' - 只显示emoji, 'text' - 只显示文字, 'auto' - 自动选择
        """
        if mode in ['emoji', 'text', 'auto']:
            self.display_mode = mode
    
    def set_icon_offset(self, offset_y):
        """
        设置图标在NPC头部上方的距离
        
        Args:
            offset_y: Y轴偏移量（负数表示向上）
        """
        self.icon_offset_y = offset_y
    
    def set_animation_params(self, amplitude, speed):
        """
        设置跳动动画参数
        
        Args:
            amplitude: 跳动幅度
            speed: 跳动速度
        """
        self.bounce_amplitude = amplitude
        self.bounce_speed = speed