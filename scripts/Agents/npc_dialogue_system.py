import requests
import time
import re
import json
import os
import random
import pygame
from collections import deque

# 设置 LLM API 端点
LLM_API_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL_NAME = "deepseek-r1-distill-qwen-7b"
AGENTS_DIR = "scripts/Agents/agents"  # 修改为正确的文件夹路径

class NPCMemory:
    def __init__(self, max_length=8):
        self.memory = deque(maxlen=max_length)  # 增加记忆长度
        self.current_topic = None
        self.topic_turns = 0  # 话题持续轮数
    
    def add_to_memory(self, speaker, text):
        """储存对话历史"""
        self.memory.append(f"{speaker}: {text}")
        self.topic_turns += 1
    
    def get_conversation_history(self, last_n=4):
        """获取最近的对话历史"""
        return list(self.memory)[-last_n:] if self.memory else []
    
    def set_topic(self, topic):
        """设置当前话题"""
        self.current_topic = topic
        self.topic_turns = 0
    
    def should_change_topic(self):
        """判断是否应该换话题"""
        return self.topic_turns >= random.randint(4, 8)  # 4-8轮后换话题
    
    def clear_memory(self):
        """清空对话历史"""
        self.memory.clear()
        self.current_topic = None
        self.topic_turns = 0

class NPCDialogueSystem:
    def __init__(self, game):
        self.game = game
        self.active = False
        self.shared_memory = NPCMemory()  # 共享记忆
        self.dialogue_history = []
        self.last_dialogue_time = 0
        self.dialogue_interval = 6  # 减少对话间隔让对话更频繁
        self.font = pygame.font.SysFont(None, 24)
        self.title_font = pygame.font.SysFont(None, 32)
        self.debug = False
        
        # 性能优化变量
        self.last_condition_check_time = 0
        self.condition_check_interval = 3.0
        self.last_debug_print_time = 0
        self.debug_print_interval = 30.0
        
        # 对话框样式
        self.box_color = (30, 30, 50, 220)
        self.text_color = (255, 255, 255)
        self.title_color = (200, 200, 100)
        self.separator_color = (100, 100, 150)
        
        # 位置和大小
        screen_width, screen_height = game.screen.get_size()
        self.width = int(screen_width * 0.5)
        self.height = int(screen_height * 0.6)
        self.x = screen_width - self.width - 20
        self.y = screen_height - self.height - 20
        self.padding = 20
        
        # 文本換行相關設置
        self.max_line_width = self.width - 2 * self.padding - 10
        self.line_height = self.font.get_linesize()
        
        # 滾動相關設置
        self.scroll_position = 0
        self.max_scroll = 0
        
        # 话题库
        self.topics = {
            "food": {
                "starter": [
                    "I tried this amazing restaurant yesterday - the flavors were incredible!",
                    "I'm craving something delicious today, maybe some homemade pasta or fresh sushi.",
                    "Have you eaten anything good lately? I'm always looking for new recipe ideas."
                ],
                "follow_ups": [
                    "What did you think of the taste? Was it as good as it looked?",
                    "Where did you find that recipe? I'd love to try making it myself.",
                    "I should try that sometime! Do you know what ingredients they used?",
                    "That sounds absolutely delicious! You're making me hungry just thinking about it."
                ]
            },
            "weather": {
                "starter": [
                    "It's such a beautiful day today - perfect for opening all the windows!",
                    "The weather has been so unpredictable lately, one day sunny, the next rainy.",
                    "I absolutely love this kind of weather - it makes me want to spend the whole day outside."
                ],
                "follow_ups": [
                    "Perfect weather for a long walk in the park, don't you think?",
                    "I really hope it stays like this for the weekend - I have so many outdoor plans!",
                    "Weather like this always puts me in such a good mood and makes me feel energetic."
                ]
            },
            "hobbies": {
                "starter": [
                    "I've been reading this really fascinating book lately - it's about ancient history and mysteries.",
                    "I picked up a new hobby recently and I'm totally obsessed with it now!",
                    "What do you like to do in your free time? I'm always curious about people's interests."
                ],
                "follow_ups": [
                    "That sounds really interesting! How did you first get started with that?",
                    "I've always wanted to try something like that - is it difficult to learn?",
                    "You seem so passionate about it! What's your favorite part about doing that?"
                ]
            },
            "daily_life": {
                "starter": [
                    "I had such a busy day today - running errands, cleaning, and still had time for some fun!",
                    "Something really funny happened to me earlier that I just have to tell you about.",
                    "I've been thinking about redecorating this place - maybe add some new colors and plants."
                ],
                "follow_ups": [
                    "Please tell me more about that! I love hearing about interesting experiences.",
                    "That must have been quite exciting! How did it all turn out in the end?",
                    "What gave you that idea? It sounds like a really creative and fun project."
                ]
            },
            "memories": {
                "starter": [
                    "This reminds me of something that happened years ago - such a sweet memory.",
                    "I was just thinking about an old friend from school and wondering how they're doing now.",
                    "Do you remember when we used to spend hours just talking about everything and nothing?"
                ],
                "follow_ups": [
                    "Those were really good times - I miss the simplicity of those days sometimes.",
                    "I miss those days sometimes, when everything felt so new and exciting.",
                    "It's funny how time flies - feels like yesterday but also like a lifetime ago."
                ]
            }
        }
        
        # 当前说话者
        self.current_speaker = "NPC1"  # 开始时NPC1先说话
        
        # 加载NPC人物设定
        self.load_character_profiles()
    
    def load_character_profiles(self):
        """加载NPC的人物设定"""
        self.npc1_profile = self.load_character_profile("Lisa")
        self.npc2_profile = self.load_character_profile("Lila")
    
    def load_character_profile(self, name):
        """从JSON文件加载角色设定"""
        file_path = os.path.join(AGENTS_DIR, f"{name}.agent.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    return data.get("persona", {}).get("style", "Default personality")
            except:
                pass
        
        # 使用默认性格
        if name == "Lisa":
            return "Cheerful and energetic, loves trying new things, speaks casually"
        else:
            return "Thoughtful and calm, good listener, speaks gently"
    
    def wrap_text(self, text, max_width):
        """將長文本按指定寬度換行"""
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_width = self.font.size(test_line)[0]
            
            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    lines.append(word)
                    current_line = ""
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def handle_scroll_event(self, event):
        """處理滾動事件"""
        if not self.active:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            if (self.x <= mouse_x <= self.x + self.width and 
                self.y <= mouse_y <= self.y + self.height):
                
                if event.button == 4:  # 滾輪向上
                    self.scroll_position = max(0, self.scroll_position - 20)
                    return True
                elif event.button == 5:  # 滾輪向下
                    self.scroll_position = min(self.max_scroll, self.scroll_position + 20)
                    return True
        
        return False
    
    def check_dialogue_conditions(self):
        """检查是否满足对话条件"""
        if not hasattr(self.game, 'game_time'):
            return False
        
        hour = self.game.game_time["hour"]
        if not (13 <= hour < 18):
            return False
        
        if not (hasattr(self.game, 'npc_controller') and self.game.npc_controller):
            return False
        
        npc1 = self.game.npc_controller.npcs.get("npc1")
        npc2 = self.game.npc_controller.npcs.get("npc2")
        
        if not (npc1 and npc2):
            return False
        
        if 13 <= hour < 18:
            npc1_on_sofa = self._is_npc_on_sofa(npc1)
            npc2_on_sofa = self._is_npc_on_sofa(npc2)
            
            if not npc1_on_sofa:
                self.game.npc_controller.move_npc_to_object("npc1", "sofa in fornt of TV")
                
            if not npc2_on_sofa:
                self.game.npc_controller.move_npc_to_object("npc2", "sofa in fornt of TV")
            
            return npc1_on_sofa or npc2_on_sofa

        return False
    
    def _is_npc_on_sofa(self, npc):
        """檢查NPC是否在沙發上"""
        if hasattr(npc, 'interaction_target'):
            target = npc.interaction_target
            if target and "sofa" in str(target).lower():
                return True
        return False
    
    def update(self):
        """更新对话系统状态"""
        current_time = time.time()
        if not self.active and current_time - self.last_condition_check_time < self.condition_check_interval:
            return
            
        self.last_condition_check_time = current_time
        dialogue_conditions_met = self.check_dialogue_conditions()
        
        if dialogue_conditions_met:
            if not self.active:
                self.active = True
                self.shared_memory.clear_memory()
                self.dialogue_history = []
                self.scroll_position = 0
                self.current_speaker = "NPC1"  # 重置说话者
                
                if hasattr(self.game, 'add_status_message'):
                    self.game.add_status_message("NPC1 and NPC2 started chatting on the sofa")
                
                # 选择初始话题并生成第一条对话
                self.start_new_topic()
                self.generate_dialogue()
            else:
                if current_time - self.last_dialogue_time >= self.dialogue_interval:
                    self.generate_dialogue()
        else:
            if self.active:
                if hasattr(self.game, 'add_status_message'):
                    self.game.add_status_message("NPC chat ended")
            self.active = False

        # 处理NPC位置（简化版本）
        in_chat_time = False
        if hasattr(self.game, 'game_time'):
            hour = self.game.game_time["hour"]
            if 13 <= hour < 18:
                in_chat_time = True
        
        if in_chat_time:
            npc1 = self.game.npc_controller.npcs.get("npc1")
            npc2 = self.game.npc_controller.npcs.get("npc2")
            
            sofa_position = None
            if hasattr(self.game, 'tmx_data'):
                for obj_group in self.game.tmx_data.objectgroups:
                    if obj_group.name.lower() == "sofa in fornt of tv":
                        for obj in obj_group:
                            grid_x = int(obj.x / 32)
                            grid_y = int(obj.y / 32)
                            sofa_position = (grid_x, grid_y)
                            break
            
            if sofa_position:
                if npc1:
                    npc1.grid_pos = list(sofa_position)
                    npc1.pos = [sofa_position[0] * 32, sofa_position[1] * 32]
                    npc1.interaction_target = "sofa in fornt of TV"
                
                if npc2:
                    npc2.grid_pos = [sofa_position[0] + 1, sofa_position[1]]
                    npc2.pos = [(sofa_position[0] + 1) * 32, sofa_position[1] * 32]
                    npc2.interaction_target = "sofa in fornt of TV"
    
    def start_new_topic(self):
        """开始新话题"""
        topic = random.choice(list(self.topics.keys()))
        self.shared_memory.set_topic(topic)
        if self.debug:
            print(f"Starting new topic: {topic}")
    
    def generate_dialogue(self):
        """生成NPC之间的对话"""
        current_time = time.time()
        self.last_dialogue_time = current_time
        
        # 检查是否需要换话题
        if self.shared_memory.should_change_topic():
            self.start_new_topic()
        
        # 生成当前说话者的对话
        if self.current_speaker == "NPC1":
            profile = self.npc1_profile
            name = "Lisa"
        else:
            profile = self.npc2_profile
            name = "Lila"
        
        message = self.generate_npc_dialogue(self.current_speaker, name, profile)
        cleaned_message = self.clean_response(message)
        
        # 记录对话
        self.shared_memory.add_to_memory(self.current_speaker, cleaned_message)
        self.dialogue_history.append((self.current_speaker, cleaned_message))
        
        # 切换说话者
        self.current_speaker = "NPC2" if self.current_speaker == "NPC1" else "NPC1"
        
        # 提升心情
        self.improve_npc_mood()
        
        # 自动滚动
        self._auto_scroll_to_bottom()
    
    def generate_npc_dialogue(self, npc_id, npc_name, profile):
        """通过LLM API生成NPC的对话内容"""
        current_topic = self.shared_memory.current_topic
        conversation_history = self.shared_memory.get_conversation_history()
        topic_turns = self.shared_memory.topic_turns
        
        # 构建上下文
        context = ""
        if conversation_history:
            context = "Recent conversation:\n" + "\n".join(conversation_history[-3:])
        
        # 决定对话类型
        if topic_turns == 0:
            # 开启新话题
            starter_options = self.topics[current_topic]["starter"]
            dialogue_type = "start_topic"
            topic_hint = f"Start talking about {current_topic}. Use one of these approaches: {random.choice(starter_options)}"
        else:
            # 回应或继续话题
            dialogue_type = "continue_topic"
            follow_up_options = self.topics[current_topic]["follow_ups"]
            topic_hint = f"Continue discussing {current_topic}. You can ask questions, share experiences, or show interest."
        
        # 构建提示
        prompt = f"""You are {npc_name} (labeled as {npc_id}), having a casual conversation with your friend on the sofa.

Your personality: {profile}

Current topic: {current_topic}
{topic_hint}

{context}

IMPORTANT RULES:
1. Respond with ONLY natural dialogue - no thinking, no analysis, no prefixes
2. Keep it conversational and detailed (1-3 sentences)
3. Stay on topic: {current_topic}
4. Be specific - mention actual details, experiences, or examples
5. Sound like a real person talking to a friend - be expressive and engaging
6. DO NOT include any thinking process or meta-commentary
7. Add personal touches, emotions, or follow-up questions to keep conversation flowing

Examples of good responses:
- "I had the most amazing pasta at that new Italian place downtown yesterday - the truffle sauce was incredible!"
- "Really? What kind of sauce did they use? I've been looking for a good Italian restaurant around here."
- "Oh, I love rainy days like this - perfect for staying cozy inside with a good book and some hot tea."

Your response (just natural dialogue, nothing else):"""

        return self.query_llm(prompt)
    
    def query_llm(self, prompt):
        """向LLM发送请求并获取回应"""
        try:
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are roleplaying as an NPC in casual conversation. Respond ONLY with natural dialogue. Do not include any thinking process, analysis, or meta-commentary. Just speak naturally as the character."
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.9,
                "max_tokens": 100,
                "top_p": 0.95,
                "frequency_penalty": 0.3,
                "presence_penalty": 0.3
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(LLM_API_URL, json=payload, headers=headers, timeout=8)
            
            if response.status_code == 200:
                response_data = response.json()
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    return self.clean_response(response_data["choices"][0]["message"]["content"])
            
            return self.get_fallback_response()
            
        except Exception as e:
            if self.debug:
                print(f"LLM API request failed: {e}")
            return self.get_fallback_response()
    
    def clean_response(self, text):
        """清理LLM响应"""
        if not text:
            return self.get_fallback_response()
        
        # 极其激进的思考过程清理
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<think>.*', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'.*</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'\[think\].*?\[/think\]', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'\(think.*?\)', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # 移除任何包含think的内容
        lines = text.split('\n')
        filtered_lines = []
        for line in lines:
            # 跳过包含思考相关词汇的行
            if any(word in line.lower() for word in ['think', 'okay so', 'hmm', 'wait', 'let me', 'i need to', 'i should']):
                continue
            if '<' in line and '>' in line:
                continue
            if line.strip():
                filtered_lines.append(line.strip())
        
        if filtered_lines:
            text = ' '.join(filtered_lines)
        
        # 移除前缀标记
        text = re.sub(r'^(NPC|NPC1|NPC2|Lisa|Lila):\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^["\']|["\']$', '', text.strip())
    
    def get_fallback_response(self):
        """备用回复 - 避免重复"""
        current_topic = self.shared_memory.current_topic
        
        # 检查最近使用过的备用回应，避免重复
        recent_responses = []
        if hasattr(self, 'dialogue_history') and self.dialogue_history:
            recent_responses = [msg[1].lower() for msg in self.dialogue_history[-4:]]
        
        if current_topic in self.topics:
            if self.shared_memory.topic_turns == 0:
                responses = self.topics[current_topic]["starter"]
            else:
                responses = self.topics[current_topic]["follow_ups"]
            
            # 选择没有使用过的回应
            available_responses = [r for r in responses if r.lower() not in recent_responses]
            if available_responses:
                return random.choice(available_responses)
            else:
                # 如果都用过了，随机选择一个
                return random.choice(responses)
        
        # 通用备用回复
        fallbacks = [
            "That's really interesting!",
            "I know what you mean.",
            "Tell me more about that.",
            "That sounds nice.",
            "I've been thinking about that too.",
            "How fascinating!",
            "I completely understand.",
            "What an interesting perspective!",
            "That's a great point.",
            "I hadn't thought of it that way."
        ]
        
        # 同样避免重复
        available_fallbacks = [f for f in fallbacks if f.lower() not in recent_responses]
        if available_fallbacks:
            return random.choice(available_fallbacks)
        else:
            return random.choice(fallbacks)
    
    def _auto_scroll_to_bottom(self):
        """自動滾動到對話歷史的底部"""
        total_height = 0
        for speaker, text in self.dialogue_history:
            wrapped_lines = self.wrap_text(text, self.max_line_width - 100)
            total_height += len(wrapped_lines) * self.line_height + 5
        
        display_height = self.height - 120
        self.max_scroll = max(0, total_height - display_height)
        self.scroll_position = self.max_scroll
    
    def improve_npc_mood(self):
        """对话会提升NPC的心情"""
        if hasattr(self.game, 'ai_bridge') and self.game.ai_bridge:
            if hasattr(self.game.ai_bridge, 'agent') and hasattr(self.game.ai_bridge.agent, 'profile'):
                mood = self.game.ai_bridge.agent.profile.status.get("mood", 0)
                if mood < 80:
                    old_mood = mood
                    self.game.ai_bridge.agent.profile.update_status("mood", 5)
                    
                    if hasattr(self.game, 'add_status_message'):
                        new_mood = self.game.ai_bridge.agent.profile.status.get("mood", 0)
                        self.game.add_status_message(f"NPC1 chatting: Mood +5 ({old_mood}->{new_mood})")
        
        if hasattr(self.game, 'ai_bridge2') and self.game.ai_bridge2:
            if hasattr(self.game.ai_bridge2, 'agent') and hasattr(self.game.ai_bridge2.agent, 'profile'):
                mood = self.game.ai_bridge2.agent.profile.status.get("mood", 0)
                if mood < 80:
                    old_mood = mood
                    self.game.ai_bridge2.agent.profile.update_status("mood", 5)
                    
                    if hasattr(self.game, 'add_status_message'):
                        new_mood = self.game.ai_bridge2.agent.profile.status.get("mood", 0)
                        self.game.add_status_message(f"NPC2 chatting: Mood +5 ({old_mood}->{new_mood})")
    
    def render(self):
        """渲染NPC对话框"""
        if not self.active or not self.dialogue_history:
            return
        
        screen = self.game.screen
        
        dialogue_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dialogue_surface.fill(self.box_color)
        
        title_text = self.title_font.render("NPC Chat", True, self.title_color)
        title_rect = title_text.get_rect(centerx=self.width//2, top=self.padding)
        dialogue_surface.blit(title_text, title_rect)
        
        pygame.draw.line(dialogue_surface, self.separator_color, 
                        (self.padding, title_rect.bottom + 10), 
                        (self.width - self.padding, title_rect.bottom + 10), 2)
        
        history_top = title_rect.bottom + 20
        history_bottom = self.height - self.padding - 30
        history_height = history_bottom - history_top
        
        self._render_dialogue_content(dialogue_surface, history_top, history_height)
        
        if self.max_scroll > 0:
            self._render_scrollbar(dialogue_surface, history_top, history_height)
        
        if self.max_scroll > 0:
            scroll_hint = self.font.render("Use mouse wheel to scroll", True, (150, 150, 150))
            scroll_rect = scroll_hint.get_rect(center=(self.width//2, self.height - 15))
            dialogue_surface.blit(scroll_hint, scroll_rect)
        
        screen.blit(dialogue_surface, (self.x, self.y))
    
    def _render_dialogue_content(self, surface, start_y, available_height):
        """渲染對話內容，支持換行和滾動"""
        current_y = start_y - self.scroll_position
        total_content_height = 0
        
        for speaker, text in self.dialogue_history:
            speaker_color = (100, 200, 100) if speaker == "NPC1" else (200, 100, 100)
            
            speaker_text = self.font.render(f"{speaker}:", True, speaker_color)
            
            if current_y > start_y - 30 and current_y < start_y + available_height + 30:
                surface.blit(speaker_text, (self.padding, current_y))
            
            current_y += self.line_height + 2
            total_content_height += self.line_height + 2
            
            message_x = self.padding + 10
            max_text_width = self.max_line_width - 20
            wrapped_lines = self.wrap_text(text, max_text_width)
            
            for line in wrapped_lines:
                if current_y > start_y - 30 and current_y < start_y + available_height + 30:
                    message_surface = self.font.render(line, True, self.text_color)
                    surface.blit(message_surface, (message_x, current_y))
                
                current_y += self.line_height
                total_content_height += self.line_height
            
            current_y += 10
            total_content_height += 10
        
        self.max_scroll = max(0, total_content_height - available_height + 20)
    
    def _render_scrollbar(self, surface, start_y, available_height):
        """渲染滾動條"""
        scrollbar_width = 10
        scrollbar_x = self.width - scrollbar_width - 5
        
        pygame.draw.rect(surface, (50, 50, 70), 
                        (scrollbar_x, start_y, scrollbar_width, available_height))
        
        if self.max_scroll > 0:
            slider_height = max(20, available_height * (available_height / (self.max_scroll + available_height)))
            slider_pos = start_y + (self.scroll_position / self.max_scroll) * (available_height - slider_height)
            
            pygame.draw.rect(surface, (150, 150, 180), 
                            (scrollbar_x, slider_pos, scrollbar_width, slider_height))
        
        # 检查是否与最近的对话重复
        if hasattr(self, 'dialogue_history') and self.dialogue_history:
            recent_messages = [msg[1].lower() for msg in self.dialogue_history[-3:]]
            if any(text.lower() in recent or recent in text.lower() for recent in recent_messages):
                return self.get_fallback_response()  # 如果重复，使用备用回应
        
        # 只保留前两句话，避免过长
        sentences = re.split(r'[.!?]+', text)
        good_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 5 and len(sentence) < 150:
                # 再次检查是否包含分析内容
                analysis_words = ['user', 'conversation', 'response', 'npc', 'scenario', 'roleplay', 'character']
                if not any(word in sentence.lower() for word in analysis_words):
                    good_sentences.append(sentence)
                    if len(good_sentences) >= 2:  # 最多2句
                        break
        
        if good_sentences:
            result = '. '.join(good_sentences)
            if not result.endswith(('.', '!', '?')):
                result += '.'
        else:
            result = text.strip()
        
        # 最终检查
        if (not result or len(result.strip()) < 5 or 
            any(word in result.lower() for word in ['think', 'user wants', 'conversation between', 'roleplay'])):
            return self.get_fallback_response()
        
        return result.strip()
    
    def get_fallback_response(self):
        """备用回复"""
        current_topic = self.shared_memory.current_topic
        
        if current_topic in self.topics:
            if self.shared_memory.topic_turns == 0:
                responses = self.topics[current_topic]["starter"]
            else:
                responses = self.topics[current_topic]["follow_ups"]
            return random.choice(responses)
        
        # 通用备用回复
        fallbacks = [
            "That's really interesting!",
            "I know what you mean.",
            "Tell me more about that.",
            "That sounds nice.",
            "I've been thinking about that too."
        ]
        return random.choice(fallbacks)
    
    def _auto_scroll_to_bottom(self):
        """自動滾動到對話歷史的底部"""
        total_height = 0
        for speaker, text in self.dialogue_history:
            wrapped_lines = self.wrap_text(text, self.max_line_width - 100)
            total_height += len(wrapped_lines) * self.line_height + 5
        
        display_height = self.height - 120
        self.max_scroll = max(0, total_height - display_height)
        self.scroll_position = self.max_scroll
    
    def improve_npc_mood(self):
        """对话会提升NPC的心情"""
        if hasattr(self.game, 'ai_bridge') and self.game.ai_bridge:
            if hasattr(self.game.ai_bridge, 'agent') and hasattr(self.game.ai_bridge.agent, 'profile'):
                mood = self.game.ai_bridge.agent.profile.status.get("mood", 0)
                if mood < 80:
                    old_mood = mood
                    self.game.ai_bridge.agent.profile.update_status("mood", 5)
                    
                    if hasattr(self.game, 'add_status_message'):
                        new_mood = self.game.ai_bridge.agent.profile.status.get("mood", 0)
                        self.game.add_status_message(f"NPC1 chatting: Mood +5 ({old_mood}->{new_mood})")
        
        if hasattr(self.game, 'ai_bridge2') and self.game.ai_bridge2:
            if hasattr(self.game.ai_bridge2, 'agent') and hasattr(self.game.ai_bridge2.agent, 'profile'):
                mood = self.game.ai_bridge2.agent.profile.status.get("mood", 0)
                if mood < 80:
                    old_mood = mood
                    self.game.ai_bridge2.agent.profile.update_status("mood", 5)
                    
                    if hasattr(self.game, 'add_status_message'):
                        new_mood = self.game.ai_bridge2.agent.profile.status.get("mood", 0)
                        self.game.add_status_message(f"NPC2 chatting: Mood +5 ({old_mood}->{new_mood})")
    
    def render(self):
        """渲染NPC对话框"""
        if not self.active or not self.dialogue_history:
            return
        
        screen = self.game.screen
        
        dialogue_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dialogue_surface.fill(self.box_color)
        
        title_text = self.title_font.render("NPC Chat", True, self.title_color)
        title_rect = title_text.get_rect(centerx=self.width//2, top=self.padding)
        dialogue_surface.blit(title_text, title_rect)
        
        pygame.draw.line(dialogue_surface, self.separator_color, 
                        (self.padding, title_rect.bottom + 10), 
                        (self.width - self.padding, title_rect.bottom + 10), 2)
        
        history_top = title_rect.bottom + 20
        history_bottom = self.height - self.padding - 30
        history_height = history_bottom - history_top
        
        self._render_dialogue_content(dialogue_surface, history_top, history_height)
        
        if self.max_scroll > 0:
            self._render_scrollbar(dialogue_surface, history_top, history_height)
        
        if self.max_scroll > 0:
            scroll_hint = self.font.render("Use mouse wheel to scroll", True, (150, 150, 150))
            scroll_rect = scroll_hint.get_rect(center=(self.width//2, self.height - 15))
            dialogue_surface.blit(scroll_hint, scroll_rect)
        
        screen.blit(dialogue_surface, (self.x, self.y))
    
    def _render_dialogue_content(self, surface, start_y, available_height):
        """渲染對話內容，支持換行和滾動"""
        current_y = start_y - self.scroll_position
        total_content_height = 0
        
        for speaker, text in self.dialogue_history:
            speaker_color = (100, 200, 100) if speaker == "NPC1" else (200, 100, 100)
            
            speaker_text = self.font.render(f"{speaker}:", True, speaker_color)
            
            if current_y > start_y - 30 and current_y < start_y + available_height + 30:
                surface.blit(speaker_text, (self.padding, current_y))
            
            current_y += self.line_height + 2
            total_content_height += self.line_height + 2
            
            message_x = self.padding + 10
            max_text_width = self.max_line_width - 20
            wrapped_lines = self.wrap_text(text, max_text_width)
            
            for line in wrapped_lines:
                if current_y > start_y - 30 and current_y < start_y + available_height + 30:
                    message_surface = self.font.render(line, True, self.text_color)
                    surface.blit(message_surface, (message_x, current_y))
                
                current_y += self.line_height
                total_content_height += self.line_height
            
            current_y += 10
            total_content_height += 10
        
        self.max_scroll = max(0, total_content_height - available_height + 20)
    
    def _render_scrollbar(self, surface, start_y, available_height):
        """渲染滾動條"""
        scrollbar_width = 10
        scrollbar_x = self.width - scrollbar_width - 5
        
        pygame.draw.rect(surface, (50, 50, 70), 
                        (scrollbar_x, start_y, scrollbar_width, available_height))
        
        if self.max_scroll > 0:
            slider_height = max(20, available_height * (available_height / (self.max_scroll + available_height)))
            slider_pos = start_y + (self.scroll_position / self.max_scroll) * (available_height - slider_height)
            
            pygame.draw.rect(surface, (150, 150, 180), 
                            (scrollbar_x, slider_pos, scrollbar_width, slider_height))