"""KRONOS_DATA_HUB - Database Models"""
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
import json

@dataclass
class League:
    id: Optional[int] = None
    name: str = ""
    country: str = ""
    tier: int = 1
    source_id: str = ""
    source_league_id: str = ""
    season: str = ""
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""

@dataclass
class Team:
    id: Optional[int] = None
    name: str = ""
    short_name: str = ""
    country: str = ""
    league_id: int = 0
    source_id: str = ""
    source_team_id: str = ""
    elo_rating: float = 1500.0
    market_value: float = 0.0
    founded_year: int = 0
    stadium: str = ""
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""

@dataclass
class Player:
    id: Optional[int] = None
    name: str = ""
    position: str = ""
    nationality: str = ""
    team_id: int = 0
    source_id: str = ""
    source_player_id: str = ""
    birth_date: str = ""
    market_value: float = 0.0
    jersey_number: int = 0
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""

@dataclass
class Match:
    id: Optional[int] = None
    source_id: str = ""
    source_match_id: str = ""
    league_id: int = 0
    season: str = ""
    match_date: str = ""
    match_time: str = ""
    home_team_id: int = 0
    away_team_id: int = 0
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    status: str = "scheduled"
    venue: str = ""
    referee: str = ""
    attendance: int = 0
    round: str = ""
    is_processed: bool = False
    created_at: str = ""
    updated_at: str = ""

@dataclass
class MatchStatistics:
    id: Optional[int] = None
    match_id: int = 0
    team_id: int = 0
    is_home: bool = True
    possession: float = 0.0
    shots_total: int = 0
    shots_on_target: int = 0
    shots_off_target: int = 0
    shots_blocked: int = 0
    corners: int = 0
    fouls: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    offsides: int = 0
    passes_total: int = 0
    passes_completed: int = 0
    crosses: int = 0
    tackles: int = 0
    interceptions: int = 0
    saves: int = 0
    xg: float = 0.0
    xa: float = 0.0
    source_id: str = ""
    created_at: str = ""

@dataclass
class Odds:
    id: Optional[int] = None
    match_id: int = 0
    source_id: str = ""
    bookmaker: str = ""
    market: str = "1X2"
    home_odds: float = 0.0
    draw_odds: float = 0.0
    away_odds: float = 0.0
    over_odds: float = 0.0
    under_odds: float = 0.0
    handicap: float = 0.0
    timestamp: str = ""
    is_live: bool = False
    created_at: str = ""

@dataclass
class Injury:
    id: Optional[int] = None
    player_id: int = 0
    team_id: int = 0
    injury_type: str = ""
    injury_detail: str = ""
    expected_return: str = ""
    status: str = "out"
    source_id: str = ""
    reported_at: str = ""
    created_at: str = ""

@dataclass
class Weather:
    id: Optional[int] = None
    match_id: int = 0
    venue: str = ""
    temperature: float = 0.0
    humidity: int = 0
    wind_speed: float = 0.0
    wind_direction: str = ""
    precipitation: float = 0.0
    visibility: float = 0.0
    condition: str = ""
    forecast_time: str = ""
    source_id: str = ""
    created_at: str = ""

@dataclass
class News:
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    url: str = ""
    source_id: str = ""
    source_name: str = ""
    category: str = ""
    team_id: Optional[int] = None
    player_id: Optional[int] = None
    published_at: str = ""
    sentiment: float = 0.0
    relevance_score: float = 0.0
    is_processed: bool = False
    created_at: str = ""

@dataclass
class Transfer:
    id: Optional[int] = None
    player_id: int = 0
    from_team_id: int = 0
    to_team_id: int = 0
    transfer_type: str = ""
    fee: float = 0.0
    currency: str = "EUR"
    transfer_date: str = ""
    season: str = ""
    source_id: str = ""
    created_at: str = ""

@dataclass
class SourceHealth:
    id: Optional[int] = None
    source_id: str = ""
    status: str = "healthy"
    last_check: str = ""
    last_success: str = ""
    last_failure: str = ""
    failure_count: int = 0
    success_count: int = 0
    avg_response_time_ms: float = 0.0
    error_rate: float = 0.0
    uptime_percentage: float = 100.0
    created_at: str = ""
    updated_at: str = ""

@dataclass
class DataQuality:
    id: Optional[int] = None
    source_id: str = ""
    table_name: str = ""
    record_count: int = 0
    null_percentage: float = 0.0
    duplicate_count: int = 0
    anomaly_count: int = 0
    confidence_score: float = 1.0
    checked_at: str = ""
    created_at: str = ""

class DatabaseSchema:
    TABLES = {
        "leagues": "CREATE TABLE IF NOT EXISTS leagues (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, country TEXT NOT NULL, tier INTEGER DEFAULT 1, source_id TEXT NOT NULL, source_league_id TEXT, season TEXT NOT NULL, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(source_id, source_league_id, season))",
        "teams": "CREATE TABLE IF NOT EXISTS teams (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, short_name TEXT, country TEXT, league_id INTEGER REFERENCES leagues(id), source_id TEXT NOT NULL, source_team_id TEXT, elo_rating REAL DEFAULT 1500.0, market_value REAL DEFAULT 0.0, founded_year INTEGER, stadium TEXT, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(source_id, source_team_id))",
        "players": "CREATE TABLE IF NOT EXISTS players (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, position TEXT, nationality TEXT, team_id INTEGER REFERENCES teams(id), source_id TEXT NOT NULL, source_player_id TEXT, birth_date TEXT, market_value REAL DEFAULT 0.0, jersey_number INTEGER, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(source_id, source_player_id))",
        "matches": "CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY AUTOINCREMENT, source_id TEXT NOT NULL, source_match_id TEXT NOT NULL, league_id INTEGER REFERENCES leagues(id), season TEXT NOT NULL, match_date TEXT NOT NULL, match_time TEXT, home_team_id INTEGER REFERENCES teams(id), away_team_id INTEGER REFERENCES teams(id), home_goals INTEGER, away_goals INTEGER, status TEXT DEFAULT 'scheduled', venue TEXT, referee TEXT, attendance INTEGER DEFAULT 0, round TEXT, is_processed INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(source_id, source_match_id))",
        "match_statistics": "CREATE TABLE IF NOT EXISTS match_statistics (id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER REFERENCES matches(id), team_id INTEGER REFERENCES teams(id), is_home INTEGER DEFAULT 1, possession REAL DEFAULT 0.0, shots_total INTEGER DEFAULT 0, shots_on_target INTEGER DEFAULT 0, shots_off_target INTEGER DEFAULT 0, shots_blocked INTEGER DEFAULT 0, corners INTEGER DEFAULT 0, fouls INTEGER DEFAULT 0, yellow_cards INTEGER DEFAULT 0, red_cards INTEGER DEFAULT 0, offsides INTEGER DEFAULT 0, passes_total INTEGER DEFAULT 0, passes_completed INTEGER DEFAULT 0, crosses INTEGER DEFAULT 0, tackles INTEGER DEFAULT 0, interceptions INTEGER DEFAULT 0, saves INTEGER DEFAULT 0, xg REAL DEFAULT 0.0, xa REAL DEFAULT 0.0, source_id TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(match_id, team_id, source_id))",
        "odds": "CREATE TABLE IF NOT EXISTS odds (id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER REFERENCES matches(id), source_id TEXT NOT NULL, bookmaker TEXT NOT NULL, market TEXT DEFAULT '1X2', home_odds REAL DEFAULT 0.0, draw_odds REAL DEFAULT 0.0, away_odds REAL DEFAULT 0.0, over_odds REAL DEFAULT 0.0, under_odds REAL DEFAULT 0.0, handicap REAL DEFAULT 0.0, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_live INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(match_id, source_id, bookmaker, market, timestamp))",
        "injuries": "CREATE TABLE IF NOT EXISTS injuries (id INTEGER PRIMARY KEY AUTOINCREMENT, player_id INTEGER REFERENCES players(id), team_id INTEGER REFERENCES teams(id), injury_type TEXT, injury_detail TEXT, expected_return TEXT, status TEXT DEFAULT 'out', source_id TEXT NOT NULL, reported_at TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(player_id, source_id, reported_at))",
        "weather": "CREATE TABLE IF NOT EXISTS weather (id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER REFERENCES matches(id), venue TEXT, temperature REAL, humidity INTEGER, wind_speed REAL, wind_direction TEXT, precipitation REAL, visibility REAL, condition TEXT, forecast_time TIMESTAMP, source_id TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(match_id, source_id, forecast_time))",
        "news": "CREATE TABLE IF NOT EXISTS news (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, content TEXT, url TEXT, source_id TEXT NOT NULL, source_name TEXT, category TEXT, team_id INTEGER REFERENCES teams(id), player_id INTEGER REFERENCES players(id), published_at TIMESTAMP, sentiment REAL DEFAULT 0.0, relevance_score REAL DEFAULT 0.0, is_processed INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(url, source_id))",
        "transfers": "CREATE TABLE IF NOT EXISTS transfers (id INTEGER PRIMARY KEY AUTOINCREMENT, player_id INTEGER REFERENCES players(id), from_team_id INTEGER REFERENCES teams(id), to_team_id INTEGER REFERENCES teams(id), transfer_type TEXT, fee REAL DEFAULT 0.0, currency TEXT DEFAULT 'EUR', transfer_date TEXT, season TEXT, source_id TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(player_id, from_team_id, to_team_id, transfer_date, source_id))",
        "source_health": "CREATE TABLE IF NOT EXISTS source_health (id INTEGER PRIMARY KEY AUTOINCREMENT, source_id TEXT NOT NULL UNIQUE, status TEXT DEFAULT 'healthy', last_check TIMESTAMP, last_success TIMESTAMP, last_failure TIMESTAMP, failure_count INTEGER DEFAULT 0, success_count INTEGER DEFAULT 0, avg_response_time_ms REAL DEFAULT 0.0, error_rate REAL DEFAULT 0.0, uptime_percentage REAL DEFAULT 100.0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        "data_quality": "CREATE TABLE IF NOT EXISTS data_quality (id INTEGER PRIMARY KEY AUTOINCREMENT, source_id TEXT NOT NULL, table_name TEXT NOT NULL, record_count INTEGER DEFAULT 0, null_percentage REAL DEFAULT 0.0, duplicate_count INTEGER DEFAULT 0, anomaly_count INTEGER DEFAULT 0, confidence_score REAL DEFAULT 1.0, checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(source_id, table_name, checked_at))",
        "collection_logs": "CREATE TABLE IF NOT EXISTS collection_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, source_id TEXT NOT NULL, operation TEXT NOT NULL, status TEXT DEFAULT 'pending', records_count INTEGER DEFAULT 0, error_message TEXT, duration_ms INTEGER DEFAULT 0, started_at TIMESTAMP, completed_at TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        "cache_entries": "CREATE TABLE IF NOT EXISTS cache_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT NOT NULL UNIQUE, value TEXT NOT NULL, expires_at TIMESTAMP NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    }

    INDEXES = [
        "CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date)",
        "CREATE INDEX IF NOT EXISTS idx_matches_league ON matches(league_id)",
        "CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status)",
        "CREATE INDEX IF NOT EXISTS idx_teams_league ON teams(league_id)",
        "CREATE INDEX IF NOT EXISTS idx_players_team ON players(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_odds_match ON odds(match_id)",
        "CREATE INDEX IF NOT EXISTS idx_news_published ON news(published_at)",
        "CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_entries(expires_at)",
    ]

    @classmethod
    def create_all(cls, conn):
        cursor = conn.cursor()
        for table_name, sql in cls.TABLES.items():
            cursor.execute(sql)
        for index_sql in cls.INDEXES:
            cursor.execute(index_sql)
        conn.commit()

    @classmethod
    def drop_all(cls, conn):
        cursor = conn.cursor()
        for table_name in reversed(list(cls.TABLES.keys())):
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()
