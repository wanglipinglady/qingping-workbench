"""
pytest 配置文件
运行方式：cd backend && pytest tests/ -v
"""
import sys
import os

# 把 backend 目录加入 Python path，让测试可以直接 import app.*
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
