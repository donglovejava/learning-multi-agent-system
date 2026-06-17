"""知识图谱种子数据（内置，不依赖 Neo4j 即可运行）。

提供「机器学习 / 深度学习」领域的真实知识点 DAG，含前置依赖关系。
当 Neo4j 不可用时，KnowledgeGraphRepo 回退到本种子数据，
保证 PathAgent 和 ExplainableRecommender 跑真实 DAG。

§6.4：节点标签 Knowledge(name/difficulty/category/description)，
关系类型 PREREQUISITE(strength)。
"""

from __future__ import annotations

# 知识点节点：(name, difficulty 1-5, category, description)
SEED_NODES: list[dict] = [
    # 数学基础
    {"name": "线性代数基础", "difficulty": 2, "category": "数学",
     "description": "向量、矩阵运算、行列式、特征值"},
    {"name": "矩阵分解", "difficulty": 3, "category": "数学",
     "description": "SVD、特征分解、QR 分解"},
    {"name": "概率论入门", "difficulty": 3, "category": "数学",
     "description": "概率分布、条件概率、贝叶斯定理"},
    {"name": "数理统计", "difficulty": 3, "category": "数学",
     "description": "期望、方差、假设检验、最大似然估计"},
    {"name": "微积分", "difficulty": 2, "category": "数学",
     "description": "导数、偏导数、链式法则、梯度"},
    # 编程基础
    {"name": "Python 编程基础", "difficulty": 1, "category": "编程",
     "description": "语法、数据结构、函数、面向对象"},
    {"name": "NumPy", "difficulty": 2, "category": "编程",
     "description": "数组运算、广播机制、线性代数运算"},
    # 机器学习
    {"name": "机器学习概论", "difficulty": 2, "category": "机器学习",
     "description": "监督/无监督/强化学习、训练流程、过拟合"},
    {"name": "线性回归", "difficulty": 2, "category": "机器学习",
     "description": "最小二乘、梯度下降、正则化"},
    {"name": "逻辑回归", "difficulty": 2, "category": "机器学习",
     "description": "分类、Sigmoid、交叉熵损失"},
    {"name": "决策树", "difficulty": 2, "category": "机器学习",
     "description": "信息增益、ID3/C4.5/CART、剪枝"},
    {"name": "梯度下降", "difficulty": 3, "category": "机器学习",
     "description": "SGD、批量梯度下降、学习率调度"},
    {"name": "反向传播", "difficulty": 3, "category": "机器学习",
     "description": "链式法则、计算图、梯度计算"},
    # 深度学习
    {"name": "神经网络基础", "difficulty": 3, "category": "深度学习",
     "description": "感知机、激活函数、多层感知机"},
    {"name": "卷积神经网络", "difficulty": 4, "category": "深度学习",
     "description": "卷积层、池化、感受野、经典架构"},
    {"name": "循环神经网络", "difficulty": 4, "category": "深度学习",
     "description": "RNN、LSTM、GRU、序列建模"},
    {"name": "注意力机制", "difficulty": 4, "category": "深度学习",
     "description": "自注意力、Q/K/V、Softmax、缩放点积"},
    {"name": "多头注意力", "difficulty": 5, "category": "深度学习",
     "description": "并行注意力头、子空间投影"},
    {"name": "位置编码", "difficulty": 4, "category": "深度学习",
     "description": "正弦位置编码、可学习位置编码"},
    {"name": "Transformer 架构", "difficulty": 5, "category": "深度学习",
     "description": "编码器-解码器、残差连接、Layer Norm"},
    {"name": "BERT", "difficulty": 5, "category": "深度学习",
     "description": "MLM 预训练、双向编码、微调"},
    {"name": "GPT", "difficulty": 5, "category": "深度学习",
     "description": "自回归生成、因果注意力、大规模预训练"},
]

# 前置依赖边：(前置知识, 后继知识, 强度 0-1)
# 语义：要学「后继」最好先掌握「前置」
SEED_EDGES: list[tuple[str, str, float]] = [
    # 数学链
    ("微积分", "线性代数基础", 0.3),
    ("线性代数基础", "矩阵分解", 0.9),
    ("概率论入门", "数理统计", 0.8),
    # 编程链
    ("Python 编程基础", "NumPy", 0.9),
    ("线性代数基础", "NumPy", 0.7),
    # 机器学习链
    ("线性代数基础", "机器学习概论", 0.6),
    ("概率论入门", "机器学习概论", 0.6),
    ("NumPy", "机器学习概论", 0.5),
    ("机器学习概论", "线性回归", 0.8),
    ("机器学习概论", "逻辑回归", 0.8),
    ("机器学习概论", "决策树", 0.7),
    ("线性回归", "逻辑回归", 0.5),
    ("微积分", "梯度下降", 0.8),
    ("线性代数基础", "梯度下降", 0.5),
    ("梯度下降", "反向传播", 0.7),
    ("机器学习概论", "神经网络基础", 0.8),
    ("反向传播", "神经网络基础", 0.9),
    # 深度学习链
    ("神经网络基础", "卷积神经网络", 0.8),
    ("神经网络基础", "循环神经网络", 0.8),
    ("循环神经网络", "注意力机制", 0.6),
    ("神经网络基础", "注意力机制", 0.7),
    ("线性代数基础", "注意力机制", 0.7),
    ("注意力机制", "多头注意力", 0.9),
    ("注意力机制", "位置编码", 0.6),
    ("多头注意力", "Transformer 架构", 0.9),
    ("位置编码", "Transformer 架构", 0.8),
    ("Transformer 架构", "BERT", 0.9),
    ("Transformer 架构", "GPT", 0.9),
]

# 建立邻接索引，供 repo 快速查询
def build_adjacency() -> tuple[
    dict[str, list[tuple[str, float]]],  # 前置 → [(后继, strength)]
    dict[str, list[tuple[str, float]]],  # 后继 → [(前置, strength)]
    dict[str, dict],                     # name → node
]:
    """构建前置/后继邻接表与节点索引。"""
    forward: dict[str, list[tuple[str, float]]] = {}
    backward: dict[str, list[tuple[str, float]]] = {}
    nodes = {n["name"]: n for n in SEED_NODES}

    for pre, succ, strength in SEED_EDGES:
        forward.setdefault(pre, []).append((succ, strength))
        backward.setdefault(succ, []).append((pre, strength))

    return forward, backward, nodes


def all_node_names() -> list[str]:
    return [n["name"] for n in SEED_NODES]


def fuzzy_match(query: str) -> str | None:
    """模糊匹配知识点名称（支持"注意力""Transformer"等简称）。"""
    q = query.strip().lower().replace(" ", "")
    # 精确
    for n in SEED_NODES:
        if n["name"].lower().replace(" ", "") == q:
            return n["name"]
    # 包含
    for n in SEED_NODES:
        if q in n["name"].lower().replace(" ", ""):
            return n["name"]
    for n in SEED_NODES:
        if n["name"].lower().replace(" ", "") in q:
            return n["name"]
    return None
