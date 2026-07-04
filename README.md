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

## 架构设计题

### 模块一：Context 

**Q: 一个 session 连续聊了 200 轮，context 快爆了。你会怎么做压缩？如何确保压缩后的对话仍然流畅？**

压缩策略分三层：

**第一层：滑动窗口**

保留最近 N 轮原文，早期的直接丢掉。好处是没有成本，缺点是用户早期说了重要信息（比如，我不吃辣），后面就忘了。

**第二层：摘要压缩**

把早期对话让 LLM 生成一段摘要，替换掉原文。比如，把前 100 轮压缩成用户偏好清淡食物，预算通常在 50 块以内，曾记录吃过火锅和拉面这一句话，保留关键信息但大幅减少 token。

food_agent 项目用的是简化版,超过 10 轮就压缩，摘要写死成共 N 条历史已压缩，生产环境换成 LLM 生成真实摘要。

**第三层：结构化提取**

不做摘要，而是从历史里抽取关键实体存到 session 的独立字段里，每次对话直接把这个结构化数据注入 context，不占历史轮次的空间。

**如何保证压缩后流畅？**

关键是记住用户的偏好、约束条件、重要决策，闲聊和中间过程可以丢。还有就是在压缩前先跑一个关键信息提取步骤，把用户说过的偏好、记录过的食物、明确表达过的限制条件单独存起来，压缩的时候这些关键信息已经单独存好了，不会跟着历史一起被丢掉。

### 模块二：Memory 

**Q: 和聊天 Agent 熟悉半个月后，用户问了一个以前问过的问题。Agent 如何做 memory 召回更合理？**

半个月的历史全部塞进 context 肯定不现实，得按相关性来召回，分三层：

**短期记忆**：当前对话历史，直接在 context 里，不需要召回。

**中期记忆**：近期几天的对话摘要，压缩后存储，每次对话开始时注入。

**长期记忆**：历史对话的关键片段，向量化后存到向量数据库（比如 Milvus）。用户发新消息时，把输入向量化，做相似度检索，把最相关的历史片段注入 context。

每次用户发新消息之前触发召回，把检索到的相关历史注入到 system prompt 末尾，让 LLM 开口之前就已经"想起来"了，格式大概长这样：

[相关历史记录]
- 两周前用户提到不吃辣，预算通常 50 块以内
- 上周推荐过火锅，用户表示喜欢

这个思路和 RAG 召回文档是一样的，只是检索对象从文档变成了历史对话片段。


### 模块三：Task

**Q: 对于长程任务，大模型执行一段时间可能会忘掉目标，你知道哪些解决方案，有什么优缺？**

| 方案 | 说明 | 优点 | 缺点 |
|------|------|------|------|
| **目标锚定** | 每步 Prompt 里都重复一遍主目标 | 简单零成本 | 每轮都要重复，白白浪费 token，LLM 还有可能忽略 |
| **显式任务状态** | 维护 scratchpad 记录已完成/待完成步骤 | 结构清晰，中途断掉也能从 checkpoint 恢复 | 需要额外设计状态管理 |
| **层级 Agent** | Orchestrator 记住目标，SubAgent 只管执行子任务 | 职责清晰，适合复杂长程任务 | 架构复杂，调试难度高 |
| **定期自检** | 每 N 步让 LLM 自问是否偏离目标 | 能及时发现偏离 | 多了额外的 LLM 调用成本 |

实际工程里一般用目标锚定 + 显式状态组合，复杂场景才上层级 Agent。本项目里的 MAX_LOOP 限制也是最简单的防漂移手段。

### 模块四：Tool / Session Runtime

**Q: Agent 工具有同步和异步两类。异步工具不能让用户一直等，但结果依然重要。你会如何设计异步工具执行和完成通知？**

核心思路是：工具在后台跑，用户不用等，结果出来了再通知。

**三个步骤**：

**第一步：提交任务，立即返回**

工具调用后不等结果，直接返回一个 `job_id`，告诉用户任务已提交，完成后通知你。用户不需要干等着。

**第二步：后台异步执行**

用队列（Redis + Celery）在后台处理任务，主对话流程继续正常响应用户，两边互不影响。

**第三步：完成后主动通知**

任务完成后通过 WebSocket 或 SSE 推送结果给用户，不需要用户主动来问。

Agent 层面的处理：调用异步工具后把 `job_id` 存入 session，用户问"结果怎么样了"时，Agent 用 `job_id` 查询状态返回结果。

整个流程就像外卖下单，下单成功立即反馈，骑手送达再通知，用户不需要一直盯着等。

### 模块五：Agent Runtime 架构对比

**Q: Claude Code 的工具输出方式和国内 GLM/豆包等 OpenAI-compatible function calling 有什么不同？他们各自这样设计的优缺点是什么？**

**OpenAI-compatible（GLM/豆包）**

本质是 LLM 调函数，给 LLM 一堆工具，LLM 决定调哪个、传什么参数，结果返回给 LLM 再回复用户。工具是被动的，每次调用都是独立的一次性操作，解决的是LLM 怎么调工具这个问题。

**Claude Code**

它是一个完整的 Agent，目标是帮你自主完成一个真实任务。只要你授权，它能主动操作电脑，读文件、写代码、跑命令、发邮件、开浏览器，整个过程可以连续调用多个工具、执行多个步骤，不需要你每步都参与。

但它不是完全自主的，每次要做危险操作（比如删文件、跑命令、发邮件）之前，都会先停下来告诉你它打算怎么做，你点确认它才动，不会自己偷偷跑。

**对比总结**

| | OpenAI-compatible（GLM/豆包） | Claude Code |
|---|---|---|
| **本质** | LLM 调函数 | 完整 Agent |
| **工具调用** | 单次查询型操作 | 连续多步执行 |
| **优点** | 生态兼容广，接入成本低，解析简单 | 工具能力强，任务执行完整，关键操作有人工确认保障 |
| **缺点** | 只能做单次操作，无法连续执行多步 | 生态相对封闭，重度依赖 Claude 自身能力 |

**核心差距**

Function calling 解决的是调一个函数，Claude Code 解决的是完成一个任务。工具调用在 Claude Code 里只是其中一个环节，不是全部。