"""
Ev sahibi avantaji motoru.

NOT: Bu dosya konusma boyunca defalarca import edildi (MasterAnalysisEngine,
core.analysis import listeleri) ama kodu hicbir zaman paylasilmadi. KRONOS-AI
projesindeki benzer mantik ve diger motorlarin (FixtureEngine, WeatherEngine
vb.) stiliyle tutarli, calisir bir implementasyon olarak yazildi.

Ev sahibi avantaji genel olarak: lig ortalamasina gore ev sahibi kazanma
oranindan, stadyum doluluk/atmosfer katkisindan ve seyahat mesafesinden
(deplasman takimi icin yorgunluk) etkilenir.
"""


class HomeAdvantageEngine:

    def calculate(
        self,
        home_win_rate: float = 45.0,
        attendance_rate: float = 80.0,
        away_travel_km: float = 0.0,
    ) -> float:
        """
        home_win_rate: bu takimin ev sahibi olarak kazanma yuzdesi (0-100)
        attendance_rate: stadyum doluluk orani (0-100)
        away_travel_km: deplasman takiminin kat ettigi mesafe (km)
        """

        score = 50.0

        # lig ortalamasi ~%45 kabul edilip sapmaya gore ayarlanir
        score += (home_win_rate - 45.0) * 0.4

        # doluluk orani atmosfer katkisi olarak eklenir
        score += (attendance_rate - 50.0) * 0.1

        # deplasman takiminin uzun seyahati ev sahibi lehine kucuk bir katki saglar
        score += min(10.0, away_travel_km / 500)

        return round(max(0.0, min(100.0, score)), 2)
