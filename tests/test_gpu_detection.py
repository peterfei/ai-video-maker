#!/usr/bin/env python3
"""
GPU检测测试脚本
测试M4芯片的GPU加速是否正常工作
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config_loader import get_config
from video_engine.gpu_accelerator import GPUVideoAccelerator
import torch

def main():
    print("=" * 60)
    print("GPU 加速检测测试")
    print("=" * 60)

    # 1. 检测PyTorch后端
    print("\n1. PyTorch 后端检测:")
    print(f"   PyTorch 版本: {torch.__version__}")
    print(f"   CUDA 可用: {torch.cuda.is_available()}")
    print(f"   MPS 可用: {hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()}")

    # 2. 加载配置
    print("\n2. 加载配置文件...")
    config = get_config("config/default_config.yaml")
    gpu_config = config.get('performance', {}).get('gpu', {})
    print(f"   GPU 启用: {gpu_config.get('enabled', False)}")
    print(f"   后端优先级: {gpu_config.get('backend_priority', ['cuda', 'mps', 'cpu'])}")

    # 3. 初始化GPU加速器
    print("\n3. 初始化 GPU 加速器...")
    accelerator = GPUVideoAccelerator(gpu_config)

    # 4. 显示GPU信息
    print("\n4. GPU 加速器状态:")
    print(f"   GPU 可用: {accelerator.is_gpu_available()}")
    print(f"   当前设备: {accelerator.get_device()}")
    print(f"   后端类型: {accelerator._backend_type}")

    # 5. 显示详细信息
    if accelerator.is_gpu_available():
        gpu_info = accelerator.get_gpu_info()
        if gpu_info:
            print("\n5. GPU 详细信息:")
            for key, value in gpu_info.items():
                print(f"   {key}: {value}")

        # 6. 内存使用情况
        print("\n6. 内存使用情况:")
        memory_info = accelerator.get_memory_usage()
        for key, value in memory_info.items():
            if 'gb' in key.lower():
                print(f"   {key}: {value:.2f} GB")
            elif 'utilization' in key.lower():
                print(f"   {key}: {value:.1f}%")
            else:
                print(f"   {key}: {value}")

        print("\n✅ GPU 加速已成功启用!")
        print(f"   您的 M4 GPU 已就绪，可以开始视频生成测试。")
    else:
        print("\n⚠️  GPU 加速未启用，将使用 CPU 处理")
        print("   请检查:")
        print("   - PyTorch 是否正确安装")
        print("   - MPS 后端是否可用")
        print("   - 配置文件中 GPU 是否启用")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
