"""业务层：完成任务的增删改查，不依赖 FastAPI 或 HTTP 状态码。"""

from uuid import uuid4

from schemas import Task, TaskRead, TaskUpdate

# 学习阶段用字典模拟数据库。重启后恢复下面的初始数据。
# 内存数据仅属于当前进程，不适合多个 worker 共享或持久化存储。
tasks_db: dict[str, dict[str, str]] = {
    "zw": {
        "title": "学习FastAPI",
        "description": "完成POST接口",
        "status": "pending",
    }
}


def get_tasks() -> list[TaskRead]:
    """列出全部任务；字典的键作为响应中的 id。"""
    return [TaskRead(id=task_id, **data) for task_id, data in tasks_db.items()]


def get_task_by_id(task_id: str) -> Task | None:
    """找不到时返回 None；返回模型，避免调用方直接修改存储字典。"""
    data = tasks_db.get(task_id)
    if data is None:
        return None
    return Task(**data)


def create_task(task_data: Task) -> TaskRead:
    """由服务端生成字符串 ID，保存任务并返回带 ID 的结果。"""
    task_id = uuid4().hex
    while task_id in tasks_db:
        task_id = uuid4().hex
    tasks_db[task_id] = task_data.model_dump(mode="json")
    return TaskRead(id=task_id, **tasks_db[task_id])


def update_task(task_id: str, updates: TaskUpdate) -> Task | None:
    """只覆盖显式提交的字段；空对象表示不修改。"""
    stored_task = get_task_by_id(task_id)
    if stored_task is None:
        return None

    # exclude_unset=True 很关键：不能拿未提交字段的默认 None 覆盖旧值。
    update_data = updates.model_dump(exclude_unset=True)
    merged_data = {**stored_task.model_dump(), **update_data}
    # 合并后重新校验完整任务，成功后才保存。
    updated_task = Task(**merged_data)
    tasks_db[task_id] = updated_task.model_dump(mode="json")
    return updated_task


def delete_task(task_id: str) -> bool:
    """删除成功返回 True；任务不存在返回 False。"""
    return tasks_db.pop(task_id, None) is not None
