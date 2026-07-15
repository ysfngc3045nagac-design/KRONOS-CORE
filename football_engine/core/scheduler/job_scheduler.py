"""
Isimle tetiklenen gorev calistirici.

NOT: Projede AYNI ISIMDE (Scheduler) UC farkli implementasyon vardi:
  1) orchestration/clock_scheduler.py -> saat:dakika bazli, otomatik dongu
  2) core/scheduler/job_scheduler.py (bu dosya) -> kayitli job'lari isimle
     manuel/API uzerinden tetikleme, otomatik zamanlama YOK
  3) interval bazli (every/tick) -> ClockScheduler'a entegre edildi (asagida)

Isim carpismasini cozmek icin bu sinif JobScheduler olarak adlandirildi.
"""

from football_engine.core.scheduler.job_registry import JobRegistry


class JobScheduler:

    def __init__(self):
        self.registry = JobRegistry()

    def register(self, job):
        self.registry.register(job)

    def run(self, name, *args, **kwargs):
        job = self.registry.get(name)
        if job is None:
            raise KeyError(name)
        return job.run(*args, **kwargs)

    def run_all(self):
        return {job.name: job.run() for job in self.registry.all()}
