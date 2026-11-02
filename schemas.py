"""模型层：定义数据的形状和校验规则，不读写任务数据。"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

TaskStatus = Literal["pending", "completed", "yes", "none"]


class Task(BaseModel):
    """完整任务；创建时三个字段都必须提供，保持原来的规则。"""

    model_config = ConfigDict(extra="forbid")

    title: str
    description: str
    status: TaskStatus


class TaskRead(Task):
    """列表和创建响应包含 ID，方便后续查询、修改和删除。"""

    id: str


class TaskUpdate(BaseModel):
    """更新时允许省略字段；省略表示保留原值。"""

    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None

    @field_validator("title", "description", "status")
    @classmethod
    def reject_explicit_null(cls, value: str | None) -> str:
        # 默认值不会触发此校验，所以省略字段可以；显式传 null 不可以。
        # 完整 Task 的字段不接受 None，更新时也遵守同一规则。
        if value is None:
            raise ValueError("字段可以省略，但不能为 null")
        return value
