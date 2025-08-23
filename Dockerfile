# 1️⃣ 使用 Python 官方镜像，指定 3.12
FROM python:3.12-slim

# 2️⃣ 安装系统依赖（Playwright 需要的一些依赖）
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk1.0-0 \
    libcups2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango1.0-0 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    libdrm2 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libxshmfence1 \
    libxrender1 \
    libxtst6 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 3️⃣ 设置工作目录
WORKDIR /app

# 4️⃣ 复制项目文件
COPY . /app

# 5️⃣ 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 6️⃣ 安装 Playwright 浏览器
RUN playwright install chromium

# 7️⃣ Render 默认启动命令
CMD ["python", "main.py"]
