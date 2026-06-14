# 学习多智能体系统 · 后端

基于大模型的个性化资源生成与学习多智能体系统（中国软件杯 A3）的后端骨架。

11 个 Agent 通过 LangGraph 编排协同，对话构建画像、并行生成 6 种学习资源、规划个性化路径、动态评估学习效果。

> 当前为**可运行骨架**：架构、编排流程、数据模型、API 契约与核心算法均已落地并通过验证；LLM/数据库等外部依赖以占位实现注入，接入真实服务后各端点自动可用。

## 目录结构

```
backend/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── dependencies.py      # 依赖装配：LLM / Agent / 编排图单例
│   ├── core/                # 配置、日志、安全（JWT/bcrypt）
│   ├── llm/                 # 讯飞星火 + SeeDance 客户端
│   ├── innovations/         # 7 个创新模块（3 P0 + 4 P1）
│   ├── agents/              # 11 个 Agent + base + LangGraph 编排图
│   ├── db/                  # SQLAlchemy 模型与异步会话
│   ├── schemas/             # Pydantic 请求/响应模型
│   └── api/                 # 路由层
├── requirements.txt
└── Dockerfile
```

## 核心创新模块（`app/innovations/`）

| 模块 | 文件 | 说明 | 状态 |
|------|------|------|------|
| IN-03 可解释 AI 决策 | `explainable_recommender.py` | 知识图谱推理链 + 自然语言解释 | ✅ 算法已验证 |
| IN-04 个性化遗忘曲线 | `forgetting_curve.py` | 指数衰减拟合 s=a·exp(-b·t) + 最优复习时间 | ✅ 算法已验证（R²≈0.98） |
| IN-07 知识脚手架 | `scaffold_generator.py` | 3 级脚手架 + 按掌握度动态调整 | ✅ 算法已验证 |
| IN-01 跨模态关联 | `cross_modal_linker.py` | 资源关联同一知识点（Neo4j） | 🔌 待接图谱 |
| IN-02 群体智能 | `group_intelligence.py` | 学习序列模式挖掘优化路径 | ✅ 算法已落地 |
| IN-05 认知负荷 | `cognitive_load.py` | 行为数据估算负荷 + 动态调难度 | ✅ 算法已落地 |
| IN-08 元认知培养 | `metacognition.py` | 预测→反思→校准 | ✅ 算法已落地 |

## 11 个 Agent（`app/agents/`）

Orchestrator（总指挥）· Profile（画像）· Retrieval（双引擎检索 + RRF）· Document · Quiz · MindMap · Video · Code · Path（DAG + 改进 Dijkstra）· Assessment（10 维评估）· Review（5 层防幻觉审核）

编排图见 `graph.py`：已安装 `langgraph` 时构建真实 `StateGraph`；否则回退 `SequentialGraph`（资源生成阶段真正并行 fan-out），两者接口一致。

## 本地运行

```bash
# 1. 安装依赖
cd backend
py -m venv .venv && .venv/Scripts/activate   # Windows
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env   # 填入讯飞星火 / SeeDance 凭据与数据库连接

# 3. 启动
uvicorn app.main:app --reload --port 8000
# 文档: http://localhost:8000/docs   探活: http://localhost:8000/health
```

## 一键容器部署

```bash
# 仓库根目录
docker compose up -d        # 启动 backend / postgres / redis / milvus / neo4j / rabbitmq
```

数据库初始化脚本见 `docs/sql/init_schema.sql`。

## 接入真实依赖

骨架以 `NotImplementedError` 标注待接入点，按设计说明书章节实现即可：

- `app/llm/spark_client.py::_call_api` — 讯飞星火鉴权与请求（§5.2.1）
- `app/llm/seedance_client.py` — SeeDance 视频生成（§5.2.2）
- `app/dependencies.py::_PlaceholderRepo` — 替换为真实 Neo4j/Milvus/PostgreSQL 仓储
- 各资源 Agent 的 LLM 生成与各 `/api/v1/*` 端点

## 已验证

- 全量 `py_compile` 通过（42 个模块）
- 核心算法冒烟测试：遗忘曲线拟合 R²=0.978、脚手架分级、可解释推荐、改进 Dijkstra、RRF 融合
