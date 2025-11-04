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

    提供GPU检测、内存管理和CUDA加速支持，
    支持自动检测硬件配置并优雅降级到CPU处理。
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

        # 初始化GPU检测
        self._detect_gpu()

    def _detect_gpu(self) -> None:
        """检测并初始化GPU"""
        try:
            # 检查PyTorch CUDA可用性
            if not torch.cuda.is_available():
                self.logger.warning("CUDA not available, falling back to CPU")
                self._device = torch.device('cpu')
                self._is_available = False
                return

            # 获取GPU数量
            gpu_count = torch.cuda.device_count()
            if gpu_count == 0:
                self.logger.warning("No CUDA devices found, falling back to CPU")
                self._device = torch.device('cpu')
                self._is_available = False
                return

            # 选择GPU设备
            device_id = self._select_gpu_device(gpu_count)
            if device_id is None:
                self.logger.warning("No suitable GPU device found, falling back to CPU")
                self._device = torch.device('cpu')
                self._is_available = False
                return

            # 验证GPU内存
            if not self._validate_gpu_memory(device_id):
                self.logger.warning("Insufficient GPU memory, falling back to CPU")
                self._device = torch.device('cpu')
                self._is_available = False
                return

            # 设置设备
            self._device = torch.device(f'cuda:{device_id}')
            self._is_available = True

            # 获取GPU信息
            self._gpu_info = self._get_gpu_info(device_id)

            self.logger.info(f"GPU acceleration enabled: {self._gpu_info['name']} "
                           f"({self._gpu_info['memory_total_gb']:.1f}GB)")

        except Exception as e:
            self.logger.error(f"GPU detection failed: {e}")
            self._device = torch.device('cpu')
            self._is_available = False

    def _select_gpu_device(self, gpu_count: int) -> Optional[int]:
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

    def _validate_gpu_memory(self, device_id: int) -> bool:
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

    def _get_gpu_info(self, device_id: int) -> Dict[str, Any]:
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
        """检查GPU是否可用"""
        return self._is_available and self._device is not None and self._device.type == 'cuda'

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
            free_bytes, total_bytes = torch.cuda.mem_get_info(self._device)
            used_bytes = total_bytes - free_bytes

            return {
                'used_gb': used_bytes / (1024**3),
                'total_gb': total_bytes / (1024**3),
                'free_gb': free_bytes / (1024**3),
                'utilization': (used_bytes / total_bytes) * 100 if total_bytes > 0 else 0.0
            }

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

        # 根据GPU能力调整编码设置
        if self._gpu_info:
            compute_capability = float(self._gpu_info['compute_capability'])

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
