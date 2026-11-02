"""通过真实的请求校验和路由调用，验证任务管理行为。"""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import services
from main import app
from schemas import Task, TaskUpdate


class TaskAPITests(unittest.TestCase):
    def setUp(self):
        # 每个测试使用空存储，结束后恢复，避免测试之间相互影响。
        storage = patch.dict(services.tasks_db, {}, clear=True)
        storage.start()
        self.addCleanup(storage.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.payload = {
            "title": "学习分层",
            "description": "保留未修改字段",
            "status": "pending",
        }

    def test_crud_lifecycle(self):
        self.assertEqual(self.client.get("/taskone").json(), [])
        response = self.client.post("/taskone", json=self.payload)
        self.assertEqual(response.status_code, 201)
        created = response.json()
        task_id = created["id"]
        self.assertIsInstance(task_id, str)
        path = f"/taskone/{task_id}"
        self.assertEqual(self.client.get(path).json(), self.payload)
        self.assertEqual(self.client.get("/taskone").json(), [created])

        response = self.client.patch(path, json={"status": "completed"})
        expected = {**self.payload, "status": "completed"}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        self.assertEqual(self.client.get(path).json(), expected)
        self.assertEqual(self.client.patch(path, json={}).json(), expected)

        response = self.client.delete(path)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.get("/taskone").json(), [])

    def test_missing_tasks_return_404(self):
        for method, kwargs in [
            ("GET", {}),
            ("PATCH", {"json": {"status": "completed"}}),
            ("DELETE", {}),
        ]:
            with self.subTest(method=method):
                response = self.client.request(method, "/taskone/missing", **kwargs)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json(), {"detail": "Task not found"})

    def test_invalid_updates_do_not_change_saved_task(self):
        created = self.client.post("/taskone", json=self.payload).json()
        path = f"/taskone/{created['id']}"
        for update in [
            {"status": "unknown"},
            {"title": None},
            {"description": None},
            {"status": None},
            {"title": 123},
            {"statsu": "completed"},
        ]:
            with self.subTest(update=update):
                self.assertEqual(self.client.patch(path, json=update).status_code, 422)
                self.assertEqual(self.client.get(path).json(), self.payload)

    def test_creation_requires_all_fields_and_valid_status(self):
        for payload in [{}, {"title": "缺少字段"}, {**self.payload, "status": "bad"}]:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post("/taskone", json=payload).status_code, 422)
        self.assertEqual(self.client.get("/taskone").json(), [])

    def test_creating_tasks_does_not_overwrite_existing_task(self):
        first = self.client.post("/taskone", json=self.payload).json()
        second = self.client.post("/taskone", json=self.payload).json()
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(len(self.client.get("/taskone").json()), 2)

    def test_services_can_be_called_without_http(self):
        created = services.create_task(Task(**self.payload))
        fetched = services.get_task_by_id(created.id)
        fetched.title = "只修改返回的模型"
        self.assertEqual(services.get_task_by_id(created.id).title, self.payload["title"])
        updated = services.update_task(created.id, TaskUpdate(status="completed"))
        self.assertEqual(updated.status, "completed")
        self.assertTrue(services.delete_task(created.id))
        self.assertIsNone(services.get_task_by_id(created.id))
        self.assertIsNone(services.update_task(created.id, TaskUpdate()))
        self.assertFalse(services.delete_task(created.id))


if __name__ == "__main__":
    unittest.main()
