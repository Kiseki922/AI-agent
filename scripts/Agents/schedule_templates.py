def npc1_schedule():
    """NPC1的日程配置：基本冰箱-沙發-床循環"""
    return {
        "activities": ["去冰箱拿东西", "去沙发上放松", "去床上休息"],
        "activity_duration": 30,  # 每個活動30分鐘
        "start_hour": 8,
        "end_hour": 22,
        "sleep_hour": 22
    }

def npc2_schedule():
    """NPC2的日程配置：不同的活動安排"""
    return {
        "activities": ["看电视", "在卧室休息", "在桌子旁工作"],
        "activity_duration": 45,  # 每個活動45分鐘
        "start_hour": 7,  # 早起15分鐘
        "end_hour": 23,   # 晚睡1小時
        "sleep_hour": 23
    }

def custom_schedule(activities, duration=30, start_hour=8, end_hour=22, sleep_hour=22):
    """自定義日程配置模板"""
    return {
        "activities": activities,
        "activity_duration": duration,
        "start_hour": start_hour,
        "end_hour": end_hour,
        "sleep_hour": sleep_hour
    }