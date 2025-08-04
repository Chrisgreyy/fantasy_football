from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from database import get_db
from models import Gameweek, User, GameweekStatus, League, Fixture, LeagueGameweekStanding, Team
from schemas import (
    GameweekResponse, GameweekCreate, GameweekUpdate, 
    GameweekResults, GameweekLeagueResult, GameweekLeagueStanding,
    LeagueFixtureResponse
)
from auth import get_current_active_user, get_current_admin_user

router = APIRouter()

@router.get("/", response_model=List[GameweekResponse])
async def get_gameweeks(
    skip: int = 0,
    limit: int = 100,
    include_results: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all gameweeks."""
    gameweeks = db.query(Gameweek).order_by(Gameweek.number).offset(skip).limit(limit).all()
    
    if include_results:
        for gameweek in gameweeks:
            gameweek.league_results = await get_gameweek_results(gameweek.id, db, current_user)
    
    return gameweeks


@router.get("/{gameweek_id}", response_model=GameweekResponse)
async def get_gameweek(
    gameweek_id: int,
    include_results: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get gameweek by ID."""
    gameweek = db.query(Gameweek).filter(Gameweek.id == gameweek_id).first()
    if not gameweek:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gameweek not found"
        )
    
    if include_results:
        gameweek.league_results = await get_gameweek_results(gameweek_id, db, current_user)
    
    return gameweek

@router.get("/{gameweek_id}/results", response_model=GameweekResults)
async def get_gameweek_results(
    gameweek_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get complete results for a gameweek across all leagues."""
    gameweek = db.query(Gameweek).filter(Gameweek.id == gameweek_id).first()
    if not gameweek:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gameweek not found"
        )
    
    # Get all leagues for this gameweek
    leagues = gameweek.leagues
    
    league_results = []
    for league in leagues:
        # Get fixtures for this league in this gameweek
        fixtures = db.query(Fixture).filter(
            Fixture.gameweek_id == gameweek_id,
            Fixture.league_id == league.id
        ).all()
        
        # Get standings for this league in this gameweek
        standings = db.query(LeagueGameweekStanding).filter(
            LeagueGameweekStanding.gameweek_id == gameweek_id,
            LeagueGameweekStanding.league_id == league.id
        ).order_by(LeagueGameweekStanding.rank).all()
        
        # Convert standings to response format
        standing_responses = []
        for standing in standings:
            user = db.query(User).filter(User.id == standing.user_id).first()
            team = db.query(Team).filter(Team.user_id == standing.user_id).first()
            standing_responses.append(GameweekLeagueStanding(
                user_id=standing.user_id,
                user_name=user.name,
                team_name=team.name if team else "No Team",
                points=standing.points,
                rank=standing.rank
            ))
        
        # Add league result
        league_results.append(GameweekLeagueResult(
            league_id=league.id,
            league_name=league.name,
            standings=standing_responses,
            fixtures=[LeagueFixtureResponse.from_orm(f) for f in fixtures]
        ))
    
    return GameweekResults(
        gameweek_id=gameweek.id,
        number=gameweek.number,
        status=gameweek.status,
        league_results=league_results
    )

@router.put("/{gameweek_id}", response_model=GameweekResponse)
async def update_gameweek(
    gameweek_id: int,
    gameweek_update: GameweekUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update gameweek (admin only)."""
    gameweek = db.query(Gameweek).filter(Gameweek.id == gameweek_id).first()
    if not gameweek:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gameweek not found"
        )
    
    # Update fields if provided
    if gameweek_update.deadline is not None:
        gameweek.deadline = gameweek_update.deadline
    if gameweek_update.status is not None:
        gameweek.status = gameweek_update.status
    
    db.commit()
    db.refresh(gameweek)
    return gameweek

@router.delete("/{gameweek_id}")
async def delete_gameweek(
    gameweek_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete gameweek (admin only)."""
    gameweek = db.query(Gameweek).filter(Gameweek.id == gameweek_id).first()
    if not gameweek:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gameweek not found"
        )
    
    db.delete(gameweek)
    db.commit()
    
    return {"message": "Gameweek deleted successfully"} 