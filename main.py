from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import engine, Base
from routers import auth, users, players, teams, gameweeks, fixtures, leagues, admin

# Create database tables
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Fantasy Football API",
    description="""
    A comprehensive Fantasy Football Web API for managing teams, players, and leagues.
    
    ## Key Features
    
    ### For Users
    * Browse and search real football players
    * Create and manage fantasy teams
    * Join leagues and compete with friends
    * Track performance and scores
    
    ### For Admins  
    * Manage the master player database
    * Create and control gameweeks
    * Oversee league operations
    * Handle user management
    
    ## Authentication
    Use `/auth/register` to create an account and `/auth/login` to get access tokens.
    Include the token in the Authorization header: `Bearer <your_token>`
    
    ## Design Philosophy
    This API separates user gameplay from system administration to ensure data integrity,
    security, and fair play across all fantasy football leagues.
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(teams.router, prefix="/teams", tags=["Teams"])
app.include_router(players.router, prefix="/players", tags=["Players"])
app.include_router(leagues.router, prefix="/leagues", tags=["Leagues"])
app.include_router(gameweeks.router, prefix="/gameweeks", tags=["Gameweeks"])
app.include_router(fixtures.router, prefix="/fixtures", tags=["Fixtures"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

@app.get("/")
async def root():
    return {"message": "Fantasy Football API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 