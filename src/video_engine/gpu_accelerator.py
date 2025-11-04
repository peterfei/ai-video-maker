"""
GPU加速器
提供GPU检测、内存管理和CUDA加速支持
"""

import torch
from typing import Optional, Tuple, Dict, Any
import logging
import psutil
import platform
import subprocess
import re


class GPUVideoAccelerator:
    """
    GPU加速视频处理

    提供GPU检测、内存管理和多后端加速支持，
    支持CUDA (NVIDIA) 和 MPS (Apple Silicon)，自动检测硬件配置并优雅降级到CPU处理。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化GPU加速器

        Args:
            config: GPU配置字典
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # GPU状态
        self._device: Optional[torch.device] = None
        self._gpu_info: Optional[Dict[str, Any]] = None
        self._is_available = False
        self._backend_type = 'cpu'  # 'cuda', 'mps', or 'cpu'

        # 初始化GPU检测
        self._detect_gpu()

    def _detect_gpu(self) -> None:
        """检测并初始化GPU，支持多后端"""
        try:
            # 获取后端优先级配置
            backend_priority = self.config.get('backend_priority', ['cuda', 'mps', 'cpu'])

            # 尝试按优先级初始化后端
            for backend in backend_priority:
                if backend == 'cuda' and self._try_init_cuda():
                    return
                elif backend == 'mps' and self._try_init_mps():
                    return
                elif backend == 'cpu':
                    self._init_cpu_fallback()
                    return

            # 如果所有后端都失败了，使用CPU
            self._init_cpu_fallback()

        except Exception as e:
            self.logger.error(f"GPU detection failed: {e}")
            self._init_cpu_fallback()

    def _try_init_cuda(self) -> bool:
        """尝试初始化CUDA后端"""
        try:
            if not torch.cuda.is_available():
                return False

            gpu_count = torch.cuda.device_count()
            if gpu_count == 0:
                return False

            device_id = self._select_cuda_device(gpu_count)
            if device_id is None:
                return False

            if not self._validate_cuda_memory(device_id):
                return False

            self._device = torch.device(f'cuda:{device_id}')
            self._backend_type = 'cuda'
            self._is_available = True
            self._gpu_info = self._get_cuda_info(device_id)

            self.logger.info(f"CUDA GPU acceleration enabled: {self._gpu_info['name']} ({self._gpu_info['memory_total_gb']:.1f}GB)")
            return True

        except Exception as e:
            self.logger.warning(f"CUDA initialization failed: {e}")
            return False

    def _try_init_mps(self) -> bool:
        """尝试初始化MPS后端 (Apple Silicon)"""
        try:
            # 检查是否为macOS
            if platform.system() != 'Darwin':
                return False

            # 检查是否为Apple Silicon
            if not self._is_apple_silicon():
                return False

            # 检查MPS支持
            if not hasattr(torch.backends, 'mps') or not torch.backends.mps.is_available():
                self.logger.warning("MPS not available on this Apple Silicon device")
                return False

            # 检查内存要求
            if not self._validate_mps_memory():
                return False

            self._device = torch.device('mps')
            self._backend_type = 'mps'
            self._is_available = True
            self._gpu_info = self._get_mps_info()

            self.logger.info(f"MPS GPU acceleration enabled: {self._gpu_info['name']} ({self._gpu_info['compute_units']} cores)")
            return True

        except Exception as e:
            self.logger.warning(f"MPS initialization failed: {e}")
            return False

    def _init_cpu_fallback(self) -> None:
        """初始化CPU回退"""
        self._device = torch.device('cpu')
        self._backend_type = 'cpu'
        self._is_available = False
        self._gpu_info = None
        self.logger.info("Using CPU processing (GPU acceleration not available)")

    def _is_apple_silicon(self) -> bool:
        """检测是否为Apple Silicon芯片"""
        try:
            result = subprocess.run(['sysctl', 'machdep.cpu.brand_string'],
                                  capture_output=True, text=True, timeout=5)
            cpu_brand = result.stdout.strip()
            return 'Apple' in cpu_brand and any(chip in cpu_brand for chip in ['M1', 'M2', 'M3', 'M4'])
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            return False

    def _validate_mps_memory(self) -> bool:
        """验证MPS内存可用性"""
        try:
            # MPS使用统一内存，检查系统内存
            system_memory = psutil.virtual_memory()
            min_memory_gb = self.config.get('min_gpu_memory', 2 * 1024**3) / (1024**3)

            if system_memory.total / (1024**3) < min_memory_gb:
                self.logger.warning(f"Insufficient system memory for MPS: {system_memory.total / (1024**3):.1f}GB < {min_memory_gb:.1f}GB")
                return False

            return True
        except Exception as e:
            self.logger.warning(f"MPS memory validation failed: {e}")
            return False

    def _get_mps_info(self) -> Dict[str, Any]:
        """获取MPS设备信息"""
        try:
            compute_units = self._get_mps_compute_units()
            return {
                'id': 0,
                'name': f'Apple Silicon GPU ({compute_units} cores)',
                'backend': 'Metal Performance Shaders',
                'compute_units': compute_units,
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),  # 统一内存
                'architecture': 'Apple Silicon'
            }
        except Exception as e:
            return {
                'id': 0,
                'name': 'Apple Silicon GPU (Unknown)',
                'backend': 'Metal Performance Shaders',
                'compute_units': 8,
                'error': str(e)
            }

    def _get_mps_compute_units(self) -> int:
        """获取MPS计算单元数"""
        try:
            result = subprocess.run(['sysctl', 'machdep.cpu.brand_string'],
                                  capture_output=True, text=True, timeout=5)
            cpu_brand = result.stdout.strip()

            # M4 系列芯片
            if 'M4' in cpu_brand:
                if 'Max' in cpu_brand:
                    return 40  # M4 Max (最高配置: 40核GPU)
                elif 'Pro' in cpu_brand:
                    return 20  # M4 Pro (最高配置: 20核GPU)
                else:
                    return 10  # M4 基础版 (10核GPU)

            # M3 系列芯片
            elif 'M3' in cpu_brand:
                if 'Max' in cpu_brand:
                    return 40  # M3 Max
                elif 'Pro' in cpu_brand:
                    return 18  # M3 Pro
                else:
                    return 10  # M3 基础版

            # M2 系列芯片
            elif 'M2' in cpu_brand:
                if 'Ultra' in cpu_brand:
                    return 76  # M2 Ultra
                elif 'Max' in cpu_brand:
                    return 38  # M2 Max
                elif 'Pro' in cpu_brand:
                    return 19  # M2 Pro
                else:
                    return 10  # M2 基础版

            # M1 系列芯片
            elif 'M1' in cpu_brand:
                if 'Ultra' in cpu_brand:
                    return 64  # M1 Ultra
                elif 'Max' in cpu_brand:
                    return 32  # M1 Max
                elif 'Pro' in cpu_brand:
                    return 16  # M1 Pro
                else:
                    return 8   # M1 基础版

            else:
                return 8   # 默认值
        except:
            return 8

    def _select_cuda_device(self, gpu_count: int) -> Optional[int]:
        """
        选择GPU设备

        Args:
            gpu_count: 可用的GPU数量

        Returns:
            选择的GPU设备ID，如果没有合适设备则返回None
        """
        device_config = self.config.get('device', 'auto')

        if device_config == 'auto':
            # 自动选择：选择内存最大的GPU
            max_memory = 0
            selected_id = None

            for i in range(gpu_count):
                try:
                    props = torch.cuda.get_device_properties(i)
                    memory_gb = props.total_memory / (1024**3)

                    if memory_gb > max_memory:
                        max_memory = memory_gb
                        selected_id = i
                except Exception as e:
                    self.logger.warning(f"Failed to get properties for GPU {i}: {e}")
                    continue

            return selected_id

        elif device_config.startswith('cuda:'):
            # 指定CUDA设备
            try:
                device_id = int(device_config.split(':')[1])
                if 0 <= device_id < gpu_count:
                    return device_id
                else:
                    self.logger.error(f"Invalid CUDA device ID: {device_id}")
                    return None
            except (ValueError, IndexError) as e:
                self.logger.error(f"Invalid CUDA device specification: {device_config}")
                return None

        else:
            self.logger.error(f"Unsupported device specification: {device_config}")
            return None

    def _validate_cuda_memory(self, device_id: int) -> bool:
        """
        验证GPU内存是否充足

        Args:
            device_id: GPU设备ID

        Returns:
            是否有足够的内存
        """
        try:
            props = torch.cuda.get_device_properties(device_id)
            total_memory = props.total_memory
            min_memory = self.config.get('min_gpu_memory', 2 * 1024**3)  # 默认2GB

            if total_memory < min_memory:
                self.logger.warning(
                    f"GPU memory insufficient: {total_memory / (1024**3):.1f}GB < "
                    f"{min_memory / (1024**3):.1f}GB"
                )
                return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to validate GPU memory: {e}")
            return False

    def _get_cuda_info(self, device_id: int) -> Dict[str, Any]:
        """
        获取GPU信息

        Args:
            device_id: GPU设备ID

        Returns:
            GPU信息字典
        """
        try:
            props = torch.cuda.get_device_properties(device_id)

            return {
                'id': device_id,
                'name': props.name,
                'memory_total_gb': props.total_memory / (1024**3),
                'memory_free_gb': torch.cuda.mem_get_info(device_id)[0] / (1024**3),
                'compute_capability': f"{props.major}.{props.minor}",
                'multi_processor_count': props.multi_processor_count,
                'max_threads_per_block': props.max_threads_per_block,
                'max_threads_per_multiprocessor': props.max_threads_per_multiprocessor
            }

        except Exception as e:
            self.logger.error(f"Failed to get GPU info: {e}")
            return {
                'id': device_id,
                'name': 'Unknown',
                'memory_total_gb': 0.0,
                'memory_free_gb': 0.0,
                'error': str(e)
            }

    def is_gpu_available(self) -> bool:
        """检查GPU是否可用（支持CUDA和MPS）"""
        return self._is_available and self._device is not None and self._device.type in ['cuda', 'mps']

    def get_device(self) -> torch.device:
        """获取当前设备"""
        return self._device

    def get_gpu_info(self) -> Optional[Dict[str, Any]]:
        """获取GPU信息"""
        return self._gpu_info

    def get_optimal_batch_size(self, video_resolution: Tuple[int, int], frame_count: int = 1) -> int:
        """
        根据GPU内存计算最优批处理大小

        Args:
            video_resolution: 视频分辨率 (width, height)
            frame_count: 帧数

        Returns:
            推荐的批处理大小
        """
        if not self.is_gpu_available():
            return 1

        try:
            width, height = video_resolution
            pixels_per_frame = width * height

            # 估算每帧内存使用量 (RGB float32)
            bytes_per_frame = pixels_per_frame * 3 * 4  # RGB * float32

            # 总内存使用量
            total_bytes = bytes_per_frame * frame_count

            # GPU内存限制
            memory_limit = self.config.get('memory_limit', 0.8)  # 使用80%内存
            available_memory = self._gpu_info['memory_free_gb'] * (1024**3) * memory_limit

            # 计算最大批处理大小
            max_batch_size = int(available_memory / total_bytes)
            max_batch_size = max(1, max_batch_size)

            # 应用配置限制
            config_max = self.config.get('max_batch_size', 16)
            optimal_batch_size = min(max_batch_size, config_max)

            self.logger.debug(
                f"Calculated optimal batch size: {optimal_batch_size} "
                f"(memory: {total_bytes * optimal_batch_size / (1024**3):.1f}GB / "
                f"{available_memory / (1024**3):.1f}GB available)"
            )

            return optimal_batch_size

        except Exception as e:
            self.logger.warning(f"Failed to calculate optimal batch size: {e}")
            return 1

    def get_memory_usage(self) -> Dict[str, float]:
        """
        获取GPU内存使用情况

        Returns:
            内存使用信息
        """
        if not self.is_gpu_available():
            return {'used_gb': 0.0, 'total_gb': 0.0, 'free_gb': 0.0, 'utilization': 0.0}

        try:
            if self._backend_type == 'cuda':
                # CUDA 内存统计
                free_bytes, total_bytes = torch.cuda.mem_get_info(self._device)
                used_bytes = total_bytes - free_bytes

                return {
                    'used_gb': used_bytes / (1024**3),
                    'total_gb': total_bytes / (1024**3),
                    'free_gb': free_bytes / (1024**3),
                    'utilization': (used_bytes / total_bytes) * 100 if total_bytes > 0 else 0.0
                }
            elif self._backend_type == 'mps':
                # MPS 使用统一内存，返回系统内存统计
                vm = psutil.virtual_memory()
                return {
                    'used_gb': vm.used / (1024**3),
                    'total_gb': vm.total / (1024**3),
                    'free_gb': vm.available / (1024**3),
                    'utilization': vm.percent
                }
            else:
                return {'used_gb': 0.0, 'total_gb': 0.0, 'free_gb': 0.0, 'utilization': 0.0}

        except Exception as e:
            self.logger.error(f"Failed to get GPU memory usage: {e}")
            return {'used_gb': 0.0, 'total_gb': 0.0, 'free_gb': 0.0, 'utilization': 0.0}

    def optimize_for_video(self, video_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据视频配置优化GPU设置

        Args:
            video_config: 视频配置

        Returns:
            优化后的配置
        """
        if not self.is_gpu_available():
            return video_config

        optimized = video_config.copy()

        # 根据后端类型调整编码设置
        if self._backend_type == 'cuda' and self._gpu_info:
            # NVIDIA GPU - 使用硬件编码
            compute_capability = float(self._gpu_info.get('compute_capability', '0.0'))

            # 为较新的GPU启用更好的编码设置
            if compute_capability >= 7.0:  # Turing及更新架构
                optimized['codec'] = 'h264_nvenc'  # NVIDIA硬件编码
                optimized['preset'] = 'fast'
                optimized['crf'] = 20  # 更好的质量
            elif compute_capability >= 6.0:  # Pascal架构
                optimized['codec'] = 'h264_nvenc'
                optimized['preset'] = 'medium'
                optimized['crf'] = 23
            else:
                # 旧GPU使用软件编码
                optimized['codec'] = 'libx264'
                optimized['preset'] = 'medium'

        elif self._backend_type == 'mps' and self._gpu_info:
            # Apple Silicon - 使用 VideoToolbox 硬件编码
            # M 系列芯片都支持 H.264/HEVC 硬件编码
            compute_units = self._gpu_info.get('compute_units', 0)

            if compute_units >= 10:  # M3/M4 系列或更高
                optimized['codec'] = 'h264_videotoolbox'  # Apple硬件编码
                optimized['preset'] = 'fast'
                optimized['crf'] = 20
            elif compute_units >= 8:  # M1/M2 系列
                optimized['codec'] = 'h264_videotoolbox'
                optimized['preset'] = 'medium'
                optimized['crf'] = 23
            else:
                # 降级到软件编码
                optimized['codec'] = 'libx264'
                optimized['preset'] = 'medium'

        return optimized

    def create_tensor(self, data, dtype=None, requires_grad=False):
        """
        在GPU上创建张量

        Args:
            data: 张量数据
            dtype: 数据类型
            requires_grad: 是否需要梯度

        Returns:
            GPU张量
        """
        if not self.is_gpu_available():
            return torch.tensor(data, dtype=dtype, requires_grad=requires_grad)

        try:
            tensor = torch.tensor(data, dtype=dtype, requires_grad=requires_grad)
            return tensor.to(self._device)
        except Exception as e:
            self.logger.warning(f"Failed to create GPU tensor: {e}")
            return torch.tensor(data, dtype=dtype, requires_grad=requires_grad)

    def to_device(self, tensor: torch.Tensor) -> torch.Tensor:
        """
        将张量移动到GPU设备

        Args:
            tensor: 输入张量

        Returns:
            GPU上的张量
        """
        if not self.is_gpu_available():
            return tensor

        try:
            return tensor.to(self._device)
        except Exception as e:
            self.logger.warning(f"Failed to move tensor to GPU: {e}")
            return tensor

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """
        获取系统硬件信息

        Returns:
            系统信息字典
        """
        info = {
            'platform': platform.system(),
            'cpu_count': psutil.cpu_count(logical=True),
            'cpu_physical': psutil.cpu_count(logical=False),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'gpu_available': torch.cuda.is_available(),
            'gpu_count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
            'cuda_version': None,
            'pytorch_version': torch.__version__
        }

        # 获取CUDA版本
        try:
            if torch.cuda.is_available():
                info['cuda_version'] = torch.version.cuda
        except:
            pass

        # 获取GPU列表
        if info['gpu_available']:
            info['gpus'] = []
            for i in range(info['gpu_count']):
                try:
                    props = torch.cuda.get_device_properties(i)
                    info['gpus'].append({
                        'id': i,
                        'name': props.name,
                        'memory_gb': props.total_memory / (1024**3),
                        'compute_capability': f"{props.major}.{props.minor}"
                    })
                except Exception as e:
                    info['gpus'].append({'id': i, 'error': str(e)})

        return info

    def __repr__(self) -> str:
        """字符串表示"""
        if self.is_gpu_available():
            return f"GPUVideoAccelerator(device={self._device}, gpu={self._gpu_info['name'] if self._gpu_info else 'Unknown'})"
        else:
            return "GPUVideoAccelerator(device=cpu, gpu=unavailable)"
