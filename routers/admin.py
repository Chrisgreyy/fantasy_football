from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from database import get_db
from models import User, AuditLog, Team, Player, League, Gameweek, PlayerStats, TeamPlayer, UserRole
from schemas import AuditLogResponse, UserResponse, LeaderboardResponse, LeaderboardEntry, UserCreate
from auth import get_current_admin_user, get_password_hash

router = APIRouter()

@router.post("/create-admin", response_model=UserResponse)
async def create_admin_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new admin user (unprotected route)."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new admin user
    db_user = User(
        name=user.name,
        email=user.email,
        password_hash=get_password_hash(user.password),
        role=UserRole.ADMIN
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Log the action
    audit_log = AuditLog(
        user_id=db_user.id,
        action="create_admin",
        resource_type="user",
        resource_id=db_user.id,
        details=f"Admin user {db_user.name} created"
    )
    db.add(audit_log)
    db.commit()
    
    return db_user

@router.get("/users/{user_id}/activity", response_model=List[AuditLogResponse])
async def get_user_activity(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get user activity logs (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logs = db.query(AuditLog).filter(
        AuditLog.user_id == user_id
    ).order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit).all()
    
    return logs

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    resource_type: str = None,
    action: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get system audit logs (admin only)."""
    query = db.query(AuditLog)
    
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if action:
        query = query.filter(AuditLog.action == action)
    
    logs = query.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit).all()
    return logs

@router.get("/stats/overview")
async def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get system overview stats (admin only)."""
    stats = {
        "total_users": db.query(User).count(),
        "total_teams": db.query(Team).count(),
        "total_players": db.query(Player).count(),
        "total_leagues": db.query(League).count(),
        "total_gameweeks": db.query(Gameweek).count(),
        "active_gameweeks": db.query(Gameweek).filter(Gameweek.status == "active").count(),
        "completed_fixtures": db.query(PlayerStats).count() > 0  # Simplified check
    }
    return stats

@router.get("/leaderboard/global", response_model=LeaderboardResponse)
async def get_global_leaderboard(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get global leaderboard (admin only)."""
    # Get leaderboard data
    leaderboard_query = db.query(
        User.id.label('user_id'),
        User.name.label('user_name'),
        Team.name.label('team_name'),
        User.total_points.label('total_points')
    ).join(
        Team, Team.user_id == User.id
    ).order_by(
        desc(User.total_points)
    ).offset(skip).limit(limit)
    
    results = leaderboard_query.all()
    
    # Add rankings
    entries = []
    for rank, result in enumerate(results, skip + 1):
        entries.append(LeaderboardEntry(
            user_id=result.user_id,
            user_name=result.user_name,
            team_name=result.team_name,
            total_points=result.total_points,
            rank=rank
        ))
    
    total_users = db.query(User).count()
    
    return LeaderboardResponse(
        entries=entries,
        total_users=total_users
    )

@router.post("/users/{user_id}/promote")
async def promote_user_to_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Promote user to admin (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.role = UserRole.ADMIN
    db.commit()
    
    # Log the action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="promote_to_admin",
        resource_type="user",
        resource_id=user_id,
        details=f"User {user.name} promoted to admin"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": f"User {user.name} promoted to admin"}

@router.post("/users/{user_id}/demote")
async def demote_admin_to_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Demote admin to regular user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself"
        )
    
    user.role = UserRole.USER
    db.commit()
    
    # Log the action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="demote_to_user",
        resource_type="user",
        resource_id=user_id,
        details=f"User {user.name} demoted to regular user"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": f"User {user.name} demoted to regular user"}

@router.post("/recalculate-points")
async def recalculate_all_points(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Recalculate all user and team points (admin only)."""
    # Reset all points
    db.query(User).update({User.total_points: 0})
    db.query(Team).update({Team.total_points: 0, Team.weekly_points: 0})
    db.query(Player).update({Player.total_points: 0})
    
    # Recalculate player points
    player_stats = db.query(PlayerStats).all()
    for stat in player_stats:
        player = db.query(Player).filter(Player.id == stat.player_id).first()
        if player:
            player.total_points += stat.points
    
    # Recalculate team and user points
    teams = db.query(Team).all()
    for team in teams:
        team_total = 0
        team_players = db.query(TeamPlayer).filter(TeamPlayer.team_id == team.id).all()
        
        for team_player in team_players:
            player = db.query(Player).filter(Player.id == team_player.player_id).first()
            if player:
                points = player.total_points
                # Double points for captain
                if team.captain_id == player.id:
                    points *= 2
                team_total += points
        
        team.total_points = team_total
        team.weekly_points = team_total  # Simplified
        
        # Update user points
        team.owner.total_points += team_total
    
    db.commit()
    
    # Log the action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="recalculate_points",
        resource_type="system",
        details="All points recalculated"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "All points recalculated successfully"}

@router.post("/reset-gameweek-points")
async def reset_weekly_points(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Reset weekly points for all teams (admin only)."""
    db.query(Team).update({Team.weekly_points: 0})
    db.commit()
    
    # Log the action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="reset_weekly_points",
        resource_type="system",
        details="Weekly points reset for all teams"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Weekly points reset successfully"} 