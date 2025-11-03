#!/bin/bash

# 视频生成工厂 - 快速启动脚本

echo "=================================="
echo "   视频生成工厂 (Video Factory)  "
echo "=================================="
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python 3"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
if [ ! -f "venv/.installed" ]; then
    echo "安装依赖..."
    pip install -r requirements.txt
    touch venv/.installed
    echo "依赖安装完成"
fi

echo ""
echo "环境准备就绪！"
echo ""

# 如果提供了参数，直接运行
if [ $# -gt 0 ]; then
    python src/main.py "$@"
else
    # 显示使用帮助
    echo "使用方法:"
    echo "  ./run.sh --script examples/sample_script.txt"
    echo "  ./run.sh --batch data/scripts"
    echo "  ./run.sh --help"
    echo ""
    echo "或者进入交互模式:"
    echo "  source venv/bin/activate"
    echo "  python src/main.py --script examples/sample_script.txt"
fi
