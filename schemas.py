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
    team: str  # Team name (e.g., "Manchester United")
    price: float

class PlayerCreate(PlayerBase):
    shirt_number: Optional[int] = None

class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[PlayerPosition] = None
    team: Optional[str] = None
    price: Optional[float] = None
    status: Optional[PlayerStatus] = None
    shirt_number: Optional[int] = None

class PlayerResponse(PlayerBase):
    id: int
    total_points: int
    status: PlayerStatus
    created_at: datetime
    
    class Config:
        from_attributes = True

# Team schemas (Fantasy Teams)
class TeamBase(BaseModel):
    name: str

class TeamCreate(TeamBase):
    league_id: int  # Must specify which league the team is for

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    captain_id: Optional[int] = None
    vice_captain_id: Optional[int] = None

class TeamResponse(TeamBase):
    id: int
    user_id: int
    league_id: int
    captain_id: Optional[int]
    vice_captain_id: Optional[int]
    weekly_points: int = 0
    total_points: int = 0
    current_budget: float  # Remaining budget
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
    player_team: str
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
    # Basic settings
    budget: Optional[float] = 100.0
    max_players_per_team: Optional[int] = 3
    max_teams: Optional[int] = 20
    
    # Squad composition rules (configurable)
    max_goalkeepers: Optional[int] = 2
    max_defenders: Optional[int] = 5
    max_midfielders: Optional[int] = 5
    max_forwards: Optional[int] = 3
    total_squad_size: Optional[int] = 15
    
    # Transfer rules (configurable)
    free_transfers_per_gameweek: Optional[int] = 1
    transfer_penalty_points: Optional[int] = 4
    max_transfers_per_gameweek: Optional[int] = 5
    
    # Scoring system settings (configurable)
    points_per_goal_forward: Optional[int] = 4
    points_per_goal_midfielder: Optional[int] = 5
    points_per_goal_defender: Optional[int] = 6
    points_per_goal_goalkeeper: Optional[int] = 6
    points_per_assist: Optional[int] = 3
    points_per_clean_sheet: Optional[int] = 4
    points_per_yellow_card: Optional[int] = -1
    points_per_red_card: Optional[int] = -3
    points_per_own_goal: Optional[int] = -2
    points_per_penalty_save: Optional[int] = 5
    points_per_penalty_miss: Optional[int] = -2
    
    # Special features (configurable)
    allow_wildcards: Optional[bool] = True
    allow_bench_boost: Optional[bool] = True
    allow_triple_captain: Optional[bool] = True

class LeagueUpdate(BaseModel):
    name: Optional[str] = None
    is_private: Optional[bool] = None
    budget: Optional[float] = None
    max_players_per_team: Optional[int] = None
    max_teams: Optional[int] = None
    
    # Squad composition
    max_goalkeepers: Optional[int] = None
    max_defenders: Optional[int] = None
    max_midfielders: Optional[int] = None
    max_forwards: Optional[int] = None
    total_squad_size: Optional[int] = None
    
    # Transfer rules
    free_transfers_per_gameweek: Optional[int] = None
    transfer_penalty_points: Optional[int] = None
    max_transfers_per_gameweek: Optional[int] = None
    
    # Scoring system
    points_per_goal_forward: Optional[int] = None
    points_per_goal_midfielder: Optional[int] = None
    points_per_goal_defender: Optional[int] = None
    points_per_goal_goalkeeper: Optional[int] = None
    points_per_assist: Optional[int] = None
    points_per_clean_sheet: Optional[int] = None
    points_per_yellow_card: Optional[int] = None
    points_per_red_card: Optional[int] = None
    points_per_own_goal: Optional[int] = None
    points_per_penalty_save: Optional[int] = None
    points_per_penalty_miss: Optional[int] = None
    
    # Special features
    allow_wildcards: Optional[bool] = None
    allow_bench_boost: Optional[bool] = None
    allow_triple_captain: Optional[bool] = None

class LeagueResponse(LeagueBase):
    id: int
    code: str
    owner_id: int
    
    # All the configurable settings
    budget: float
    max_players_per_team: int
    max_teams: int
    
    # Squad composition rules
    max_goalkeepers: int
    max_defenders: int
    max_midfielders: int
    max_forwards: int
    total_squad_size: int
    
    # Transfer rules
    free_transfers_per_gameweek: int
    transfer_penalty_points: int
    max_transfers_per_gameweek: int
    
    # Scoring system settings
    points_per_goal_forward: int
    points_per_goal_midfielder: int
    points_per_goal_defender: int
    points_per_goal_goalkeeper: int
    points_per_assist: int
    points_per_clean_sheet: int
    points_per_yellow_card: int
    points_per_red_card: int
    points_per_own_goal: int
    points_per_penalty_save: int
    points_per_penalty_miss: int
    
    # Special features
    allow_wildcards: bool
    allow_bench_boost: bool
    allow_triple_captain: bool
    
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