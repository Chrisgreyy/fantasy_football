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
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    position = Column(SQLEnum(PlayerPosition), nullable=False)
    team = Column(String, nullable=False)  # Real football team
    price = Column(Float, nullable=False)
    total_points = Column(Integer, default=0)
    status = Column(SQLEnum(PlayerStatus), default=PlayerStatus.AVAILABLE)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    team_players = relationship("TeamPlayer", back_populates="player")
    player_stats = relationship("PlayerStats", back_populates="player")

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    captain_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    weekly_points = Column(Integer, default=0)
    total_points = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="teams")
    captain = relationship("Player", foreign_keys=[captain_id])
    team_players = relationship("TeamPlayer", back_populates="team")

class TeamPlayer(Base):
    __tablename__ = "team_players"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    is_starter = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="team_players")
    player = relationship("Player", back_populates="team_players")

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
    __tablename__ = "fixtures"
    
    id = Column(Integer, primary_key=True, index=True)
    gameweek_id = Column(Integer, ForeignKey("gameweeks.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)  # New: Link fixture to league
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    gameweek = relationship("Gameweek", back_populates="fixtures")
    league = relationship("League", back_populates="fixtures")  # New: Relationship to league
    player_stats = relationship("PlayerStats", back_populates="fixture")

class PlayerStats(Base):
    __tablename__ = "player_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    minutes_played = Column(Integer, default=0)
    clean_sheet = Column(Boolean, default=False)
    own_goals = Column(Integer, default=0)
    penalty_saves = Column(Integer, default=0)
    penalty_misses = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    points = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    player = relationship("Player", back_populates="player_stats")
    fixture = relationship("Fixture", back_populates="player_stats")

class League(Base):
    __tablename__ = "leagues"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_private = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="owned_leagues")
    memberships = relationship("LeagueMembership", back_populates="league")
    gameweeks = relationship("Gameweek", secondary=gameweek_leagues, back_populates="leagues")
    fixtures = relationship("Fixture", back_populates="league")  # New: League fixtures
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
    __tablename__ = "transfers"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    player_in_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    player_out_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    gameweek_id = Column(Integer, ForeignKey("gameweeks.id"), nullable=False)
    cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    team = relationship("Team", foreign_keys=[team_id])
    player_in = relationship("Player", foreign_keys=[player_in_id])
    player_out = relationship("Player", foreign_keys=[player_out_id])
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