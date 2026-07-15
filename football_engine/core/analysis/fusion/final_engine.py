"""
Son analiz ciktisi - tum fusion bilesenlerini birlestiren motor.
"""

from football_engine.core.analysis.fusion.score_fusion import ScoreFusion
from football_engine.core.analysis.fusion.confidence import ConfidenceCalculator
from football_engine.core.analysis.fusion.voting import VotingEngine
from football_engine.core.analysis.fusion.risk_manager import RiskManager
from football_engine.core.analysis.fusion.decision_engine import DecisionEngine


class FinalAnalysisEngine:

    def __init__(self):
        self.score = ScoreFusion()
        self.confidence = ConfidenceCalculator()
        self.vote = VotingEngine()
        self.risk = RiskManager()
        self.decision = DecisionEngine()

    def build(self, context):

        score = self.score.calculate(context)
        confidence = self.confidence.calculate(context)
        voting = self.vote.calculate(context)
        risk = self.risk.calculate(context)

        decision = self.decision.decide(score, confidence, risk, voting)

        return {
            "overall_score": score,
            "confidence": confidence,
            "risk": risk,
            "prediction": voting["prediction"],
            "votes": voting["votes"],
            "decision": decision,
            "details": context.results,
        }
