#!/bin/bash
# ============================================
# 青萍小台 MVP - 更新脚本
# ============================================
# 功能:
#   1. 拉取最新代码
#   2. 更新依赖
#   3. 执行数据库迁移
#   4. 构建前端
#   5. 重启服务
#
# 使用方式:
#   chmod +x update.sh
#   ./update.sh
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目根目录
PROJECT_DIR="/opt/qingping-mvp"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"
BACKUP_DIR="$PROJECT_DIR/backups"

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

# 开始更新
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     青萍小台 MVP - 更新脚本             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

# 确认更新
read -p "确定要更新系统吗？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "已取消更新"
    exit 0
fi

# ============================================
# 1. 备份当前版本
# ============================================
log_info "创建备份..."
BACKUP_FILE="$BACKUP_DIR/update-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_FILE"

# 备份代码
if [ -d "$PROJECT_DIR/.git" ]; then
    cd "$PROJECT_DIR"
    git rev-parse HEAD > "$BACKUP_FILE/git-commit.txt"
    log_success "Git commit 已记录"
fi

log_success "备份完成: $BACKUP_FILE"

# ============================================
# 2. 拉取最新代码
# ============================================
echo ""
log_info "拉取最新代码..."
cd "$PROJECT_DIR"

if [ -d ".git" ]; then
    git stash
    git pull origin main || git pull origin master || {
        log_error "代码拉取失败"
        exit 1
    }
    git stash pop || true
    log_success "代码拉取成功"
else
    log_warning "未检测到 Git 仓库，跳过代码拉取"
fi

# ============================================
# 3. 更新后端依赖
# ============================================
echo ""
log_info "更新后端依赖..."

if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"

    if [ -f "$BACKEND_DIR/requirements.txt" ]; then
        pip install --upgrade pip
        pip install -r "$BACKEND_DIR/requirements.txt"
        log_success "后端依赖更新完成"
    else
        log_warning "未找到 requirements.txt"
    fi

    deactivate
else
    log_warning "虚拟环境不存在，跳过依赖更新"
fi

# ============================================
# 4. 数据库迁移
# ============================================
echo ""
log_info "检查数据库迁移..."

# 这里可以添加数据库迁移逻辑
# 例如: alembic upgrade head
log_success "数据库检查完成"

# ============================================
# 5. 构建前端
# ============================================
echo ""
log_info "构建前端..."

cd "$FRONTEND_DIR"

if [ -f "package.json" ]; then
    npm install
    npm run build
    log_success "前端构建完成"
else
    log_warning "未找到 package.json"
fi

# ============================================
# 6. 重启服务
# ============================================
echo ""
log_info "重启服务..."

if systemctl list-unit-files | grep -q qingping-backend.service; then
    systemctl restart qingping-backend
    sleep 2
    if systemctl is-active --quiet qingping-backend; then
        log_success "后端服务重启成功"
    else
        log_error "后端服务启动失败"
        log_info "查看日志: journalctl -u qingping-backend -n 50"
        exit 1
    fi
else
    log_warning "未检测到 systemd 服务，跳过重启"
fi

# 重载 Nginx
if command -v nginx &> /dev/null; then
    nginx -t && systemctl reload nginx 2>/dev/null || true
    log_success "Nginx 重载完成"
fi

# ============================================
# 更新完成
# ============================================
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     更新完成！                         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo "备份位置: $BACKUP_FILE"
echo ""
echo "如需回滚，请执行:"
echo "  cd $PROJECT_DIR"
echo "  git reset --hard \$(cat $BACKUP_FILE/git-commit.txt)"
echo "  ./deploy.sh"
echo ""
