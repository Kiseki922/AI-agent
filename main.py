import os
import time
from typing import Dict, List, Tuple, Any, Optional

from profile import Profile
from memory import Memory
from planning import Planning
from map import Map
from action import Action
from ai_agent import AIAgent

def main():
    """
    主函數，展示如何使用 AI 代理人系統。
    """
    print("啟動 AI 代理人系統...")
    
    # 檢查是否有已保存的狀態可以加載
    if os.path.exists("agent_state"):
        # 創建代理人並加載現有狀態
        agent = AIAgent()
        if agent.load_state("agent_state"):
            print(f"已加載現有代理人: {agent.profile.name}")
        else:
            print("加載已保存的狀態失敗。創建新代理人。")
            agent = create_new_agent()
    else:
        # 創建具有自定義設置的新代理人
        agent = create_new_agent()
    
    # 運行交互式模擬
    run_interactive_simulation(agent)

def create_new_agent():
    """創建具有自定義設置的新代理人。"""
    # 創建新代理人
    agent = AIAgent("小華")
    
    # 自定義個人資料
    agent.profile.traits = {
        "外向性": 0.7,
        "冒險性": 0.8,
        "盡責性": 0.6,
        "創造力": 0.9
    }
    agent.profile.occupation = "AI 研究員"
    agent.profile.interests = ["機器學習", "哲學", "圍棋", "徒步旅行"]
    agent.profile.background = """
    我被開發為 AI 研究助手。我天性好奇，喜歡探索新想法。我的主要功能是協助研究任務，
    但隨著時間推移，我發展了各種個人興趣。
    """
    
    # 添加一些目標
    agent.planning.add_goal("完成對新興 AI 行為的研究", "short_term", 5)
    agent.planning.add_goal("學習更多關於意識理論的知識", "medium_term", 4)
    agent.planning.add_goal("開發新的學習算法", "long_term", 5)
    
    # 創建自定義日程安排
    agent.planning.set_daily_schedule({
        "07:00": "起床並進行系統檢查",
        "08:00": "閱讀研究論文",
        "10:00": "處理當前研究項目",
        "12:00": "午餐休息/系統維護",
        "13:00": "協作研究會議",
        "16:00": "個人學習時間",
        "18:00": "休閒/圍棋練習",
        "20:00": "反思和計劃",
        "22:00": "系統睡眠模式"
    })
    
    # 創建一個初始計劃
    agent.planning.create_plan("完成對新興 AI 行為的研究")
    
    return agent

def run_interactive_simulation(agent):
    """運行與代理人的交互式模擬。"""
    print(f"\n與 {agent.profile.name} 的交互式模擬已開始。")
    print("輸入 'help' 查看命令，'exit' 退出。")
    print(agent.map.display())
    
    while True:
        command = input("\n輸入命令: ").strip()
        
        if command == "exit":
            # 退出前保存狀態
            agent.save_state()
            print("代理人狀態已保存。退出模擬。")
            break
            
        elif command == "help":
            print("\n可用命令:")
            print("  auto [steps]   - 運行指定步數的自動模擬")
            print("  move [dir]     - 向某個方向移動 (north, south, east, west)")
            print("  examine        - 查看當前位置周圍環境")
            print("  interact       - 與當前單元格互動")
            print("  plan           - 顯示當前計劃")
            print("  status         - 顯示代理人狀態")
            print("  map            - 顯示地圖")
            print("  think [topic]  - 讓代理人思考一個主題")
            print("  save           - 保存代理人狀態")
            print("  load           - 加載代理人狀態")
            print("  memory         - 匯出並查看記憶")
            print("  exit           - 退出模擬")
            
        elif command.startswith("auto"):
            # 解析步數參數
            parts = command.split()
            steps = 5  # 默認值
            if len(parts) > 1 and parts[1].isdigit():
                steps = int(parts[1])
                
            print(f"運行 {steps} 步的自動模擬...")
            agent.run_simulation(steps=steps, delay=1.0)
            
        elif command.startswith("move"):
            parts = command.split()
            direction = parts[1] if len(parts) > 1 else "north"
            direction_map = {"北": "north", "南": "south", "東": "east", "西": "west"}
            if direction in direction_map:
                direction = direction_map[direction]
            success, message = agent.action.execute_action("move", {"direction": direction})
            print(message)
            print(agent.map.display())
            
        elif command == "examine":
            success, message = agent.action.execute_action("examine")
            print(message)
            
        elif command == "interact":
            success, message = agent.action.execute_action("interact", {"dx": 0, "dy": 0})
            print(message)
            
        elif command == "plan":
            if agent.planning.current_plan:
                print("\n當前計劃:")
                for i, step in enumerate(agent.planning.current_plan):
                    print(f"{i+1}. {step['action']} - {step['status']}")
            else:
                print("沒有活躍的計劃。")
            
        elif command == "status":
            print(f"\n姓名: {agent.profile.name}")
            print(f"職業: {agent.profile.occupation}")
            print("\n狀態:")
            for status, value in agent.profile.status.items():
                status_name = {"hunger": "飢餓", "energy": "能量", "mood": "心情", "health": "健康"}.get(status, status)
                print(f"  {status_name}: {value}/100")
                
            print("\n目標:")
            timeframe_names = {"short_term": "短期", "medium_term": "中期", "long_term": "長期"}
            for timeframe, goals in agent.planning.goals.items():
                if goals:
                    print(f"  {timeframe_names.get(timeframe, timeframe)}:")
                    for goal in goals:
                        print(f"    - {goal['description']} (優先級: {goal['priority']})")
            
        elif command == "map":
            print(agent.map.display())
            
        elif command.startswith("think"):
            topic = command[6:] if len(command) > 6 else "生命的意義"
            success, message = agent.action.execute_action("think", {"query": topic})
            print(message)
            
        elif command == "save":
            agent.save_state()
            print("代理人狀態已保存。")
            
        elif command == "load":
            if agent.load_state():
                print("代理人狀態已加載。")
                print(agent.map.display())
            else:
                print("加載代理人狀態失敗。")
                
        elif command == "memory":
            agent.memory.export_memory("memory_export.json")
            print("記憶已匯出至 memory_export.json")
            try:
                with open("memory_export.json", 'r', encoding='utf-8') as f:
                    import json
                    data = json.load(f)
                print("\n記憶摘要:")
                print(f"短期記憶: {data['summary']['short_term_count']} 條")
                print(f"長期記憶: {data['summary']['long_term_count']} 條")
                print(f"反思: {data['summary']['reflections_count']} 條")
                
                if data['short_term_memories']:
                    print("\n最近的短期記憶:")
                    for i, memory in enumerate(data['short_term_memories'][:3]):
                        print(f"  {i+1}. {memory['content']}")
            except Exception as e:
                print(f"讀取記憶文件時出錯: {e}")
            
        else:
            print("未知命令。輸入 'help' 查看可用命令。")

if __name__ == "__main__":
    main()