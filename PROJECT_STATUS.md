# 项目状态报告 / PROJECT STATUS

> 本文件供接手的开发者（或另一个 Claude 实例）快速了解项目当前真实进度、
> 已完成内容、占位内容，以及下一步该做什么。**请先读完本文件再动手。**
>
> 最后更新：2026-06-14

---

## 一句话结论

**目前是「骨架 + 3 个能跑的算法」，距离文档描述的可用系统约完成 15%。**
现在还不能演示任何端到端功能——因为整个系统的「大脑」（LLM 调用）还是空的。

---

## 项目背景

第十五届中国软件杯 A3 赛题：**基于大模型的个性化资源生成与学习多智能体系统**。

- 设计文档：`docs/A3_设计说明书_V5.md`、`docs/A3_需求规格说明书_V5.md`（**权威依据，所有实现以此为准**）
- 技术栈：FastAPI + LangGraph + 讯飞星火 + PostgreSQL/Redis/Milvus/Neo4j/RabbitMQ + React（前端未建）
- 核心：11 个 Agent 协同；6 种资源 30 秒并行生成；6 维画像；10 维评估；3 个 P0 创新

---

## 真实实现 vs 占位（务必看清）

| 部分 | 状态 | 说明 |
|------|------|------|
| 3 个 P0 创新算法 | ✅ **真实可运行** | 遗忘曲线 / 脚手架 / 可解释推荐，纯算法，已冒烟测试 |
| 4 个 P1 创新模块 | 🟡 有代码，**未测试** | 跨模态 / 群体智能 / 认知负荷 / 元认知 |
| 项目结构 / 配置 / 编排图 | ✅ 骨架完整 | LangGraph 编排、依赖装配、FastAPI 路由都搭好了 |
| **讯飞星火 LLM 调用** | ❌ **空的** | `_call_api`、`embed`、`classify_intent` 全是 `NotImplementedError` |
| **SeeDance 视频** | ❌ 空的 | `NotImplementedError` |
| **数据库 / Milvus / Neo4j** | ❌ 全是空桩 | `app/dependencies.py` 的 `_PlaceholderRepo` 返回空数据 |
| 6 种资源生成 | ❌ 不可用 | 依赖 LLM，现在调用就抛错 |
| 画像 / 评估 API | ❌ 不可用 | `NotImplementedError` |
| 前端 | ❌ **完全没有** | 一行代码都没写（文档列了 12 个页面） |
| 测试套件 | ❌ 没有 | 只做了手动冒烟，无 pytest |
| 依赖安装 | ❌ 没装 | fastapi/sqlalchemy/langgraph 等都没装 |

后端约 2600 行 Python，但相当比例是「接口定义 + 占位」，真正含业务逻辑的是几个算法文件。

### 已验证可运行的算法（手动冒烟测试通过）
- **遗忘曲线**（`app/innovations/forgetting_curve.py`）：指数衰减最小二乘拟合，测试 R²=0.978
- **脚手架**（`app/innovations/scaffold_generator.py`）：按掌握度正确分级 0.3→high / 0.65→medium / 0.9→low
- **可解释推荐**（`app/innovations/explainable_recommender.py`）：识别薄弱前置 + 自然语言解释
- **改进 Dijkstra**（`app/agents/path_agent.py`）：按画像掌握度调整边权的路径规划

---

## 为什么卡在 15%

关键：**这是一个 AI 系统，而 AI 的部分（LLM）现在是空的。**
`spark_client._call_api` 没实现，意味着 11 个 Agent 里有 8 个（文档/题目/画像/代码/审核/检索/编排/视频）一调用就报错。算法再漂亮，没有 LLM 喂数据也跑不起来。

---

## 下一步路线图（按依赖顺序，括号为粗略工作量，熟练 1 人）

### 第一梯队 —— 让它「活过来」（约 5-7 天）
1. **实现 `app/llm/spark_client.py` 的 `_call_api`，真实接讯飞星火 API（最高优先级，所有功能的前提）**
2. 实现 `embed` + `classify_intent`
3. 接 PostgreSQL 真实仓储（替换 `_PlaceholderRepo`，画像/学习记录读写）
4. 装依赖（`pip install -r backend/requirements.txt`）+ 跑通一条端到端链路

### 第二梯队 —— 核心功能成形（约 7-10 天）
5. Neo4j 知识图谱 + 真实数据导入（路径规划、可解释推荐都依赖它）
6. Milvus 向量库 + RAG 文档预处理流水线（检索 Agent）
7. 6 种资源生成的 Prompt 工程 + 输出校验（尤其题目答案正确性 FR-018）
8. 前端从零搭（React + 对话页 + 资源展示）

### 第三梯队 —— 达到文档承诺（约 7-10 天）
9. SeeDance 视频生成异步流程
10. Review Agent 5 层防幻觉真实逻辑
11. 测试覆盖、压测、安全项
12. P1 创新接入主流程

**粗估：1 人约 20-27 天；4-5 人团队并行约可压到文档说的 20 天 MVP。**
前提是 LLM 和数据层先打通，否则前端和资源生成都是空中楼阁。

---

## 立刻能做的第一件事

**接通讯飞星火 API**（`app/llm/spark_client.py:_call_api`）。这是单点瓶颈，打通后能立刻验证一条真实链路（如「输入知识点 → 真实生成讲解文档」），整个系统才算从「骨架」变成「能演示」。

需要：讯飞开放平台 `APP_ID / API_KEY / API_SECRET`，填入 `backend/.env`（从 `.env.example` 复制）。
注意确认用 HTTP 版还是 WebSocket 版接口。

---

## 如何启动（当前骨架阶段）

```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # 然后填入真实密钥
uvicorn app.main:app --reload # /health 可立即访问；其余端点接通 LLM 后可用
```

完整环境（含数据库）：项目根目录 `docker compose up -d`

---

## 开发约定（沿用现有代码风格）
- 全异步（`async def`），中文 docstring，引用设计文档章节号（如 `§4.2.3`）
- 日志用标准库 `logging`（不要用 loguru，创新模块已统一为标准库）
- 占位用 `NotImplementedError` 并注明待接入内容
- 接真实依赖时替换 `app/dependencies.py` 的工厂函数即可，对上层透明
