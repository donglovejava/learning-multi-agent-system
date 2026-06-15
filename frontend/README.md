# 前端

基于 React + TypeScript + Vite + Tailwind CSS 的学习多智能体系统前端。

## 快速启动

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:3000

## 页面

- **首页** (`/`)：项目介绍、功能入口
- **对话** (`/chat`)：与 AI 对话构建画像、请求资源
- **资源** (`/resources`)：输入知识点，一次生成 5 种学习资源

## 技术栈

- React 18 + TypeScript
- Vite 5（开发服务器 + 构建）
- Tailwind CSS 3（样式）
- React Router 6（路由）
- React Markdown（文档渲染）
- Recharts（图表，预留）

## 与后端对接

Vite 开发服务器已配置代理，`/api` 请求自动转发到 `http://localhost:8000`。

确保后端已启动：
```bash
cd backend
uvicorn app.main:app --reload
```
