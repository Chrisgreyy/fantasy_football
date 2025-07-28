from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Team, User, Player, TeamPlayer, Transfer, Gameweek, League, PlayerPosition
from schemas import TeamResponse, TeamCreate, TeamUpdate, PlayerResponse
from auth import get_current_active_user, check_user_owns_resource
from datetime import datetime
from sqlalchemy import and_

router = APIRouter()


@router.get("/", response_model=List[TeamResponse])
async def get_my_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all my fantasy teams across different leagues."""
    teams = db.query(Team).filter(Team.user_id == current_user.id).all()
    return teams

@router.post("/", response_model=TeamResponse)
async def create_team(
    team: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new fantasy team in a league."""
    
    # Verify league exists and user is a member
    league = db.query(League).filter(League.id == team.league_id).first()
    if not league:
        raise HTTPException(404, "League not found")
    
    # Check if user already has a team in this league
    existing_team = db.query(Team).filter(
        and_(Team.user_id == current_user.id, Team.league_id == team.league_id)
    ).first()
    if existing_team:
        raise HTTPException(400, "You already have a team in this league")
    
    db_team = Team(
        name=team.name,
        user_id=current_user.id,
        league_id=team.league_id,
        current_budget=league.budget  # Start with full league budget
    )
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team

@router.get("/{team_id}/squad")
async def get_my_squad(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get my current squad of up to 15 players
    
    This is what users actually want - a simple view of their squad
    """
    
    # Verify user owns this team
    team = db.query(Team).filter(
        and_(Team.id == team_id, Team.user_id == current_user.id)
    ).first()
    
    if not team:
        raise HTTPException(404, "Team not found or you don't own it")
    
    # Get current squad (players where left_at is NULL)
    current_squad = db.query(TeamPlayer).join(Player).filter(
        and_(
            TeamPlayer.team_id == team_id,
            TeamPlayer.left_at.is_(None)
        )
    ).all()
    
    # Group by position for easy viewing
    squad_summary = {
        "team_name": team.name,
        "league": team.league.name,
        "current_budget": team.current_budget,
        "squad_count": len(current_squad),
        "goalkeepers": [],
        "defenders": [],
        "midfielders": [],
        "forwards": [],
        "total_value": 0
    }
    
    for team_player in current_squad:
        player = team_player.player
        player_info = {
            "id": player.id,
            "name": player.name,
            "team": player.team,
            "position": player.position.value,
            "price": player.price,
            "total_points": player.total_points,
            "purchase_price": team_player.purchase_price,
            "joined_at": team_player.joined_at
        }
        
        squad_summary["total_value"] += player.price
        
        if player.position == PlayerPosition.GOALKEEPER:
            squad_summary["goalkeepers"].append(player_info)
        elif player.position == PlayerPosition.DEFENDER:
            squad_summary["defenders"].append(player_info)
        elif player.position == PlayerPosition.MIDFIELDER:
            squad_summary["midfielders"].append(player_info)
        elif player.position == PlayerPosition.FORWARD:
            squad_summary["forwards"].append(player_info)
    
    return squad_summary

@router.put("/{team_id}/squad")
async def select_squad(
    team_id: int,
    player_ids: List[int],  # Simple list of 15 player IDs
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Select your squad of 15 players (completely replace current squad)
    
    This is the kind of simple endpoint users actually want:
    - Send 15 player IDs
    - API handles all the complexity (validation, budget, position rules, etc.)
    """
    
    # Verify user owns this team
    team = db.query(Team).filter(
        and_(Team.id == team_id, Team.user_id == current_user.id)
    ).first()
    
    if not team:
        raise HTTPException(404, "Team not found")
    
    if len(player_ids) != 15:
        raise HTTPException(400, "Must select exactly 15 players")
    
    if len(set(player_ids)) != 15:
        raise HTTPException(400, "Cannot select duplicate players")
    
    # Get the selected players
    selected_players = db.query(Player).filter(Player.id.in_(player_ids)).all()
    
    if len(selected_players) != 15:
        raise HTTPException(400, "Some player IDs are invalid")
    
    # Validate squad composition (2 GK, 5 DEF, 5 MID, 3 FWD)
    position_counts = {}
    total_cost = 0
    team_counts = {}
    
    for player in selected_players:
        # Count positions
        pos = player.position.value
        position_counts[pos] = position_counts.get(pos, 0) + 1
        
        # Calculate total cost
        total_cost += player.price
        
        # Count players per real team
        team_counts[player.team] = team_counts.get(player.team, 0) + 1
    
    # Validate position requirements
    if position_counts.get("goalkeeper", 0) != 2:
        raise HTTPException(400, "Must select exactly 2 goalkeepers")
    if position_counts.get("defender", 0) != 5:
        raise HTTPException(400, "Must select exactly 5 defenders")
    if position_counts.get("midfielder", 0) != 5:
        raise HTTPException(400, "Must select exactly 5 midfielders")
    if position_counts.get("forward", 0) != 3:
        raise HTTPException(400, "Must select exactly 3 forwards")
    
    # Check budget
    league = team.league
    if total_cost > league.budget:
        raise HTTPException(400, f"Squad costs £{total_cost}m, but budget is £{league.budget}m")
    
    # Check max players per real team
    for team, count in team_counts.items():
        if count > league.max_players_per_team:
            raise HTTPException(400, f"Cannot select more than {league.max_players_per_team} players from {team}")
    
    # All validations passed - update the squad
    # First, mark all current players as left
    db.query(TeamPlayer).filter(
        and_(
            TeamPlayer.team_id == team_id,
            TeamPlayer.left_at.is_(None)
        )
    ).update({"left_at": datetime.utcnow()})
    
    # Add new players
    for player in selected_players:
        new_team_player = TeamPlayer(
            team_id=team_id,
            player_id=player.id,
            purchase_price=player.price,
            joined_at=datetime.utcnow()
        )
        db.add(new_team_player)
    
    # Update team budget
    team.current_budget = league.budget - total_cost
    
    db.commit()
    
    return {
        "message": "Squad updated successfully",
        "total_cost": total_cost,
        "remaining_budget": team.current_budget,
        "squad_count": 15
    }
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
    
@router.post("/{team_id}/transfers")
async def make_transfer(
    team_id: int,
    player_out_id: int,
    player_in_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Make a transfer - swap one player for another
    
    This is what users actually want to do - simple player swap
    API handles all the complexity: budget, transfer costs, position validation
    """
    
    # Verify user owns this team
    team = db.query(Team).filter(
        and_(Team.id == team_id, Team.user_id == current_user.id)
    ).first()
    
    if not team:
        raise HTTPException(404, "Team not found")
    
    # Get league rules
    league = team.league
    
    # Get current gameweek
    current_gameweek = db.query(Gameweek).filter(
        Gameweek.status.in_(["upcoming", "active"])
    ).first()
    
    if not current_gameweek:
        raise HTTPException(400, "No active gameweek for transfers")
    
    # Check deadline hasn't passed
    if datetime.utcnow() > current_gameweek.deadline:
        raise HTTPException(400, "Transfer deadline has passed")
    
    # Verify player_out is in squad
    player_out_in_squad = db.query(TeamPlayer).filter(
        and_(
            TeamPlayer.team_id == team_id,
            TeamPlayer.player_id == player_out_id,
            TeamPlayer.left_at.is_(None)
        )
    ).first()
    
    if not player_out_in_squad:
        raise HTTPException(400, "Player to transfer out is not in your squad")
    
    # Get player objects
    player_out = db.query(Player).filter(Player.id == player_out_id).first()
    player_in = db.query(Player).filter(Player.id == player_in_id).first()
    
    if not player_out or not player_in:
        raise HTTPException(400, "Invalid player IDs")
    
    # Check positions match (can only transfer like for like)
    if player_out.position != player_in.position:
        raise HTTPException(400, f"Can only transfer {player_out.position.value} for {player_out.position.value}")
    
    # Check budget
    price_difference = player_in.price - player_out.price
    if team.current_budget < price_difference:
        raise HTTPException(400, f"Insufficient budget. Need £{price_difference}m more")
    
    # Count transfers already made this gameweek
    transfers_this_gameweek = db.query(Transfer).filter(
        and_(
            Transfer.team_id == team_id,
            Transfer.gameweek_id == current_gameweek.id
        )
    ).count()
    
    # Check if exceeds max transfers per gameweek
    if transfers_this_gameweek >= league.max_transfers_per_gameweek:
        raise HTTPException(400, f"Maximum {league.max_transfers_per_gameweek} transfers per gameweek exceeded")
    
    # Calculate transfer cost based on league rules
    transfer_number = transfers_this_gameweek + 1
    is_free = transfer_number <= league.free_transfers_per_gameweek
    points_cost = 0 if is_free else league.transfer_penalty_points
    
    # Check if player_in is already in team (shouldn't happen but safety check)
    existing_player_in = db.query(TeamPlayer).filter(
        and_(
            TeamPlayer.team_id == team_id,
            TeamPlayer.player_id == player_in_id,
            TeamPlayer.left_at.is_(None)
        )
    ).first()
    
    if existing_player_in:
        raise HTTPException(400, "Player is already in your squad")
    
    # Execute the transfer
    # 1. Mark old player as left
    player_out_in_squad.left_at = datetime.utcnow()
    
    # 2. Add new player
    new_team_player = TeamPlayer(
        team_id=team_id,
        player_id=player_in_id,
        purchase_price=player_in.price,
        joined_at=datetime.utcnow()
    )
    db.add(new_team_player)
    
    # 3. Update budget
    team.current_budget -= price_difference
    
    # 4. Record the transfer with detailed information
    transfer = Transfer(
        team_id=team_id,
        gameweek_id=current_gameweek.id,
        player_out_id=player_out_id,
        player_in_id=player_in_id,
        points_cost=points_cost,
        money_out=player_out.price,
        money_in=player_in.price,
        money_change=price_difference,
        is_free_transfer=is_free,
        transfer_number_in_gameweek=transfer_number
    )
    db.add(transfer)
    
    # 5. Deduct points from team if applicable
    if points_cost > 0:
        team.total_points -= points_cost
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Transfer completed: {player_out.name} → {player_in.name}",
        "transfer_details": {
            "player_out": {
                "id": player_out.id,
                "name": player_out.name,
                "position": player_out.position.value,
                "price": player_out.price
            },
            "player_in": {
                "id": player_in.id,
                "name": player_in.name,
                "position": player_in.position.value,
                "price": player_in.price
            },
            "cost_breakdown": {
                "money_change": price_difference,
                "points_cost": points_cost,
                "is_free_transfer": is_free,
                "transfer_number": transfer_number,
                "remaining_free_transfers": max(0, league.free_transfers_per_gameweek - transfer_number)
            },
            "new_budget": team.current_budget,
            "gameweek": current_gameweek.number
        }
    }

@router.get("/{team_id}/transfers")
async def get_transfer_history(
    team_id: int,
    gameweek_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get transfer history for this team"""
    
    # Verify user owns this team
    team = db.query(Team).filter(
        and_(Team.id == team_id, Team.user_id == current_user.id)
    ).first()
    
    if not team:
        raise HTTPException(404, "Team not found")
    
    query = db.query(Transfer).filter(Transfer.team_id == team_id)
    
    if gameweek_id:
        query = query.filter(Transfer.gameweek_id == gameweek_id)
    
    transfers = query.order_by(Transfer.created_at.desc()).all()
    
    transfer_history = []
    for transfer in transfers:
        transfer_history.append({
            "id": transfer.id,
            "gameweek": transfer.gameweek.number,
            "player_out": {
                "name": transfer.player_out.name,
                "position": transfer.player_out.position.value,
                "price": transfer.money_out
            },
            "player_in": {
                "name": transfer.player_in.name,
                "position": transfer.player_in.position.value,
                "price": transfer.money_in
            },
            "money_change": transfer.money_change,
            "points_cost": transfer.points_cost,
            "is_free_transfer": transfer.is_free_transfer,
            "transfer_number": transfer.transfer_number_in_gameweek,
            "date": transfer.created_at
        })
    
    return {
        "team_name": team.name,
        "total_transfers": len(transfer_history),
        "transfers": transfer_history
    }

@router.get("/{team_id}/transfer-info")
async def get_transfer_info(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current transfer information for this gameweek"""
    
    # Verify user owns this team
    team = db.query(Team).filter(
        and_(Team.id == team_id, Team.user_id == current_user.id)
    ).first()
    
    if not team:
        raise HTTPException(404, "Team not found")
    
    # Get current gameweek
    current_gameweek = db.query(Gameweek).filter(
        Gameweek.status.in_(["upcoming", "active"])
    ).first()
    
    if not current_gameweek:
        return {
            "message": "No active gameweek",
            "transfers_available": 0,
            "deadline": None
        }
    
    # Count transfers made this gameweek
    transfers_made = db.query(Transfer).filter(
        and_(
            Transfer.team_id == team_id,
            Transfer.gameweek_id == current_gameweek.id
        )
    ).count()
    
    league = team.league
    free_transfers_remaining = max(0, league.free_transfers_per_gameweek - transfers_made)
    total_transfers_remaining = league.max_transfers_per_gameweek - transfers_made
    
    return {
        "gameweek": current_gameweek.number,
        "deadline": current_gameweek.deadline,
        "transfers_made": transfers_made,
        "free_transfers_remaining": free_transfers_remaining,
        "total_transfers_remaining": total_transfers_remaining,
        "next_transfer_cost": 0 if free_transfers_remaining > 0 else league.transfer_penalty_points,
        "current_budget": team.current_budget,
        "league_rules": {
            "free_transfers_per_gameweek": league.free_transfers_per_gameweek,
            "transfer_penalty_points": league.transfer_penalty_points,
            "max_transfers_per_gameweek": league.max_transfers_per_gameweek
        }
    }

@router.put("/{team_id}/captain")
async def set_captain(
    team_id: int,
    captain_id: int,
    vice_captain_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Set captain and vice-captain for the team"""
    
    # Verify user owns this team
    team = db.query(Team).filter(
        and_(Team.id == team_id, Team.user_id == current_user.id)
    ).first()
    
    if not team:
        raise HTTPException(404, "Team not found")
    
    # Verify both players are in the squad
    squad_player_ids = [
        tp.player_id for tp in db.query(TeamPlayer).filter(
            and_(
                TeamPlayer.team_id == team_id,
                TeamPlayer.left_at.is_(None)
            )
        ).all()
    ]
    
    if captain_id not in squad_player_ids:
        raise HTTPException(400, "Captain must be in your squad")
    if vice_captain_id not in squad_player_ids:
        raise HTTPException(400, "Vice-captain must be in your squad")
    if captain_id == vice_captain_id:
        raise HTTPException(400, "Captain and vice-captain must be different players")
    
    # Update team
    team.captain_id = captain_id
    team.vice_captain_id = vice_captain_id
    
    db.commit()
    
    captain = db.query(Player).filter(Player.id == captain_id).first()
    vice_captain = db.query(Player).filter(Player.id == vice_captain_id).first()
    
    return {
        "message": "Captain and vice-captain updated",
        "captain": captain.name,
        "vice_captain": vice_captain.name
    } 