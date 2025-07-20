from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Player, PlayerStats, User, PlayerStatus, PlayerPosition, Team, TeamPlayer
from schemas import PlayerResponse, PlayerCreate, PlayerUpdate, PlayerStatsResponse
from auth import get_current_active_user, get_current_user

router = APIRouter()

@router.get("/", response_model=List[PlayerResponse])
async def get_players(
    skip: int = 0,
    limit: int = 100,
    status: Optional[PlayerStatus] = Query(None),
    position: Optional[PlayerPosition] = Query(None),
    team: Optional[str] = Query(None),
    sort: Optional[str] = Query(None, description="Sort by: points, name, price"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all players with optional filtering and sorting."""
    query = db.query(Player)
    
    # Apply filters
    if status:
        query = query.filter(Player.status == status)
    if position:
        query = query.filter(Player.position == position)
    if team:
        query = query.filter(Player.team.ilike(f"%{team}%"))
    
    # Apply sorting
    if sort == "points":
        query = query.order_by(Player.total_points.desc())
    elif sort == "name":
        query = query.order_by(Player.name)
    elif sort == "price":
        query = query.order_by(Player.price.desc())
    
    players = query.offset(skip).limit(limit).all()
    return players

@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get player by ID."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    return player

@router.post("/", response_model=PlayerResponse)
async def create_player(
    player: PlayerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new player.
       param player: PlayerCreate - Player creation schema
       return: PlayerResponse - Created player details
    """
    existing_player = db.query(Player).filter(Player.name == player.name).first()
    if existing_player:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Player with this name already exists"
        )
    
    # Get user's default team (they must have one)
    user_team = db.query(Team).filter(Team.user_id == current_user.id).first()
    if not user_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must create a team first before creating players"
        )
    
    # Create the player 
    db_player = Player(
        name=player.name,
        position=player.position,
        team=user_team.name,  # Use the user's default team name
        price=player.price
    )
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    
    # Automatically add the player to the user's default team
    team_player = TeamPlayer(
        team_id=user_team.id,
        player_id=db_player.id,
        is_starter=True  # Default to starter
    )
    db.add(team_player)
    db.commit()
    db.refresh(team_player)
    
    return db_player

@router.put("/{player_id}", response_model=PlayerResponse)
async def update_player(
    player_id: int,
    player_update: PlayerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update player information ."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    # Update fields if provided
    if player_update.name is not None:
        player.name = player_update.name
    if player_update.position is not None:
        player.position = player_update.position
    if player_update.team is not None:
        # Check if team exists in teams table, if not create it
        team_exists = db.query(Team).filter(Team.name == player_update.team).first()
        if not team_exists:
            # Create a new team entry
            new_team = Team(
                name=player_update.team,
                user_id=current_user.id
            )
            db.add(new_team)
            db.commit()
            db.refresh(new_team)
        player.team = player_update.team
    if player_update.price is not None:
        player.price = player_update.price
    if player_update.status is not None:
        player.status = player_update.status
    
    db.commit()
    db.refresh(player)
    return player

@router.patch("/{player_id}/status")
async def update_player_status(
    player_id: int,
    player_status: PlayerStatus = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update player status."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    player.status = player_status
    db.commit()
    db.refresh(player)
    return {"message": f"Player status updated to {player_status.value}"}

@router.get("/{player_id}/history", response_model=List[PlayerStatsResponse])
async def get_player_history(
    player_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get player's performance history."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    stats = db.query(PlayerStats).filter(
        PlayerStats.player_id == player_id
    ).order_by(PlayerStats.created_at.desc()).limit(limit).all()
    
    return stats

@router.get("/{player_id}/stats", response_model=List[PlayerStatsResponse])
async def get_player_stats(
    player_id: int,
    gameweek: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get player statistics, optionally filtered by gameweek."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    query = db.query(PlayerStats).filter(PlayerStats.player_id == player_id)
    
    if gameweek:
        # Filter by gameweek if provided
        query = query.join(PlayerStats.fixture).filter(
            PlayerStats.fixture.has(gameweek_id=gameweek)
        )
    
    stats = query.all()
    return stats

@router.delete("/{player_id}")
async def delete_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete player"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    # First delete all TeamPlayer relationships for this player
    db.query(TeamPlayer).filter(TeamPlayer.player_id == player_id).delete()
    
    # Then delete the player
    db.delete(player)
    db.commit()
    return {"message": "Player deleted successfully"} 