FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM python:3.13-slim
WORKDIR /app

# 复制前端构建产物到后端的static目录
COPY --from=frontend-build /app/frontend/dist /app/static

# 复制后端代码
COPY backend/ .

# 安装后端依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]