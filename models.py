from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"

class PlayerStatus(enum.Enum):
    AVAILABLE = "available"
    INJURED = "injured"
    SUSPENDED = "suspended"
    UNAVAILABLE = "unavailable"

class PlayerPosition(enum.Enum):
    GOALKEEPER = "goalkeeper"
    DEFENDER = "defender"
    MIDFIELDER = "midfielder"
    FORWARD = "forward"

class GameweekStatus(enum.Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"

# Association table for gameweeks and leagues
gameweek_leagues = Table('gameweek_leagues', Base.metadata,
    Column('gameweek_id', Integer, ForeignKey('gameweeks.id')),
    Column('league_id', Integer, ForeignKey('leagues.id'))
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    total_points = Column(Integer, default=0)
    budget = Column(Float, default=100.0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    teams = relationship("Team", back_populates="owner")
    league_memberships = relationship("LeagueMembership", back_populates="user")
    owned_leagues = relationship("League", back_populates="owner")

class Player(Base):
    """Real football players (e.g., Mohamed Salah, Marcus Rashford) - Admin managed only"""
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    position = Column(SQLEnum(PlayerPosition), nullable=False)
    team = Column(String, nullable=False)  
    price = Column(Float, nullable=False)  
    total_points = Column(Integer, default=0)  
    status = Column(SQLEnum(PlayerStatus), default=PlayerStatus.AVAILABLE)
    shirt_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    team_players = relationship("TeamPlayer", back_populates="player")
    player_stats = relationship("PlayerStats", back_populates="player")

class Team(Base):
    """Fantasy teams - User's collection of real players in a league"""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)  
    captain_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    vice_captain_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    total_points = Column(Integer, default=0)
    current_budget = Column(Float, default=100.0)  
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="teams")
    league = relationship("League", back_populates="teams")
    captain = relationship("Player", foreign_keys=[captain_id])
    vice_captain = relationship("Player", foreign_keys=[vice_captain_id])
    team_players = relationship("TeamPlayer", back_populates="team")
    gameweek_scores = relationship("TeamGameweekScore", back_populates="team")

class TeamPlayer(Base):
    """Which real players are currently in a fantasy team's squad (max 15)"""
    __tablename__ = "team_players"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    
    # Track when player joined/left the fantasy team (crucial for transfer history)
    joined_at = Column(DateTime, default=func.now())
    left_at = Column(DateTime, nullable=True)  
    purchase_price = Column(Float, nullable=False)  
    
    # Relationships
    team = relationship("Team", back_populates="team_players")
    player = relationship("Player", back_populates="team_players")
    selections = relationship("TeamPlayerSelection", back_populates="team_player")

class Gameweek(Base):
    __tablename__ = "gameweeks"
    
    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, nullable=False, unique=True)
    deadline = Column(DateTime, nullable=False)
    status = Column(SQLEnum(GameweekStatus), default=GameweekStatus.UPCOMING)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    fixtures = relationship("Fixture", back_populates="gameweek")
    leagues = relationship("League", secondary=gameweek_leagues, back_populates="gameweeks")
    league_standings = relationship("LeagueGameweekStanding", back_populates="gameweek")

class Fixture(Base):
    """Real football matches (e.g., Manchester United vs Liverpool) - Admin managed"""
    __tablename__ = "fixtures"
    
    id = Column(Integer, primary_key=True, index=True)
    gameweek_id = Column(Integer, ForeignKey("gameweeks.id"), nullable=False)
    home_team = Column(String, nullable=False) 
    away_team = Column(String, nullable=False)  
    kickoff_time = Column(DateTime, nullable=False)
    
    # Match results (null until match finishes)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    completed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    gameweek = relationship("Gameweek", back_populates="fixtures")
    player_stats = relationship("PlayerStats", back_populates="fixture")

class PlayerStats(Base):
    """How a real player performed in a specific real fixture - generates fantasy points"""
    __tablename__ = "player_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False)
    
    # Performance data (entered by admin after real match)
    minutes_played = Column(Integer, default=0)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    clean_sheet = Column(Boolean, default=False) 
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    own_goals = Column(Integer, default=0)
    penalty_saves = Column(Integer, default=0) 
    penalty_misses = Column(Integer, default=0)
    saves = Column(Integer, default=0) 
    
    # Calculated fantasy points for this specific fixture
    fantasy_points = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    player = relationship("Player", back_populates="player_stats")
    fixture = relationship("Fixture", back_populates="player_stats")

class League(Base):
    """Fantasy leagues that users can create and join"""
    __tablename__ = "leagues"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)  # Join code like "ABC123"
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # League settings/rules (configurable by league owner)
    budget = Column(Float, default=100.0) 
    max_players_per_team = Column(Integer, default=3)  
    max_teams = Column(Integer, default=20)  
    
    # Squad composition rules (configurable)
    max_goalkeepers = Column(Integer, default=2) 
    max_defenders = Column(Integer, default=5)    
    max_midfielders = Column(Integer, default=5)  
    max_forwards = Column(Integer, default=3)     
    total_squad_size = Column(Integer, default=15) 
    
    # Transfer rules (configurable)
    free_transfers_per_gameweek = Column(Integer, default=1)  
    transfer_penalty_points = Column(Integer, default=4)     
    max_transfers_per_gameweek = Column(Integer, default=5)  
    
    # Scoring system settings (configurable)
    points_per_goal_forward = Column(Integer, default=4)     
    points_per_goal_midfielder = Column(Integer, default=5)   
    points_per_goal_defender = Column(Integer, default=6)     
    points_per_goal_goalkeeper = Column(Integer, default=6)  
    points_per_assist = Column(Integer, default=3)          
    points_per_clean_sheet = Column(Integer, default=4)      
    points_per_yellow_card = Column(Integer, default=-1)     
    points_per_red_card = Column(Integer, default=-3)        
    points_per_own_goal = Column(Integer, default=-2)       
    points_per_penalty_save = Column(Integer, default=5)    
    points_per_penalty_miss = Column(Integer, default=-2)    
    
    # Special features (configurable)
    allow_wildcards = Column(Boolean, default=True)          
    allow_bench_boost = Column(Boolean, default=True)       
    allow_triple_captain = Column(Boolean, default=True)     
    
    is_private = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="owned_leagues")
    teams = relationship("Team", back_populates="league")  
    memberships = relationship("LeagueMembership", back_populates="league")
    gameweeks = relationship("Gameweek", secondary=gameweek_leagues, back_populates="leagues")
    standings = relationship("LeagueGameweekStanding", back_populates="league")

class LeagueMembership(Base):
    __tablename__ = "league_memberships"
    
    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, default=func.now())
    
    # Relationships
    league = relationship("League", back_populates="memberships")
    user = relationship("User", back_populates="league_memberships")

class LeagueGameweekStanding(Base):
    __tablename__ = "league_gameweek_standings"
    
    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    gameweek_id = Column(Integer, ForeignKey("gameweeks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    points = Column(Integer, default=0)
    rank = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    league = relationship("League", back_populates="standings")
    gameweek = relationship("Gameweek", back_populates="league_standings")
    user = relationship("User")

class Transfer(Base):
    """Record of transfers - swapping real players in/out of fantasy teams"""
    __tablename__ = "transfers"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    player_out_id = Column(Integer, ForeignKey("players.id"), nullable=False)  
    player_in_id = Column(Integer, ForeignKey("players.id"), nullable=False)   
    gameweek_id = Column(Integer, ForeignKey("gameweeks.id"), nullable=False)
    
    # Transfer cost and pricing
    points_cost = Column(Integer, default=0)  
    money_out = Column(Float, nullable=False) 
    money_in = Column(Float, nullable=False)   
    money_change = Column(Float, nullable=False)  
    
    # Transfer tracking
    is_free_transfer = Column(Boolean, default=True) 
    transfer_number_in_gameweek = Column(Integer, nullable=False)  
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    team = relationship("Team", foreign_keys=[team_id])
    player_out = relationship("Player", foreign_keys=[player_out_id])
    player_in = relationship("Player", foreign_keys=[player_in_id])
    gameweek = relationship("Gameweek", foreign_keys=[gameweek_id])

class ChipUsage(Base):
    """Track when users play special chips (wildcard, bench boost, etc.)"""
    __tablename__ = "chip_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    gameweek_id = Column(Integer, ForeignKey("gameweeks.id"), nullable=False)
    chip_type = Column(String, nullable=False)  
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    team = relationship("Team", foreign_keys=[team_id])
    gameweek = relationship("Gameweek", foreign_keys=[gameweek_id])

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id]) 

class TeamGameweekScore(Base):
    """Track team's points for each gameweek"""
    __tablename__ = "team_gameweek_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    gameweek_id = Column(Integer, ForeignKey("gameweeks.id"), nullable=False)
    points = Column(Integer, default=0)
    bench_points = Column(Integer, default=0)  
    captain_points = Column(Integer, default=0)  
    chip_used = Column(String, nullable=True)  
    transfers_made = Column(Integer, default=0)
    transfer_cost = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="gameweek_scores")
    gameweek = relationship("Gameweek")

class TeamPlayerSelection(Base):
    """Track player selection status for each gameweek"""
    __tablename__ = "team_player_selections"
    
    id = Column(Integer, primary_key=True, index=True)
    team_player_id = Column(Integer, ForeignKey("team_players.id"), nullable=False)
    gameweek_id = Column(Integer, ForeignKey("gameweeks.id"), nullable=False)
    is_starter = Column(Boolean, nullable=False)  # True if in starting 11, False if on bench
    bench_position = Column(Integer, nullable=True)  # Position on bench (1-4) if benched
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    team_player = relationship("TeamPlayer", back_populates="selections")
    gameweek = relationship("Gameweek")