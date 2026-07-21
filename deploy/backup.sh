#!/bin/bash
# ============================================
# 青萍小台 MVP - 备份脚本
# ============================================
# 功能:
#   1. 备份 MySQL 数据库 (mysqldump)
#   2. 备份上传文件
#   3. 备份配置文件
#   4. 按日期命名
#   5. 自动清理旧备份
#
# 使用方式:
#   chmod +x backup.sh
#   ./backup.sh
#
# 定时备份 (crontab):
#   0 2 * * * /opt/qingping-mvp/deploy/backup.sh >> /var/log/qingping-backup.log 2>&1
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
BACKUP_DIR="$PROJECT_DIR/backups"

# 备份保留天数
KEEP_DAYS=30

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

# 开始备份
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     青萍小台 MVP - 备份脚本             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份时间戳
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="qingping-backup-$TIMESTAMP"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# 创建备份目录
mkdir -p "$BACKUP_PATH"

log_info "开始备份: $BACKUP_NAME"

# ============================================
# 1. 备份数据库
# ============================================
log_info "[1/4] 备份数据库..."

# 从 .env 文件读取数据库配置
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

DB_HOST=${DB_HOST:-127.0.0.1}
DB_PORT=${DB_PORT:-3306}
DB_USER=${DB_USER:-root}
DB_PASSWORD=${DB_PASSWORD:-}
DB_NAME=${DB_NAME:-qingping}

DB_BACKUP_FILE="$BACKUP_PATH/database.sql"

if command -v mysqldump &> /dev/null; then
    if [ -n "$DB_PASSWORD" ]; then
        mysqldump \
            --host="$DB_HOST" \
            --port="$DB_PORT" \
            --user="$DB_USER" \
            --password="$DB_PASSWORD" \
            --databases "$DB_NAME" \
            --single-transaction \
            --routines \
            --triggers \
            --default-character-set=utf8mb4 \
            > "$DB_BACKUP_FILE" 2>/dev/null
    else
        mysqldump \
            --host="$DB_HOST" \
            --port="$DB_PORT" \
            --user="$DB_USER" \
            --databases "$DB_NAME" \
            --single-transaction \
            --routines \
            --triggers \
            --default-character-set=utf8mb4 \
            > "$DB_BACKUP_FILE" 2>/dev/null
    fi

    if [ $? -eq 0 ]; then
        # 压缩 SQL 文件
        gzip "$DB_BACKUP_FILE"
        DB_SIZE=$(du -h "$DB_BACKUP_FILE.gz" | cut -f1)
        log_success "数据库备份完成 ($DB_SIZE)"
    else
        log_error "数据库备份失败"
        rm -f "$DB_BACKUP_FILE"
    fi
else
    log_warning "未检测到 mysqldump，跳过数据库备份"
fi

# ============================================
# 2. 备份上传文件
# ============================================
log_info "[2/4] 备份上传文件..."

UPLOADS_DIR="$PROJECT_DIR/uploads"
UPLOADS_BACKUP_FILE="$BACKUP_PATH/uploads.tar.gz"

if [ -d "$UPLOADS_DIR" ] && [ "$(ls -A "$UPLOADS_DIR" 2>/dev/null)" ]; then
    tar -czf "$UPLOADS_BACKUP_FILE" -C "$PROJECT_DIR" uploads 2>/dev/null
    if [ $? -eq 0 ]; then
        UPLOAD_SIZE=$(du -h "$UPLOADS_BACKUP_FILE" | cut -f1)
        log_success "上传文件备份完成 ($UPLOAD_SIZE)"
    else
        log_warning "上传文件备份失败"
    fi
else
    log_warning "上传目录为空或不存在，跳过"
fi

# ============================================
# 3. 备份配置文件
# ============================================
log_info "[3/4] 备份配置文件..."

CONFIG_BACKUP_DIR="$BACKUP_PATH/config"
mkdir -p "$CONFIG_BACKUP_DIR"

# 备份 .env 文件
if [ -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env" "$CONFIG_BACKUP_DIR/env"
fi

# 备份 Nginx 配置
if [ -f "/etc/nginx/conf.d/qingping.conf" ]; then
    cp "/etc/nginx/conf.d/qingping.conf" "$CONFIG_BACKUP_DIR/nginx.conf"
fi

# 备份 systemd 服务文件
if [ -f "/etc/systemd/system/qingping-backend.service" ]; then
    cp "/etc/systemd/system/qingping-backend.service" "$CONFIG_BACKUP_DIR/qingping-backend.service"
fi

log_success "配置文件备份完成"

# ============================================
# 4. 生成备份信息
# ============================================
log_info "[4/4] 生成备份信息..."

INFO_FILE="$BACKUP_PATH/backup-info.txt"
cat > "$INFO_FILE" <<EOF
==========================================
  青萍小台 MVP - 备份信息
==========================================

备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份版本: $BACKUP_NAME
服务器: $(hostname)
IP 地址: $(hostname -I | awk '{print $1}')

数据库:
  主机: $DB_HOST
  端口: $DB_PORT
  数据库名: $DB_NAME

文件列表:
EOF

# 列出备份文件
find "$BACKUP_PATH" -type f -printf "  %p (%s bytes)\n" | sort >> "$INFO_FILE"

# 计算总大小
TOTAL_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
echo "" >> "$INFO_FILE"
echo "总大小: $TOTAL_SIZE" >> "$INFO_FILE"

log_success "备份信息生成完成"

# ============================================
# 清理旧备份
# ============================================
log_info "清理 $KEEP_DAYS 天前的旧备份..."

find "$BACKUP_DIR" -type d -name "qingping-backup-*" -mtime +$KEEP_DAYS -exec rm -rf {} + 2>/dev/null || true

DELETED_COUNT=$(find "$BACKUP_DIR" -type d -name "qingping-backup-*" -mtime +$KEEP_DAYS 2>/dev/null | wc -l)
log_success "旧备份清理完成"

# ============================================
# 备份完成
# ============================================
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     备份完成！                         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo "备份名称: $BACKUP_NAME"
echo "备份位置: $BACKUP_PATH"
echo "备份大小: $TOTAL_SIZE"
echo "保留天数: $KEEP_DAYS 天"
echo ""
echo "恢复方式:"
echo "  1. 解压文件: tar -xzf $BACKUP_PATH/uploads.tar.gz -C $PROJECT_DIR"
echo "  2. 恢复数据库: gunzip < $BACKUP_PATH/database.sql.gz | mysql -u$DB_USER -p $DB_NAME"
echo "  3. 恢复配置: 参考 $BACKUP_PATH/config/ 目录下的文件"
echo ""
