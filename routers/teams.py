from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Team, User, Player, TeamPlayer, Transfer, Gameweek
from schemas import TeamResponse, TeamCreate, TeamUpdate, TeamPlayerResponse, TeamPlayerDetailResponse, CaptainSelection, TransferRequest, TransferResponse
from auth import get_current_active_user, check_user_owns_resource

router = APIRouter()

@router.get("/", response_model=List[TeamResponse])
async def get_user_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's team (only one per user)."""
    teams = db.query(Team).filter(Team.user_id == current_user.id).all()
    return teams

@router.post("/", response_model=TeamResponse)
async def create_team(
    team: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new team for the current user. A user can only have one team."""
    # Check if user already has a team
    existing_team = db.query(Team).filter(Team.user_id == current_user.id).first()
    if existing_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a team. Only one team per user is allowed."
        )
    
    db_team = Team(
        name=team.name,
        user_id=current_user.id
    )
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team

@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get team by ID."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    check_user_owns_resource(current_user, team.user_id)
    return team

@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    team_update: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update team information."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    check_user_owns_resource(current_user, team.user_id)
    
    # Update fields if provided
    if team_update.name is not None:
        team.name = team_update.name
    if team_update.captain_id is not None:
        # Verify captain is in the team
        captain_in_team = db.query(TeamPlayer).filter(
            TeamPlayer.team_id == team_id,
            TeamPlayer.player_id == team_update.captain_id
        ).first()
        if not captain_in_team:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Captain must be a player in the team"
            )
        team.captain_id = team_update.captain_id
    
    db.commit()
    db.refresh(team)
    return team

@router.get("/{team_id}/players", response_model=List[TeamPlayerDetailResponse])
async def get_team_players(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all players in a team and their details. (player name, position, price, status, team name, etc)"""
    # Check if team exists and user has access
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    check_user_owns_resource(current_user, team.user_id)
    
    # Get team players with detailed information using joins
    team_players_query = db.query(
        TeamPlayer.id,
        TeamPlayer.team_id,
        TeamPlayer.player_id,
        TeamPlayer.is_starter,
        TeamPlayer.created_at,
        Player.name.label('player_name'),
        Player.position.label('player_position'),
        Player.team.label('player_real_team'),
        Player.price.label('player_price'),
        Player.total_points.label('player_total_points'),
        Player.status.label('player_status'),
        Team.name.label('fantasy_team_name'),
        Team.captain_id
    ).join(
        Player, TeamPlayer.player_id == Player.id
    ).join(
        Team, TeamPlayer.team_id == Team.id
    ).filter(
        TeamPlayer.team_id == team_id
    ).all()
    
    # Convert to response format
    team_players_response = []
    for tp in team_players_query:
        team_players_response.append(TeamPlayerDetailResponse(
            id=tp.id,
            team_id=tp.team_id,
            player_id=tp.player_id,
            is_starter=tp.is_starter,
            created_at=tp.created_at,
            player_name=tp.player_name,
            player_position=tp.player_position,
            player_real_team=tp.player_real_team,
            player_price=tp.player_price,
            player_total_points=tp.player_total_points,
            player_status=tp.player_status,
            fantasy_team_name=tp.fantasy_team_name,
            is_captain=(tp.captain_id == tp.player_id)
        ))
    
    return team_players_response

@router.post("/{team_id}/players")
async def add_player_to_team(
    team_id: int,
    player_id: int,
    is_starter: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a player to the team."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    check_user_owns_resource(current_user, team.user_id)
    
    # Check if player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    # Check if player is already in the team
    existing_team_player = db.query(TeamPlayer).filter(
        TeamPlayer.team_id == team_id,
        TeamPlayer.player_id == player_id
    ).first()
    if existing_team_player:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Player is already in the team"
        )
    
    # Check team size limit (15 players max)
    team_count = db.query(TeamPlayer).filter(TeamPlayer.team_id == team_id).count()
    if team_count >= 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team is full (maximum 15 players)"
        )
    
    # Add player to team
    team_player = TeamPlayer(
        team_id=team_id,
        player_id=player_id,
        is_starter=is_starter
    )
    db.add(team_player)
    db.commit()
    db.refresh(team_player)
    
    return {"message": "Player added to team successfully"}

@router.delete("/{team_id}/players/{player_id}")
async def remove_player_from_team(
    team_id: int,
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a player from the team."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    check_user_owns_resource(current_user, team.user_id)
    
    team_player = db.query(TeamPlayer).filter(
        TeamPlayer.team_id == team_id,
        TeamPlayer.player_id == player_id
    ).first()
    if not team_player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found in team"
        )
    
    # Remove captain if this player is the captain
    if team.captain_id == player_id:
        team.captain_id = None
        db.commit()
    
    db.delete(team_player)
    db.commit()
    
    return {"message": "Player removed from team successfully"}

@router.put("/{team_id}/captain")
async def set_team_captain(
    team_id: int,
    captain_selection: CaptainSelection,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Set team captain."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    check_user_owns_resource(current_user, team.user_id)
    
    # Verify captain is in the team
    captain_in_team = db.query(TeamPlayer).filter(
        TeamPlayer.team_id == team_id,
        TeamPlayer.player_id == captain_selection.player_id
    ).first()
    if not captain_in_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Captain must be a player in the team"
        )
    
    team.captain_id = captain_selection.player_id
    db.commit()
    db.refresh(team)
    
    return {"message": "Team captain updated successfully"}

@router.post("/{team_id}/transfers", response_model=TransferResponse)
async def make_transfer(
    team_id: int,
    transfer_request: TransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Make a player transfer."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    check_user_owns_resource(current_user, team.user_id)
    
    # Check if player_out is in the team
    player_out_in_team = db.query(TeamPlayer).filter(
        TeamPlayer.team_id == team_id,
        TeamPlayer.player_id == transfer_request.player_out_id
    ).first()
    if not player_out_in_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Player to transfer out is not in the team"
        )
    
    # Check if player_in exists and is available
    player_in = db.query(Player).filter(Player.id == transfer_request.player_in_id).first()
    if not player_in:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player to transfer in not found"
        )
    
    # Check if player_in is already in the team
    player_in_team = db.query(TeamPlayer).filter(
        TeamPlayer.team_id == team_id,
        TeamPlayer.player_id == transfer_request.player_in_id
    ).first()
    if player_in_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Player to transfer in is already in the team"
        )
    
    # Get current gameweek
    current_gameweek = db.query(Gameweek).filter(Gameweek.status == "active").first()
    if not current_gameweek:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active gameweek found"
        )
    
    # Calculate transfer cost (simplified)
    player_out = db.query(Player).filter(Player.id == transfer_request.player_out_id).first()
    transfer_cost = player_in.price - player_out.price
    
    # Check if user has enough budget
    if current_user.budget < transfer_cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient budget for transfer"
        )
    
    # Perform the transfer
    # Remove old player
    db.delete(player_out_in_team)
    
    # Add new player
    new_team_player = TeamPlayer(
        team_id=team_id,
        player_id=transfer_request.player_in_id,
        is_starter=player_out_in_team.is_starter
    )
    db.add(new_team_player)
    
    # Update user budget
    current_user.budget -= transfer_cost
    
    # Record transfer
    transfer = Transfer(
        team_id=team_id,
        player_in_id=transfer_request.player_in_id,
        player_out_id=transfer_request.player_out_id,
        gameweek_id=current_gameweek.id,
        cost=transfer_cost
    )
    db.add(transfer)
    
    db.commit()
    db.refresh(transfer)
    
    return transfer

@router.delete("/{team_id}")
async def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a team."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    check_user_owns_resource(current_user, team.user_id)
    
    db.delete(team)
    db.commit()
    
    return {"message": "Team deleted successfully"} 