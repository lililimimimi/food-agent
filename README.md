# 🍜 Food Decision Agent

基于 LLM + Tool-Calling 的轻量级智能食物决策系统，帮你解决每天"今天吃什么"的问题。

## 演示视频

[点击查看录屏演示](https://drive.google.com/file/d/1EpLRgp0beWW6Y7owdQVKQdkmof-3a5WK/view?usp=sharing)

## 技术栈

- **LLM**: DeepSeek-V3（通过 SiliconFlow API 调用）
- **Agent Runtime**: 自实现 ReAct Loop
- **天气 API**: wttr.in
- **语言**: Python 3.12


---

## 运行方式

### 1. 克隆项目

```bash
git clone https://github.com/lililimimimi/food-agent.git
cd food-agent
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

打开 `.env`，填入你的 SiliconFlow API Key：

```
SILICONFLOW_API_KEY=你的key
```

### 5. 启动 Agent

```bash
python main.py
```

### 6. 运行测试

```bash
pytest tests/test_agent.py -v
```

---

## 系统设计

### 架构概览

```
用户输入
  ↓
run_agent()          ← 核心 ReAct Loop（runtime.py）
  ↓
build_context()      ← 从 session 中取出历史消息（context.py）
  ↓
call_llm()           ← 调用 DeepSeek-V3（llm_client.py）
  ↓
判断输出类型
  ├── 有 tool_calls  → execute_tool() → 工具执行 → Observation → 继续 Loop
  └── 无 tool_calls  → Final Answer → 返回用户 + 存入 session history
```

### ReAct Loop 流程

每一轮 Loop 打印完整 Trace：

```
[Thought]      LLM 的推理过程
[Action]       调用的工具名称 + 参数
[Observation]  工具执行结果
[Final]        最终回复给用户的答案
```

最大 Loop 次数限制为 **5 次**，防止无限循环。

### 工具列表

| 工具 | 功能 | 参数 |
|------|------|------|
| `get_weather` | 查询城市实时天气（wttr.in） | city |
| `random_pick` | 按条件随机推荐食物 | max_price, spicy, weather, food_type |
| `search_food` | 查询食物详细信息 | name, food_type, max_price, max_calorie |
| `calculator` | 预算/热量计算 | expression |
| `add_todo` | 记录饮食历史 | content |
| `list_todo` | 查看饮食历史列表 | - |
| `complete_todo` | 标记某条记录完成 | index |

### 工具注册机制

所有工具统一在 `agent/tools/registry.py` 注册，每个工具包含：

- `name`: 工具名称
- `description`: 工具描述（LLM 基于此决定是否调用）
- `parameters`: JSON Schema（LLM 基于此决定传什么参数）
- `fn`: 实际执行函数

LLM 通过 Function Calling 自主决策调用哪个工具、传入什么参数，不依赖硬编码规则。

### Session 管理

每个对话窗口对应一个独立的 Session，存储在内存中：

```python
sessions = {
    "session_id_1": {
        "history": [...],       # 对话历史
        "todo_list": [...],     # 饮食记录（独立）
        "weather_cache": {...}  # 天气缓存（30分钟有效）
    },
    "session_id_2": { ... }     # 完全独立，互不影响
}
```

不同 Session 之间的 `todo_list`、`history`、`weather_cache` 完全隔离，切换 Session 用 `new` 命令。

### 天气缓存

同一 Session 内，天气数据缓存 **30 分钟**，避免重复调用外部 API：

```python
if cache["data"] and (now - cache["fetched_at"] < 1800):
    return f"(缓存) {cache['data']}"
```

---

## Memory 的召回时机与放置方式

### 哪些信息存入 Context

每轮对话后，以下内容会存入 `session["history"]`：

| 内容 | 存入方式 | 说明 |
|------|----------|------|
| 用户输入 | `role: user` | 完整保留 |
| 工具调用过程 | `role: assistant` + `role: tool` | 包含 tool_calls 和 Observation |
| 最终回复 | `role: assistant` | Agent 的 Final Answer |

**不存入 Context 的内容**：
- LLM 的中间 Thought（只打印到终端 Trace，不进历史）
- 天气缓存原始数据（存在 session 单独字段里）

### 召回时机

每次用户发送新消息时，`build_context()` 被调用：

```python
# runtime.py
summarize_if_needed(session_id)           # 先判断是否需要压缩
history = build_context(session_id)        # 取出历史
messages = [SYSTEM_PROMPT] + history      # 拼上 system prompt 一起发给 LLM
```

### 放置位置

```
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},   ← 第一位：系统提示词
    {"role": "user",   "content": "第1轮用户输入"},  ← 历史从这里开始
    {"role": "assistant", "content": "第1轮回复"},
    {"role": "user",   "content": "第2轮用户输入"},
    ...
    {"role": "user",   "content": "本轮用户输入"}    ← 最新输入在最后
]
```

### Context 压缩策略

当历史超过 **10 条**时触发压缩：

- 保留最近 10 条原文
- 更早的历史压缩为一条摘要：`[早期对话摘要]: 共N条历史记录已压缩`

这是基础压缩策略，保证对话不会因为历史过长而超出 Token 限制。

---

## AI Prompt 与问题解决记录

### 关键设计决策

**1. 天气城市如何获取**
讨论了IP定位、GPS定位、显式传参三种方案，最终选择显式传参。测试题场景下测试用例需要确定性，IP定位在代理环境下容易定位错误，显式传参最稳定可控。Agent在用户未提供城市时会主动追问，这本身也体现了ReAct"发现缺失信息→主动询问"的能力。

**2. 天气API选型**
先尝试和风天气，免费套餐不包含GeoAPI城市查询接口，返回404。改用wttr.in，完全免费、无需Key、直接用城市名查询，适合Demo场景。

**3. 要不要做前端**
题目要求终端或网页操作录屏二选一，选择纯终端。核心考察点在Agent Runtime，前端不加分反而费时。终端Trace输出（Thought/Action/Observation）本身已经很直观。

**4. Session级别天气缓存**
同一Session内天气数据缓存30分钟，避免重复调用外部API。用内存dict存储，不引入Redis，Session结束后自动释放。生产环境扩展多worker时可替换为Redis。

### Prompt调优心得

在开发过程中，发现Prompt对Agent行为影响非常大。初版Prompt容易导致模型直接回答而不调用工具——LLM会自己编造食物推荐（番茄牛肉面、鲜虾云吞面等），而不是调用`random_pick`从数据库里取结果。

通过在System Prompt里明确加入强制规则：
- "禁止自己编造食物推荐，所有推荐必须来自random_pick工具的结果"
- "推荐食物时永远调用random_pick，不要自己列举食物"

调整后Agent能够正确调用工具，推荐结果完全来自`FOOD_DB`。这一过程让我体会到，Prompt不仅是提示词，更是Agent行为逻辑的重要组成部分。