from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import (
    User, Player, Gameweek, PlayerStats, Fixture,
    UserRole, GameweekStatus, PlayerPosition, PlayerStatus
)
from schemas import (
    PlayerResponse, PlayerCreate, UserResponse, 
    GameweekResponse, FixtureResponse, FixtureCreate,
    PlayerStatsCreate, PlayerStatsResponse
)
from auth import get_current_active_user
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["Admin"])

def require_admin(current_user: User = Depends(get_current_active_user)):
    """Ensure the current user is an admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Get all users in the system (admin only)"""
    return db.query(User).all()

@router.post("/players", response_model=PlayerResponse)
def create_player(
    player_data: PlayerCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Create a new player (admin only)
    Note: PlayerPosition is an enum with values like:
    GOALKEEPER= "goalkeeper"
    DEFENDER = "defender"
    MIDFIELDER = "midfielder"
    FORWARD = "forward"
    """
    
    # Check if player already exists
    existing = db.query(Player).filter(
        Player.name == player_data.name,
        Player.team == player_data.team
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Player already exists in this team"
        )
    
    player = Player(**player_data.dict())
    db.add(player)
    db.commit()
    db.refresh(player)
    
    return player

@router.get("/players", response_model=List[PlayerResponse])
def get_all_players(
    team: Optional[str] = None,
    position: Optional[PlayerPosition] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Get all players with optional filters (admin only)"""
    
    query = db.query(Player)
    
    if team:
        query = query.filter(Player.team == team)
    
    if position:
        query = query.filter(Player.position == position)
    
    return query.all()

@router.put("/players/{player_id}/price")
def update_player_price(
    player_id: int,
    new_price: float,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Update a player's price (admin only)"""
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    player.price = new_price
    db.commit()
    
    return {"message": f"Updated {player.name}'s price to £{new_price}m"}

@router.post("/gameweeks", response_model=GameweekResponse)
def create_gameweek(
    number: int,
    deadline: datetime,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Create a new gameweek (admin only)"""
    
    # Check if gameweek already exists
    existing = db.query(Gameweek).filter(Gameweek.number == number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gameweek {number} already exists"
        )
    
    gameweek = Gameweek(
        number=number,
        deadline=deadline,
        status=GameweekStatus.UPCOMING
    )
    db.add(gameweek)
    db.commit()
    db.refresh(gameweek)
    
    return gameweek

@router.put("/gameweeks/{gameweek_id}/status")
def update_gameweek_status(
    gameweek_id: int,
    status: GameweekStatus,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Update gameweek status (admin only)"""
    
    gameweek = db.query(Gameweek).filter(Gameweek.id == gameweek_id).first()
    if not gameweek:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gameweek not found"
        )
    
    gameweek.status = status
    db.commit()
    
    return {"message": f"Updated gameweek {gameweek.number} status to {status.value}"}

@router.post("/player-stats", response_model=PlayerStatsResponse)
def create_player_stats(
    stats_data: PlayerStatsCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Add player statistics for a gameweek (admin only)"""
    
    # Verify player exists
    player = db.query(Player).filter(Player.id == stats_data.player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    # Verify gameweek exists
    gameweek = db.query(Gameweek).filter(Gameweek.id == stats_data.gameweek_id).first()
    if not gameweek:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gameweek not found"
        )
    
    # Check if stats already exist for this player/gameweek
    existing = db.query(PlayerStats).filter(
        PlayerStats.player_id == stats_data.player_id,
        PlayerStats.gameweek_id == stats_data.gameweek_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stats already exist for this player/gameweek"
        )
    
    stats = PlayerStats(**stats_data.dict())
    db.add(stats)
    db.commit()
    db.refresh(stats)
    
    return stats

@router.post("/fixtures", response_model=FixtureResponse)
def create_fixture(
    fixture_data: FixtureCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Create a new fixture (admin only)"""
    
    # Verify gameweek exists
    gameweek = db.query(Gameweek).filter(Gameweek.id == fixture_data.gameweek_id).first()
    if not gameweek:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gameweek not found"
        )
    
    fixture = Fixture(**fixture_data.dict())
    db.add(fixture)
    db.commit()
    db.refresh(fixture)
    
    return fixture

@router.get("/fixtures", response_model=List[FixtureResponse])
def get_fixtures(
    gameweek_id: Optional[int] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Get all fixtures with optional gameweek filter (admin only)"""
    
    query = db.query(Fixture)
    
    if gameweek_id:
        query = query.filter(Fixture.gameweek_id == gameweek_id)
    
    return query.all()

@router.put("/fixtures/{fixture_id}/result")
def update_fixture_result(
    fixture_id: int,
    home_score: int,
    away_score: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Update fixture result (admin only)"""
    
    fixture = db.query(Fixture).filter(Fixture.id == fixture_id).first()
    if not fixture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixture not found"
        )
    
    fixture.home_score = home_score
    fixture.away_score = away_score
    db.commit()
    
    return {
        "message": f"Updated fixture result: {fixture.home_team} {home_score}-{away_score} {fixture.away_team}"
    }

@router.get("/system/stats")
def get_system_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Get system statistics (admin only)"""
    
    total_users = db.query(User).count()
    total_players = db.query(Player).count()
    total_gameweeks = db.query(Gameweek).count()
    
    # Count players by position
    from sqlalchemy import func
    position_counts = db.query(
        Player.position, 
        func.count(Player.id)
    ).group_by(Player.position).all()
    
    position_breakdown = {pos.value: count for pos, count in position_counts}
    
    return {
        "total_users": total_users,
        "total_players": total_players,
        "total_gameweeks": total_gameweeks,
        "position_breakdown": position_breakdown
    }
