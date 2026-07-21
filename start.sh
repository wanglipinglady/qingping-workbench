#!/bin/bash
# ============================================
# 青萍小台 MVP - 一键启动脚本
# 同时启动前端开发服务器和后端服务
# ============================================

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  青萍小台 MVP - 一键启动${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: 未检测到 Node.js，请先安装 Node.js >= 18${NC}"
    exit 1
fi
echo -e "${GREEN}[✓]${NC} Node.js 版本: $(node --version)"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未检测到 Python3，请先安装 Python >= 3.10${NC}"
    exit 1
fi
echo -e "${GREEN}[✓]${NC} Python 版本: $(python3 --version)"

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[!]${NC} 未找到根目录 .env 文件，正在从 .env.example 复制..."
    cp .env.example .env
    echo -e "${YELLOW}[!]${NC} 请根据实际情况修改 .env 配置"
fi

if [ ! -f "frontend/.env" ]; then
    echo -e "${YELLOW}[!]${NC} 未找到前端 .env 文件，正在从 .env.example 复制..."
    cp frontend/.env.example frontend/.env
fi

echo ""
echo -e "${YELLOW}[*]${NC} 安装前端依赖..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
else
    echo -e "${GREEN}[✓]${NC} 前端依赖已存在"
fi
cd "$SCRIPT_DIR"

echo ""
echo -e "${YELLOW}[*]${NC} 检查后端依赖..."
cd backend
if [ -f "requirements.txt" ]; then
    if python3 -c "import fastapi" 2>/dev/null; then
        echo -e "${GREEN}[✓]${NC} 后端依赖已安装"
    else
        echo -e "${YELLOW}[!]${NC} 正在安装后端依赖..."
        pip install -r requirements.txt
    fi
fi
cd "$SCRIPT_DIR"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  启动服务${NC}"
echo -e "${GREEN}========================================${NC}"

# 启动后端
echo -e "${GREEN}[后端]${NC} 启动中... (端口 8081)"
if [ -d "backend/app" ]; then
    cd backend
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8081 &
    BACKEND_PID=$!
    cd "$SCRIPT_DIR"
    echo -e "${GREEN}[后端]${NC} 进程 PID: $BACKEND_PID"
else
    echo -e "${YELLOW}[后端]${NC} 后端代码目录不存在，跳过启动"
    BACKEND_PID=""
fi

# 启动前端
echo -e "${GREEN}[前端]${NC} 启动中... (端口 5173)"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"
echo -e "${GREEN}[前端]${NC} 进程 PID: $FRONTEND_PID"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  服务启动完成${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "前端地址: ${YELLOW}http://localhost:5173${NC}"
echo -e "后端地址: ${YELLOW}http://localhost:8081${NC}"
echo -e "API 文档: ${YELLOW}http://localhost:8081/docs${NC}"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}"

# 捕获退出信号
cleanup() {
    echo ""
    echo -e "${YELLOW}[*]${NC} 正在停止服务..."
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}[后端]${NC} 已停止"
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}[前端]${NC} 已停止"
    fi
    echo -e "${GREEN}[✓]${NC} 所有服务已停止"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 等待子进程
wait
