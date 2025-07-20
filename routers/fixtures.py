from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Fixture, User, PlayerStats, Player, Team, TeamPlayer
from schemas import FixtureResponse, FixtureCreate, FixtureUpdate, FixtureDataSubmission, PlayerStatsResponse
from auth import get_current_active_user, get_current_admin_user

router = APIRouter()

def calculate_player_points(stats: PlayerStats) -> int:
    """Calculate fantasy points for a player based on their stats."""
    points = 0
    
    # Base points for playing
    if stats.minutes_played > 0:
        points += 1
    if stats.minutes_played >= 60:
        points += 1
    
    # Goals
    if stats.player.position == "goalkeeper":
        points += stats.goals * 6
    elif stats.player.position == "defender":
        points += stats.goals * 6
    elif stats.player.position == "midfielder":
        points += stats.goals * 5
    elif stats.player.position == "forward":
        points += stats.goals * 4
    
    # Assists
    points += stats.assists * 3
    
    # Clean sheets
    if stats.clean_sheet:
        if stats.player.position in ["goalkeeper", "defender"]:
            points += 4
        elif stats.player.position == "midfielder":
            points += 1
    
    # Penalty saves
    points += stats.penalty_saves * 5
    
    # Saves (goalkeepers)
    if stats.player.position == "goalkeeper":
        points += (stats.saves // 3) * 1  # 1 point per 3 saves
    
    # Penalties
    points -= stats.penalty_misses * 2
    points -= stats.own_goals * 2
    points -= stats.yellow_cards * 1
    points -= stats.red_cards * 3
    
    return points

@router.get("/", response_model=List[FixtureResponse])
async def get_fixtures(
    skip: int = 0,
    limit: int = 100,
    gameweek_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all fixtures, optionally filtered by gameweek."""
    query = db.query(Fixture)
    
    if gameweek_id:
        query = query.filter(Fixture.gameweek_id == gameweek_id)
    
    fixtures = query.order_by(Fixture.date).offset(skip).limit(limit).all()
    return fixtures

@router.post("/", response_model=FixtureResponse)
async def create_fixture(
    fixture: FixtureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new fixture (admin only)."""
    db_fixture = Fixture(
        gameweek_id=fixture.gameweek_id,
        league_id=fixture.league_id,  # Add league_id
        home_team=fixture.home_team,
        away_team=fixture.away_team,
        date=fixture.date
    )
    db.add(db_fixture)
    db.commit()
    db.refresh(db_fixture)
    return db_fixture

@router.get("/{fixture_id}", response_model=FixtureResponse)
async def get_fixture(
    fixture_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get fixture by ID."""
    fixture = db.query(Fixture).filter(Fixture.id == fixture_id).first()
    if not fixture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixture not found"
        )
    return fixture

@router.put("/{fixture_id}", response_model=FixtureResponse)
async def update_fixture(
    fixture_id: int,
    fixture_update: FixtureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update fixture (admin only)."""
    fixture = db.query(Fixture).filter(Fixture.id == fixture_id).first()
    if not fixture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixture not found"
        )
    
    # Update fields if provided
    if fixture_update.home_team is not None:
        fixture.home_team = fixture_update.home_team
    if fixture_update.away_team is not None:
        fixture.away_team = fixture_update.away_team
    if fixture_update.date is not None:
        fixture.date = fixture_update.date
    if fixture_update.completed is not None:
        fixture.completed = fixture_update.completed
    
    db.commit()
    db.refresh(fixture)
    return fixture

@router.post("/{fixture_id}/results")
async def submit_fixture_results(
    fixture_id: int,
    fixture_data: FixtureDataSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Submit fixture results with player statistics (admin only)."""
    fixture = db.query(Fixture).filter(Fixture.id == fixture_id).first()
    if not fixture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixture not found"
        )
    
    if fixture.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fixture results already submitted"
        )
    
    # Process each player's stats
    for player_stat in fixture_data.players_stats:
        # Check if player exists
        player = db.query(Player).filter(Player.id == player_stat.player_id).first()
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player with ID {player_stat.player_id} not found"
            )
        
        # Create player stats record
        db_player_stats = PlayerStats(
            player_id=player_stat.player_id,
            fixture_id=fixture_id,
            goals=player_stat.goals,
            assists=player_stat.assists,
            yellow_cards=player_stat.yellow_cards,
            red_cards=player_stat.red_cards,
            minutes_played=player_stat.minutes_played,
            clean_sheet=player_stat.clean_sheet,
            own_goals=player_stat.own_goals,
            penalty_saves=player_stat.penalty_saves,
            penalty_misses=player_stat.penalty_misses,
            saves=player_stat.saves
        )
        
        # Calculate points
        db_player_stats.points = calculate_player_points(db_player_stats)
        
        db.add(db_player_stats)
        
        # Update player's total points
        player.total_points += db_player_stats.points
    
    # Mark fixture as completed
    fixture.completed = True
    
    # Update team points
    update_team_points(db, fixture_id)
    
    db.commit()
    
    return {"message": "Fixture results submitted successfully"}

def update_team_points(db: Session, fixture_id: int):
    """Update team points based on fixture results."""
    # Get all player stats for this fixture
    player_stats = db.query(PlayerStats).filter(PlayerStats.fixture_id == fixture_id).all()
    
    # Group by teams and calculate points
    team_points = {}
    for stat in player_stats:
        # Find teams that have this player
        team_players = db.query(TeamPlayer).filter(TeamPlayer.player_id == stat.player_id).all()
        
        for team_player in team_players:
            team = db.query(Team).filter(Team.id == team_player.team_id).first()
            if team:
                if team.id not in team_points:
                    team_points[team.id] = 0
                
                points = stat.points
                
                # Double points for captain
                if team.captain_id == stat.player_id:
                    points *= 2
                
                team_points[team.id] += points
    
    # Update team points
    for team_id, points in team_points.items():
        team = db.query(Team).filter(Team.id == team_id).first()
        if team:
            team.weekly_points += points
            team.total_points += points
            
            # Update user's total points
            team.owner.total_points += points

@router.get("/{fixture_id}/stats", response_model=List[PlayerStatsResponse])
async def get_fixture_stats(
    fixture_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get player statistics for a specific fixture."""
    fixture = db.query(Fixture).filter(Fixture.id == fixture_id).first()
    if not fixture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixture not found"
        )
    
    stats = db.query(PlayerStats).filter(PlayerStats.fixture_id == fixture_id).all()
    return stats

@router.delete("/{fixture_id}")
async def delete_fixture(
    fixture_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete fixture (admin only)."""
    fixture = db.query(Fixture).filter(Fixture.id == fixture_id).first()
    if not fixture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixture not found"
        )
    
    db.delete(fixture)
    db.commit()
    
    return {"message": "Fixture deleted successfully"} 