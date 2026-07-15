"""Gorev isleyicisi."""


class TaskWorker:

    def __init__(self, queue):
        self.queue = queue

    def run(self):
        results = []
        while not self.queue.empty():
            task = self.queue.pop()
            if task is None:
                continue
            try:
                results.append({"status": "ok", "result": task.execute()})
            except Exception as exc:
                results.append({"status": "error", "error": str(exc)})
        return results
