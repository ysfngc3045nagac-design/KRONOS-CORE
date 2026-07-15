"""Analiz sonuclarini oylama sistemi ile birlestirir."""


class VotingEngine:

    def calculate(self, context):

        votes = {"HOME": 0, "DRAW": 0, "AWAY": 0}

        for result in context.results.values():
            if not isinstance(result, dict):
                continue

            prediction = result.get("prediction")

            if prediction in votes:
                votes[prediction] += 1

        if sum(votes.values()) == 0:
            return {"prediction": None, "votes": votes}

        winner = max(votes, key=votes.get)

        return {"prediction": winner, "votes": votes}
