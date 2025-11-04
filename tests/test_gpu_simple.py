#!/usr/bin/env python3
"""
简化版GPU检测脚本
不依赖项目配置，直接测试PyTorch和MPS
"""

def main():
    print("=" * 60)
    print("简化版 GPU 检测测试")
    print("=" * 60)

    # 1. 检测PyTorch
    print("\n1. 检测 PyTorch...")
    try:
        import torch
        print(f"   ✅ PyTorch 已安装")
        print(f"   版本: {torch.__version__}")
    except ImportError:
        print(f"   ❌ PyTorch 未安装")
        print(f"   请运行: pip install torch")
        return

    # 2. 检测CUDA
    print("\n2. 检测 CUDA...")
    if torch.cuda.is_available():
        print(f"   ✅ CUDA 可用")
        print(f"   设备数量: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"   设备 {i}: {torch.cuda.get_device_name(i)}")
    else:
        print(f"   ⚠️  CUDA 不可用")

    # 3. 检测MPS (Apple Silicon)
    print("\n3. 检测 MPS (Apple Silicon)...")
    if hasattr(torch.backends, 'mps'):
        if torch.backends.mps.is_available():
            print(f"   ✅ MPS 可用")
            print(f"   这是 Apple Silicon 芯片!")

            # 尝试创建MPS设备
            try:
                device = torch.device('mps')
                print(f"   MPS 设备: {device}")

                # 测试张量创建
                test_tensor = torch.randn(100, 100, device=device)
                print(f"   ✅ 成功在 MPS 设备上创建张量")
                print(f"   测试张量形状: {test_tensor.shape}")

                # 简单计算测试
                result = test_tensor @ test_tensor.T
                print(f"   ✅ MPS 矩阵运算测试通过")

            except Exception as e:
                print(f"   ❌ MPS 测试失败: {e}")
        else:
            print(f"   ⚠️  MPS 不可用")
            print(f"   可能原因:")
            print(f"   - 不是 Apple Silicon 芯片")
            print(f"   - macOS 版本过低")
            print(f"   - PyTorch 版本不支持 MPS")
    else:
        print(f"   ⚠️  torch.backends.mps 不存在")
        print(f"   请更新到 PyTorch 2.0+")

    # 4. 检测芯片型号
    print("\n4. 检测芯片型号...")
    try:
        import subprocess
        import platform

        if platform.system() == 'Darwin':
            result = subprocess.run(['sysctl', 'machdep.cpu.brand_string'],
                                  capture_output=True, text=True, timeout=5)
            cpu_brand = result.stdout.strip()
            print(f"   CPU: {cpu_brand}")

            if 'Apple' in cpu_brand:
                if 'M4' in cpu_brand:
                    print(f"   🎉 检测到 Apple M4 芯片!")
                    if 'Max' in cpu_brand:
                        print(f"   型号: M4 Max (40核GPU)")
                    elif 'Pro' in cpu_brand:
                        print(f"   型号: M4 Pro (20核GPU)")
                    else:
                        print(f"   型号: M4 基础版 (10核GPU)")
                elif 'M3' in cpu_brand:
                    print(f"   🎉 检测到 Apple M3 芯片!")
                elif 'M2' in cpu_brand:
                    print(f"   🎉 检测到 Apple M2 芯片!")
                elif 'M1' in cpu_brand:
                    print(f"   🎉 检测到 Apple M1 芯片!")
        else:
            print(f"   平台: {platform.system()}")

    except Exception as e:
        print(f"   ⚠️  无法检测芯片型号: {e}")

    # 5. 系统内存
    print("\n5. 系统内存...")
    try:
        import psutil
        vm = psutil.virtual_memory()
        print(f"   总内存: {vm.total / (1024**3):.1f} GB")
        print(f"   可用内存: {vm.available / (1024**3):.1f} GB")
        print(f"   使用率: {vm.percent}%")
    except ImportError:
        print(f"   ⚠️  psutil 未安装，无法获取内存信息")
    except Exception as e:
        print(f"   ⚠️  获取内存信息失败: {e}")

    # 总结
    print("\n" + "=" * 60)
    print("检测总结:")

    has_gpu = False
    if torch.cuda.is_available():
        print("✅ NVIDIA GPU (CUDA) 可用 - 视频渲染将使用 GPU 加速")
        has_gpu = True
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        print("✅ Apple Silicon GPU (MPS) 可用 - 视频渲染将使用 GPU 加速")
        has_gpu = True

    if not has_gpu:
        print("⚠️  GPU 加速不可用 - 将使用 CPU 处理")

    print("=" * 60)

if __name__ == "__main__":
    main()
