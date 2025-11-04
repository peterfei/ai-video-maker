"""
测试GPU加速器
"""

import pytest
from unittest.mock import Mock, patch
from video_engine.gpu_accelerator import GPUVideoAccelerator


class TestGPUVideoAccelerator:
    """测试GPU视频加速器"""

    @patch('video_engine.gpu_accelerator.torch.cuda.is_available')
    def test_cpu_fallback_when_cuda_unavailable(self, mock_cuda_available):
        """测试CUDA不可用时的CPU回退"""
        mock_cuda_available.return_value = False

        config = {
            'enabled': True,
            'device': 'auto',
            'memory_limit': 0.8,
            'min_gpu_memory': 2 * 1024**3
        }

        accelerator = GPUVideoAccelerator(config)

        assert not accelerator.is_gpu_available()
        assert str(accelerator.get_device()) == 'cpu'
        assert accelerator.get_gpu_info() is None

    @patch('video_engine.gpu_accelerator.torch.cuda.is_available')
    @patch('video_engine.gpu_accelerator.torch.cuda.device_count')
    def test_cpu_fallback_when_no_devices(self, mock_device_count, mock_cuda_available):
        """测试没有GPU设备时的CPU回退"""
        mock_cuda_available.return_value = True
        mock_device_count.return_value = 0

        config = {
            'enabled': True,
            'device': 'auto'
        }

        accelerator = GPUVideoAccelerator(config)

        assert not accelerator.is_gpu_available()
        assert str(accelerator.get_device()) == 'cpu'

    @patch('video_engine.gpu_accelerator.torch.cuda.is_available')
    @patch('video_engine.gpu_accelerator.torch.cuda.device_count')
    @patch('video_engine.gpu_accelerator.torch.cuda.get_device_properties')
    def test_insufficient_memory_fallback(self, mock_get_props, mock_device_count, mock_cuda_available):
        """测试GPU内存不足时的CPU回退"""
        mock_cuda_available.return_value = True
        mock_device_count.return_value = 1

        # 模拟GPU属性（只有1GB内存）
        mock_props = Mock()
        mock_props.total_memory = 1024**3  # 1GB
        mock_get_props.return_value = mock_props

        config = {
            'enabled': True,
            'device': 'auto',
            'min_gpu_memory': 2 * 1024**3  # 需要2GB
        }

        accelerator = GPUVideoAccelerator(config)

        assert not accelerator.is_gpu_available()
        assert str(accelerator.get_device()) == 'cpu'

    @patch('video_engine.gpu_accelerator.torch.cuda.is_available')
    @patch('video_engine.gpu_accelerator.torch.cuda.device_count')
    @patch('video_engine.gpu_accelerator.torch.cuda.get_device_properties')
    @patch('video_engine.gpu_accelerator.torch.cuda.mem_get_info')
    def test_successful_gpu_initialization(self, mock_mem_get_info, mock_get_props, mock_device_count, mock_cuda_available):
        """测试成功的GPU初始化"""
        mock_cuda_available.return_value = True
        mock_device_count.return_value = 1
        mock_mem_get_info.return_value = (4 * 1024**3, 8 * 1024**3)  # 4GB free, 8GB total

        # 模拟GPU属性
        mock_props = Mock()
        mock_props.name = "Tesla V100"
        mock_props.total_memory = 8 * 1024**3  # 8GB
        mock_props.major = 7
        mock_props.minor = 0
        mock_props.multi_processor_count = 80
        mock_props.max_threads_per_block = 1024
        mock_props.max_threads_per_multiprocessor = 2048
        mock_get_props.return_value = mock_props

        config = {
            'enabled': True,
            'device': 'auto',
            'min_gpu_memory': 2 * 1024**3
        }

        accelerator = GPUVideoAccelerator(config)

        assert accelerator.is_gpu_available()
        assert str(accelerator.get_device()) == 'cuda:0'

        gpu_info = accelerator.get_gpu_info()
        assert gpu_info is not None
        assert gpu_info['name'] == "Tesla V100"
        assert gpu_info['memory_total_gb'] == 8.0
        assert gpu_info['compute_capability'] == "7.0"

    def test_batch_size_calculation_cpu(self):
        """测试CPU模式下的批大小计算"""
        config = {
            'enabled': False,
            'max_batch_size': 16
        }

        accelerator = GPUVideoAccelerator(config)

        batch_size = accelerator.get_optimal_batch_size((1920, 1080), 30)
        assert batch_size == 1  # CPU模式下返回1

    @patch('video_engine.gpu_accelerator.torch.cuda.is_available')
    @patch('video_engine.gpu_accelerator.torch.cuda.device_count')
    @patch('video_engine.gpu_accelerator.torch.cuda.get_device_properties')
    @patch('video_engine.gpu_accelerator.torch.cuda.mem_get_info')
    def test_batch_size_calculation_gpu(self, mock_mem_get_info, mock_get_props, mock_device_count, mock_cuda_available):
        """测试GPU模式下的批大小计算"""
        mock_cuda_available.return_value = True
        mock_device_count.return_value = 1
        mock_mem_get_info.return_value = (6 * 1024**3, 8 * 1024**3)  # 6GB free, 8GB total

        mock_props = Mock()
        mock_props.total_memory = 8 * 1024**3
        mock_props.name = "GPU"
        mock_props.major = 7
        mock_props.minor = 0
        mock_props.multi_processor_count = 1
        mock_props.max_threads_per_block = 1
        mock_props.max_threads_per_multiprocessor = 1
        mock_get_props.return_value = mock_props

        config = {
            'enabled': True,
            'device': 'auto',
            'memory_limit': 0.8,
            'max_batch_size': 16
        }

        accelerator = GPUVideoAccelerator(config)
        batch_size = accelerator.get_optimal_batch_size((1920, 1080), 30)

        # 应该根据内存计算出合理的批大小
        assert batch_size > 0
        assert batch_size <= 16

    def test_memory_usage_cpu(self):
        """测试CPU模式下的内存使用"""
        config = {'enabled': False}
        accelerator = GPUVideoAccelerator(config)

        memory = accelerator.get_memory_usage()
        assert memory['used_gb'] == 0.0
        assert memory['total_gb'] == 0.0
        assert memory['free_gb'] == 0.0
        assert memory['utilization'] == 0.0

    @patch('video_engine.gpu_accelerator.torch.cuda.is_available')
    @patch('video_engine.gpu_accelerator.torch.cuda.mem_get_info')
    def test_memory_usage_gpu(self, mock_mem_get_info, mock_cuda_available):
        """测试GPU模式下的内存使用"""
        mock_cuda_available.return_value = True
        mock_mem_get_info.return_value = (2 * 1024**3, 8 * 1024**3)  # 2GB free, 8GB total

        config = {'enabled': True, 'device': 'cuda:0'}
        accelerator = GPUVideoAccelerator(config)

        memory = accelerator.get_memory_usage()
        assert memory['used_gb'] == 6.0  # 8GB - 2GB
        assert memory['total_gb'] == 8.0
        assert memory['free_gb'] == 2.0
        assert memory['utilization'] == 75.0

    def test_video_config_optimization_cpu(self):
        """测试CPU模式下的视频配置优化"""
        config = {'enabled': False}
        accelerator = GPUVideoAccelerator(config)

        video_config = {'codec': 'auto', 'preset': 'auto'}
        optimized = accelerator.optimize_for_video(video_config)

        # CPU模式下应该返回原始配置
        assert optimized == video_config

    @patch('video_engine.gpu_accelerator.torch.cuda.is_available')
    @patch('video_engine.gpu_accelerator.torch.cuda.device_count')
    @patch('video_engine.gpu_accelerator.torch.cuda.get_device_properties')
    def test_video_config_optimization_gpu(self, mock_get_props, mock_device_count, mock_cuda_available):
        """测试GPU模式下的视频配置优化"""
        mock_cuda_available.return_value = True
        mock_device_count.return_value = 1

        mock_props = Mock()
        mock_props.total_memory = 8 * 1024**3
        mock_props.name = "Tesla V100"
        mock_props.major = 7
        mock_props.minor = 0
        mock_get_props.return_value = mock_props

        config = {'enabled': True, 'device': 'auto'}
        accelerator = GPUVideoAccelerator(config)

        video_config = {'codec': 'auto', 'preset': 'auto'}
        optimized = accelerator.optimize_for_video(video_config)

        # 应该为新GPU优化配置
        assert optimized['codec'] == 'h264_nvenc'
        assert optimized['preset'] == 'fast'

    @staticmethod
    def test_system_info():
        """测试系统信息获取"""
        info = GPUVideoAccelerator.get_system_info()

        assert 'platform' in info
        assert 'cpu_count' in info
        assert 'memory_total_gb' in info
        assert 'gpu_available' in info
        assert 'gpu_count' in info
        assert 'pytorch_version' in info

        if info['gpu_available']:
            assert 'gpus' in info
            assert len(info['gpus']) == info['gpu_count']


if __name__ == "__main__":
    pytest.main([__file__])
