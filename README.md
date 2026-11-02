# 任务 API：分层学习示例

本项目将原来写在路由中的字典操作抽成独立业务函数，并补全增删改查。
适合 Python 3.10+、Pydantic 2。

## 先看每个文件负责什么

| 文件 | 职责 | 例子 |
| --- | --- | --- |
| `schemas.py` | 定义输入、输出的数据结构和校验规则 | 状态必须在允许值内；更新时可省略字段 |
| `services.py` | 操作任务数据，执行增删改查 | 找任务、合并字段、保存、删除 |
| `main.py` | 定义 URL、HTTP 方法和状态码，调用业务函数 | 将业务函数返回的 `None` 转换成 404 |
| `tasks.http` | 手工请求示例 | 创建任务后，用返回的 ID 查询和修改 |
| `tests/test_tasks.py` | 自动验证接口行为和业务函数 | 部分更新、非法输入、404、删除 |

这里采用三个模块划分职责。模型是路由和业务共享的数据约定，不是必须逐层调用的第三站。
当前数据存取很简单，先把内存字典放在业务模块中；以后接数据库时，可以再抽出 repository 数据访问层。

```text
客户端发送 JSON
    ↓
FastAPI 按 schemas.py 的模型校验输入
    ↓
main.py 中的路由函数
    ↓
services.py 中的业务函数 → tasks_db
    ↓
路由将结果返回为 HTTP 响应
```

依赖方向是 `main → services → schemas`，同时 `main` 也引用 `schemas`。
业务层不导入 `main`，也不使用 `HTTPException`，所以能在脚本或测试中直接调用。

## 启动与验证

已有 `zgzStudy` Conda 环境可使用：

```powershell
conda activate zgzStudy
python -m uvicorn main:app --reload
```

其他 Python 环境先运行 `python -m pip install -r requirements.txt`。
服务启动后访问 http://127.0.0.1:8000/docs ，或按顺序运行 `tasks.http`。

运行自动测试：

```powershell
python -m unittest discover -s tests -v
```

## 接口约定

| 方法 | 路径 | 成功结果 |
| --- | --- | --- |
| GET | `/taskone` | 200，任务列表，每项带 `id` |
| POST | `/taskone` | 201，创建后的任务，带 `id` |
| GET | `/taskone/{task_id}` | 200，任务的三个字段 |
| PATCH | `/taskone/{task_id}` | 200，更新后的三个字段 |
| DELETE | `/taskone/{task_id}` | 204，无响应体 |

保留原有查询、更新路径和成功响应字段。任务 ID 是字符串；初始任务为 `zw`，新任务使用 UUID。
查询、更新、删除不存在的任务均返回 404；请求字段不合法返回 422。
创建仍要求 `title`、`description`、`status` 三个字段，状态保留 `pending`、`completed`、`yes`、`none`。
新增了未知字段校验，拼错字段名会返回 422。标题仍遵循原来的字符串规则，允许空字符串。

## 按“修改状态”追踪一次调用

请求：`PATCH /taskone/zw`，内容为 `{"status": "completed"}`。

1. `schemas.TaskUpdate` 校验请求。字段可以不传，但显式传 `null` 会被拒绝。
2. `main.update_task_route` 收到模型对象，调用 `services.update_task`。
3. 业务函数通过 `get_task_by_id` 查找任务，不存在则返回 `None`。
4. `model_dump(exclude_unset=True)` 只提取本次提交的 `status`。
5. 旧数据与更新数据合并，重新构建完整 `Task` 校验后写回字典。
6. 路由返回更新结果；如果拿到 `None`，则抛出 HTTP 404。

`Task` 表示完整任务，`TaskUpdate` 表示本次修改，`TaskRead` 在完整任务上增加 `id`。
PATCH 传 `{}` 时不改变数据；省略字段和传 `null` 是两件不同的事。
部分更新的关键参数可对照 [FastAPI 官方说明](https://fastapi.tiangolo.com/tutorial/body-updates/)；
字段校验可对照 [Pydantic 官方说明](https://docs.pydantic.dev/latest/concepts/validators/)。

## 建议阅读顺序

先看 `schemas.py` 的三个模型，再看 `services.py` 中最简单的查询函数，
然后看 `main.py` 如何调用它并处理 404，最后沿着上面的流程阅读更新函数。
可以尝试只修改标题，再查询任务，观察描述和状态是否保留。

数据保存在单个进程的内存中，重启后恢复初始任务 `zw`，新建和修改的数据不会持久保存。
本示例适合单进程学习；数据库持久化、多进程共享和并发更新控制属于后续扩展。


