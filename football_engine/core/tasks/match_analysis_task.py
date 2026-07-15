"""Mac Analiz Gorevi - bir AnalysisPipeline/Orchestrator uzerinden calisir."""

from football_engine.core.tasks.task import Task


class MatchAnalysisTask(Task):

    def __init__(self, pipeline, match):
        self.pipeline = pipeline
        self.match = match

    def execute(self):
        return self.pipeline.analyze(self.match)
