#!/usr/bin/env python3
"""
视频生成工厂 - 启动脚本
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载.env环境变量
load_dotenv()

# 添加src到路径
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# 导入并运行主程序
from main import main

if __name__ == "__main__":
    main()
