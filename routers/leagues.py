from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
import random
import string
from database import get_db
from models import League, User, LeagueMembership, Team, UserRole
from schemas import LeagueResponse, LeagueCreate, LeagueUpdate, LeagueMembershipCreate, LeagueMembershipResponse, DetailedLeagueMembershipResponse, LeaderboardResponse, LeaderboardEntry
from auth import get_current_active_user, get_current_admin_user, check_user_owns_resource

router = APIRouter()

def generate_league_code(length: int = 6) -> str:
    """Generate a random league code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@router.get("/", response_model=List[LeagueResponse])
async def get_user_leagues(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get leagues the current user is a member of or all leagues if admin."""
    if current_user.role == UserRole.ADMIN:
        # Admins can see all leagues
        return db.query(League).all()
    
    # Regular users can only see leagues they're members of
    leagues = db.query(League).join(LeagueMembership).filter(
        LeagueMembership.user_id == current_user.id
    ).all()
    return leagues

@router.post("/", response_model=LeagueResponse)
async def create_league(
    league: LeagueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new league. The creator becomes the league owner."""
    # Generate unique league code
    while True:
        code = generate_league_code()
        existing_league = db.query(League).filter(League.code == code).first()
        if not existing_league:
            break
    
    db_league = League(
        name=league.name,
        code=code,
        owner_id=current_user.id,
        is_private=league.is_private,
        
        # Basic settings
        budget=league.budget,
        max_players_per_team=league.max_players_per_team,
        max_teams=league.max_teams,
        
        # Squad composition rules
        max_goalkeepers=league.max_goalkeepers,
        max_defenders=league.max_defenders,
        max_midfielders=league.max_midfielders,
        max_forwards=league.max_forwards,
        total_squad_size=league.total_squad_size,
        
        # Transfer rules
        free_transfers_per_gameweek=league.free_transfers_per_gameweek,
        transfer_penalty_points=league.transfer_penalty_points,
        max_transfers_per_gameweek=league.max_transfers_per_gameweek,
        
        # Scoring system
        points_per_goal_forward=league.points_per_goal_forward,
        points_per_goal_midfielder=league.points_per_goal_midfielder,
        points_per_goal_defender=league.points_per_goal_defender,
        points_per_goal_goalkeeper=league.points_per_goal_goalkeeper,
        points_per_assist=league.points_per_assist,
        points_per_clean_sheet=league.points_per_clean_sheet,
        points_per_yellow_card=league.points_per_yellow_card,
        points_per_red_card=league.points_per_red_card,
        points_per_own_goal=league.points_per_own_goal,
        points_per_penalty_save=league.points_per_penalty_save,
        points_per_penalty_miss=league.points_per_penalty_miss,
        
        # Special features
        allow_wildcards=league.allow_wildcards,
        allow_bench_boost=league.allow_bench_boost,
        allow_triple_captain=league.allow_triple_captain
    )
    db.add(db_league)
    db.commit()
    db.refresh(db_league)
    
    # Automatically add creator to the league
    membership = LeagueMembership(
        league_id=db_league.id,
        user_id=current_user.id
    )
    db.add(membership)
    db.commit()
    
    return db_league

@router.get("/{league_id}", response_model=LeagueResponse)
async def get_league(
    league_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get league by ID."""
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    # Admins have access to all leagues
    if current_user.role == UserRole.ADMIN:
        return league
    
    # Check if user is a member of the league
    membership = db.query(LeagueMembership).filter(
        LeagueMembership.league_id == league_id,
        LeagueMembership.user_id == current_user.id
    ).first()
    
    if not membership and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this league"
        )
    
    return league

@router.put("/{league_id}", response_model=LeagueResponse)
async def update_league(
    league_id: int,
    league_update: LeagueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update league settings (league owner or admin only)."""
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )

    # Check if user is league owner or admin
    if league.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only league owner or admin can update league settings"
        )
    
    # Update all configurable fields if provided
    if league_update.name is not None:
        league.name = league_update.name
    if league_update.is_private is not None:
        league.is_private = league_update.is_private
    if league_update.budget is not None:
        league.budget = league_update.budget
    if league_update.max_players_per_team is not None:
        league.max_players_per_team = league_update.max_players_per_team
    if league_update.max_teams is not None:
        league.max_teams = league_update.max_teams
        
    # Squad composition rules
    if league_update.max_goalkeepers is not None:
        league.max_goalkeepers = league_update.max_goalkeepers
    if league_update.max_defenders is not None:
        league.max_defenders = league_update.max_defenders
    if league_update.max_midfielders is not None:
        league.max_midfielders = league_update.max_midfielders
    if league_update.max_forwards is not None:
        league.max_forwards = league_update.max_forwards
    if league_update.total_squad_size is not None:
        league.total_squad_size = league_update.total_squad_size
        
    # Transfer rules
    if league_update.free_transfers_per_gameweek is not None:
        league.free_transfers_per_gameweek = league_update.free_transfers_per_gameweek
    if league_update.transfer_penalty_points is not None:
        league.transfer_penalty_points = league_update.transfer_penalty_points
    if league_update.max_transfers_per_gameweek is not None:
        league.max_transfers_per_gameweek = league_update.max_transfers_per_gameweek
        
    # Scoring system
    if league_update.points_per_goal_forward is not None:
        league.points_per_goal_forward = league_update.points_per_goal_forward
    if league_update.points_per_goal_midfielder is not None:
        league.points_per_goal_midfielder = league_update.points_per_goal_midfielder
    if league_update.points_per_goal_defender is not None:
        league.points_per_goal_defender = league_update.points_per_goal_defender
    if league_update.points_per_goal_goalkeeper is not None:
        league.points_per_goal_goalkeeper = league_update.points_per_goal_goalkeeper
    if league_update.points_per_assist is not None:
        league.points_per_assist = league_update.points_per_assist
    if league_update.points_per_clean_sheet is not None:
        league.points_per_clean_sheet = league_update.points_per_clean_sheet
    if league_update.points_per_yellow_card is not None:
        league.points_per_yellow_card = league_update.points_per_yellow_card
    if league_update.points_per_red_card is not None:
        league.points_per_red_card = league_update.points_per_red_card
    if league_update.points_per_own_goal is not None:
        league.points_per_own_goal = league_update.points_per_own_goal
    if league_update.points_per_penalty_save is not None:
        league.points_per_penalty_save = league_update.points_per_penalty_save
    if league_update.points_per_penalty_miss is not None:
        league.points_per_penalty_miss = league_update.points_per_penalty_miss
        
    # Special features
    if league_update.allow_wildcards is not None:
        league.allow_wildcards = league_update.allow_wildcards
    if league_update.allow_bench_boost is not None:
        league.allow_bench_boost = league_update.allow_bench_boost
    if league_update.allow_triple_captain is not None:
        league.allow_triple_captain = league_update.allow_triple_captain
    
    db.commit()
    db.refresh(league)
    return league

@router.post("/{league_id}/join", response_model=LeagueMembershipResponse)
async def join_league(
    league_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Join a league by ID."""
    # Check if user has a team first
    user_team = db.query(Team).filter(Team.user_id == current_user.id).first()
    if not user_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must create a team first before joining a league"
        )
    
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    # Check if user is already a member
    existing_membership = db.query(LeagueMembership).filter(
        LeagueMembership.league_id == league_id,
        LeagueMembership.user_id == current_user.id
    ).first()
    
    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a member of this league"
        )
    
    # Create membership
    membership = LeagueMembership(
        league_id=league_id,
        user_id=current_user.id
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    
    return membership

@router.post("/join", response_model=LeagueMembershipResponse)
async def join_league_by_code(
    join_request: LeagueMembershipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Join a league by code."""
    # Check if user has a team first
    user_team = db.query(Team).filter(Team.user_id == current_user.id).first()
    if not user_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must create a team first before joining a league"
        )
    
    league = db.query(League).filter(League.code == join_request.league_code).first()
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    # Check if user is already a member
    existing_membership = db.query(LeagueMembership).filter(
        LeagueMembership.league_id == league.id,
        LeagueMembership.user_id == current_user.id
    ).first()
    
    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a member of this league"
        )
    
    # Create membership
    membership = LeagueMembership(
        league_id=league.id,
        user_id=current_user.id
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    
    return membership

@router.get("/{league_id}/leaderboard", response_model=LeaderboardResponse)
async def get_league_leaderboard(
    league_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get league leaderboard."""
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    # Check if user is a member of the league
    membership = db.query(LeagueMembership).filter(
        LeagueMembership.league_id == league_id,
        LeagueMembership.user_id == current_user.id
    ).first()
    
    if not membership and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this league"
        )
    
    # Get leaderboard data
    leaderboard_query = db.query(
        User.id.label('user_id'),
        User.name.label('user_name'),
        Team.name.label('team_name'),
        User.total_points.label('total_points')
    ).join(
        LeagueMembership, LeagueMembership.user_id == User.id
    ).join(
        Team, Team.user_id == User.id
    ).filter(
        LeagueMembership.league_id == league_id
    ).order_by(
        desc(User.total_points)
    )
    
    results = leaderboard_query.all()
    
    # Add rankings
    entries = []
    for rank, result in enumerate(results, 1):
        entries.append(LeaderboardEntry(
            user_id=result.user_id,
            user_name=result.user_name,
            team_name=result.team_name,
            total_points=result.total_points,
            rank=rank
        ))
    
    return LeaderboardResponse(
        entries=entries,
        total_users=len(entries)
    )

@router.get("/{league_id}/members", response_model=List[DetailedLeagueMembershipResponse])
async def get_league_members(
    league_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed league member information."""
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    # Check if user is a member of the league
    membership = db.query(LeagueMembership).filter(
        LeagueMembership.league_id == league_id,
        LeagueMembership.user_id == current_user.id
    ).first()
    
    if not membership and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this league"
        )
    
    # Get detailed member information with user and team data
    members_query = db.query(
        LeagueMembership.id,
        LeagueMembership.user_id,
        LeagueMembership.joined_at,
        User.name.label('user_name'),
        User.email.label('user_email'),
        User.total_points,
        User.budget,
        Team.id.label('team_id'),
        Team.name.label('team_name')
    ).join(
        User, User.id == LeagueMembership.user_id
    ).join(
        Team, Team.user_id == User.id
    ).filter(
        LeagueMembership.league_id == league_id
    ).order_by(
        desc(User.total_points)
    )
    
    results = members_query.all()
    
    # Add rankings and create detailed response objects
    detailed_members = []
    for rank, result in enumerate(results, 1):
        detailed_members.append(DetailedLeagueMembershipResponse(
            id=result.id,
            user_id=result.user_id,
            user_name=result.user_name,
            user_email=result.user_email,
            team_name=result.team_name,
            team_id=result.team_id,
            total_points=result.total_points,
            budget=result.budget,
            joined_at=result.joined_at,
            rank=rank
        ))
    
    return detailed_members

@router.delete("/{league_id}/leave")
async def leave_league(
    league_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Leave a league."""
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    # Check if user is the owner
    if league.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="League owner cannot leave the league. Transfer ownership or delete the league."
        )
    
    membership = db.query(LeagueMembership).filter(
        LeagueMembership.league_id == league_id,
        LeagueMembership.user_id == current_user.id
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not a member of this league"
        )
    
    db.delete(membership)
    db.commit()
    
    return {"message": "Successfully left the league"}

@router.delete("/{league_id}")
async def delete_league(
    league_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)  # Changed to admin only
):
    """Delete a league (admin only)."""
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    db.delete(league)
    db.commit()
    
    return {"message": "League deleted successfully"} 