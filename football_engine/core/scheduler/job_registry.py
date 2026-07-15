"""Gorev kayit sistemi."""

from football_engine.core.scheduler.job import Job


class JobRegistry:

    def __init__(self):
        self.jobs: dict[str, Job] = {}

    def register(self, job: Job):
        self.jobs[job.name] = job

    def get(self, name):
        return self.jobs.get(name)

    def all(self):
        return list(self.jobs.values())
