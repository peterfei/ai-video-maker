"""
任务队列管理
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime
from pathlib import Path
import json


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class VideoTask:
    """视频生成任务"""

    task_id: str
    script_path: Optional[str] = None
    script_text: Optional[str] = None
    materials_dir: Optional[str] = None
    output_path: Optional[str] = None
    config_override: Dict[str, Any] = field(default_factory=dict)

    # 任务状态
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # 结果
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'script_path': self.script_path,
            'script_text': self.script_text,
            'materials_dir': self.materials_dir,
            'output_path': self.output_path,
            'config_override': self.config_override,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'result': self.result
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoTask':
        """从字典创建"""
        task = cls(
            task_id=data['task_id'],
            script_path=data.get('script_path'),
            script_text=data.get('script_text'),
            materials_dir=data.get('materials_dir'),
            output_path=data.get('output_path'),
            config_override=data.get('config_override', {}),
            status=TaskStatus(data['status']),
            error_message=data.get('error_message'),
            result=data.get('result')
        )

        if data.get('created_at'):
            task.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('started_at'):
            task.started_at = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            task.completed_at = datetime.fromisoformat(data['completed_at'])

        return task


class TaskQueue:
    """任务队列类"""

    def __init__(self, persistence_file: Optional[str] = None):
        """
        初始化任务队列

        Args:
            persistence_file: 持久化文件路径
        """
        self.tasks: Dict[str, VideoTask] = {}
        self.persistence_file = Path(persistence_file) if persistence_file else None

        # 加载已保存的任务
        if self.persistence_file and self.persistence_file.exists():
            self.load_tasks()

    def add_task(self, task: VideoTask) -> None:
        """
        添加任务

        Args:
            task: VideoTask对象
        """
        self.tasks[task.task_id] = task
        self._save_tasks()

    def get_task(self, task_id: str) -> Optional[VideoTask]:
        """
        获取任务

        Args:
            task_id: 任务ID

        Returns:
            VideoTask对象或None
        """
        return self.tasks.get(task_id)

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        error_message: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            error_message: 错误信息
            result: 结果数据
        """
        task = self.tasks.get(task_id)
        if not task:
            return

        task.status = status

        if status == TaskStatus.PROCESSING and not task.started_at:
            task.started_at = datetime.now()

        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.now()

        if error_message:
            task.error_message = error_message

        if result:
            task.result = result

        self._save_tasks()

    def get_pending_tasks(self) -> List[VideoTask]:
        """
        获取待处理任务列表

        Returns:
            VideoTask列表
        """
        return [
            task for task in self.tasks.values()
            if task.status == TaskStatus.PENDING
        ]

    def get_tasks_by_status(self, status: TaskStatus) -> List[VideoTask]:
        """
        按状态获取任务

        Args:
            status: 任务状态

        Returns:
            VideoTask列表
        """
        return [
            task for task in self.tasks.values()
            if task.status == status
        ]

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        task = self.tasks.get(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return False

        self.update_task_status(task_id, TaskStatus.CANCELLED)
        return True

    def clear_completed_tasks(self) -> int:
        """
        清除已完成的任务

        Returns:
            清除的任务数量
        """
        completed_ids = [
            task_id for task_id, task in self.tasks.items()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]

        for task_id in completed_ids:
            del self.tasks[task_id]

        self._save_tasks()

        return len(completed_ids)

    def get_statistics(self) -> Dict[str, int]:
        """
        获取统计信息

        Returns:
            统计字典
        """
        stats = {
            'total': len(self.tasks),
            'pending': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0,
            'cancelled': 0
        }

        for task in self.tasks.values():
            stats[task.status.value] += 1

        return stats

    def _save_tasks(self) -> None:
        """保存任务到文件"""
        if not self.persistence_file:
            return

        self.persistence_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            task_id: task.to_dict()
            for task_id, task in self.tasks.items()
        }

        with open(self.persistence_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_tasks(self) -> None:
        """从文件加载任务"""
        if not self.persistence_file or not self.persistence_file.exists():
            return

        with open(self.persistence_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.tasks = {
            task_id: VideoTask.from_dict(task_data)
            for task_id, task_data in data.items()
        }

    def __len__(self) -> int:
        """返回任务总数"""
        return len(self.tasks)

    def __repr__(self) -> str:
        """字符串表示"""
        stats = self.get_statistics()
        return f"TaskQueue(total={stats['total']}, pending={stats['pending']}, completed={stats['completed']})"
