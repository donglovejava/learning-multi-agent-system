"""应用配置：从环境变量加载，集中管理。"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # 应用
    app_name: str = "learning-multi-agent"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 120
    algorithm: str = "HS256"

    # 讯飞星火
    # HTTP OpenAI 兼容版鉴权：只需 APIPassword（控制台「http服务接口认证信息」）。
    spark_api_password: str = ""
    # 以下三项为 WebSocket 版鉴权所需，HTTP 版可留空。
    spark_app_id: str = ""
    spark_api_key: str = ""
    spark_api_secret: str = ""
    # OpenAI 兼容端点；chat 实际请求 {base_url}/v1/chat/completions。
    spark_base_url: str = "https://spark-api-open.xf-yun.com"
    # Spark Lite 免费无限量，model 名为 "lite"；升级时改为 4.0Ultra / generalv3.5 等。
    spark_model: str = "lite"
    spark_timeout: float = 60.0

    # SeeDance
    seedance_api_key: str = ""
    seedance_base_url: str = "https://api.seedance.com"

    # 数据库
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/learning_db"
    redis_url: str = "redis://localhost:6379/0"

    # Milvus
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "knowledge_chunks"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"

    # Embedding
    embedding_dim: int = 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
