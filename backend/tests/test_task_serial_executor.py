import importlib.util
import pathlib
import threading
import time
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "app" / "services" / "task_serial_executor.py"
spec = importlib.util.spec_from_file_location("task_serial_executor", MODULE_PATH)
if spec is None or spec.loader is None:
    raise ImportError("task_serial_executor module spec not found")
task_serial_executor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(task_serial_executor)
SerialTaskExecutor = task_serial_executor.SerialTaskExecutor


class TestTaskSerialExecutor(unittest.TestCase):
    """执行器已经从「全局串行锁」改成线程池，并发上限由 max_workers 决定。

    `SerialTaskExecutor` 这个旧名字仍然作为 `ConcurrentTaskExecutor` 的别名导出，
    所以这里验证的是「并发数受 max_workers 约束」这条契约。
    """

    def _peak_active(self, max_workers, tasks=2):
        executor = SerialTaskExecutor(max_workers=max_workers)
        state_lock = threading.Lock()
        state = {"active": 0, "peak_active": 0}

        def critical_work():
            with state_lock:
                state["active"] += 1
                state["peak_active"] = max(state["peak_active"], state["active"])
            time.sleep(0.05)
            with state_lock:
                state["active"] -= 1

        try:
            threads = [
                threading.Thread(target=lambda: executor.run(critical_work))
                for _ in range(tasks)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        finally:
            executor.shutdown(wait=True)
        return state["peak_active"]

    def test_single_worker_still_runs_tasks_one_by_one(self):
        self.assertEqual(self._peak_active(max_workers=1), 1)

    def test_workers_allow_tasks_to_overlap(self):
        self.assertEqual(self._peak_active(max_workers=2), 2)


if __name__ == "__main__":
    unittest.main()
