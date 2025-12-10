"""
Background Task Manager
백그라운드 작업 관리자

비동기 작업 실행 및 진행 상황 추적을 담당합니다.
"""

import uuid
import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field
from queue import Queue
import traceback


class TaskStatus(Enum):
    """작업 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskProgress:
    """작업 진행 상황"""
    current: int = 0
    total: int = 100
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0
        return min(100, (self.current / self.total) * 100)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'current': self.current,
            'total': self.total,
            'percentage': round(self.percentage, 1),
            'message': self.message,
            'details': self.details
        }


@dataclass
class Task:
    """비동기 작업"""
    id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    progress: TaskProgress = field(default_factory=TaskProgress)
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    logs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status.value,
            'progress': self.progress.to_dict(),
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'logs': self.logs[-50:],  # 최근 50개 로그만
            'duration': self._get_duration()
        }

    def _get_duration(self) -> Optional[float]:
        """작업 소요 시간 (초)"""
        if not self.started_at:
            return None
        end = self.completed_at or datetime.now()
        return (end - self.started_at).total_seconds()


class TaskManager:
    """
    백그라운드 작업 관리자

    스레드 기반으로 비동기 작업을 실행하고 진행 상황을 추적합니다.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._tasks: Dict[str, Task] = {}
        self._threads: Dict[str, threading.Thread] = {}
        self._cancel_flags: Dict[str, threading.Event] = {}
        self._progress_callbacks: Dict[str, List[Callable]] = {}
        self._max_tasks = 100  # 최대 저장 작업 수
        self._initialized = True

    def create_task(self, name: str) -> Task:
        """새 작업 생성"""
        task_id = str(uuid.uuid4())[:8]
        task = Task(id=task_id, name=name)
        self._tasks[task_id] = task
        self._cancel_flags[task_id] = threading.Event()

        # 오래된 작업 정리
        self._cleanup_old_tasks()

        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """작업 조회"""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[Task]:
        """모든 작업 목록"""
        return sorted(
            self._tasks.values(),
            key=lambda t: t.created_at,
            reverse=True
        )

    def run_task(
        self,
        task: Task,
        func: Callable,
        *args,
        **kwargs
    ) -> None:
        """
        백그라운드에서 작업 실행

        Args:
            task: 작업 객체
            func: 실행할 함수 (첫 번째 인자로 TaskContext 받음)
            *args, **kwargs: 함수에 전달할 인자
        """
        def wrapper():
            ctx = TaskContext(task, self, self._cancel_flags[task.id])
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            self._emit_progress(task)

            try:
                result = func(ctx, *args, **kwargs)
                if task.status == TaskStatus.RUNNING:  # 취소되지 않은 경우
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.progress.current = task.progress.total
                    task.progress.message = "완료"
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.logs.append(f"ERROR: {traceback.format_exc()}")
            finally:
                task.completed_at = datetime.now()
                self._emit_progress(task)

        thread = threading.Thread(target=wrapper, daemon=True)
        self._threads[task.id] = thread
        thread.start()

    def cancel_task(self, task_id: str) -> bool:
        """작업 취소"""
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            return False

        # 취소 플래그 설정
        cancel_flag = self._cancel_flags.get(task_id)
        if cancel_flag:
            cancel_flag.set()

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        task.progress.message = "취소됨"
        self._emit_progress(task)

        return True

    def add_progress_callback(
        self,
        task_id: str,
        callback: Callable[[Task], None]
    ) -> None:
        """진행 상황 콜백 등록"""
        if task_id not in self._progress_callbacks:
            self._progress_callbacks[task_id] = []
        self._progress_callbacks[task_id].append(callback)

    def _emit_progress(self, task: Task) -> None:
        """진행 상황 이벤트 발생"""
        callbacks = self._progress_callbacks.get(task.id, [])
        for callback in callbacks:
            try:
                callback(task)
            except Exception:
                pass

    def _cleanup_old_tasks(self) -> None:
        """오래된 완료 작업 정리"""
        if len(self._tasks) <= self._max_tasks:
            return

        completed_tasks = [
            t for t in self._tasks.values()
            if t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]
        completed_tasks.sort(key=lambda t: t.completed_at or t.created_at)

        # 가장 오래된 것부터 삭제
        to_remove = len(self._tasks) - self._max_tasks
        for task in completed_tasks[:to_remove]:
            del self._tasks[task.id]
            self._cancel_flags.pop(task.id, None)
            self._threads.pop(task.id, None)
            self._progress_callbacks.pop(task.id, None)


class TaskContext:
    """
    작업 컨텍스트

    작업 함수 내에서 진행 상황을 업데이트하는 데 사용됩니다.
    """

    def __init__(
        self,
        task: Task,
        manager: TaskManager,
        cancel_flag: threading.Event
    ):
        self._task = task
        self._manager = manager
        self._cancel_flag = cancel_flag

    @property
    def task_id(self) -> str:
        return self._task.id

    @property
    def is_cancelled(self) -> bool:
        """취소 여부 확인"""
        return self._cancel_flag.is_set()

    def check_cancelled(self) -> None:
        """취소되었으면 예외 발생"""
        if self.is_cancelled:
            raise TaskCancelledException("작업이 취소되었습니다")

    def update_progress(
        self,
        current: Optional[int] = None,
        total: Optional[int] = None,
        message: Optional[str] = None,
        **details
    ) -> None:
        """진행 상황 업데이트"""
        if current is not None:
            self._task.progress.current = current
        if total is not None:
            self._task.progress.total = total
        if message is not None:
            self._task.progress.message = message
        if details:
            self._task.progress.details.update(details)

        self._manager._emit_progress(self._task)

    def log(self, message: str) -> None:
        """로그 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._task.logs.append(f"[{timestamp}] {message}")
        self._manager._emit_progress(self._task)

    def set_result(self, result: Any) -> None:
        """결과 설정"""
        self._task.result = result


class TaskCancelledException(Exception):
    """작업 취소 예외"""
    pass


# 싱글톤 인스턴스
task_manager = TaskManager()
