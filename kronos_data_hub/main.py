#!/usr/bin/env python3
"""KRONOS_DATA_HUB v1.0.0 - Ana giris noktasi"""
import argparse
import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SQLiteManager, CacheManager, BackupManager
from core import RateLimiter, RetryManager, Scheduler, SourceManager
from core import SourceValidator, SourceRanker, SourceHealthMonitor
from ai import SourceAI, AnomalyDetector, ConfidenceScorer, DataCleaner, DuplicateDetector
from dashboard import SourceMonitor, StatisticsPanel, LogManager
from collectors import (FootballDataCollector, FBRefCollector, UnderstatCollector,
                        OddsCollector, ClubELOCollector, SofascoreCollector,
                        WeatherCollector, NewsCollector, APIFootballCollector,
                        TheOddsAPICollector, FootballDataOrgCollector, OddsAPIIOCollector)


def setup_logging(config_path="config/settings.json"):
    log_format = "%(asctime)s | %(levelname)s | %(module)s | %(message)s"
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(level=logging.INFO, format=log_format,
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("logs/kronos.log", encoding="utf-8")])
    return logging.getLogger("kronos")


def initialize_system():
    logger = setup_logging()
    logger.info("=== KRONOS_DATA_HUB v1.0.0 Baslatiliyor ===")
    db = SQLiteManager("data/kronos.db")
    logger.info("Veritabani baglantisi kuruldu")
    cache = CacheManager(db, memory_size=1000, default_ttl_seconds=3600)
    rate_limiter = RateLimiter()
    retry_manager = RetryManager()
    source_manager = SourceManager(config_path="config/sources.json", db=db, rate_limiter=rate_limiter,
                                    retry_manager=retry_manager, cache=cache)
    logger.info(f"{len(source_manager.get_all_sources())} kaynak yuklendi")
    _register_collectors(source_manager, db, rate_limiter, retry_manager, cache)
    source_ai = SourceAI(db)
    anomaly_detector = AnomalyDetector(db)
    confidence_scorer = ConfidenceScorer(db)
    data_cleaner = DataCleaner()
    duplicate_detector = DuplicateDetector(db)
    source_monitor = SourceMonitor(db, source_manager)
    stats_panel = StatisticsPanel(db)
    log_manager = LogManager(db)
    scheduler = Scheduler()
    health_monitor = SourceHealthMonitor(db)
    return {"db": db, "cache": cache, "rate_limiter": rate_limiter, "retry_manager": retry_manager,
        "source_manager": source_manager, "scheduler": scheduler, "source_ai": source_ai,
        "anomaly_detector": anomaly_detector, "confidence_scorer": confidence_scorer,
        "data_cleaner": data_cleaner, "duplicate_detector": duplicate_detector,
        "source_monitor": source_monitor, "stats_panel": stats_panel, "log_manager": log_manager,
        "health_monitor": health_monitor, "logger": logger}


def _register_collectors(source_manager, db, rate_limiter, retry_manager, cache):
    collectors_config = {
        "football_data": (FootballDataCollector, {"season": "2425", "league": "E0"}),
        "fbref": (FBRefCollector, {"league": "Premier League", "season": "2024-2025"}),
        "understat": (UnderstatCollector, {"league": "EPL", "season": "2024"}),
        "odds_api": (OddsCollector, {"sport": "soccer_epl"}),
        "clubelo": (ClubELOCollector, {}),
        "sofascore": (SofascoreCollector, {}),
        "weather_api": (WeatherCollector, {}),
        "news_api": (NewsCollector, {}),
        "api_football": (APIFootballCollector, {"league": "premier_league", "season": "2025"}),
        "theoddsapi": (TheOddsAPICollector, {"sport": "soccer_epl"}),
        "football_data_org": (FootballDataOrgCollector, {"competition": "premier_league"}),
        "odds_api_io": (OddsAPIIOCollector, {"region": "eu"}),
    }
    for source_id, (collector_class, default_params) in collectors_config.items():
        config = source_manager.get_source(source_id)
        if config and config.get("enabled", True):
            collector = collector_class(source_id=source_id, config=config, db=db, rate_limiter=rate_limiter,
                                         retry_manager=retry_manager, cache=cache)
            source_manager.register_collector(source_id, collector)


def mode_collect(ctx, source="all", **kwargs):
    logger = ctx["logger"]
    source_manager = ctx["source_manager"]
    logger.info(f"Veri toplama baslatiliyor: {source}")
    if source == "all":
        sources = source_manager.get_enabled_sources()
    else:
        sources = {source: source_manager.get_source(source)}
    results = {}
    for sid, config in sources.items():
        if source == "all" and config and not config.get("bulk_collectable", True):
            logger.info(f"'{sid}' atlandi (bulk_collectable=false)")
            continue
        collector = source_manager.get_collector(sid)
        if collector:
            try:
                result = collector.collect(**kwargs)
                results[sid] = result
            except Exception as e:
                results[sid] = {"status": "error", "error": str(e)}
        else:
            logger.warning(f"Collector bulunamadi: {sid}")
    return results


def mode_dashboard(ctx):
    monitor = ctx["source_monitor"]
    stats = ctx["stats_panel"]
    dashboard_data = monitor.get_dashboard_data()
    overview = stats.get_overview()
    print("KRONOS DATA HUB - DASHBOARD")
    print(dashboard_data["summary"])
    return dashboard_data


def mode_test(ctx):
    import unittest
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for module in ['tests.test_collectors', 'tests.test_parsers', 'tests.test_ai']:
        try:
            suite.addTests(loader.loadTestsFromName(module))
        except Exception as e:
            ctx["logger"].warning(f"Test modulu yuklenemedi: {module} - {e}")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return {"tests_run": result.testsRun, "failures": len(result.failures),
            "errors": len(result.errors), "success": result.wasSuccessful()}


def mode_schedule(ctx):
    scheduler = ctx["scheduler"]
    scheduler.add_task("hourly_odds", "Saatlik Oran Toplama", lambda: mode_collect(ctx, source="odds_api"), interval_minutes=60)
    scheduler.add_task("daily_matches", "Gunluk Mac Toplama", lambda: mode_collect(ctx, source="football_data"), interval_minutes=360)
    scheduler.add_task("health_check", "Saglik Kontrolu", lambda: ctx["health_monitor"].check_all_sources(), interval_minutes=30)
    scheduler.add_task("backup", "Gunluk Yedekleme", lambda: BackupManager("data/kronos.db").create_backup("auto"), interval_minutes=1440)
    scheduler.start()
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()


def mode_validate(ctx):
    validator = SourceValidator()
    source_manager = ctx["source_manager"]
    sources = source_manager.get_enabled_sources()
    results = validator.validate_all(sources)
    return results


def main():
    parser = argparse.ArgumentParser(description="KRONOS_DATA_HUB")
    parser.add_argument("--mode", "-m", choices=["collect", "dashboard", "test", "schedule", "validate"], default="dashboard")
    parser.add_argument("--source", "-s", default="all")
    parser.add_argument("--league", "-l")
    parser.add_argument("--season")
    parser.add_argument("--detailed", "-d", action="store_true")
    args = parser.parse_args()
    ctx = initialize_system()
    if args.mode == "collect":
        kwargs = {}
        if args.league:
            kwargs["league"] = args.league
        if args.season:
            kwargs["season"] = args.season
        if args.detailed:
            kwargs["detailed"] = True
        result = mode_collect(ctx, source=args.source, **kwargs)
        print(result)
    elif args.mode == "dashboard":
        mode_dashboard(ctx)
    elif args.mode == "test":
        result = mode_test(ctx)
        sys.exit(0 if result['success'] else 1)
    elif args.mode == "schedule":
        mode_schedule(ctx)
    elif args.mode == "validate":
        mode_validate(ctx)


if __name__ == "__main__":
    main()
