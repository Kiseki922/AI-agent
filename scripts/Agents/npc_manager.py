from scripts.Agents.ai_npc_bridge import TMXAIBridge

class NPCManager:
    """統一管理所有NPC的AI系統"""
    
    def __init__(self, game):
        self.game = game
        self.npcs = {}  # 存儲所有NPC的AI系統 {npc_id: ai_bridge}
        
    def create_npc(self, npc_id, agent_name, schedule_config=None):
        """
        創建一個新的NPC
        
        參數:
            npc_id: NPC的唯一標識符
            agent_name: AI代理的名稱
            schedule_config: 自定義日程配置（如果為None則使用默認配置）
        """
        # 創建獨立的AI Bridge
        ai_bridge = TMXAIBridge(self.game, npc_id)
        ai_bridge.initialize_agent(agent_name)
        
        # 設置獨立的日程表
        if schedule_config:
            ai_bridge.agent.set_custom_schedule(schedule_config)
        else:
            # 使用默認日程表生成（每個NPC都是獨立的副本）
            ai_bridge.agent._generate_dynamic_schedule()
        
        # 註冊交互效果
        self._register_interaction_effects(ai_bridge)
        
        # 存儲到管理器中
        self.npcs[npc_id] = ai_bridge
        
        return ai_bridge
    
    def get_npc(self, npc_id):
        """獲取指定NPC的AI Bridge"""
        return self.npcs.get(npc_id)
    
    def update_all(self):
        """更新所有NPC的狀態"""
        for npc_id, ai_bridge in self.npcs.items():
            ai_bridge.process_next_command()
    
    def start_all_ai(self):
        """啟動所有NPC的AI"""
        for ai_bridge in self.npcs.values():
            ai_bridge.start_ai_loop()
    
    def stop_all_ai(self):
        """停止所有NPC的AI"""
        for ai_bridge in self.npcs.values():
            ai_bridge.stop_ai_loop()
    
    def _register_interaction_effects(self, ai_bridge):
        """為NPC註冊交互效果"""
        # 基本交互效果
        effects = {
            "bed": ({"mood": 65, "health": 60}, "Sleep in bed"),
            "sofa": ({"mood": 60, "health": -10}, "Relax on sofa"),
            "chair": ({"mood": 55, "health": 0}, "Sit on chair"),
            "chair_in_fornt_of_desk": ({"mood": 55}, "Sit at desk"),
            "sofa in fornt of TV": ({"mood": 65, "health": -10}, "Relax on sofa in front of TV"),
            "refrigerator": ({"mood": 55, "health": 60}, "Get food from refrigerator"),
            "ref": ({"mood": 55, "health": 60}, "Get food from refrigerator"),
            # ... 添加所有其他效果
        }
        
        for obj_type, (status_changes, description) in effects.items():
            ai_bridge.register_interaction_effect(obj_type, status_changes, description)