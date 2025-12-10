"""
Background Task Manager for long-running data collection tasks
"""
import uuid
import threading
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from sqlalchemy import text

from .database import get_db
from .logger import get_logger

logger = get_logger(__name__)


class TaskManager:
    """
    Manages background tasks with database-backed state persistence
    """

    # Task status constants
    STATUS_PENDING = 'pending'
    STATUS_RUNNING = 'running'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'

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
        self._initialized = True
        self._running_tasks: Dict[str, threading.Thread] = {}
        logger.info("TaskManager initialized")

    def create_task(self, task_type: str, total_items: int = 0) -> str:
        """
        Create a new task and return its ID

        Args:
            task_type: Type of task (e.g., 'kr_stock_collection', 'us_stock_collection')
            total_items: Total number of items to process

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())[:8]
        db = get_db()

        with db.engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO background_tasks
                (id, task_type, status, total_items, completed_items, created_at, updated_at)
                VALUES (:id, :task_type, :status, :total_items, 0, :now, :now)
            """), {
                'id': task_id,
                'task_type': task_type,
                'status': self.STATUS_PENDING,
                'total_items': total_items,
                'now': datetime.now().isoformat()
            })

        logger.info(f"Created task {task_id} of type {task_type}")
        return task_id

    def update_task(self, task_id: str,
                    status: str = None,
                    completed_items: int = None,
                    current_item: str = None,
                    result: str = None,
                    error_message: str = None) -> None:
        """
        Update task status

        Args:
            task_id: Task ID
            status: New status
            completed_items: Number of completed items
            current_item: Currently processing item
            result: Result message
            error_message: Error message if failed
        """
        db = get_db()

        updates = ["updated_at = :now"]
        params = {'id': task_id, 'now': datetime.now().isoformat()}

        if status is not None:
            updates.append("status = :status")
            params['status'] = status

        if completed_items is not None:
            updates.append("completed_items = :completed_items")
            params['completed_items'] = completed_items

        if current_item is not None:
            updates.append("current_item = :current_item")
            params['current_item'] = current_item

        if result is not None:
            updates.append("result = :result")
            params['result'] = result

        if error_message is not None:
            updates.append("error_message = :error_message")
            params['error_message'] = error_message

        query = f"UPDATE background_tasks SET {', '.join(updates)} WHERE id = :id"

        with db.engine.begin() as conn:
            conn.execute(text(query), params)

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task status

        Args:
            task_id: Task ID

        Returns:
            Task info dictionary or None
        """
        db = get_db()

        result = db.execute_query(
            "SELECT * FROM background_tasks WHERE id = :id",
            {'id': task_id}
        )

        if result.empty:
            return None

        row = result.iloc[0]
        import pandas as pd

        # Helper to safely get value (handle NaN)
        def safe_get(val):
            if pd.isna(val):
                return None
            return val

        total = int(row['total_items']) if pd.notna(row['total_items']) else 0
        completed = int(row['completed_items']) if pd.notna(row['completed_items']) else 0

        return {
            'id': row['id'],
            'task_type': row['task_type'],
            'status': row['status'],
            'total_items': total,
            'completed_items': completed,
            'current_item': safe_get(row.get('current_item')),
            'result': safe_get(row.get('result')),
            'error_message': safe_get(row.get('error_message')),
            'created_at': str(row['created_at']) if pd.notna(row['created_at']) else None,
            'updated_at': str(row['updated_at']) if pd.notna(row['updated_at']) else None,
            'progress_percent': round(completed / total * 100, 1) if total > 0 else 0
        }

    def get_active_tasks(self, task_type: str = None) -> list:
        """
        Get all active (running or pending) tasks

        Args:
            task_type: Filter by task type

        Returns:
            List of task info dictionaries
        """
        db = get_db()

        query = """
            SELECT * FROM background_tasks
            WHERE status IN ('pending', 'running')
        """
        params = {}

        if task_type:
            query += " AND task_type = :task_type"
            params['task_type'] = task_type

        query += " ORDER BY created_at DESC"

        result = db.execute_query(query, params)

        import pandas as pd

        def safe_get(val):
            if pd.isna(val):
                return None
            return val

        tasks = []
        for _, row in result.iterrows():
            total = int(row['total_items']) if pd.notna(row['total_items']) else 0
            completed = int(row['completed_items']) if pd.notna(row['completed_items']) else 0
            tasks.append({
                'id': row['id'],
                'task_type': row['task_type'],
                'status': row['status'],
                'total_items': total,
                'completed_items': completed,
                'current_item': safe_get(row.get('current_item')),
                'progress_percent': round(completed / total * 100, 1) if total > 0 else 0
            })

        return tasks

    def run_in_background(self, task_id: str, func: Callable, *args, **kwargs) -> None:
        """
        Run a function in background thread

        Args:
            task_id: Task ID to track
            func: Function to run
            *args, **kwargs: Arguments to pass to function
        """
        def wrapper():
            try:
                self.update_task(task_id, status=self.STATUS_RUNNING)
                result = func(task_id, *args, **kwargs)
                self.update_task(task_id, status=self.STATUS_COMPLETED, result=str(result) if result else None)
            except Exception as e:
                logger.error(f"Task {task_id} failed: {str(e)}")
                self.update_task(task_id, status=self.STATUS_FAILED, error_message=str(e))
            finally:
                if task_id in self._running_tasks:
                    del self._running_tasks[task_id]

        thread = threading.Thread(target=wrapper, daemon=True)
        self._running_tasks[task_id] = thread
        thread.start()
        logger.info(f"Started background task {task_id}")

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task (marks as cancelled, thread may still run)

        Args:
            task_id: Task ID

        Returns:
            True if task was cancelled
        """
        task = self.get_task(task_id)
        if task and task['status'] in [self.STATUS_PENDING, self.STATUS_RUNNING]:
            self.update_task(task_id, status=self.STATUS_CANCELLED)
            return True
        return False

    def cleanup_old_tasks(self, days: int = 7) -> int:
        """
        Remove old completed/failed tasks

        Args:
            days: Remove tasks older than this many days

        Returns:
            Number of tasks removed
        """
        db = get_db()

        with db.engine.begin() as conn:
            result = conn.execute(text("""
                DELETE FROM background_tasks
                WHERE status IN ('completed', 'failed', 'cancelled')
                AND created_at < datetime('now', :days)
            """), {'days': f'-{days} days'})

            return result.rowcount


# Singleton instance
_task_manager = None


def get_task_manager() -> TaskManager:
    """Get global TaskManager instance"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager
