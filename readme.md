# AI智能代理游戏系统

一个融合认知科学与游戏技术的智能NPC系统，实现了完整的AI认知架构，包含记忆、规划、决策和自然语言交互能力。

##  项目亮点

- **完整认知架构**：模拟人类的感知-记忆-规划-行动认知循环
- **智能对话系统**：基于大语言模型的自然语言交互
- **多NPC社交**：NPC之间的智能对话和社交互动
- **生活模拟**：24小时作息管理和个性化日程安排
- **开放世界**：基于TMX地图的完整游戏环境
- **状态管理**：实时的情感和健康状态系统
- **智能寻路**：多算法路径规划和环境感知

##  系统要求

- **Python**: 3.8 或更高版本
- **操作系统**: Windows 10/11, macOS 10.14+, Linux
- **内存**: 至少 4GB RAM
- **存储**: 500MB 可用空间
- **网络**: 用于LLM API调用

##  快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/your-username/ai-agent-system.git
cd ai-agent-system

# 创建虚拟环境
python -m venv myenv

# 激活虚拟环境
# Windows:
myenv\Scripts\activate
# macOS/Linux:
source myenv/bin/activate

# 安装依赖
pip install pygame pytmx requests numpy
```

### 2. LLM服务配置

**方式一：使用LM Studio（推荐）**

1. 下载 [LM Studio](https://lmstudio.ai/)
2. 安装并下载模型：`deepseek-r1-distill-qwen-7b`
3. 启动本地服务器，端口设为 `1234`

**方式二：使用Ollama**

```bash
# 安装Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 下载模型
ollama pull deepseek-r1

# 启动服务（端口1234）
ollama serve --port 1234
```

### 3. 运行系统

```bash
# 启动完整游戏（推荐）
python window_test2.py

# 或启动命令行版本
python main.py
```

##  游戏操作指南

### 基础控制

| 操作 | 按键 | 说明 |
|------|------|------|
| 移动 | `WASD` | 控制玩家角色移动 |
| 对话 | `E` | 与附近NPC开始对话 |
| 命令模式 | `Enter` | 进入命令行输入模式 |
| 退出 | `ESC` | 退出对话或命令模式 |

### 时间控制

| 功能 | 快捷键 | 说明 |
|------|--------|------|
| AI控制 | `F1` | 开启/关闭NPC智能控制 |
| 暂停时间 | `F2` | 暂停/恢复游戏时间 |
| 减慢时间 | `F3` | 降低时间流速 |
| 加快时间 | `F4` | 提高时间流速 |
| 重置时间 | `F5` | 恢复正常时间流速 |

### 命令系统

#### NPC控制命令
```bash
# AI控制
ai on                    # 启用AI自主控制
ai off                   # 禁用AI控制
ai status               # 查看AI状态

# NPC操作
goto npc1 ref           # 让NPC1前往冰箱
goto npc2 bed           # 让NPC2前往床铺
interact npc1 sofa      # 让NPC1与沙发交互
status                  # 查看所有NPC状态
```

#### 时间管理命令
```bash
time set 14 30          # 设置时间为14:30
time scale 2.0          # 设置时间流速为2倍
time pause              # 暂停时间
```

#### 调试命令
```bash
list                    # 列出附近物品
debug objects           # 显示调试信息
help                    # 显示帮助信息
```

##  系统架构

### 核心AI模块

```
AI Agent Core
├── Profile (profile.py)         # 个性和基础属性
├── Memory (memory.py)           # 短期/长期记忆系统
├── Planning (planning.py)       # 目标规划和任务管理
├── Action (action.py)           # 动作执行和环境交互
└── AI Agent (ai_agent.py)       # 主控制器
```

### 游戏引擎模块

```
Game Engine
├── NPC System
│   ├── npc.py                   # NPC物理控制
│   ├── npc_controller.py        # 多NPC管理
│   └── ai_npc_bridge.py         # AI-游戏桥接
├── Dialogue System
│   ├── dialogue_system.py       # 玩家对话
│   └── npc_dialogue_system.py   # NPC互聊
├── Environment
│   ├── level.py                 # 地图加载
│   ├── path_finder.py           # 寻路算法
│   └── tilemaps.py              # 瓦片地图
└── UI & Display
    ├── status_display.py        # 状态显示
    └── npc_target_indicator.py  # 目标指示
```

##  AI认知系统详解

### 记忆系统
- **短期记忆**：最近10个动作的工作记忆
- **长期记忆**：重要经验的永久存储
- **反思机制**：每10个动作后自动生成反思
- **记忆检索**：基于相关性的智能搜索

### 决策系统
1. **环境感知**：位置、时间、状态感知
2. **记忆整合**：检索相关经验和知识
3. **目标规划**：基于个性的行为规划
4. **动作执行**：具体行为的执行和反馈

### 个性系统
- **外向性**：影响社交行为倾向
- **冒险性**：影响探索和风险承担
- **尽责性**：影响计划执行严格程度
- **创造力**：影响行为创新性

##  配置与自定义

### NPC角色配置

编辑 `scripts/Agents/agents/` 目录下的配置文件：

```json
{
  "type": "TinyPerson",
  "persona": {
    "name": "Lisa",
    "style": "活泼开朗，喜欢聊天，性格外向"
  }
}
```

### 日程表自定义

在 `schedule_templates.py` 中创建自定义日程：

```python
def custom_schedule():
    return {
        "activities": ["去冰箱拿东西", "去沙发上放松", "去床上休息"],
        "activity_duration": 30,  # 分钟
        "start_hour": 8,
        "end_hour": 22,
        "sleep_hour": 22
    }
```

### 交互效果配置

添加新的物品交互效果：

```python
# 在交互效果配置中添加
"piano": ({"mood": 85, "health": -5}, "弹钢琴")
```

##  游戏特色体验

### 智能NPC生活

- **作息规律**：NPC有完整的24小时生活作息
- **个性差异**：每个NPC都有独特的性格和行为模式
- **社交互动**：NPC之间会在特定时间进行对话交流
- **状态影响**：心情和健康会影响NPC的行为选择

### 沉浸式对话

- **自然语言**：使用大语言模型实现自然对话
- **上下文记忆**：对话具有连贯性和记忆性
- **情感反馈**：对话会影响NPC的情感状态
- **个性化回应**：基于NPC个性的差异化对话风格

### 动态世界

- **时间系统**：完整的24小时时间循环
- **环境交互**：丰富的物品交互和状态反馈
- **寻路系统**：智能的路径规划和避障
- **状态可视化**：实时的NPC状态和目标显示

##  故障排除

### 常见问题

**Q: NPC不移动**
```bash
# 解决步骤：
1. 按F1检查AI是否启用
2. 按F2检查时间是否暂停
3. 使用命令 "ai status" 查看状态
```

**Q: 对话系统无响应**
```bash
# 检查清单：
1. LLM服务是否在端口1234运行
2. 网络连接是否正常
3. 模型是否正确加载
```

**Q: 游戏崩溃或黑屏**
```bash
# 尝试解决：
1. 更新显卡驱动
2. 检查Python版本（需要3.8+）
3. 重新安装pygame：pip install --upgrade pygame
```

**Q: 表情符号显示异常**
```bash
# 运行测试：
python test_emoji_support.py
# 如果不支持，系统会自动切换到文字模式
```

### 性能优化

如果遇到性能问题，可以调整以下参数：

```python
# 在 window_test2.py 中：
self.command_cooldown = 2.0        # 增加AI决策间隔
self.status_update_interval = 60   # 减少状态更新频率
self.max_status_messages = 3       # 减少状态消息数量
```

##  输出文件说明

运行过程中会生成以下文件：

- `memory_export.json` - NPC记忆数据导出
- `profile.json` - NPC角色配置保存
- `planning.json` - 规划和目标数据
- `action.json` - 动作历史记录
- `ai_system.log` - 系统运行日志

##  技术特色

### 认知科学基础
- 模拟人类记忆和决策过程
- 情感计算和个性建模

### 游戏技术创新
- 完整的TMX地图编辑器支持
- 多层渲染和复杂场景管理
- 实时AI-游戏状态同步

### AI技术集成
- 大语言模型深度集成
- 多智能体协作
- 动态行为权重调整

## 🆘 获取帮助

如果遇到问题：

1. 查看本文档的故障排除部分
2. 检查代码注释和示例
3. 确认所有依赖正确安装
4. 验证LLM API服务正常运行

---
