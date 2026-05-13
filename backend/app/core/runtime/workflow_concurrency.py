"""工作流并发控制器，负责限制同一时刻可启动的工作流数量"""

from threading import Lock

from app.config import settings


class WorkflowConcurrencyController:
    """进程内工作流并发控制器，基于当前配置维护活动执行槽位"""

    def __init__(self) -> None:
        """初始化并发控制器，并准备活动工作流集合"""

        self._lock = Lock()
        self._active_workflow_ids: set[int] = set()

    def reserve_slot(self, workflow_id: int) -> bool:
        """尝试为工作流预留执行槽位，超出并发上限时返回失败"""

        with self._lock:
            if workflow_id in self._active_workflow_ids:
                return False

            if len(self._active_workflow_ids) >= settings.max_concurrent_workflows:
                return False

            self._active_workflow_ids.add(workflow_id)
            return True

    def release_slot(self, workflow_id: int) -> None:
        """释放指定工作流占用的执行槽位"""

        with self._lock:
            self._active_workflow_ids.discard(workflow_id)

    def get_active_workflow_count(self) -> int:
        """返回当前正在占用执行槽位的工作流数量"""

        with self._lock:
            return len(self._active_workflow_ids)

    def build_runtime_snapshot(self) -> dict[str, int | bool]:
        """返回当前并发配置和活动槽位快照，供接口层展示"""

        active_workflow_count = self.get_active_workflow_count()
        max_concurrent_workflows = settings.max_concurrent_workflows
        remaining_slots = max(max_concurrent_workflows - active_workflow_count, 0)
        return {
            "max_concurrent_workflows": max_concurrent_workflows,
            "active_workflow_count": active_workflow_count,
            "remaining_slots": remaining_slots,
            "is_limit_reached": remaining_slots == 0,
        }


workflow_concurrency_controller = WorkflowConcurrencyController()
