# XM03 题库智能问答

这是题库 RAG 项目的工程练习，当前定位是 **多智能体编排的工程练习**，不是生产级多智能体产品。

## 当前架构

```text
START -> supervisor
          -> planner   -> supervisor
          -> retriever -> supervisor
          -> critic    -> supervisor
          -> answerer  -> supervisor -> END
```

- `supervisor`：只决定下一步，不执行业务。
- `planner`：拆解问题、生成初始查询和补充查询。
- `retriever`：从 Skill registry 取 `search_questions` 和 `get_question` 执行检索与题目详情补全。
- `critic`：判断材料是否足够，也会参考 `check_citation` 的结果。
- `answerer`：生成答案后调用 `check_citation`，校验答案引用的题号是否来自检索结果。
- `MAX_ROUNDS = 12`：防止编排死循环。

## 运行

```powershell
cd D:\CodexXM\XM03
$env:DEEPSEEK_API_KEY = "你的密钥"
.\venv\Scripts\python.exe -m flask --app app run --port 5002
```

不传 `thread_id`：

```powershell
curl --noproxy '*' -X POST http://127.0.0.1:5002/api/agent/ask `
  -H "Content-Type: application/json" `
  -d '{"question":"Spring 依赖注入有哪几种方式"}'
```

传 `thread_id` 时，同一线程会从 SQLite checkpointer 恢复上下文：

```json
{
  "question": "继续追问",
  "thread_id": "demo-thread-1"
}
```

## Agent Skills

Skill 代码在 `skills/`，注册表单例在 `skills.registry.registry`。Agent 运行时会通过 registry 取技能，例如：

```python
from skills.registry import registry

skill = registry.get("search_questions")
result = skill.run("依赖注入", top_k=5)
```

新增 Skill：

1. 新建 `skills/your_skill.py`，定义 `Skill(name=..., description=..., run=..., input_schema=...)`。
2. 在 `agent.py` 的 `_register_default_skills()` 中注册。
3. 给正常、失败和边界场景补测试。

## Checkpointer

默认使用 `langgraph-checkpoint-sqlite`，状态写入：

```text
data/agent_state.db
```

如果 SQLite checkpointer 不可用，代码会降级到 `InMemorySaver`，但跨进程恢复需要换回 `SqliteSaver`。

## 测试

```powershell
.\venv\Scripts\python.exe -m pytest tests -p no:warnings
```

测试全程 mock 模型调用，不消耗 API。
