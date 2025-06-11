import pygame
import time
import re
import requests  # 新增 - 用于LLM API调用
import json      # 新增 - 用于JSON处理

class DialogueSystem:
    def __init__(self, game):
        # 在初始化函数中添加滚动位置变量
        self.scroll_position = 0
        self.max_scroll = 0
        self.game = game
        self.active = False
        self.dialogue_history = []
        self.current_input = ""
        self.font = pygame.font.SysFont(None, 24)
        self.title_font = pygame.font.SysFont(None, 32)
        self.prev_game_time_paused = False
        self.agent_response = ""
        self.task_assigned = False
        self.task_description = ""
        self.task_completed = False
        
        # 新增：跟踪玩家是否是第一次与NPC对话
        self.first_interaction = True
        self.player_has_sent_message = False  # 跟踪玩家是否发送过消息
        
        # LLM API配置 - 新增
        self.llm_api_url = "http://127.0.0.1:1234/v1/chat/completions"
        self.model_name = "deepseek-r1-distill-qwen-7b"
        
        # 对话上下文管理 - 新增
        self.conversation_context = []
        self.max_context_messages = 10  # 保留最近10条对话作为上下文
        
        # NPC角色设定 - 新增
        self.npc_persona = {
            "name": "AI Assistant",
            "personality": "helpful, friendly, and knowledgeable",
            "role": "home assistant",
            "background": "I am an AI assistant living in this virtual home. I can help with various tasks and enjoy chatting with residents.",
            "interests": ["helping others", "learning new things", "home management", "technology"],
            "speaking_style": "casual and warm, but informative when needed"
        }
        
        # Style for the dialogue box
        self.box_color = (30, 30, 50, 220)  # Dark blue with alpha
        self.text_color = (255, 255, 255)  # White
        self.input_color = (220, 220, 220)  # Light grey
        self.title_color = (200, 200, 100)  # Gold-like
        self.separator_color = (100, 100, 150)  # Light blue
        
        # Colors for status bars
        self.status_colors = {
            "good": (100, 200, 100),      # Green
            "medium": (200, 200, 100),    # Yellow
            "bad": (200, 100, 100)        # Red
        }
        
        # Size and position
        screen_width, screen_height = game.screen.get_size()
        self.width = int(screen_width * 0.6)
        self.height = int(screen_height * 0.6)
        self.x = (screen_width - self.width) // 2
        self.y = (screen_height - self.height) // 2
        
        # 添加缺失的 padding 属性 - 修复
        self.padding = 20
        
        # Input box dimensions
        self.input_box_height = 40
        self.input_box_y = self.y + self.height - self.input_box_height - self.padding
        
        # Status bar dimensions
        self.status_bar_height = 20
        self.status_bar_width = 150
        
        # 加载NPC人物设定 - 新增
        self.load_npc_persona()
        
        # Sound effects (optional)
        self.sound_open = None
        self.sound_close = None
        self.sound_type = None

    def load_npc_persona(self):
        """从AI agent加载NPC人物设定"""
        if hasattr(self.game, 'ai_bridge') and self.game.ai_bridge and hasattr(self.game.ai_bridge, 'agent'):
            agent = self.game.ai_bridge.agent
            if hasattr(agent, 'profile'):
                # 更新NPC角色信息
                self.npc_persona.update({
                    "name": agent.profile.name,
                    "personality": ", ".join([f"{k}: {v}" for k, v in agent.profile.traits.items()]),
                    "role": agent.profile.occupation,
                    "background": agent.profile.background,
                    "interests": ", ".join(agent.profile.interests) if agent.profile.interests else "general topics"
                })
            
    def is_player_near_agent(self):
        """Check if the player is within 3x3 grid around the agent"""
        if not hasattr(self.game, 'player') or not hasattr(self.game, 'npc_controller'):
            return False
            
        if 'npc1' not in self.game.npc_controller.npcs:
            return False
            
        npc = self.game.npc_controller.npcs['npc1']
        
        # Get grid positions
        player_grid_x = self.game.player.grid_pos[0]
        player_grid_y = self.game.player.grid_pos[1]
        npc_grid_x = npc.grid_pos[0]
        npc_grid_y = npc.grid_pos[1]
        
        # Check if player is within 3x3 grid around agent
        distance_x = abs(player_grid_x - npc_grid_x)
        distance_y = abs(player_grid_y - npc_grid_y)
        
        return distance_x <= 1 and distance_y <= 1  # 3x3 area means 1 cell in each direction
        
    def handle_input_event(self, event):
        """Handle input events for the dialogue system"""
        if not self.active:
            # Check for E key press to start dialogue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                if self.is_player_near_agent():
                    self.open_dialogue()
                    return True  # Return True to indicate event was handled
            return False
            
        # When dialogue is active
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Close dialogue on ESC
                self.close_dialogue()
                return True
            elif event.key == pygame.K_RETURN:
                # Process input on ENTER
                if self.current_input.strip():  # 只有当输入不为空时才处理
                    self.process_dialogue_input()
                return True
            elif event.key == pygame.K_BACKSPACE:
                # Backspace to delete characters
                self.current_input = self.current_input[:-1]
                return True
            # 添加上下箭头键滚动支持
            elif event.key == pygame.K_UP:
                self.scroll_position = max(0, self.scroll_position - 30)
                return True
            elif event.key == pygame.K_DOWN:
                self.scroll_position = min(self.max_scroll, self.scroll_position + 30)
                return True
            # 添加Page Up/Down支持
            elif event.key == pygame.K_PAGEUP:
                self.scroll_position = max(0, self.scroll_position - 100)
                return True
            elif event.key == pygame.K_PAGEDOWN:
                self.scroll_position = min(self.max_scroll, self.scroll_position + 100)
                return True
            else:
                # Add typed characters to input - show in real time
                if event.unicode and ord(event.unicode) >= 32:  # printable characters
                    self.current_input += event.unicode
                    return True
            
            # 处理鼠标滚轮事件
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查鼠标是否在对话框内
            mouse_x, mouse_y = event.pos
            if (self.x <= mouse_x <= self.x + self.width and 
                self.y <= mouse_y <= self.y + self.height):
                
                if event.button == 4:  # 滚轮向上滚动
                    self.scroll_position = max(0, self.scroll_position - 40)
                    return True
                elif event.button == 5:  # 滚轮向下滚动
                    self.scroll_position = min(self.max_scroll, self.scroll_position + 40)
                    return True
                
        return self.active  # Return True if dialogue is active to consume the event
    
    def auto_scroll_to_bottom(self):
        """自动滚动到对话历史的底部"""
        # 这个方法会在新消息添加后调用
        self.scroll_position = self.max_scroll

    def process_dialogue_input(self):
        """Process player input and generate agent response"""
        player_input = self.current_input
        self.current_input = ""  # Clear input field
        
        # 标记玩家已经发送过消息
        self.player_has_sent_message = True
        
        # Add player input to history
        self.dialogue_history.append(("Player", player_input))
        
        # 更新对话上下文
        self.update_conversation_context("Player", player_input)
        
        # 提升NPC心情（与玩家对话）
        self.improve_npc_mood()

        if hasattr(self.game, 'ai_bridge') and self.game.ai_bridge and hasattr(self.game.ai_bridge, 'agent'):
            agent = self.game.ai_bridge.agent
            if hasattr(agent, 'profile'):
                # 与玩家对话，心情+10
                old_mood = agent.profile.status.get("mood", 0)
                agent.profile.update_status("mood", 10)
                new_mood = agent.profile.status.get("mood", 0)
                
                # 添加状态消息
                if hasattr(self.game, 'add_status_message'):
                    self.game.add_status_message(f"NPC与玩家对话: 心情+10 ({old_mood}->{new_mood})")

        # Process the input to detect tasks
        task_detected = self.detect_task(player_input)
        
        if task_detected:
            # If a task is detected, acknowledge it
            self.agent_response = f"Alright, I'll {self.task_description}. Talk to you later!"
            self.task_assigned = True
            # Set up the task in agent's schedule
            self.setup_task_for_agent()
        elif "bye" in player_input.lower() or "goodbye" in player_input.lower():
            # Farewell message
            self.agent_response = self.generate_llm_response(player_input, is_farewell=True)
        else:
            # 只有在玩家发送了实际消息后才使用LLM生成回应
            self.agent_response = self.generate_llm_response(player_input)
        
        # Add agent response to history and context
        self.dialogue_history.append(("NPC", self.agent_response))
        self.update_conversation_context("NPC", self.agent_response)
        
        # 自动滚动到底部显示最新消息
        self.auto_scroll_to_bottom()
        
        # If this was a goodbye or task assignment, close the dialogue
        if self.task_assigned or "bye" in player_input.lower() or "goodbye" in player_input.lower():
            # Wait a short moment to show the response before closing
            pygame.time.delay(1500)  # 1.5 seconds delay
            self.close_dialogue()
    
    def open_dialogue(self):
        """Open the dialogue interface"""
        if self.active:
            return
            
        self.active = True
        
        # Remember game time state to restore it later
        self.prev_game_time_paused = self.game.game_time["paused"]
        
        # CRITICAL FIX: Force time to pause completely
        self.game.game_time["paused"] = True
        
        # Also stop all NPC movement and AI behavior temporarily
        if hasattr(self.game, 'ai_bridge') and self.game.ai_bridge:
            if self.game.ai_enabled:
                # Store AI state to restore later
                self.prev_ai_enabled = self.game.ai_enabled
                # Temporarily disable AI
                self.game.ai_enabled = False
        
        # 加载最新的NPC信息 - 新增
        self.load_npc_persona()
        
        # 根据交互状态生成初始回应
        if self.task_completed:
            self.agent_response = "I've completed the task you gave me! What else would you like me to do?"
            self.task_completed = False  # Reset after informing the player
        elif self.first_interaction:
            # 第一次交互，根据时间生成问候语
            self.agent_response = self.generate_time_based_greeting()
            self.first_interaction = False
        else:
            # 后续交互，使用固定回应
            self.agent_response = "Hello, see you again!"
        
        # Add initial response to history
        self.dialogue_history.append(("NPC", self.agent_response))
        
        # Clear current input
        self.current_input = ""
    
    def close_dialogue(self):
        """Close the dialogue interface"""
        if not self.active:
            return
            
        self.active = False
        
        # Restore game time state
        self.game.game_time["paused"] = self.prev_game_time_paused
        
        # Restore AI state if needed
        if hasattr(self.game, 'ai_bridge') and self.game.ai_bridge and hasattr(self, 'prev_ai_enabled'):
            self.game.ai_enabled = self.prev_ai_enabled
        
        # Play sound if available
        # if self.sound_close:
        #     self.sound_close.play()
    
    def update_conversation_context(self, speaker, message):
        """更新对话上下文"""
        self.conversation_context.append({"role": speaker.lower(), "content": message})
        
        # 保持上下文在合理范围内
        if len(self.conversation_context) > self.max_context_messages:
            # 移除最老的对话，但保留系统prompt
            self.conversation_context = self.conversation_context[-self.max_context_messages:]
            
    def generate_time_based_greeting(self):
        """生成基于时间的问候语（仅第一次交互使用）"""
        # 获取当前游戏时间
        hour = self.game.game_time["hour"]
        minute = int(self.game.game_time["minute"])
        
        # 根据时间生成简单的问候语
        if 5 <= hour < 12:
            return "Good morning! How can I help you today?"
        elif 12 <= hour < 18:
            return "Good afternoon! What would you like to chat about?"
        else:
            return "Good evening! How are you doing?"
            
    def generate_llm_response(self, user_input, is_farewell=False):
        """使用LLM生成回应（仅在玩家发送消息后使用）"""
        # 只有在玩家发送过消息后才使用LLM
        if not self.player_has_sent_message and not is_farewell:
            return "Hello, see you again!"
        
        # 获取NPC当前状态
        npc_status = self._get_npc_status()
        current_hour = self.game.game_time["hour"]
        current_minute = int(self.game.game_time["minute"])
        
        # 构建系统提示 - 强制英文
        system_prompt = f"""You are {self.npc_persona['name']}, a {self.npc_persona['role']} in a virtual home environment.

Your personality and traits:
- {self.npc_persona['personality']}
- Background: {self.npc_persona['background']}
- Interests: {self.npc_persona['interests']}
- Speaking style: {self.npc_persona['speaking_style']}

Current context:
- Time: {current_hour:02d}:{current_minute:02d}
- Your mood: {npc_status.get('mood', 50) if npc_status else 50}/100
- Your health: {npc_status.get('health', 100) if npc_status else 100}

CRITICAL INSTRUCTIONS:
- Respond ONLY in English
- Do NOT use Chinese characters
- Do NOT include thinking process or <think> tags
- Respond naturally and conversationally
- Stay in character based on your personality
- Reference your current mood/status if relevant
- Be helpful when asked questions
- Keep responses concise but engaging (1-3 sentences usually)
- Don't use prefixes like "NPC:" or "Assistant:"
- You can mention what you've been doing today if appropriate

IMPORTANT: Your entire response must be in English only."""

        # 构建对话历史
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加最近的对话上下文
        for context in self.conversation_context[-6:]:  # 取最近6条对话
            role = "user" if context["role"] == "player" else "assistant"
            messages.append({"role": role, "content": context["content"]})
        
        # 添加当前用户输入
        messages.append({"role": "user", "content": user_input})
        
        # 如果是告别，添加特殊指示
        if is_farewell:
            messages.append({"role": "system", "content": "The user is saying goodbye. Respond warmly and naturally in English only."})
        
        # 首先尝试使用LLM
        try:
            response = self.query_llm_with_messages(messages)
            if response and len(response.strip()) > 0:
                return response
        except Exception as e:
            print(f"LLM response generation failed: {e}")
        
        # 如果LLM失败，使用智能备用响应
        return self.get_smart_fallback_response(user_input, is_farewell, npc_status)
    
    def wrap_text(self, text, max_width, font=None):
        """
        将长文本按指定宽度换行
        
        Args:
            text: 要换行的文本
            max_width: 最大宽度（像素）
            font: 使用的字体，如果为None则使用默认字体
        
        Returns:
            包含换行后文本的列表
        """
        if font is None:
            font = self.font
        
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            # 测试加入这个单词后的行宽
            test_line = current_line + (" " if current_line else "") + word
            test_width = font.size(test_line)[0]
            
            if test_width <= max_width:
                # 如果宽度允许，添加单词到当前行
                current_line = test_line
            else:
                # 如果宽度超出，开始新行
                if current_line:  # 如果当前行不为空
                    lines.append(current_line)
                    current_line = word
                else:
                    # 如果单个单词就超出宽度，强制添加并换行
                    lines.append(word)
                    current_line = ""
        
        # 添加最后一行
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def get_smart_fallback_response(self, user_input, is_farewell, npc_status):
        """获取智能备用响应"""
        import random
        
        if is_farewell:
            farewell_responses = [
                "Take care! See you later!",
                "Goodbye! Have a great day!",
                "See you soon! Take care of yourself!",
                "Bye! It was nice talking to you!",
                "Until next time! Stay safe!"
            ]
            return random.choice(farewell_responses)
        
        # 根据用户输入内容给出相应回应
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ["hello", "hi", "hey"]):
            greetings = [
                "Hello! Nice to see you!",
                "Hi there! How are you doing?",
                "Hey! What's up?",
                "Hello! Good to see you again!"
            ]
            return random.choice(greetings)
        
        elif any(word in user_lower for word in ["how", "doing", "feeling"]):
            if npc_status and npc_status.get('mood', 50) > 70:
                return "I'm feeling pretty good today! Thanks for asking."
            elif npc_status and npc_status.get('mood', 50) < 30:
                return "I'm not feeling my best, but talking to you helps."
            else:
                return "I'm doing alright, thanks for asking!"
        
        elif any(word in user_lower for word in ["thank", "thanks"]):
            return "You're welcome! Happy to help!"
        
        elif any(word in user_lower for word in ["help", "assist"]):
            return "I'd be happy to help! What do you need assistance with?"
        
        else:
            general_responses = [
                "That's interesting! Tell me more.",
                "I see what you mean.",
                "That sounds nice!",
                "What would you like to know?",
                "I'm here if you need anything else.",
                "That's a good point!",
                "I understand. Is there anything specific you'd like to discuss?"
            ]
            return random.choice(general_responses)

    def query_llm_with_messages(self, messages):
        """向LLM发送对话消息列表"""
        try:
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 200
            }
            
            # 增加超时时间并添加重试机制
            response = requests.post(self.llm_api_url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return self.clean_response(result["choices"][0]["message"]["content"])
                
        except requests.exceptions.Timeout:
            print(f"LLM conversation query timeout - using fallback response")
            return None
        except requests.exceptions.ConnectionError:
            print(f"LLM connection error - check if LM Studio is running")
            return None
        except requests.exceptions.RequestException as e:
            print(f"LLM request error: {e}")
            return None
        except Exception as e:
            print(f"LLM conversation query failed: {e}")
            return None
            
        return None
    
    def clean_response(self, text):
        """清理LLM响应"""
        # 移除可能的前缀
        text = re.sub(r'^(NPC|Assistant|AI):\s*', '', text)
        text = re.sub(r'^["\']|["\']$', '', text)  # 移除首尾引号
        
        # 移除思考过程标记
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        
        return text.strip()
    
    def improve_npc_mood(self):
        """对话提升NPC心情"""
        if hasattr(self.game, 'ai_bridge') and self.game.ai_bridge:
            if hasattr(self.game.ai_bridge, 'agent') and hasattr(self.game.ai_bridge.agent, 'profile'):
                agent = self.game.ai_bridge.agent
                old_mood = agent.profile.status.get("mood", 0)
                agent.profile.update_status("mood", 10)  # 与玩家对话，心情+10
                new_mood = agent.profile.status.get("mood", 0)
                
                # 添加状态消息
                if hasattr(self.game, 'add_status_message'):
                    self.game.add_status_message(f"NPC与玩家对话: 心情+10 ({old_mood}->{new_mood})")

    def detect_task(self, input_text):
        """Detect if the input contains a task assignment"""
        # Look for common task patterns
        task_patterns = [
            r"go to(.+?)and(.+)",
            r"help me(.+)",
            r"can you(.+)",
            r"please go(.+)",
            r"would you(.+)",
            r"get(.+)",
            r"bring(.+)",
            r"fetch(.+)",
        ]
        
        for pattern in task_patterns:
            match = re.search(pattern, input_text.lower())
            if match:
                # Extract the task description
                if "fridge" in input_text.lower() and "table" in input_text.lower():
                    self.task_description = "get food from the fridge"
                elif "fridge" in input_text.lower():
                    self.task_description = "get something from the fridge"
                elif "table" in input_text.lower():
                    self.task_description = "get something from the table"
                elif "bed" in input_text.lower():
                    self.task_description = "go to bed and rest"
                elif "sofa" in input_text.lower():
                    self.task_description = "go to sofa and rest"
                elif "sofa" in input_text.lower():
                    self.task_description = "relax on the sofa"
                elif "shower" in input_text.lower():
                    self.task_description = "take a shower"
                elif "tv" in input_text.lower() or "television" in input_text.lower():
                    self.task_description = "watch TV"
                else:
                    # Default task description if no specific objects mentioned
                    self.task_description = match.group(1) if len(match.groups()) > 0 else "complete the task"
                
                return True
        
        return False
    
    def setup_task_for_agent(self):
        """Set up the task in the agent's schedule"""
        if not hasattr(self.game, 'ai_bridge') or not self.game.ai_bridge:
            print("AI Bridge not initialized, cannot set up task")
            return
        
        # Clear existing commands
        self.game.ai_bridge.commands_queue.clear()

        # 设置任务标志
        self.task_assigned = True
        self.task_completed = False
        
        # 解析任务确定所需的操作
        # [保持现有的任务解析代码不变]
        
        # 使AI执行这些命令
        if not self.game.ai_enabled:
            self.game.enable_ai_control()
        
        # 添加状态消息到游戏
        if hasattr(self.game, 'add_status_message'):
            self.game.add_status_message(f"玩家任务已分配: {self.task_description}")
            self.game.add_status_message("玩家任务优先级高于日程表")
        
        # Parse the task to determine required actions
        if "fridge" in self.task_description and "table" in self.task_description:
            # Task: Get something from fridge and put it on table
            # First go to fridge
            self.game.ai_bridge.commands_queue.append(("goto", "ref"))
            # Interact with fridge
            self.game.ai_bridge.commands_queue.append(("interact_with", "ref"))
            # Then go to table
            self.game.ai_bridge.commands_queue.append(("goto", "table"))
            # Return to player after completing task
            self.game.ai_bridge.commands_queue.append(("return_to_player", None))
        elif "fridge" in self.task_description:
            # Task: Go to fridge
            self.game.ai_bridge.commands_queue.append(("goto", "ref"))
            self.game.ai_bridge.commands_queue.append(("interact_with", "ref"))
            self.game.ai_bridge.commands_queue.append(("return_to_player", None))
        elif "table" in self.task_description:
            # Task: Go to table
            self.game.ai_bridge.commands_queue.append(("goto", "table"))
            self.game.ai_bridge.commands_queue.append(("interact_with", "table"))
            self.game.ai_bridge.commands_queue.append(("return_to_player", None))
        elif "bed" in self.task_description:
            # Task: Go to bed
            self.game.ai_bridge.commands_queue.append(("goto", "bed"))
            self.game.ai_bridge.commands_queue.append(("interact_with", "bed"))
            self.game.ai_bridge.commands_queue.append(("return_to_player", None))
        elif "shower" in self.task_description:
            # Task: Take a shower
            self.game.ai_bridge.commands_queue.append(("goto", "shower"))
            self.game.ai_bridge.commands_queue.append(("interact_with", "shower"))
            self.game.ai_bridge.commands_queue.append(("return_to_player", None))
        elif "tv" in self.task_description:
            # Task: Watch TV
            self.game.ai_bridge.commands_queue.append(("goto", "tv"))
            self.game.ai_bridge.commands_queue.append(("interact_with", "tv"))
            self.game.ai_bridge.commands_queue.append(("return_to_player", None))
        else:
            # Generic task - use LLM-like response to determine action
            # Default to random movement and return
            self.game.ai_bridge.commands_queue.append(("random_move", None))
            self.game.ai_bridge.commands_queue.append(("return_to_player", None))
            
            # Process the task description to determine best action
            common_objects = ["bed", "sofa", "chair", "fridge", "ref", "kitchen", 
                            "tv", "bookshelf", "computer", "game", "toilet", 
                            "shower", "window", "door"]
            
            for obj in common_objects:
                if obj in self.task_description.lower():
                    # Found a matching object in the task description
                    self.game.ai_bridge.commands_queue.clear()  # Clear default commands
                    self.game.ai_bridge.commands_queue.append(("goto", obj))
                    self.game.ai_bridge.commands_queue.append(("interact_with", obj))
                    self.game.ai_bridge.commands_queue.append(("return_to_player", None))
                    break
        
        # Enable AI control if not already enabled
        if not self.game.ai_enabled:
            self.game.enable_ai_control()
            
        # Force AI to execute these commands
        self.game.ai_bridge.commands_queue.insert(0, ("force_actions", None))
        
        # Add status message to game
        if hasattr(self.game, 'add_status_message'):
            self.game.add_status_message(f"Task assigned: {self.task_description}")
    
    def get_status_color(self, value):
        """Get the appropriate color for a status value"""
        if value > 70:
            return self.status_colors["good"]
        elif value > 30:
            return self.status_colors["medium"]
        else:
            return self.status_colors["bad"]
    
    def _get_npc_status(self):
        """Get NPC status from the AI bridge"""
        if hasattr(self.game, 'ai_bridge') and self.game.ai_bridge and hasattr(self.game.ai_bridge, 'agent'):
            agent = self.game.ai_bridge.agent
            if hasattr(agent, 'profile'):
                return agent.profile.status
        return None
    
    def render(self):
        """Render the dialogue interface with NPC status and real-time typing"""
        if not self.active:
            return
            
        screen = self.game.screen
        
        # 创建带透明度的对话框表面
        dialogue_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dialogue_surface.fill(self.box_color)
        
        # 获取NPC状态
        npc_status = self._get_npc_status()
        
        # 绘制标题
        title_text = self.title_font.render("Dialogue", True, self.title_color)
        title_rect = title_text.get_rect(centerx=self.width//2, top=self.padding)
        dialogue_surface.blit(title_text, title_rect)
        
        # 绘制分隔线
        pygame.draw.line(dialogue_surface, self.separator_color, 
                        (self.padding, title_rect.bottom + 10), 
                        (self.width - self.padding, title_rect.bottom + 10), 2)
        
        # 计算对话历史区域
        history_top = title_rect.bottom + 20
        
        # 添加状态条区域（如果状态可用）
        if npc_status:
            # 绘制NPC状态标签   
            status_label = self.font.render("NPC Status:", True, self.title_color)
            dialogue_surface.blit(status_label, (self.padding, history_top))
            
            # 水平放置状态条
            status_y = history_top + status_label.get_height() + 5
            
            # 绘制心情条
            self._draw_status_bar(dialogue_surface, "Mood", npc_status.get("mood", 0), 
                                self.padding, status_y)
            
            # 在心情条右侧绘制健康条
            health_x = self.padding + self.status_bar_width + 20
            self._draw_status_bar(dialogue_surface, "Health", npc_status.get("health", 0), 
                                health_x, status_y)
            
            # 更新历史区域起始位置
            history_top = status_y + self.status_bar_height + 15
        
        # 输入框底部位置，留出足够空间
        input_box_height = 40
        input_box_y = self.height - input_box_height - self.padding * 2

        # 重新计算对话区域
        history_bottom = input_box_y - 10
        history_height = history_bottom - history_top
        
        # 计算文本的最大宽度（为发言者名称和边距留出空间）
        max_text_width = self.width - self.padding * 2 - 100  # 100像素留给发言者名称
        
        # 计算包含换行的对话历史总高度
        wrapped_dialogue_data = []
        total_height = 0
        line_height = self.font.get_linesize()
        
        for speaker, text in self.dialogue_history:
            # 换行处理
            wrapped_lines = self.wrap_text(text, max_text_width)
            wrapped_dialogue_data.append((speaker, wrapped_lines))
            # 计算总高度：发言者名称 + 换行文本行数 + 间距
            total_height += line_height + len(wrapped_lines) * line_height + 5  # 5像素间距
        
        # 计算最大滚动位置
        self.max_scroll = max(0, total_height - history_height)
        
        # 确保滚动位置在有效范围内
        self.scroll_position = min(self.max_scroll, self.scroll_position)
        
        # 渲染对话历史（支持换行和滚动）
        current_y = history_top - self.scroll_position
        
        for speaker, wrapped_lines in wrapped_dialogue_data:
            # 检查是否在可见区域内
            if current_y > history_top + history_height + 50:
                break  # 如果太靠下，跳出循环
            if current_y < history_top - 100:
                # 如果太靠上，跳过但更新位置
                current_y += line_height + len(wrapped_lines) * line_height + 5
                continue
            
            # 发言者名称颜色
            speaker_color = (100, 200, 100) if speaker == "Player" else (100, 100, 200)
            
            # 绘制发言者名称
            if current_y >= history_top - line_height and current_y <= history_top + history_height:
                speaker_text = self.font.render(f"{speaker}:", True, speaker_color)
                dialogue_surface.blit(speaker_text, (self.padding, current_y))
            
            current_y += line_height
            
            # 绘制换行后的文本
            for line in wrapped_lines:
                if current_y >= history_top - line_height and current_y <= history_top + history_height:
                    # 缩进对话内容
                    message_surface = self.font.render(line, True, self.text_color)
                    dialogue_surface.blit(message_surface, (self.padding + 10, current_y))
                current_y += line_height
            
            # 对话间距
            current_y += 5
        
        # 绘制滚动条（如果需要）
        if self.max_scroll > 0:
            # 滚动条背景
            scrollbar_width = 10
            scrollbar_x = self.width - scrollbar_width - 5
            pygame.draw.rect(dialogue_surface, (50, 50, 70), 
                            (scrollbar_x, history_top, scrollbar_width, history_height))
            
            # 滚动条滑块
            if self.max_scroll > 0:
                scrollbar_height = max(20, history_height * (history_height / (self.max_scroll + history_height)))
                scrollbar_pos = history_top + (self.scroll_position / self.max_scroll) * (history_height - scrollbar_height)
                pygame.draw.rect(dialogue_surface, (150, 150, 180), 
                                (scrollbar_x, scrollbar_pos, scrollbar_width, scrollbar_height))
        
        # 绘制输入框
        pygame.draw.rect(dialogue_surface, (60, 60, 80), 
                        (self.padding, input_box_y, 
                        self.width - 2*self.padding, input_box_height))
        
        # 添加输入提示标签
        input_label = self.font.render("Your message: ", True, (180, 180, 200))
        dialogue_surface.blit(input_label, (self.padding, input_box_y + 5))
        label_width = input_label.get_width()
        
        # 显示当前输入文本（支持换行）
        input_text_area_width = self.width - 2*self.padding - label_width - 5
        
        if self.current_input:
            # 如果输入文本太长，也进行换行处理
            input_lines = self.wrap_text(self.current_input, input_text_area_width)
            # 只显示最后几行（如果输入框不够高）
            max_input_lines = input_box_height // self.font.get_linesize()
            display_lines = input_lines[-max_input_lines:] if len(input_lines) > max_input_lines else input_lines
            
            for i, line in enumerate(display_lines):
                input_text = self.font.render(line, True, (255, 255, 255))
                line_y = input_box_y + 5 + i * self.font.get_linesize()
                dialogue_surface.blit(input_text, (self.padding + label_width + 5, line_y))
            
            # 绘制光标在最后一行的末尾
            if display_lines:
                last_line = display_lines[-1]
                cursor_x = self.padding + label_width + 5 + self.font.size(last_line)[0]
                cursor_y = input_box_y + 5 + (len(display_lines) - 1) * self.font.get_linesize()
                
                # 闪烁光标
                if pygame.time.get_ticks() % 1000 < 500:
                    pygame.draw.line(dialogue_surface, (255, 255, 255), 
                                (cursor_x, cursor_y), 
                                (cursor_x, cursor_y + self.font.get_linesize()), 2)
        else:
            # 没有文本时显示占位符
            placeholder_text = self.font.render("Type your message here...", True, (120, 120, 150))
            dialogue_surface.blit(placeholder_text, (self.padding + label_width + 5, input_box_y + 10))
        
        # 绘制提示文本
        hint_text = self.font.render("Press Enter to send, Esc to exit", True, (150, 150, 150))
        hint_rect = hint_text.get_rect(bottom=self.height - 5, right=self.width - self.padding)
        dialogue_surface.blit(hint_text, hint_rect)
        
        # 将对话表面绘制到游戏屏幕
        screen.blit(dialogue_surface, (self.x, self.y))
    
    def _draw_status_bar(self, surface, label, value, x, y):
        """Draw a status bar with label and value"""
        # Draw label
        label_surface = self.font.render(f"{label}:", True, self.text_color)
        surface.blit(label_surface, (x, y))
        
        # Draw background bar
        bar_x = x + label_surface.get_width() + 5
        pygame.draw.rect(surface, (50, 50, 50), 
                        (bar_x, y, self.status_bar_width - label_surface.get_width() - 5, self.status_bar_height))
        
        # Draw value bar
        value_width = int((self.status_bar_width - label_surface.get_width() - 5) * (value / 100))
        color = self.get_status_color(value)
        pygame.draw.rect(surface, color, 
                        (bar_x, y, value_width, self.status_bar_height))
        
        # Draw value text
        value_text = self.font.render(f"{value}", True, self.text_color)
        value_rect = value_text.get_rect(center=(bar_x + (self.status_bar_width - label_surface.get_width() - 5)//2, 
                                                y + self.status_bar_height//2))
        surface.blit(value_text, value_rect)