from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Player, PlayerStats, User, PlayerStatus, PlayerPosition, UserRole
from schemas import PlayerResponse, PlayerCreate, PlayerUpdate, PlayerStatsResponse
from auth import get_current_active_user

router = APIRouter()

def require_admin(current_user: User = Depends(get_current_active_user)):
    """Ensure current user is an admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# =============================================================================
# PUBLIC ENDPOINTS - What users actually need to browse players
# =============================================================================

@router.get("/", response_model=List[PlayerResponse])
async def get_players(
    skip: int = 0,
    limit: int = 100,
    status: Optional[PlayerStatus] = Query(None, description="Filter by player status"),
    position: Optional[PlayerPosition] = Query(None, description="Filter by position"),
    real_team: Optional[str] = Query(None, description="Filter by real team"),
    sort: Optional[str] = Query("points", description="Sort by: points, name, price"),
    search: Optional[str] = Query(None, description="Search by player name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all real players available for fantasy teams
    
    This is what users need - browse all available players to pick for their fantasy team
    """
    query = db.query(Player)
    
    # Apply filters
    if status:
        query = query.filter(Player.status == status)
    if position:
        query = query.filter(Player.position == position)
    if real_team:
        query = query.filter(Player.real_team.ilike(f"%{real_team}%"))
    if search:
        query = query.filter(Player.name.ilike(f"%{search}%"))
    
    # Apply sorting
    if sort == "points":
        query = query.order_by(Player.total_points.desc())
    elif sort == "name":
        query = query.order_by(Player.name)
    elif sort == "price_desc":
        query = query.order_by(Player.price.desc())
    elif sort == "price_asc":
        query = query.order_by(Player.price.asc())
    else:
        query = query.order_by(Player.total_points.desc())  # Default sort by points
    
    players = query.offset(skip).limit(limit).all()
    return players

@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information about a specific player"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    return player

@router.get("/{player_id}/stats")
async def get_player_performance_history(
    player_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a player's recent performance history"""
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(404, "Player not found")
    
    # Get recent performances
    recent_stats = db.query(PlayerStats).filter(
        PlayerStats.player_id == player_id
    ).order_by(PlayerStats.created_at.desc()).limit(limit).all()
    
    performance_history = []
    for stat in recent_stats:
        performance_history.append({
            "fixture_id": stat.fixture_id,
            "opponent": f"{stat.fixture.home_team} vs {stat.fixture.away_team}",
            "gameweek": stat.fixture.gameweek.number,
            "minutes_played": stat.minutes_played,
            "goals": stat.goals,
            "assists": stat.assists,
            "fantasy_points": stat.fantasy_points,
            "yellow_cards": stat.yellow_cards,
            "red_cards": stat.red_cards,
            "date": stat.fixture.kickoff_time
        })
    
    return {
        "player_name": player.name,
        "real_team": player.real_team,
        "position": player.position.value,
        "season_total_points": player.total_points,
        "recent_performances": performance_history
    }

# =============================================================================
# ADMIN-ONLY ENDPOINTS - For managing the real player database
# =============================================================================

@router.post("/", response_model=PlayerResponse)
async def create_player(
    player: PlayerCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Create a new real player (ADMIN ONLY)
    
    This is how real players like Salah, Rashford get added to the system
    """
    
    # Check if player already exists
    existing_player = db.query(Player).filter(Player.name == player.name).first()
    if existing_player:
        raise HTTPException(400, "Player with this name already exists")
    
    db_player = Player(
        name=player.name,
        position=player.position,
        real_team=player.real_team,
        price=player.price,
        shirt_number=player.shirt_number
    )
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    
    return db_player

@router.put("/{player_id}", response_model=PlayerResponse)
async def update_player(
    player_id: int,
    player_update: PlayerUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Update player information (ADMIN ONLY)"""
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(404, "Player not found")
    
    # Update fields if provided
    if player_update.name is not None:
        player.name = player_update.name
    if player_update.position is not None:
        player.position = player_update.position
    if player_update.real_team is not None:
        player.real_team = player_update.real_team
    if player_update.price is not None:
        player.price = player_update.price
    if player_update.status is not None:
        player.status = player_update.status
    if player_update.shirt_number is not None:
        player.shirt_number = player_update.shirt_number
    
    db.commit()
    db.refresh(player)
    return player

@router.patch("/{player_id}/price")
async def update_player_price(
    player_id: int,
    new_price: float,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Update player price (ADMIN ONLY)"""
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(404, "Player not found")
    
    old_price = player.price
    player.price = new_price
    db.commit()
    
    return {
        "message": f"Updated {player.name} price from £{old_price}m to £{new_price}m",
        "player": player.name,
        "old_price": old_price,
        "new_price": new_price
    } 