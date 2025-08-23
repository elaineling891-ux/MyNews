# 使用 Playwright 官方 Python 镜像
FROM mcr.microsoft.com/playwright/python:v1.41.0-focal

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# Render 默认启动命令
CMD ["python", "main.py"]
