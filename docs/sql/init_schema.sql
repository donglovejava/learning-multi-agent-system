-- ============================================================
-- 学习多智能体系统 数据库初始化脚本
-- 对应设计说明书 §6.1（核心表）+ §3.2.4（遗忘曲线相关表）
-- 目标库：PostgreSQL 15+
-- ============================================================

-- ---------- 用户与画像 ----------

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'student',  -- student/teacher/admin
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- 学生画像表（6 维度，§3.1.1）
CREATE TABLE IF NOT EXISTS student_profiles (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES users(id),
    major VARCHAR(100),
    grade VARCHAR(20),
    learning_goal VARCHAR(50),
    knowledge_base FLOAT CHECK (knowledge_base >= 0 AND knowledge_base <= 1),
    learning_style VARCHAR(20),
    motivation VARCHAR(20),
    motivation_strength FLOAT,
    metacognition FLOAT,
    scaffold_level VARCHAR(10) DEFAULT 'medium',
    version INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ---------- 知识图谱（关系镜像，主图谱在 Neo4j）----------

CREATE TABLE IF NOT EXISTS knowledge_nodes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    difficulty INT CHECK (difficulty >= 1 AND difficulty <= 5),
    category VARCHAR(50),
    description TEXT,
    course_id INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS knowledge_relations (
    id SERIAL PRIMARY KEY,
    from_node_id INT REFERENCES knowledge_nodes(id),
    to_node_id INT REFERENCES knowledge_nodes(id),
    relation_type VARCHAR(20),  -- prerequisite / related / transfer
    strength FLOAT CHECK (strength >= 0 AND strength <= 1),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ---------- 学习行为与效果 ----------

-- 学习记录表（同时作为遗忘曲线拟合数据源，§3.2.4）
CREATE TABLE IF NOT EXISTS learning_records (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES users(id),
    knowledge_id INT REFERENCES knowledge_nodes(id),
    action_type VARCHAR(20) NOT NULL,  -- learn / review / test
    score FLOAT CHECK (score >= 0 AND score <= 1),
    time_spent_seconds INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 遗忘曲线参数表（IN-04，§3.2.4）
CREATE TABLE IF NOT EXISTS forgetting_curves (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES users(id),
    knowledge_id INT REFERENCES knowledge_nodes(id),
    a FLOAT NOT NULL CHECK (a > 0 AND a <= 1),
    b FLOAT NOT NULL CHECK (b > 0),
    optimal_interval FLOAT NOT NULL,
    data_points INT NOT NULL DEFAULT 0,
    r_squared FLOAT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(student_id, knowledge_id)
);

-- 复习计划表（IN-04）
CREATE TABLE IF NOT EXISTS review_schedules (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES users(id),
    knowledge_id INT REFERENCES knowledge_nodes(id),
    scheduled_time TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    predicted_score FLOAT,
    actual_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ---------- 资源与路径 ----------

-- 生成资源表（6 种资源，§3.1.2）
CREATE TABLE IF NOT EXISTS generated_resources (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES users(id),
    knowledge_id INT REFERENCES knowledge_nodes(id),
    resource_type VARCHAR(20) NOT NULL,  -- document/quiz/mindmap/video/code/reading
    content JSONB NOT NULL,
    scaffold_level VARCHAR(10),
    quality_score FLOAT,
    review_status VARCHAR(20) DEFAULT 'pending',  -- pending/passed/rejected
    created_at TIMESTAMP DEFAULT NOW()
);

-- 学习路径表（DAG，§3.1.3）
CREATE TABLE IF NOT EXISTS learning_paths (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES users(id),
    path_data JSONB NOT NULL,
    current_node_id INT,
    status VARCHAR(20) DEFAULT 'active',  -- active/completed/archived
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 元认知预测记录表（IN-08）
CREATE TABLE IF NOT EXISTS metacognition_predictions (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES users(id),
    topic VARCHAR(200) NOT NULL,
    prediction INT CHECK (prediction >= 1 AND prediction <= 10),
    actual_score FLOAT,
    calibration FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ---------- 索引优化 ----------

CREATE INDEX IF NOT EXISTS idx_profiles_student ON student_profiles(student_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_relations_from ON knowledge_relations(from_node_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_relations_to ON knowledge_relations(to_node_id);
CREATE INDEX IF NOT EXISTS idx_learning_records_student ON learning_records(student_id, knowledge_id);
CREATE INDEX IF NOT EXISTS idx_forgetting_curves_student ON forgetting_curves(student_id);
CREATE INDEX IF NOT EXISTS idx_review_schedules_time ON review_schedules(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_generated_resources_student ON generated_resources(student_id);
CREATE INDEX IF NOT EXISTS idx_learning_paths_student ON learning_paths(student_id);
