"""
完整的NPC狀態處理系統，處理NPC與環境物件互動時的狀態變化。
這個檔案可以直接添加到遊戲專案中，不需要修改現有代碼。

使用方法：
1. 將此檔案放置到scripts目錄下
2. 在遊戲的主檔案中導入此模組
3. 在遊戲初始化後，創建狀態處理器並設置整合

範例:
```
from scripts.complete_npc_status_handler import NPCStatusSystem

# 在遊戲類的__init__方法中:
self.npc_status_system = NPCStatusSystem(self)
self.npc_status_system.initialize()
```
"""

import time
import random
from typing import Dict, List, Tuple, Optional, Any

class NPCStatusSystem:
    """整合式NPC狀態處理系統，包含處理器、UI整合和命令擴展"""
    
    def __init__(self, game_instance):
        """
        初始化NPC狀態系統
        
        參數:
            game_instance: 遊戲實例，包含AI Bridge和NPC控制器
        """
        self.game = game_instance
        self.status_handler = None
        self.initialized = False
        
        # 保存原有方法的引用
        self._original_methods = {}
    
    def initialize(self):
        """初始化並整合狀態系統到遊戲中"""
        if self.initialized:
            print("NPC狀態系統已經初始化")
            return
            
        # 創建狀態處理器
        self.status_handler = NPCStatusHandler(self.game)
        
        # 整合到遊戲中
        self._integrate_with_game()
        
        # 標記為已初始化
        self.initialized = True
        print("NPC狀態系統已初始化並整合到遊戲中")
    
    def _integrate_with_game(self):
        """將狀態系統整合到遊戲中"""
        # 整合到NPC控制器
        if hasattr(self.game, 'npc_controller'):
            self._integrate_with_npc_controller()
        
        # 整合到遊戲UI
        self._enhance_game_ui()
        
        # 整合到命令處理
        self._enhance_command_handling()
    
    def _integrate_with_npc_controller(self):
        """整合到NPC控制器"""
        # 確保NPC控制器存在
        if not hasattr(self.game, 'npc_controller'):
            print("警告: 找不到NPC控制器，無法完全整合狀態系統")
            return
            
        # 保存原始方法
        self._original_methods['npc_interact_with'] = self.game.npc_controller.npc_interact_with
        
        # 替換互動方法
        def enhanced_npc_interact_with(npc_id, object_name):
            # 調用原始方法
            result = self._original_methods['npc_interact_with'](npc_id, object_name)
            
            # 如果互動成功，處理狀態變化
            if result:
                self.status_handler.handle_interaction(npc_id, object_name)
            
            return result
        
        # 使用新方法替換原始方法 (使用lambda以確保self.game.npc_controller正確傳遞)
        self.game.npc_controller.npc_interact_with = lambda npc_id, object_name: enhanced_npc_interact_with(npc_id, object_name)
    
    def _enhance_game_ui(self):
        """增強遊戲UI以顯示NPC狀態"""
        # 確保render_status方法存在
        if not hasattr(self.game, 'render_status'):
            print("警告: 找不到render_status方法，無法增強UI")
            return
            
        # 保存原始方法
        self._original_methods['render_status'] = self.game.render_status
        
        # 定義增強版的渲染方法
        def enhanced_render_status():
            # 調用原始渲染方法
            self._original_methods['render_status']()
            
            # 添加NPC狀態顯示
            self._render_npc_status()
        
        # 替換渲染方法
        self.game.render_status = enhanced_render_status
    
    def _render_npc_status(self):
        """渲染NPC狀態信息"""
        import pygame  # 導入pygame用於渲染
        
        # 確保遊戲窗口和字體存在
        if not hasattr(self.game, 'screen'):
            return
            
        # 創建字體
        font = pygame.font.SysFont(None, 20)
        
        # 獲取NPC狀態
        if hasattr(self.game, 'ai_bridge') and self.game.ai_bridge and hasattr(self.game.ai_bridge, 'agent'):
            agent = self.game.ai_bridge.agent
            if hasattr(agent, 'profile'):
                status = agent.profile.status
                
                # 生成狀態文本
                status_text = f"NPC狀態: 能量={status['energy']}, 飢餓={status['hunger']}, 心情={status['mood']}, 健康={status['health']}"
                
                # 渲染狀態文本
                status_surface = font.render(status_text, True, (220, 220, 100))
                self.game.screen.blit(status_surface, (10, 610))
                
                # 顯示最近狀態變化
                if hasattr(self, 'status_handler'):
                    history = self.status_handler.get_status_history("npc1", 1)
                    if history:
                        last_change = history[0]
                        change_surface = font.render(str(last_change), True, (180, 220, 180))
                        self.game.screen.blit(change_surface, (10, 630))
    
    def _enhance_command_handling(self):
        """增強命令處理以支持狀態命令"""
        # 確保process_command方法存在
        if not hasattr(self.game, 'process_command'):
            print("警告: 找不到process_command方法，無法增強命令處理")
            return
            
        # 保存原始方法
        self._original_methods['process_command'] = self.game.process_command
        
        # 定義增強版的命令處理方法
        def enhanced_process_command(command):
            # 分割命令
            parts = command.strip().split()
            
            # 處理狀態相關命令
            if parts and parts[0].lower() == "status":
                self._handle_status_command(parts)
                return
                
            # 對於其他命令，調用原始方法
            self._original_methods['process_command'](command)
        
        # 替換命令處理方法
        self.game.process_command = enhanced_process_command
        
        # 如果存在print_help方法，也擴展它
        if hasattr(self.game, 'print_help'):
            self._original_methods['print_help'] = self.game.print_help
            
            def enhanced_print_help():
                # 調用原始方法
                self._original_methods['print_help']()
                
                # 添加狀態命令幫助
                if hasattr(self.game, 'add_status_message'):
                    self.game.add_status_message("--- 狀態命令 ---")
                    self.game.add_status_message("status - 顯示NPC基本狀態")
                    self.game.add_status_message("status detail - 顯示NPC詳細狀態")
                    self.game.add_status_message("status history - 顯示NPC狀態變化歷史")
            
            # 替換幫助方法
            self.game.print_help = enhanced_print_help
    
    def _handle_status_command(self, parts):
        """處理狀態相關命令"""
        # 確保add_status_message方法存在
        if not hasattr(self.game, 'add_status_message'):
            print("警告: 找不到add_status_message方法，無法顯示命令結果")
            return
            
        # 獲取NPC狀態
        if not hasattr(self.game, 'ai_bridge') or not self.game.ai_bridge or not hasattr(self.game.ai_bridge, 'agent'):
            self.game.add_status_message("無法獲取NPC狀態")
            return
            
        agent = self.game.ai_bridge.agent
        if not hasattr(agent, 'profile'):
            self.game.add_status_message("無法獲取NPC狀態")
            return
            
        status = agent.profile.status
        
        # 處理不同的狀態命令
        if len(parts) == 1:
            # 基本狀態
            self.game.add_status_message(f"NPC狀態: 能量={status['energy']}, 飢餓={status['hunger']}, 心情={status['mood']}, 健康={status['health']}")
        elif len(parts) >= 2:
            if parts[1].lower() == "detail":
                # 詳細狀態
                self.game.add_status_message(f"詳細狀態: 能量={status['energy']}, 飢餓={status['hunger']}, 心情={status['mood']}, 健康={status['health']}")
                
                # 顯示能量狀態描述
                energy = status['energy']
                if energy > 70:
                    self.game.add_status_message("能量: 充沛 (可以進行所有活動)")
                elif energy > 30:
                    self.game.add_status_message("能量: 正常 (可以進行大部分活動)")
                else:
                    self.game.add_status_message("能量: 低下 (需要休息，移動變慢)")
                
                # 顯示飢餓狀態描述
                hunger = status['hunger']
                if hunger < 30:
                    self.game.add_status_message("飢餓: 飽足 (不需要進食)")
                elif hunger < 70:
                    self.game.add_status_message("飢餓: 有些餓 (應該考慮進食)")
                else:
                    self.game.add_status_message("飢餓: 非常餓 (需要立即進食)")
                
                # 顯示心情狀態描述
                mood = status['mood']
                if mood > 70:
                    self.game.add_status_message("心情: 愉快 (更傾向於社交活動)")
                elif mood > 30:
                    self.game.add_status_message("心情: 普通 (一般狀態)")
                else:
                    self.game.add_status_message("心情: 低落 (避免社交活動)")
                
                # 顯示健康狀態描述
                health = status['health']
                if health > 70:
                    self.game.add_status_message("健康: 良好 (身體狀況極佳)")
                elif health > 30:
                    self.game.add_status_message("健康: 一般 (正常健康狀態)")
                else:
                    self.game.add_status_message("健康: 欠佳 (需要照顧)")
                
                # 顯示最近狀態變化
                if hasattr(self, 'status_handler'):
                    history = self.status_handler.get_status_history("npc1", 3)
                    if history:
                        self.game.add_status_message("最近狀態變化:")
                        for entry in history:
                            self.game.add_status_message(f"  {entry}")
                    else:
                        self.game.add_status_message("尚無狀態變化記錄")
                
            elif parts[1].lower() == "history":
                # 顯示歷史狀態變化
                if hasattr(self, 'status_handler'):
                    history = self.status_handler.get_status_history("npc1", 5)
                    if history:
                        self.game.add_status_message("狀態變化歷史:")
                        for entry in history:
                            self.game.add_status_message(f"  {entry}")
                    else:
                        self.game.add_status_message("尚無狀態變化記錄")
            else:
                # 未知子命令
                self.game.add_status_message("未知的狀態命令。可用命令: status, status detail, status history")


class NPCStatusHandler:
    """負責處理NPC與環境對象互動時的狀態變化。"""
    
    def __init__(self, game_instance):
        """
        初始化NPC狀態處理器
        
        參數:
            game_instance: 遊戲實例，包含AI Bridge和NPC控制器
        """
        self.game = game_instance
        self.interaction_effects = self._initialize_interaction_effects()
        self.status_history = {}  # 記錄NPC的狀態變化歷史 {npc_id: [StatusChange objects]}
        self.last_interaction_time = {}  # 記錄上次互動時間 {npc_id: {object_type: timestamp}}
        
        # 配置
        self.display_status_changes = True  # 是否顯示狀態變化
        self.max_history_items = 10  # 每個NPC保存的歷史記錄數量
    
    class StatusChange:
        """記錄一次狀態變化的類"""
        def __init__(self, timestamp, object_name, changes):
            self.timestamp = timestamp  # 時間戳
            self.object_name = object_name  # 互動對象名稱
            self.changes = changes  # 狀態變化 {"energy": +10, "hunger": -5, ...}
            
            # 格式化時間為小時:分鐘
            self.time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
        
        def __str__(self):
            change_texts = []
            for stat, value in self.changes.items():
                prefix = "+" if value > 0 else ""
                change_texts.append(f"{stat}: {prefix}{value}")
            
            return f"[{self.time_str}] 與 {self.object_name} 互動: {', '.join(change_texts)}"
    
    def _initialize_interaction_effects(self) -> Dict:
        """
        初始化各種物件互動的效果配置
        
        返回:
            互動效果字典 {物件類型: (狀態變化字典, 效果描述)}
        """
        return {
            # 休息類物件
            "bed": ({"energy": 30, "hunger": 5, "mood": 60}, "睡覺恢復精力"),
            "sofa": ({"energy": 15, "mood": 60}, "在沙發上放鬆"),
            "chair": ({"energy": 10, "mood": 55}, "坐在椅子上休息"),
            "chair_in_fornt_of_desk": ({"energy": 10, "mood": 55}, "坐在桌前的椅子上"),
            "sofa in fornt of TV": ({"energy": 15, "mood": 65, "hunger": 2}, "在電視前的沙發上放鬆"),
            
            # 食物類物件
            "refrigerator": ({"hunger": -40, "energy": 15, "mood": 60}, "從冰箱取出食物"),
            "ref": ({"hunger": -40, "energy": 15, "mood": 60}, "從冰箱取出食物"),
            "food": ({"hunger": -25, "energy": 10, "mood": 55}, "吃了食物"),
            "kitchen": ({"hunger": -35, "energy": -5, "mood": 60}, "在廚房做飯"),
            
            # 娛樂類物件
            "tv": ({"energy": -5, "mood": 70, "hunger": 5}, "看電視放鬆"),
            "bookshelf": ({"energy": -10, "mood": 65}, "閱讀書籍"),
            "computer": ({"energy": -15, "mood": 65, "hunger": 5}, "使用電腦"),
            "game": ({"energy": -20, "mood": 75, "hunger": 10}, "玩遊戲"),
            
            # 功能類物件
            "toilet": ({"health": 10, "mood": 55}, "使用廁所"),
            "shower": ({"health": 15, "mood": 65, "energy": 10}, "洗澡"),
            "window": ({"mood": 55}, "看窗外風景"),
            "door": ({"mood": 52}, "開關門"),
            
            # 默認互動
            "default": ({"mood": 52}, "查看物品")
        }
    
    def register_interaction_effect(self, object_type: str, status_changes: Dict[str, int], description: str) -> None:
        """
        註冊新的互動效果
        
        參數:
            object_type: 物件類型
            status_changes: 狀態變化字典 {"energy": 10, "hunger": -5, ...}
            description: 互動效果描述
        """
        self.interaction_effects[object_type] = (status_changes, description)
    
    def handle_interaction(self, npc_id: str, object_name: str) -> bool:
        """
        處理NPC與物件的互動並更新狀態
        
        參數:
            npc_id: NPC的ID
            object_name: 互動物件名稱
            
        返回:
            如果成功處理互動返回True，否則返回False
        """
        # 獲取NPC的AI Agent
        agent = self._get_agent(npc_id)
        if not agent:
            print(f"無法找到NPC {npc_id} 的AI Agent")
            return False
        
        # 確定物件類型
        object_type = self._determine_object_type(object_name)
        
        # 獲取互動效果
        if object_type in self.interaction_effects:
            status_changes, description = self.interaction_effects[object_type]
        else:
            # 使用默認效果
            status_changes, description = self.interaction_effects["default"]
            
        # 紀錄當前狀態以便計算變化
        old_status = {key: value for key, value in agent.profile.status.items()}
        
        # 應用狀態變化
        for status_type, change in status_changes.items():
            if status_type in agent.profile.status:
                agent.profile.update_status(status_type, change)
        
        # 計算狀態變化
        status_diff = {}
        for key in old_status:
            diff = agent.profile.status[key] - old_status[key]
            if diff != 0:
                status_diff[key] = diff
        
        # 紀錄這次的狀態變化
        self._record_status_change(npc_id, object_name, status_diff)
        
        # 始終顯示狀態變化 (不論display_status_changes的設置)
        self._display_status_change(npc_id, object_name, status_diff, description)
        
        return True
    
    def _record_status_change(self, npc_id: str, object_name: str, status_diff: Dict[str, int]) -> None:
        """記錄狀態變化到歷史記錄"""
        if npc_id not in self.status_history:
            self.status_history[npc_id] = []
        
        # 創建新的狀態變化記錄
        status_change = self.StatusChange(
            timestamp=time.time(),
            object_name=object_name,
            changes=status_diff
        )
        
        # 添加到歷史記錄
        self.status_history[npc_id].append(status_change)
        
        # 保持歷史記錄不超過最大數量
        if len(self.status_history[npc_id]) > self.max_history_items:
            self.status_history[npc_id].pop(0)
        
        # 更新上次互動時間
        object_type = self._determine_object_type(object_name)
        if npc_id not in self.last_interaction_time:
            self.last_interaction_time[npc_id] = {}
        self.last_interaction_time[npc_id][object_type] = time.time()
    
    def _display_status_change(self, npc_id: str, object_name: str, status_diff: Dict[str, int], description: str) -> None:
        """在控制台顯示狀態變化"""
        # 生成更改文本
        changes_text = []
        for status_type, change in status_diff.items():
            prefix = "+" if change > 0 else ""
            changes_text.append(f"{status_type}: {prefix}{change}")
        
        # 獲取當前狀態
        agent = self._get_agent(npc_id)
        current_status = {}
        if agent and hasattr(agent, 'profile'):
            current_status = agent.profile.status
        
        # 簡潔方式顯示在控制台（與遊戲輸出風格匹配）
        print(f"NPC與{object_name}互動: {description}")
        print(f"狀態變化: {', '.join(changes_text)}")
        print(f"當前狀態: 能量={current_status.get('energy', 0)}, 飢餓={current_status.get('hunger', 0)}, 心情={current_status.get('mood', 0)}, 健康={current_status.get('health', 0)}")
        
        # 添加到遊戲狀態消息中（如果可用）
        if hasattr(self.game, 'add_status_message'):
            # 獲取當前遊戲時間
            time_str = ""
            if hasattr(self.game, 'game_time'):
                hour = self.game.game_time["hour"]
                minute = int(self.game.game_time["minute"])
                time_str = f"[{hour:02d}:{minute:02d}] "
            
            self.game.add_status_message(f"{time_str}NPC與{object_name}互動: {description}")
            self.game.add_status_message(f"狀態變化: {', '.join(changes_text)}")
            self.game.add_status_message(f"當前狀態: 能量={current_status.get('energy', 0)}, 飢餓={current_status.get('hunger', 0)}, 心情={current_status.get('mood', 0)}")
    
    def _determine_object_type(self, object_name: str) -> str:
        """
        根據物件名稱確定其類型
        
        參數:
            object_name: 物件名稱
            
        返回:
            物件類型字符串
        """
        # 首先檢查是否直接匹配已知類型
        if object_name in self.interaction_effects:
            return object_name
        
        # 檢查TMX對象組
        if hasattr(self.game, 'tmx_data'):
            for obj_group in self.game.tmx_data.objectgroups:
                # 檢查組名匹配
                if obj_group.name.lower() == object_name.lower():
                    return obj_group.name.lower()
                
                # 檢查對象名匹配
                for obj in obj_group:
                    if hasattr(obj, 'name') and obj.name and obj.name.lower() == object_name.lower():
                        return obj_group.name.lower()
        
        # 根據名稱中的關鍵詞確定類型
        lower_name = object_name.lower()
        if "bed" in lower_name:
            return "bed"
        elif "sofa" in lower_name or "couch" in lower_name:
            return "sofa"
        elif "chair" in lower_name:
            return "chair"
        elif "refrigerator" in lower_name or "fridge" in lower_name or "ref" in lower_name:
            return "refrigerator"
        elif "food" in lower_name:
            return "food"
        elif "tv" in lower_name:
            return "tv"
        elif "book" in lower_name:
            return "bookshelf"
        elif "toilet" in lower_name:
            return "toilet"
        elif "shower" in lower_name:
            return "shower"
        elif "window" in lower_name:
            return "window"
        elif "door" in lower_name:
            return "door"
        
        # 默認類型
        return "default"
    
    def _get_agent(self, npc_id: str):
        """獲取與NPC關聯的AI代理"""
        # 嘗試從AI Bridge獲取
        if hasattr(self.game, 'ai_bridge') and self.game.ai_bridge and hasattr(self.game.ai_bridge, 'agent'):
            return self.game.ai_bridge.agent
        
        # 如果NPC自己有代理人
        if hasattr(self.game, 'npc_controller'):
            npc = self.game.npc_controller.get_npc(npc_id)
            if npc and hasattr(npc, 'agent'):
                return npc.agent
        
        return None
    
    def get_status_history(self, npc_id: str, limit: int = None) -> List[str]:
        """
        獲取NPC的狀態變化歷史
        
        參數:
            npc_id: NPC的ID
            limit: 返回的歷史記錄數量，None表示全部
            
        返回:
            狀態變化歷史的文本列表
        """
        if npc_id not in self.status_history:
            return []
        
        history = self.status_history[npc_id]
        if limit:
            history = history[-limit:]
        
        return [str(item) for item in history]
    
    def get_current_status(self, npc_id: str) -> Dict[str, int]:
        """獲取NPC的當前狀態"""
        agent = self._get_agent(npc_id)
        if agent and hasattr(agent, 'profile'):
            return agent.profile.status.copy()
        return {}

# 使用範例：
"""
# 在遊戲主檔案中:
from scripts.complete_npc_status_handler import NPCStatusSystem

# 在遊戲類的__init__方法中
self.npc_status_system = NPCStatusSystem(self)
self.npc_status_system.initialize()

# 可選：註冊自定義互動效果
self.npc_status_system.status_handler.register_interaction_effect(
    "piano", 
    {"energy": -10, "mood": 25, "hunger": 5}, 
    "彈鋼琴"
)
"""