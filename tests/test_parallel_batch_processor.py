"""
测试并行批处理器
"""

import pytest
import time
from unittest.mock import Mock, patch
from tasks.parallel_batch_processor import ParallelBatchProcessor, ResourceManager
from tasks.task_queue import TaskQueue, VideoTask


class TestResourceManager:
    """测试资源管理器"""

    def test_calculate_optimal_workers_auto(self):
        """测试自动计算最优工作线程数"""
        config = {
            'performance': {
                'threading': {
                    'max_workers': 'auto'
                }
            }
        }

        manager = ResourceManager(config)
        workers = manager.calculate_optimal_workers()

        # 应该返回正整数
        assert workers > 0
        assert isinstance(workers, int)

    def test_calculate_optimal_workers_fixed(self):
        """测试固定工作线程数"""
        config = {
            'performance': {
                'threading': {
                    'max_workers': 4
                }
            }
        }

        manager = ResourceManager(config)
        workers = manager.calculate_optimal_workers()

        assert workers == 4

    def test_resource_limits(self):
        """测试资源限制"""
        config = {
            'performance': {
                'threading': {
                    'max_concurrent_tasks': 2,
                    'worker_memory_limit': 1024
                }
            }
        }

        manager = ResourceManager(config)

        # 应该允许启动第一个任务
        assert manager.can_start_task(512)

        # 应该允许启动第二个任务
        assert manager.can_start_task(512)

        # 不应该允许启动第三个任务（超过并发限制）
        assert not manager.can_start_task(512)

        # 完成任务后应该可以启动新任务
        manager.task_completed(512)
        assert manager.can_start_task(512)


class TestParallelBatchProcessor:
    """测试并行批处理器"""

    @patch('tasks.parallel_batch_processor.psutil')
    def test_initialization(self, mock_psutil):
        """测试初始化"""
        # 模拟系统信息
        mock_psutil.cpu_count.return_value = 8
        mock_psutil.virtual_memory.return_value.total = 16 * 1024**3  # 16GB

        config = {
            'performance': {
                'threading': {
                    'max_workers': 4,
                    'task_timeout': 1800
                }
            },
            'log_level': 'INFO'
        }

        task_queue = Mock(spec=TaskQueue)
        processor = ParallelBatchProcessor(task_queue, config)

        assert processor.max_workers == 4
        assert processor.task_timeout == 1800
        assert processor.executor is not None

        processor.shutdown()

    def test_process_batch_empty(self):
        """测试处理空批次"""
        config = {
            'performance': {
                'threading': {
                    'max_workers': 2
                }
            },
            'log_level': 'INFO'
        }

        task_queue = Mock(spec=TaskQueue)
        task_queue.get_pending_tasks.return_value = []

        processor = ParallelBatchProcessor(task_queue, config)
        result = processor.process_batch()

        assert result.total_tasks == 0
        assert result.successful_tasks == 0
        assert result.failed_tasks == 0

        processor.shutdown()

    def test_process_batch_with_mock_tasks(self):
        """测试处理模拟任务"""
        def mock_video_generator(task):
            time.sleep(0.1)  # 模拟处理时间
            return {"output_path": f"output/{task.task_id}.mp4"}

        config = {
            'performance': {
                'threading': {
                    'max_workers': 2,
                    'task_timeout': 10
                }
            },
            'log_level': 'WARNING'  # 减少日志输出
        }

        # 创建模拟任务
        tasks = [
            VideoTask(task_id=f"task_{i}", script_text=f"Test script {i}")
            for i in range(3)
        ]

        task_queue = Mock(spec=TaskQueue)
        task_queue.get_pending_tasks.return_value = tasks

        processor = ParallelBatchProcessor(task_queue, config, mock_video_generator)
        result = processor.process_batch(tasks)

        assert result.total_tasks == 3
        assert result.successful_tasks == 3
        assert result.failed_tasks == 0
        assert result.average_task_duration > 0
        assert result.throughput > 0

        processor.shutdown()

    def test_performance_stats(self):
        """测试性能统计"""
        config = {
            'performance': {
                'threading': {
                    'max_workers': 2
                }
            },
            'log_level': 'INFO'
        }

        task_queue = Mock(spec=TaskQueue)
        processor = ParallelBatchProcessor(task_queue, config)

        stats = processor.get_performance_stats()

        assert 'thread_pool' in stats
        assert 'resource_usage' in stats
        assert 'processing_stats' in stats
        assert 'config' in stats

        processor.shutdown()


if __name__ == "__main__":
    pytest.main([__file__])
