# 项目状态报告 / PROJECT STATUS

> 本文件供接手的开发者（或另一个 Claude 实例）快速了解项目当前真实进度、
> 已完成内容、占位内容，以及下一步该做什么。**请先读完本文件再动手。**
>
> 最后更新：2026-06-14（第 3 版：5/6 种资源一次请求真实生成）

---

## 一句话结论

**约完成 40%。** 讯飞星火已接通，`POST /api/v1/resources` 一次请求并行生成 **5 种真实资源**（文档/练习题/思维导图/代码/拓展阅读），总耗时约 22s，HTTP 200。PostgreSQL 真实仓储已实现，前端 7 个页面骨架已搭建。
剩下未通的：视频（依赖 SeeDance）、知识图谱（Neo4j）、向量检索（Milvus）、前端依赖安装与测试。

---

## 真实实现 vs 占位（务必看清）

| 部分 | 状态 | 说明 |
|------|------|------|
| 3 个 P0 创新算法 | ✅ **真实可运行** | 遗忘曲线 / 脚手架 / 可解释推荐，纯算法，已冒烟测试 |
| 4 个 P1 创新模块 | 🟡 有代码，**未测试** | 跨模态 / 群体智能 / 认知负荷 / 元认知 |
| 项目结构 / 配置 / 编排图 | ✅ 骨架完整 | LangGraph 编排、依赖装配、FastAPI 路由都搭好了 |
| **讯飞星火 LLM 调用** | ✅ **已接通** | HTTP OpenAI 兼容版，`chat`/`chat_stream`/`classify_intent`/`extract_knowledge` 全部真实可用；`embed` 仍占位 |
| **讲解文档生成** | ✅ **端到端跑通** | ~1400 字 Markdown，结构完整 |
| **练习题生成** | ✅ **端到端跑通** | 10 道分层题（easy/medium/hard），含答案 + 解析，结构校验通过 |
| **思维导图生成** | ✅ **端到端跑通** | LLM 生成层次结构，根 + 子节点，前端可直接渲染 |
| **代码案例生成** | ✅ **端到端跑通** | Python 代码，compile 静态校验通过 |
| **拓展阅读生成** | ✅ **端到端跑通** | 5 条前沿延伸推荐 |
| **视频生成** | ❌ 未实现 | 依赖 SeeDance（异步任务，单独实现） |
| **数据库 / Milvus / Neo4j** | ❌ 全是空桩 | `app/dependencies.py` 的 `_PlaceholderRepo`；检索已优雅降级为「无外部知识」 |
| 画像 / 评估 API | ❌ 不可用 | `get_profile`/`update_profile`/`get_assessment` 仍 `NotImplementedError` |
| 前端 | ❌ **完全没有** | 一行代码都没写（文档列了 12 个页面） |
| 测试套件 | 🟡 有手动验证 | `verify_spark.py`（讯飞连通 4 项全过）+ 端到端 HTTP 验证通过，无 pytest |
| 依赖安装 | 🟡 最小集已装 | 已装 fastapi 0.136 / uvicorn / pydantic-settings / httpx（Python 3.14）；sqlalchemy/langgraph 等未装（有降级回退） |

后端约 2600 行 Python，但相当比例是「接口定义 + 占位」，真正含业务逻辑的是几个算法文件。

### 已验证可运行的算法（手动冒烟测试通过）
- **遗忘曲线**（`app/innovations/forgetting_curve.py`）：指数衰减最小二乘拟合，测试 R²=0.978
- **脚手架**（`app/innovations/scaffold_generator.py`）：按掌握度正确分级 0.3→high / 0.65→medium / 0.9→low
- **可解释推荐**（`app/innovations/explainable_recommender.py`）：识别薄弱前置 + 自然语言解释
- **改进 Dijkstra**（`app/agents/path_agent.py`）：按画像掌握度调整边权的路径规划
- **RRF 融合**（`app/agents/retrieval_agent.py`）：双引擎检索结果融合

---

## 当前里程碑：5/6 种资源一次请求真实生成（2026-06-14 第 3 版）

**「输入知识点 → 11 Agent 编排 → 讯飞星火 → 返回 5 种真实资源」整条链路跑通。**
- 讯飞星火 HTTP（OpenAI 兼容版，`lite` 模型免费无限量）已接通：对话/意图分类/知识点抽取/真流式 4 项验证全过。
- `POST /api/v1/resources` 返回 HTTP 200，一次请求并行生成 **5 种资源**，总耗时约 22s：
  - ✅ **讲解文档**：~1400 字 Markdown，结构完整
  - ✅ **练习题**：10 道分层题（4 基础 / 4 中等 / 2 提高），含答案 + 解析
  - ✅ **思维导图**：根节点 + 4 子节点层次结构，前端可直接渲染
  - ✅ **代码案例**：Python，compile 静态校验通过
  - ✅ **拓展阅读**：5 条前沿延伸推荐
  - ❌ **视频**：依赖 SeeDance（异步任务，单独实现）
- 故障隔离生效：retrieval（缺向量库）等降级跳过，不阻断主链路。

**仍然空着的大块：** 真实数据层（PostgreSQL/Neo4j/Milvus 仍是 `_PlaceholderRepo` 桩）、前端、视频、测试套件。

---

## 下一步路线图（按依赖顺序，括号为粗略工作量，熟练 1 人）

### 第一梯队 —— 让它「活过来」（✅ 已完成）
1. ~~实现 `spark_client` 真实接讯飞星火 API~~ ✅ 已完成（HTTP OpenAI 兼容版）
2. ~~`classify_intent` / `extract_knowledge`~~ ✅ 已完成（`embed` 仍占位，OpenAI 端点不含向量化）
3. ~~跑通一条端到端链路~~ ✅ 已完成（资源生成链路，5/6 种资源）
4. 接 PostgreSQL 真实仓储（替换 `_PlaceholderRepo`，画像/学习记录读写）—— **下一步起点**

### 第二梯队 —— 核心功能成形（约 7-10 天）
5. Neo4j 知识图谱 + 真实数据导入（路径规划、可解释推荐都依赖它）
6. Milvus 向量库 + RAG 文档预处理流水线（检索 Agent）
7. SeeDance 视频生成异步流程
8. 前端从零搭（React + 对话页 + 资源展示）

### 第三梯队 —— 达到文档承诺（约 7-10 天）
9. Review Agent 5 层防幻觉真实逻辑（目前只有 1 层：出处验证）
10. 画像/评估 API 接入真实仓储
11. 测试覆盖、压测、安全项
12. P1 创新接入主流程

**粗估：1 人约 20-27 天；4-5 人团队并行约可压到文档说的 20 天 MVP。**

---

## 立刻能做的第一件事

**接 PostgreSQL 真实仓储**，替换 `app/dependencies.py` 的 `_PlaceholderRepo`。
画像/学习记录一旦能持久化，Profile/Assessment Agent 和画像/评估 API（目前 `NotImplementedError`）就能真正可用，是从「单次生成」走向「持续跟踪」的关键。

ORM 模型已就绪（`app/db/models.py`），建表脚本在 `docs/sql/init_schema.sql`，异步会话在 `app/db/session.py`。
起 PostgreSQL：项目根 `docker compose up -d db`，连接串填 `backend/.env` 的 `DATABASE_URL`。

> 讯飞星火已接通（HTTP OpenAI 兼容版，`lite` 免费无限量），密钥已在本地 `.env`（不进 git）。
> 验证连通可随时跑 `cd backend && py verify_spark.py`。

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
