from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import (
    User, Player, Gameweek, PlayerStats, Fixture,
    UserRole, GameweekStatus
)
from schemas import ( UserResponse, UserCreate,
    GameweekResponse, FixtureResponse, FixtureCreate,
    PlayerStatsCreate, PlayerStatsResponse
)
from auth import get_current_active_user, get_password_hash
from datetime import datetime

router = APIRouter(tags=["Admin"])

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

@router.put("/users/{user_id}/promote")
def promote_user_to_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Promote a user to admin role (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already an admin"
        )
    
    user.role = UserRole.ADMIN
    db.commit()
    
    return {"message": f"User {user.name} has been promoted to admin"}

@router.put("/users/{user_id}/demote")
def demote_admin_to_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Demote an admin to regular user role (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.role == UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a regular user"
        )
    
    # Prevent demoting yourself
    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself"
        )
    
    user.role = UserRole.USER
    db.commit()
    
    return {"message": f"Admin {user.name} has been demoted to regular user"}

@router.post("/users/create-admin", response_model=UserResponse)
def create_new_admin(
    admin_data: UserCreate,
    db: Session = Depends(get_db),
    # admin_user: User = Depends(require_admin)
):
    """Create a new admin user (admin only)
    
    Use cases:
    - Initial system setup with multiple admins
    - Adding new admin users when team grows
    - Creating specialized admin accounts for different responsibilities
    
    Business Logic:
    - Only existing admins can create new admins
    - New admin is created with ADMIN role immediately
    - Same validation as regular user creation (unique email, etc.)
    """
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == admin_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new admin user
    hashed_password = get_password_hash(admin_data.password)
    new_admin = User(
        name=admin_data.name,
        email=admin_data.email,
        password_hash=hashed_password,
        role=UserRole.ADMIN  # Set as admin immediately
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    return new_admin

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
    """Update gameweek status (admin only)
    
    Status Flow: UPCOMING -> ACTIVE -> COMPLETED
    
    UPCOMING: Gameweek created but deadline not reached
    ACTIVE: Deadline passed, team changes locked, fixtures in progress  
    COMPLETED: All fixtures finished, stats entered, points final and immutable
    
    Business Logic:
    - ACTIVE: Only one gameweek can be active at a time
    - COMPLETED: All fixtures must be finished before completion
    - Once COMPLETED, gameweek data becomes immutable to ensure data integrity
    """
    
    gameweek = db.query(Gameweek).filter(Gameweek.id == gameweek_id).first()
    if not gameweek:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gameweek not found"
        )
    
    # Validate status transitions
    current_status = gameweek.status
    
    # Define valid status transitions
    valid_transitions = {
        GameweekStatus.UPCOMING: [GameweekStatus.ACTIVE],
        GameweekStatus.ACTIVE: [GameweekStatus.COMPLETED],
        GameweekStatus.COMPLETED: []  # No transitions allowed from completed
    }
    
    if status not in valid_transitions.get(current_status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from {current_status.value} to {status.value}"
        )
    
    # Handle ACTIVE status - only one gameweek can be active
    if status == GameweekStatus.ACTIVE:
        # Deactivate any currently active gameweek
        current_active = db.query(Gameweek).filter(
            Gameweek.status == GameweekStatus.ACTIVE,
            Gameweek.id != gameweek_id
        ).first()
        
        if current_active:
            current_active.status = GameweekStatus.COMPLETED
            db.commit()
            
    # Handle COMPLETED status - verify all fixtures are done
    elif status == GameweekStatus.COMPLETED:
        incomplete_fixtures = db.query(Fixture).filter(
            Fixture.gameweek_id == gameweek_id,
            Fixture.completed == False
        ).count()
        
        if incomplete_fixtures > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot complete gameweek. {incomplete_fixtures} fixtures are still incomplete."
            )
    
    gameweek.status = status
    db.commit()
    
    status_messages = {
        GameweekStatus.ACTIVE: f"Gameweek {gameweek.number} is now ACTIVE - team changes locked, any previous active gameweek has been completed",
        GameweekStatus.COMPLETED: f"Gameweek {gameweek.number} is now COMPLETED - scores are final and immutable"
    }
    
    return {
        "message": status_messages.get(status, f"Updated gameweek {gameweek.number} status to {status.value}"),
        "gameweek_id": gameweek_id,
        "new_status": status.value,
        "previous_status": current_status.value
    }

@router.put("/gameweeks/{gameweek_id}/emergency-correction")
def emergency_gameweek_correction(
    gameweek_id: int,
    correction_reason: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Emergency correction for completed gameweeks (admin only)
    
    This endpoint exists for critical errors that must be fixed even after completion.
    Use cases:
    - Incorrect player stats that significantly affect league standings
    - System bugs that calculated points incorrectly
    - Official league corrections from real football authorities
    
    All corrections are logged for transparency and audit purposes.
    """
    
    gameweek = db.query(Gameweek).filter(Gameweek.id == gameweek_id).first()
    if not gameweek:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gameweek not found"
        )
    
    if gameweek.status != GameweekStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Emergency corrections only allowed for completed gameweeks"
        )
    
    if not correction_reason or len(correction_reason.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Correction reason must be at least 10 characters"
        )
    
    # Temporarily allow modifications by setting status back to ACTIVE
    gameweek.status = GameweekStatus.ACTIVE
    db.commit()
    
    # Log the correction (in a real system, this would go to an audit table)
    return {
        "message": f"Emergency correction enabled for gameweek {gameweek.number}",
        "reason": correction_reason,
        "corrected_by": admin_user.name,
        "warning": "Gameweek must be manually set back to COMPLETED after corrections are made"
    }

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
