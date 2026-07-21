#!/bin/bash
# ============================================
# 青萍小台 MVP - 一键部署脚本
# ============================================
# 功能:
#   1. 拉取/上传代码
#   2. 安装 Python 依赖
#   3. 初始化数据库
#   4. 构建前端
#   5. 重启服务
#
# 使用方式:
#   chmod +x deploy.sh
#   ./deploy.sh
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_DIR="/opt/qingping-mvp"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 打印分隔线
separator() {
    echo ""
    echo "============================================"
    echo "$1"
    echo "============================================"
    echo ""
}

# 开始部署
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     青萍小台 MVP - 一键部署脚本         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then
    log_warning "建议使用 root 用户执行部署，否则可能需要手动处理权限问题"
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# ============================================
# 1. 检查环境
# ============================================
separator "1/5 检查环境"

# 检查 Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_info "Python 版本: $PYTHON_VERSION"
else
    log_error "未检测到 Python3，请先安装 Python 3.10+"
    exit 1
fi

# 检查 Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    log_info "Node.js 版本: $NODE_VERSION"
else
    log_error "未检测到 Node.js，请先安装 Node.js 18+"
    exit 1
fi

# 检查 MySQL
if command -v mysql &> /dev/null; then
    log_info "MySQL 客户端已安装"
else
    log_warning "未检测到 MySQL 客户端，跳过数据库初始化"
    SKIP_DB_INIT=true
fi

# 检查 Nginx
if command -v nginx &> /dev/null; then
    log_info "Nginx 已安装"
else
    log_warning "未检测到 Nginx，请手动配置 Nginx"
fi

# ============================================
# 2. 拉取代码
# ============================================
separator "2/5 拉取代码"

if [ -d "$PROJECT_DIR/.git" ]; then
    log_info "检测到 Git 仓库，正在拉取最新代码..."
    cd "$PROJECT_DIR"
    git pull origin main || git pull origin master || {
        log_error "代码拉取失败"
        exit 1
    }
    log_success "代码拉取成功"
else
    log_warning "未检测到 Git 仓库，假设代码已手动上传"
fi

# ============================================
# 3. 后端部署
# ============================================
separator "3/5 部署后端"

# 检查后端目录
if [ ! -d "$BACKEND_DIR" ]; then
    log_error "后端目录不存在: $BACKEND_DIR"
    exit 1
fi

cd "$BACKEND_DIR"

# 创建虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    log_info "创建 Python 虚拟环境..."
    python3 -m venv "$VENV_DIR"
    log_success "虚拟环境创建成功"
else
    log_info "虚拟环境已存在，跳过创建"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 安装依赖
if [ -f "requirements.txt" ]; then
    log_info "安装 Python 依赖..."
    pip install --upgrade pip
    pip install -r requirements.txt
    log_success "Python 依赖安装完成"
else
    log_warning "未找到 requirements.txt，跳过依赖安装"
fi

# 初始化数据库
if [ "$SKIP_DB_INIT" != "true" ] && [ -f "$PROJECT_DIR/backend/sql/init.sql" ]; then
    log_info "初始化数据库..."

    # 从 .env 文件读取数据库配置
    if [ -f "$PROJECT_DIR/.env" ]; then
        export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
    fi

    DB_HOST=${DB_HOST:-127.0.0.1}
    DB_PORT=${DB_PORT:-3306}
    DB_USER=${DB_USER:-root}
    DB_PASSWORD=${DB_PASSWORD:-}
    DB_NAME=${DB_NAME:-qingping}

    if [ -n "$DB_PASSWORD" ]; then
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" < "$PROJECT_DIR/backend/sql/init.sql" 2>/dev/null || {
            log_error "数据库初始化失败，请检查配置"
            exit 1
        }
    else
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" < "$PROJECT_DIR/backend/sql/init.sql" 2>/dev/null || {
            log_error "数据库初始化失败，请检查配置"
            exit 1
        }
    fi

    log_success "数据库初始化完成"
else
    log_warning "跳过数据库初始化"
fi

# 创建必要目录
log_info "创建必要目录..."
mkdir -p "$PROJECT_DIR/uploads"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/vector_store"
mkdir -p "$PROJECT_DIR/backups"
log_success "目录创建完成"

# 设置权限
log_info "设置文件权限..."
chown -R www-data:www-data "$PROJECT_DIR/uploads"
chown -R www-data:www-data "$PROJECT_DIR/logs"
chown -R www-data:www-data "$PROJECT_DIR/vector_store"
chmod -R 755 "$PROJECT_DIR/uploads"
log_success "权限设置完成"

# 退出虚拟环境
deactivate

# ============================================
# 4. 前端构建
# ============================================
separator "4/5 构建前端"

if [ ! -d "$FRONTEND_DIR" ]; then
    log_error "前端目录不存在: $FRONTEND_DIR"
    exit 1
fi

cd "$FRONTEND_DIR"

# 检查 .env 文件
if [ ! -f ".env" ]; then
    log_info "创建前端 .env 文件..."
    cp .env.example .env
    log_warning "请检查 .env 配置是否正确"
fi

# 安装依赖
if [ ! -d "node_modules" ]; then
    log_info "安装前端依赖..."
    npm install
    log_success "前端依赖安装完成"
else
    log_info "node_modules 已存在，执行 npm install 更新..."
    npm install
    log_success "前端依赖更新完成"
fi

# 构建
log_info "构建前端..."
npm run build
log_success "前端构建完成"

# ============================================
# 5. 重启服务
# ============================================
separator "5/5 重启服务"

# 后端服务
if systemctl list-unit-files | grep -q qingping-backend.service; then
    log_info "重启后端服务..."
    systemctl restart qingping-backend
    sleep 2
    if systemctl is-active --quiet qingping-backend; then
        log_success "后端服务启动成功"
    else
        log_error "后端服务启动失败，请检查日志: journalctl -u qingping-backend -n 50"
        exit 1
    fi
else
    log_warning "未检测到 qingping-backend 服务，请手动配置 systemd 服务"
    log_info "  sudo cp deploy/qingping-backend.service /etc/systemd/system/"
    log_info "  sudo systemctl daemon-reload"
    log_info "  sudo systemctl enable qingping-backend"
    log_info "  sudo systemctl start qingping-backend"
fi

# Nginx 配置
if command -v nginx &> /dev/null; then
    log_info "检查 Nginx 配置..."
    if [ -f "/etc/nginx/conf.d/qingping.conf" ] || [ -f "/etc/nginx/sites-enabled/qingping" ]; then
        nginx -t && systemctl reload nginx
        log_success "Nginx 配置重载成功"
    else
        log_warning "未检测到青萍 Nginx 配置文件"
        log_info "  sudo cp deploy/nginx.conf /etc/nginx/conf.d/qingping.conf"
        log_info "  sudo nginx -t"
        log_info "  sudo systemctl reload nginx"
    fi
fi

# ============================================
# 部署完成
# ============================================
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     部署完成！                         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo "访问地址:"
echo "  前端: http://$(hostname -I | awk '{print $1}'):8080"
echo "  后端: http://$(hostname -I | awk '{print $1}'):8081"
echo "  API文档: http://$(hostname -I | awk '{print $1}'):8081/docs"
echo ""
echo "默认账号:"
echo "  用户名: admin"
echo "  密码: admin123"
echo ""
echo "服务管理:"
echo "  后端: systemctl start/stop/restart/status qingping-backend"
echo "  Nginx: systemctl start/stop/restart/reload nginx"
echo "  日志: journalctl -u qingping-backend -f"
echo ""
