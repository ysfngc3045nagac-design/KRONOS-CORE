"""Hava durumu etkisi"""


class WeatherEngine:

    def calculate(self, temperature: float, wind_speed: float, rain: bool):
        score = 100
        if temperature < -5 or temperature > 35:
            score -= 15
        if wind_speed > 40:
            score -= 20
        if rain:
            score -= 10
        return max(0, score)
