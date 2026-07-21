#!/usr/bin/env python3
"""
青萍小台 - 环境检测与验证脚本
使用方法：python verify_setup.py
检测内容：Python 环境、依赖、配置文件、数据库、后端服务、外部 API、前端
"""
import sys
import os
import platform
from pathlib import Path

# ==================== 颜色输出 ====================
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def ok(msg):   print(f"{Colors.GREEN}[✓]{Colors.RESET} {msg}")
def fail(msg): print(f"{Colors.RED}[✗]{Colors.RESET} {msg}")
def warn(msg): print(f"{Colors.YELLOW}[!]{Colors.RESET} {msg}")
def info(msg): print(f"{Colors.BLUE}[i]{Colors.RESET} {msg}")

# ==================== 全局统计 ====================
total = 0
passed = 0
failed = 0
warnings = 0

def check(name, condition, fail_msg="", warning=False):
    """执行一项检查"""
    global total, passed, failed, warnings
    total += 1
    if condition:
        passed += 1
        ok(name)
    else:
        if warning:
            warnings += 1
            warn(f"{name} - {fail_msg}")
        else:
            failed += 1
            fail(f"{name} - {fail_msg}")

# ==================== 主检测流程 ====================
def main():
    print(f"\n{Colors.BOLD}===== 青萍小台 - 环境检测脚本 ====={Colors.RESET}\n")

    project_root = Path(__file__).parent.resolve()
    backend_dir = project_root / "backend"
    frontend_dir = project_root / "frontend"
    info(f"项目根目录: {project_root}")

    # ============== 1. Python 环境 ==============
    print(f"\n{Colors.BOLD}--- 1. Python 环境 ---{Colors.RESET}")

    py_version = sys.version_info
    check(
        f"Python 版本: {py_version.major}.{py_version.minor}.{py_version.micro}",
        py_version.major == 3 and 10 <= py_version.minor < 13,
        "需要 Python 3.10 ~ 3.12（3.13 有兼容问题）"
    )

    check(
        "操作系统检测",
        True,
        f"{platform.system()} {platform.release()}"
    )

    # ============== 2. 后端依赖 ==============
    print(f"\n{Colors.BOLD}--- 2. 后端依赖 ---{Colors.RESET}")

    os.chdir(backend_dir)
    sys.path.insert(0, str(backend_dir))

    required_packages = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("sqlalchemy", "SQLAlchemy"),
        ("pydantic", "Pydantic"),
        ("pydantic_settings", "Pydantic Settings"),
        ("jose", "python-jose"),
        ("bcrypt", "bcrypt"),
        ("requests", "requests"),
        ("chromadb", "ChromaDB"),
    ]

    for pkg_name, display_name in required_packages:
        try:
            __import__(pkg_name)
            check(f"{display_name} 已安装", True)
        except ImportError:
            check(f"{display_name} 已安装", False, f"请执行: pip install {pkg_name}")

    # ============== 3. 配置文件 ==============
    print(f"\n{Colors.BOLD}--- 3. 配置文件 ---{Colors.RESET}")

    backend_env = backend_dir / ".env"
    backend_env_example = backend_dir / ".env.example"

    check(
        "backend/.env.example 存在",
        backend_env_example.exists(),
        "模板文件缺失，请从仓库拉取"
    )

    if backend_env.exists():
        ok("backend/.env 存在")
        # 检查关键配置
        try:
            from app.core.config import settings
            check(
                "MINIMAX_API_KEY 已配置",
                bool(settings.MINIMAX_API_KEY),
                "API Key 为空，AI 功能不可用"
            )
            check(
                "MINIMAX_BASE_URL 已配置",
                bool(settings.MINIMAX_BASE_URL),
                "使用默认值"
            )
            check(
                "DATABASE_URL 已配置",
                bool(settings.DATABASE_URL),
                "使用默认值（SQLite）"
            )
        except Exception as e:
            fail(f"加载配置失败: {e}")
    else:
        fail("backend/.env 不存在 - 请复制 .env.example 为 .env 并填入配置")

    # ============== 4. 数据库 ==============
    print(f"\n{Colors.BOLD}--- 4. 数据库 ---{Colors.RESET}")

    try:
        from app.core.database import init_db, get_db
        from sqlalchemy import text
        db = next(get_db())
        db.execute(text("SELECT 1"))
        ok("数据库连接成功")
        init_db()
        ok("数据表初始化成功")
    except Exception as e:
        fail(f"数据库检测失败: {e}")

    # ============== 5. 后端服务 ==============
    print(f"\n{Colors.BOLD}--- 5. 后端服务 ---{Colors.RESET}")

    try:
        import requests
        from app.core.config import settings
        # 用 127.0.0.1 代替 0.0.0.0（后者某些系统会返回 403）
        host = "127.0.0.1" if settings.HOST == "0.0.0.0" else settings.HOST
        health_url = f"http://{host}:{settings.PORT}/api/health"
        try:
            resp = requests.get(health_url, timeout=3)
            if resp.status_code == 200:
                ok(f"后端服务运行中: {health_url}")
                data = resp.json()
                if data.get("code") == 200 or data.get("code") == 0:
                    ok("健康检查返回正常")
            else:
                warn(f"后端服务响应异常: HTTP {resp.status_code}")
        except requests.ConnectionError:
            warn("后端服务未启动 - 请运行: cd backend && python main.py")
        except requests.Timeout:
            warn("后端服务响应超时")
    except Exception as e:
        fail(f"后端服务检测失败: {e}")

    # ============== 6. MiniMax API ==============
    print(f"\n{Colors.BOLD}--- 6. MiniMax API ---{Colors.RESET}")

    try:
        from app.core.config import settings
        if settings.MINIMAX_API_KEY:
            from app.capabilities.llm.minimax_client import minimax_client
            try:
                result = minimax_client.chat(
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=10,
                    temperature=0,
                )
                if result and "choices" in result:
                    ok("MiniMax API 调用成功")
                else:
                    warn(f"MiniMax API 返回格式异常: {str(result)[:100]}")
            except Exception as e:
                fail(f"MiniMax API 调用失败: {e}")
        else:
            warn("MINIMAX_API_KEY 未配置，跳过 API 检测")
    except Exception as e:
        fail(f"MiniMax API 检测失败: {e}")

    # ============== 7. 前端环境 ==============
    print(f"\n{Colors.BOLD}--- 7. 前端环境 ---{Colors.RESET}")

    os.chdir(project_root)

    # Node 版本检测
    import subprocess
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
        node_ver = result.stdout.strip().lstrip("v")
        parts = node_ver.split(".")
        major = int(parts[0]) if parts else 0
        check(
            f"Node.js 版本: {node_ver}",
            major >= 18,
            "建议 Node.js >= 18，或已降级 Vite 到 4.x 适配",
            warning=True
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        fail("Node.js 未安装或不在 PATH 中")

    # 前端依赖检测
    node_modules = frontend_dir / "node_modules"
    check(
        "前端依赖已安装 (node_modules 存在)",
        node_modules.exists(),
        "请执行: cd frontend && npm install",
        warning=True
    )

    # 前端 .env 检测
    frontend_env = frontend_dir / ".env"
    frontend_env_example = frontend_dir / ".env.example"
    if frontend_env_example.exists() and not frontend_env.exists():
        warn("frontend/.env 不存在（如需要自定义 API 地址请创建）")

    # ============== 8. Git 状态 ==============
    print(f"\n{Colors.BOLD}--- 8. Git 状态 ---{Colors.RESET}")

    gitignore = project_root / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        check(
            ".gitignore 包含 *.sqlite3",
            "*.sqlite3" in content,
            "建议添加，避免数据库文件被追踪",
            warning=True
        )
        check(
            ".gitignore 包含 .env",
            ".env" in content,
            "建议添加，避免敏感配置被提交",
            warning=True
        )
    else:
        warn(".gitignore 不存在")

    # ============== 总结 ==============
    print(f"\n{Colors.BOLD}===== 检测结果 ====={Colors.RESET}")
    print(f"总计: {total} 项 | 通过: {Colors.GREEN}{passed}{Colors.RESET} | 失败: {Colors.RED}{failed}{Colors.RESET} | 警告: {Colors.YELLOW}{warnings}{Colors.RESET}")

    if failed > 0:
        print(f"\n{Colors.RED}有 {failed} 项未通过，请先修复后再继续。{Colors.RESET}")
        return 1
    elif warnings > 0:
        print(f"\n{Colors.YELLOW}有 {warnings} 项警告，核心功能可用，但建议尽快处理。{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.GREEN}所有检查通过！环境配置完整，可以开始使用。{Colors.RESET}")
        return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}检测被用户中断{Colors.RESET}")
        sys.exit(130)
