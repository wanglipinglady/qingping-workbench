#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================
青萍小台 MVP - 跨平台一键启动脚本
兼容 macOS / Windows / Linux
============================================
使用方法：
    python3 start.py            # macOS / Linux
    python start.py             # Windows

功能：
    1. 自动检测 Python / Node.js 环境
    2. 自动创建虚拟环境并安装后端依赖
    3. 自动安装前端依赖
    4. 自动从 .env.example 复制 .env
    5. 同时启动后端 (8080) 和前端 (5173)
    6. Ctrl+C 优雅停止所有服务
"""
import os
import sys
import time
import signal
import shutil
import platform
import subprocess
import re
from pathlib import Path

# ==================== 颜色输出（兼容 Windows）====================
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def enable_ansi_colors():
    """Windows 的 cmd.exe 默认不支持 ANSI 颜色，启用 VT 模式"""
    if platform.system() == 'Windows':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x4
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x4)
        except Exception:
            pass


enable_ansi_colors()


def green(msg):  print(f"{Colors.GREEN}{msg}{Colors.RESET}")
def red(msg):    print(f"{Colors.RED}{msg}{Colors.RESET}")
def yellow(msg): print(f"{Colors.YELLOW}{msg}{Colors.RESET}")
def blue(msg):   print(f"{Colors.BLUE}{msg}{Colors.RESET}")
def bold(msg):   print(f"{Colors.BOLD}{msg}{Colors.RESET}")


# ==================== 工具函数 ====================
SCRIPT_DIR = Path(__file__).parent.resolve()
IS_WINDOWS = platform.system() == 'Windows'


def get_python():
    """获取 Python 可执行文件
    macOS/Linux 优先 python3；Windows 优先 python"""
    candidates = ['python3', 'python'] if not IS_WINDOWS else ['python', 'python3', 'py']
    for cmd in candidates:
        if shutil.which(cmd):
            return cmd
    return None


def run_quiet(cmd, cwd=None, timeout=30):
    """静默执行命令（用于检测）"""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True,
            text=True, timeout=timeout
        )
        return result.returncode == 0, (result.stdout or result.stderr).strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return False, ''


def check_version(name, cmd, min_major=None, version_arg='--version'):
    """检查工具版本"""
    ok, output = run_quiet([cmd, version_arg], timeout=5)
    if not ok:
        red(f"[✗] 未检测到 {name}")
        return False
    match = re.search(r'(\d+)\.(\d+)', output)
    if match and min_major is not None:
        major = int(match.group(1))
        if major < min_major:
            red(f"[✗] {name} 版本过低: {output}（需要 >= {min_major}.0）")
            return False
    green(f"[✓] {name}: {output}")
    return True


# ==================== 依赖安装 ====================
def ensure_venv(backend_dir: Path):
    """创建虚拟环境并安装后端依赖，返回 venv 中的 python 路径"""
    venv_dir = backend_dir / '.venv'
    py = get_python()

    if not venv_dir.exists():
        yellow(f"[*] 创建 Python 虚拟环境: {venv_dir.name}/")
        subprocess.run([py, '-m', 'venv', str(venv_dir)], check=True)

    # 虚拟环境中的 Python / pip 路径
    if IS_WINDOWS:
        venv_py = venv_dir / 'Scripts' / 'python.exe'
    else:
        venv_py = venv_dir / 'bin' / 'python'

    # 检测依赖是否已安装（用 fastapi 作为探针）
    yellow("[*] 检查后端依赖...")
    ok, _ = run_quiet([str(venv_py), '-c', 'import fastapi'], timeout=10)
    if ok:
        green("[✓] 后端依赖已安装")
    else:
        yellow("[*] 安装后端依赖（首次需要 2~3 分钟）...")
        # Windows 下 venv 中的 pip 也是 .exe
        pip_cmd = [str(venv_py), '-m', 'pip', 'install', '-r', str(backend_dir / 'requirements.txt')]
        subprocess.run(pip_cmd, check=True)
        green("[✓] 后端依赖安装完成")

    return str(venv_py)


def install_frontend_deps(frontend_dir: Path):
    """安装前端依赖"""
    yellow("[*] 检查前端依赖...")
    node_modules = frontend_dir / 'node_modules'
    if node_modules.exists():
        green("[✓] 前端依赖已安装")
        return

    yellow("[*] 安装前端依赖（首次需要 1~2 分钟）...")
    # Windows 上 npm.cmd 必须通过 shell=True 调用，否则 spawn 失败
    if IS_WINDOWS:
        subprocess.run('npm install', cwd=str(frontend_dir), shell=True, check=True)
    else:
        subprocess.run(['npm', 'install'], cwd=str(frontend_dir), check=True)
    green("[✓] 前端依赖安装完成")


# ==================== 主流程 ====================
def main():
    bold("\n===== 青萍小台 MVP - 一键启动 =====\n")
    blue(f"[i] 操作系统: {platform.system()} {platform.release()}")
    blue(f"[i] 项目目录: {SCRIPT_DIR}\n")

    # ---------- 1. 环境检查 ----------
    bold("--- 1. 环境检查 ---")
    py = get_python()
    if not check_version("Python", py):
        red("请先安装 Python 3.10+，下载地址: https://www.python.org/downloads/")
        sys.exit(1)

    # 检查 Python 子版本 >= 3.10 且 < 3.13
    ok, ver_str = run_quiet([py, '-c', 'import sys; print("%d.%d" % (sys.version_info.major, sys.version_info.minor))'])
    if ok:
        major, minor = (int(x) for x in ver_str.split('.'))
        if not (major == 3 and 10 <= minor <= 12):
            yellow(f"[!] 推荐 Python 3.10 ~ 3.12，当前是 3.{minor}（3.13 部分包缺 wheel）")

    if not check_version("Node.js", 'node', min_major=18):
        red("请先安装 Node.js >= 18，下载地址: https://nodejs.org/")
        sys.exit(1)

    if not check_version("npm", 'npm'):
        red("npm 未安装（通常随 Node.js 一起安装）")
        sys.exit(1)

    # ---------- 2. 准备配置文件 ----------
    bold("\n--- 2. 准备配置文件 ---")
    backend_dir = SCRIPT_DIR / 'backend'
    frontend_dir = SCRIPT_DIR / 'frontend'

    env_file = backend_dir / '.env'
    env_example = backend_dir / '.env.example'
    if not env_file.exists():
        if env_example.exists():
            yellow("[!] backend/.env 不存在，正在从 .env.example 复制...")
            shutil.copy(env_example, env_file)
            yellow("[!] 请编辑 backend/.env，至少配置 MINIMAX_API_KEY")
        else:
            red("backend/.env.example 也不存在，请检查项目完整性")
            sys.exit(1)
    else:
        green("[✓] backend/.env 已存在")

    fe_env = frontend_dir / '.env'
    fe_env_example = frontend_dir / '.env.example'
    if fe_env_example.exists() and not fe_env.exists():
        yellow("[!] frontend/.env 不存在，正在从 .env.example 复制...")
        shutil.copy(fe_env_example, fe_env)

    # ---------- 3. 安装依赖 ----------
    bold("\n--- 3. 安装依赖 ---")
    venv_python = ensure_venv(backend_dir)
    install_frontend_deps(frontend_dir)

    # ---------- 4. 启动服务 ----------
    bold("\n--- 4. 启动服务 ---")
    processes = []

    def cleanup(signum=None, frame=None):
        bold("\n[*] 正在停止服务...")
        for name, proc in processes:
            try:
                proc.terminate()
            except Exception:
                pass
        time.sleep(1.5)
        for name, proc in processes:
            try:
                if proc.poll() is None:
                    proc.kill()
            except Exception:
                pass
        green("\n[✓] 所有服务已停止，再见 👋\n")
        sys.exit(0)

    # 注册信号处理
    signal.signal(signal.SIGINT, cleanup)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, cleanup)
    if IS_WINDOWS and hasattr(signal, 'SIGBREAK'):
        signal.signal(signal.SIGBREAK, cleanup)

    # 启动后端
    green("[后端] 启动中... (端口 8080)")
    backend_proc = subprocess.Popen(
        [venv_python, 'main.py'],
        cwd=str(backend_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        text=True,
    )
    processes.append(('后端', backend_proc))
    time.sleep(2)  # 给后端一点启动时间

    # 启动前端
    green("[前端] 启动中... (端口 5173)")
    if IS_WINDOWS:
        # Windows 下 npm.cmd 需要 shell=True
        frontend_proc = subprocess.Popen(
            'npm run dev',
            cwd=str(frontend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            bufsize=1,
            text=True,
        )
    else:
        frontend_proc = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd=str(frontend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            text=True,
        )
    processes.append(('前端', frontend_proc))

    bold("\n===== 服务启动完成 =====")
    yellow("前端地址: http://localhost:5173")
    yellow("后端地址: http://localhost:8080")
    yellow("API 文档: http://localhost:8080/docs")
    bold("\n按 Ctrl+C 停止所有服务\n")

    # 实时转发子进程输出 + 检测子进程是否退出
    try:
        import threading

        def stream_output(name, proc):
            try:
                for line in iter(proc.stdout.readline, ''):
                    if line:
                        print(f"[{name}] {line.rstrip()}")
            except Exception:
                pass

        for name, proc in processes:
            t = threading.Thread(target=stream_output, args=(name, proc), daemon=True)
            t.start()

        # 主循环：检测子进程状态
        while True:
            time.sleep(1)
            for name, proc in processes:
                if proc.poll() is not None:
                    red(f"\n[!] {name} 进程意外退出（returncode={proc.returncode}）")
                    cleanup()
    except KeyboardInterrupt:
        cleanup()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)