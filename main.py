"""路由层：接收 HTTP 请求，调用业务函数，返回 HTTP 响应。"""

from fastapi import FastAPI, HTTPException, Response, status

import services
from schemas import Task, TaskRead, TaskUpdate

app = FastAPI(title="任务管理 API")


@app.get("/taskone")
def list_tasks_route() -> list[TaskRead]:
    return services.get_tasks()


@app.post("/taskone", status_code=status.HTTP_201_CREATED)
def create_task_route(task_data: Task) -> TaskRead:
    return services.create_task(task_data)


@app.get("/taskone/{task_id}")
def get_task_route(task_id: str) -> Task:
    task = services.get_task_by_id(task_id)
    if task is None:
        # HTTP 状态码属于路由层；业务层只表达“没有找到”。
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/taskone/{task_id}")
def update_task_route(task_id: str, task_data: TaskUpdate) -> Task:
    task = services.update_task(task_id, task_data)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/taskone/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_route(task_id: str) -> Response:
    if not services.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    # 204 表示删除成功，响应中不携带 JSON 内容。
    return Response(status_code=status.HTTP_204_NO_CONTENT)
