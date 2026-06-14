# 后端镜像（§8.2）：FastAPI + Uvicorn
FROM python:3.11-slim

WORKDIR /app

# 系统依赖（asyncpg/bcrypt 等需编译工具）
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# 先装依赖以利用层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
