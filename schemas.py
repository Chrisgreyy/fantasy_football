from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr
from models import UserRole, PlayerStatus, PlayerPosition, GameweekStatus

# Base schemas
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True

# User schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserResponse(UserBase):
    id: int
    role: UserRole
    total_points: int
    budget: float
    created_at: datetime
    
    class Config:
        from_attributes = True

# Player schemas
class PlayerBase(BaseModel):
    name: str
    position: PlayerPosition
    team: str
    price: float

class PlayerCreate(PlayerBase):
    pass

class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[PlayerPosition] = None
    team: Optional[str] = None
    price: Optional[float] = None
    status: Optional[PlayerStatus] = None

class PlayerResponse(PlayerBase):
    id: int
    total_points: int
    status: PlayerStatus
    created_at: datetime
    
    class Config:
        from_attributes = True

# Team schemas
class TeamBase(BaseModel):
    name: str

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    captain_id: Optional[int] = None

class TeamResponse(TeamBase):
    id: int
    user_id: int
    captain_id: Optional[int]
    weekly_points: int
    total_points: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Team Player schemas
class TeamPlayerBase(BaseModel):
    team_id: int
    player_id: int
    is_starter: bool = True

class TeamPlayerCreate(TeamPlayerBase):
    pass

class TeamPlayerResponse(TeamPlayerBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class TeamPlayerDetailResponse(BaseModel):
    id: int
    team_id: int
    player_id: int
    is_starter: bool
    created_at: datetime
    # Player details
    player_name: str
    player_position: PlayerPosition
    player_real_team: str
    player_price: float
    player_total_points: int
    player_status: PlayerStatus
    # Fantasy team details
    fantasy_team_name: str
    is_captain: bool
    
    class Config:
        from_attributes = True

# Transfer schemas
class TransferBase(BaseModel):
    team_id: int
    player_in_id: int
    player_out_id: int
    gameweek_id: int
    cost: float = 0.0

class TransferCreate(TransferBase):
    pass

class TransferResponse(TransferBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# League schemas
class LeagueBase(BaseModel):
    name: str
    is_private: bool = True

class LeagueCreate(LeagueBase):
    pass

class LeagueUpdate(BaseModel):
    name: Optional[str] = None
    is_private: Optional[bool] = None

class LeagueResponse(LeagueBase):
    id: int
    code: str
    owner_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# League Membership schemas
class LeagueMembershipBase(BaseModel):
    league_id: int
    user_id: int

class LeagueMembershipCreate(BaseModel):
    league_code: str

class LeagueMembershipResponse(LeagueMembershipBase):
    id: int
    joined_at: datetime
    
    class Config:
        from_attributes = True

class DetailedLeagueMembershipResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_email: str
    team_name: str
    team_id: int
    total_points: int
    budget: float
    joined_at: datetime
    rank: Optional[int] = None
    
    class Config:
        from_attributes = True

# Fixture schemas
class FixtureBase(BaseModel):
    gameweek_id: int
    league_id: int  # Add league_id as required field
    home_team: str
    away_team: str
    date: datetime

class FixtureCreate(FixtureBase):
    pass

class FixtureUpdate(BaseModel):
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    date: Optional[datetime] = None
    completed: Optional[bool] = None

class FixtureResponse(FixtureBase):
    id: int
    completed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Player Stats schemas
class PlayerStatsBase(BaseModel):
    player_id: int
    fixture_id: int
    goals: int = 0
    assists: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    minutes_played: int = 0
    clean_sheet: bool = False
    own_goals: int = 0
    penalty_saves: int = 0
    penalty_misses: int = 0
    saves: int = 0

class PlayerStatsCreate(PlayerStatsBase):
    pass

class PlayerStatsUpdate(BaseModel):
    goals: Optional[int] = None
    assists: Optional[int] = None
    yellow_cards: Optional[int] = None
    red_cards: Optional[int] = None
    minutes_played: Optional[int] = None
    clean_sheet: Optional[bool] = None
    own_goals: Optional[int] = None
    penalty_saves: Optional[int] = None
    penalty_misses: Optional[int] = None
    saves: Optional[int] = None

class PlayerStatsResponse(PlayerStatsBase):
    id: int
    points: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Fixture Data Submission Schema
class FixtureDataSubmission(BaseModel):
    gameweek: int
    fixture_id: int
    home_team: str
    away_team: str
    date: datetime
    players_stats: List[PlayerStatsBase]

# League Fixture schemas
class LeagueFixtureBase(BaseModel):
    gameweek_id: int
    league_id: int
    home_team: str
    away_team: str
    date: datetime

class LeagueFixtureCreate(LeagueFixtureBase):
    pass

class LeagueFixtureResponse(LeagueFixtureBase):
    id: int
    completed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Gameweek League Standing schema
class GameweekLeagueStanding(BaseModel):
    user_id: int
    user_name: str
    team_name: str
    points: int
    rank: int
    
    class Config:
        from_attributes = True

# Gameweek League Result schema
class GameweekLeagueResult(BaseModel):
    league_id: int
    league_name: str
    standings: List[GameweekLeagueStanding]
    fixtures: List[LeagueFixtureResponse]
    
    class Config:
        from_attributes = True

# Gameweek schemas
class GameweekBase(BaseModel):
    number: int
    deadline: datetime

class GameweekCreate(GameweekBase):
    pass

class GameweekUpdate(BaseModel):
    deadline: Optional[datetime] = None
    status: Optional[GameweekStatus] = None

class GameweekResponse(GameweekBase):
    id: int
    status: GameweekStatus
    created_at: datetime
    league_results: Optional[List[GameweekLeagueResult]] = None
    
    class Config:
        from_attributes = True

class GameweekResults(BaseModel):
    gameweek_id: int
    number: int
    status: GameweekStatus
    league_results: List[GameweekLeagueResult]
    
    class Config:
        from_attributes = True

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Leaderboard schemas
class LeaderboardEntry(BaseModel):
    user_id: int
    user_name: str
    team_name: str
    total_points: int
    rank: int
    
    class Config:
        from_attributes = True

class LeaderboardResponse(BaseModel):
    entries: List[LeaderboardEntry]
    total_users: int

# Captain Selection
class CaptainSelection(BaseModel):
    player_id: int

# Transfer Request
class TransferRequest(BaseModel):
    player_in_id: int
    player_out_id: int

# Audit Log
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    resource_type: str
    resource_id: Optional[int]
    details: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True 