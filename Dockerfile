# 使用 Python 3.12 slim 镜像
FROM python:3.12-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libnss3 libxss1 libasound2 libatk1.0-0 libcups2 libxcomposite1 \
    libxdamage1 libxrandr2 libgbm1 libpango1.0-0 libpangocairo-1.0-0 \
    libgtk-3-0 libdrm2 libx11-xcb1 libxcb-dri3-0 libxshmfence1 \
    libxrender1 libxtst6 ca-certificates wget curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 浏览器
RUN playwright install chromium

CMD ["python", "main.py"]
