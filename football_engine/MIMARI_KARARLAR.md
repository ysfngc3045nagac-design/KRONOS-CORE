# KRONOS — Mimari Karar Dokümanı

Bu doküman, ~100 dosyalık ham kod parçasından tek, tutarlı bir `kronos/`
paketi oluşturulurken alınan tüm kararları özetler. 4 zip dosyasını
aşağıdaki gibi birleştirmen yeterli:

```
kronos/
├── core/
│   ├── config/, logging/, events/, tools/, models/, memory/      ← Paket 1
│   ├── data/, storage/, analysis/                                 ← Paket 2
│   ├── scheduler/, tasks/, monitoring/, plugins/, session/,
│   │   validation/, report/, state/, bootstrap.py, orchestrator.py,
│   │   app.py                                                     ← Paket 3
│   └── version.py                                                 ← Paket 1
├── interface/, tests/, requirements.txt, MIMARI_KARARLAR.md        ← Paket 4
```

Sadece 4 zip'i aynı klasöre (üst üste) çıkart, `core/` klasörleri birleşir.

## Kurulum

```bash
pip install -r requirements.txt --break-system-packages
export ANTHROPIC_API_KEY=...   # veya MODEL_PROVIDER=gemini + GEMINI_API_KEY
cd kronos
python3 -m unittest tests.test_end_to_end -v   # 6 test, hepsi geçmeli
uvicorn interface.api:app --reload             # REST API
```

## Tek giriş noktası

```python
from core.app import KronosApplication

app = KronosApplication()
report = app.analyze({
    "id": "12345",
    "home_elo": 1650, "away_elo": 1500,
    "xg": 1.8, "xga": 0.9,
    "scored": [2, 1, 3], "conceded": [0, 1, 1],
    "recent_results": [{"home_goals": 2, "away_goals": 1, "home": True}],
    "odds": {"home": 1.8, "draw": 3.6, "away": 4.2},
})
```

`match` sözlüğüne ne kadar çok alan koyarsan (`injured_players`,
`league_position`, `temperature`, `referee_yellow_avg` vb.), o kadar çok
ajan gerçek veriyle çalışır — eksik alanlar için her ajan makul bir
varsayılana düşer, çökmez.

---

## Düzeltilen somut hatalar

| Dosya | Hata | Düzeltme |
|---|---|---|
| `core/tools/uuid_tools.py` | `str(uuid.uuid4()` — kapanmamış parantez (SyntaxError) | Parantez kapatıldı |
| `core/tools/http_tools.py` | Cache mantığı fonksiyon dışında yarım fragman halindeydi | Tek, tamamlanmış `http_get` içinde birleştirildi |
| `core/tools/csv_tools.py` | `write_csv`/`append_csv` sadece ilk satırın key'lerini kullanıyordu → farklı key'lerde `ValueError`/yanlış sütun | Tüm satırların key birleşimi (union) kullanılıyor, mevcut header korunuyor |
| `core/analysis/engines/form_engine.py` | `match.home` bayrağı hiç kullanılmıyordu — deplasman maçları yanlış hesaplanıyordu | Takımın kendi perspektifinden (own/opp goals) hesaplanıyor |
| `core/analysis/engines/goal_engine.py` | `conceded` boşsa `ZeroDivisionError` | İkisi de kontrol ediliyor |
| `core/analysis/engines/streak_engine.py` | `results` boşsa `ZeroDivisionError` | Boşluk kontrolü eklendi |
| `core/analysis/engines/referee_engine.py` | `discipline` negatife düşebiliyordu | `max(0, ...)` ile clamp edildi |
| `core/storage/report_store.py` | Dosya adı saniye hassasiyetinde — aynı saniyede iki rapor birbirini eziyordu | Mikrosaniye + benzersiz sonek eklendi |
| `core/events/event.py` | `created_at: datetime = datetime.utcnow()` — sınıf tanımlanırken bir kez çalışıyordu, tüm `Event`'ler aynı zaman damgasını paylaşıyordu | `field(default_factory=datetime.utcnow)` |
| `core/data/datahub.py` | `team()`/`matches()` metodlarında `match()`'teki `None` kontrolü yoktu → anlaşılmaz `AttributeError` | Üç metoda da aynı `RuntimeError` koruması eklendi |

## Eksik olup sıfırdan yazılan dosyalar

Bu dosyalar konuşma boyunca import ediliyordu ama kodu hiç paylaşılmamıştı:

- `core/analysis/engines/home_advantage_engine.py` — `HomeAdvantageEngine`
- `core/analysis/agents/health_agent.py` — `HealthAgent`
- `core/models/anthropic_adapter.py` — `AnthropicAdapter`
- `core/models/gemini_adapter.py` — `GeminiAdapter`
- `interface/api.py` — FastAPI servisi (önceki oturum özetinde "✅ tamamlandı" deniyordu ama hiç kod paylaşılmamıştı)

## Kritik mimari hata: Fusion katmanı hep boş/sıfır dönüyordu

`ScoreFusion`, `VotingEngine`, `ConfidenceCalculator` gibi birleştiriciler
`result["score"]` ve `result["prediction"]` anahtarlarını bekliyordu, ama
motorların (`GoalEngine`, `XGEngine`, `EloEngine` vb.) hiçbiri bu anahtarları
doldurmuyordu — her biri kendi özel anahtarlarını kullanıyordu
(`"attack"/"defense"`, `"home"/"draw"/"away"` vb.). Sonuç: sistem çalışıyor
gibi görünüyordu ama pratikte hep `0` skor / `None` tahmin üretiyordu.

**Çözüm:** `core/analysis/agents/` katmanı eklendi — her motoru standart
`{"score", "prediction", "confidence", "details"}` formatına saran bir
adapter ajan. Bu, `tests/test_end_to_end.py`'de gerçek veriyle doğrulandı.

---

## İsim çakışmaları ve verilen kararlar

| Çakışan isim | Kaç versiyon | Seçilen | Gerekçe |
|---|---|---|---|
| `Scheduler` | 3 (saat:dakika, interval, isimle-tetikleme) | `ClockScheduler` (ilk ikisi birleşti) + `JobScheduler` (üçüncüsü) | Farklı gerçek ihtiyaçlar — biri "her gün 03:00'te çalıştır", diğeri "API'den tetikle" |
| `TaskManager`/`Task` | 3 | Queue+Worker, `Task` ABC (`execute()`) | En genişletilebilir; `MatchAnalysisTask` gibi somut görevler kolayca eklenebiliyor |
| `AgentManager` | 2 (imza farklı) | `__init__(self, registry)`, try/except'li | Hataya dayanıklı — bir ajan çökerse diğerleri durmuyor |
| `DataHub`/`DataProvider` | 2 | `search_matches(date)` imzalı, çoklu-sağlayıcı destekli | Gerçek API entegrasyonunda tarih bazlı arama zorunlu |
| `Settings` | 2 | En güncel (v1.0.0, `DATABASE_PATH` içeren) | Daha kapsamlı |
| `KronosLogger` | 2 | Instance tabanlı | Global `basicConfig` çakışmasını önlüyor |
| `EventBus` / `EventManager` | 2 | `EventBus` (subscribe/publish) | Daha yaygın kullanılan isimlendirme |
| `Plugin` mimarisi | 2 | 3 metodlu (`name/initialize/shutdown`) | `shutdown()` ayrımı kaynak temizliği için gerekli |
| `ReportHistory`/`HistoryManager`/`HistoryStore`/`AnalysisHistory` | 4 (birebir aynı kod) | Tek `ReportHistory` | Kod tekrarını önlemek için |
| "Merkezi giriş noktası" (`KronosEngine`, `AnalysisPipeline`, `AnalysisManager`, `MasterAnalysisEngine`, `MasterPipeline`, `MasterController`, `Kernel`, 2x `KronosApplication`) | 9 | `Bootstrap → Orchestrator → KronosApplication` | En bütünleşik olan, gerçekten çalışan zincirdi |

Elenen alternatifler (`KronosEngine`, `AnalysisPipeline`, `MasterPipeline`,
`Kernel` vb.) bu pakete dahil edilmedi — hepsi aynı işi yapıyordu ve fiilen
kullanılmıyordu (ölü kod). İstersen referans olarak ayrıca isteyebilirsin.

---

## Bundan sonrası: KRONOS-AI ile ilişki

Bu proje (`kronos/` — çok-ajanlı orkestrasyon iskeleti), mevcut
**KRONOS-AI** (Flask tabanlı bahis/futbol analiz uygulaması, Render'da
deploy edilen `ysfngc3045nagac-design/KRONOS-AI`) ile **aynı repo değil,
farklı bir mimari**. `DEFAULT_CRITERIA` listesi ve analiz motorları
KRONOS-AI'deki mantığa çok benziyor ama kod tabanı ayrı.

Bu ikisini birleştirmek mi istiyorsun (örneğin KRONOS-AI'nin Flask
route'larının bu yeni agent mimarisini çağırması), yoksa bu tamamen ayrı,
bağımsız bir proje olarak mı kalacak? Ona göre bir sonraki adımı (gerçek
API-Football/odds-api entegrasyonu, deploy, vb.) planlayalım.
