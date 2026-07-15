"""
Merkezi Gorev Yoneticisi.

NOT: Projede UC farkli TaskManager vardi:
  1) orchestration/task_manager.py -> threading.Thread worker havuzu, Queue,
     register(name, handler) deseni
  2) core/tasks/manager.py (eski) -> handler dict + TaskQueue/TaskExecutor
  3) core/queue/manager.py -> bu dosya, TaskQueue + TaskWorker (Task.execute())

Bu ucuncusunu "kanonik" sectim cunku Task nesnelerinin kendi execute()
mantigini tasimasi (orn. MatchAnalysisTask), sabit bir handler sozlugune
bagli kalmaktan daha esnek ve genisletilebilir.
"""

from football_engine.core.tasks.queue import TaskQueue
from football_engine.core.tasks.worker import TaskWorker


class TaskManager:

    def __init__(self):
        self.queue = TaskQueue()
        self.worker = TaskWorker(self.queue)

    def submit(self, task):
        self.queue.push(task)

    def execute(self):
        return self.worker.run()
