"""
Database seeding script for real Premier League players
This populates the database with real football players so users can select from them
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal, engine
from models import Player, PlayerPosition, PlayerStatus, Base
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Real Premier League players data (2024/25 season sample)
REAL_PLAYERS_DATA = [
    # Manchester City
    {"name": "Erling Haaland", "position": PlayerPosition.FORWARD, "team": "Manchester City", "price": 15.0, "shirt_number": 9},
    {"name": "Kevin De Bruyne", "position": PlayerPosition.MIDFIELDER, "team": "Manchester City", "price": 12.5, "shirt_number": 17},
    {"name": "Ederson", "position": PlayerPosition.GOALKEEPER, "team": "Manchester City", "price": 5.5, "shirt_number": 31},
    {"name": "Ruben Dias", "position": PlayerPosition.DEFENDER, "team": "Manchester City", "price": 6.0, "shirt_number": 3},
    {"name": "Bernardo Silva", "position": PlayerPosition.MIDFIELDER, "team": "Manchester City", "price": 9.5, "shirt_number": 20},
    {"name": "Phil Foden", "position": PlayerPosition.MIDFIELDER, "team": "Manchester City", "price": 9.0, "shirt_number": 47},
    {"name": "Kyle Walker", "position": PlayerPosition.DEFENDER, "team": "Manchester City", "price": 5.5, "shirt_number": 2},
    {"name": "Julian Alvarez", "position": PlayerPosition.FORWARD, "team": "Manchester City", "price": 8.0, "shirt_number": 19},
    
    # Arsenal
    {"name": "Bukayo Saka", "position": PlayerPosition.MIDFIELDER, "team": "Arsenal", "price": 10.0, "shirt_number": 7},
    {"name": "Gabriel Jesus", "position": PlayerPosition.FORWARD, "team": "Arsenal", "price": 8.5, "shirt_number": 9},
    {"name": "Martin Odegaard", "position": PlayerPosition.MIDFIELDER, "team": "Arsenal", "price": 8.5, "shirt_number": 8},
    {"name": "Aaron Ramsdale", "position": PlayerPosition.GOALKEEPER, "team": "Arsenal", "price": 5.0, "shirt_number": 1},
    {"name": "William Saliba", "position": PlayerPosition.DEFENDER, "team": "Arsenal", "price": 6.0, "shirt_number": 12},
    {"name": "Gabriel Magalhaes", "position": PlayerPosition.DEFENDER, "team": "Arsenal", "price": 5.5, "shirt_number": 6},
    {"name": "Ben White", "position": PlayerPosition.DEFENDER, "team": "Arsenal", "price": 5.0, "shirt_number": 4},
    {"name": "Declan Rice", "position": PlayerPosition.MIDFIELDER, "team": "Arsenal", "price": 6.5, "shirt_number": 41},
    
    # Liverpool
    {"name": "Mohamed Salah", "position": PlayerPosition.FORWARD, "team": "Liverpool", "price": 13.0, "shirt_number": 11},
    {"name": "Sadio Mane", "position": PlayerPosition.FORWARD, "team": "Liverpool", "price": 10.0, "shirt_number": 10},
    {"name": "Virgil van Dijk", "position": PlayerPosition.DEFENDER, "team": "Liverpool", "price": 6.5, "shirt_number": 4},
    {"name": "Alisson", "position": PlayerPosition.GOALKEEPER, "team": "Liverpool", "price": 5.5, "shirt_number": 1},
    {"name": "Sadio Mane", "position": PlayerPosition.MIDFIELDER, "team": "Liverpool", "price": 8.0, "shirt_number": 19},
    {"name": "Andrew Robertson", "position": PlayerPosition.DEFENDER, "team": "Liverpool", "price": 6.0, "shirt_number": 26},
    {"name": "Trent Alexander-Arnold", "position": PlayerPosition.DEFENDER, "team": "Liverpool", "price": 7.5, "shirt_number": 66},
    {"name": "Jordan Henderson", "position": PlayerPosition.MIDFIELDER, "team": "Liverpool", "price": 5.0, "shirt_number": 14},
    
    # Chelsea
    {"name": "Christopher Nkunku", "position": PlayerPosition.FORWARD, "team": "Chelsea", "price": 9.0, "shirt_number": 18},
    {"name": "Enzo Fernandez", "position": PlayerPosition.MIDFIELDER, "team": "Chelsea", "price": 7.5, "shirt_number": 5},
    {"name": "Thiago Silva", "position": PlayerPosition.DEFENDER, "team": "Chelsea", "price": 5.0, "shirt_number": 6},
    {"name": "Kepa Arrizabalaga", "position": PlayerPosition.GOALKEEPER, "team": "Chelsea", "price": 5.0, "shirt_number": 1},
    {"name": "Reece James", "position": PlayerPosition.DEFENDER, "team": "Chelsea", "price": 6.0, "shirt_number": 24},
    {"name": "Mason Mount", "position": PlayerPosition.MIDFIELDER, "team": "Chelsea", "price": 7.0, "shirt_number": 19},
    {"name": "Raheem Sterling", "position": PlayerPosition.FORWARD, "team": "Chelsea", "price": 10.0, "shirt_number": 17},
    {"name": "Ben Chilwell", "position": PlayerPosition.DEFENDER, "team": "Chelsea", "price": 5.5, "shirt_number": 21},
    
    # Manchester United
    {"name": "Marcus Rashford", "position": PlayerPosition.FORWARD, "team": "Manchester United", "price": 9.5, "shirt_number": 10},
    {"name": "Bruno Fernandes", "position": PlayerPosition.MIDFIELDER, "team": "Manchester United", "price": 8.5, "shirt_number": 18},
    {"name": "Casemiro", "position": PlayerPosition.MIDFIELDER, "team": "Manchester United", "price": 5.5, "shirt_number": 18},
    {"name": "Andre Onana", "position": PlayerPosition.GOALKEEPER, "team": "Manchester United", "price": 5.0, "shirt_number": 24},
    {"name": "Raphael Varane", "position": PlayerPosition.DEFENDER, "team": "Manchester United", "price": 5.5, "shirt_number": 19},
    {"name": "Luke Shaw", "position": PlayerPosition.DEFENDER, "team": "Manchester United", "price": 5.0, "shirt_number": 23},
    {"name": "Antony", "position": PlayerPosition.FORWARD, "team": "Manchester United", "price": 7.0, "shirt_number": 21},
    {"name": "Lisandro Martinez", "position": PlayerPosition.DEFENDER, "team": "Manchester United", "price": 5.0, "shirt_number": 6},
    
    # Tottenham
    {"name": "Harry Kane", "position": PlayerPosition.FORWARD, "team": "Tottenham", "price": 12.5, "shirt_number": 10},
    {"name": "Son Heung-min", "position": PlayerPosition.FORWARD, "team": "Tottenham", "price": 11.0, "shirt_number": 7},
    {"name": "James Maddison", "position": PlayerPosition.MIDFIELDER, "team": "Tottenham", "price": 8.0, "shirt_number": 10},
    {"name": "Hugo Lloris", "position": PlayerPosition.GOALKEEPER, "team": "Tottenham", "price": 5.0, "shirt_number": 1},
    {"name": "Cristian Romero", "position": PlayerPosition.DEFENDER, "team": "Tottenham", "price": 5.5, "shirt_number": 17},
    {"name": "Pedro Porro", "position": PlayerPosition.DEFENDER, "team": "Tottenham", "price": 5.5, "shirt_number": 23},
    {"name": "Dejan Kulusevski", "position": PlayerPosition.MIDFIELDER, "team": "Tottenham", "price": 8.5, "shirt_number": 21},
    {"name": "Richarlison", "position": PlayerPosition.FORWARD, "team": "Tottenham", "price": 7.5, "shirt_number": 9},
    
    # Newcastle United
    {"name": "Alexander Isak", "position": PlayerPosition.FORWARD, "team": "Newcastle", "price": 8.5, "shirt_number": 14},
    {"name": "Bruno Guimaraes", "position": PlayerPosition.MIDFIELDER, "team": "Newcastle", "price": 6.5, "shirt_number": 39},
    {"name": "Nick Pope", "position": PlayerPosition.GOALKEEPER, "team": "Newcastle", "price": 5.0, "shirt_number": 22},
    {"name": "Sven Botman", "position": PlayerPosition.DEFENDER, "team": "Newcastle", "price": 4.5, "shirt_number": 4},
    {"name": "Kieran Trippier", "position": PlayerPosition.DEFENDER, "team": "Newcastle", "price": 6.0, "shirt_number": 2},
    {"name": "Allan Saint-Maximin", "position": PlayerPosition.MIDFIELDER, "team": "Newcastle", "price": 6.5, "shirt_number": 10},
    {"name": "Callum Wilson", "position": PlayerPosition.FORWARD, "team": "Newcastle", "price": 7.0, "shirt_number": 9},
    {"name": "Dan Burn", "position": PlayerPosition.DEFENDER, "team": "Newcastle", "price": 4.5, "shirt_number": 33},
    
    # Brighton
    {"name": "Kaoru Mitoma", "position": PlayerPosition.MIDFIELDER, "team": "Brighton", "price": 6.5, "shirt_number": 22},
    {"name": "Evan Ferguson", "position": PlayerPosition.FORWARD, "team": "Brighton", "price": 5.5, "shirt_number": 28},
    {"name": "Moises Caicedo", "position": PlayerPosition.MIDFIELDER, "team": "Brighton", "price": 5.5, "shirt_number": 25},
    {"name": "Jason Steele", "position": PlayerPosition.GOALKEEPER, "team": "Brighton", "price": 4.5, "shirt_number": 23},
    {"name": "Lewis Dunk", "position": PlayerPosition.DEFENDER, "team": "Brighton", "price": 4.5, "shirt_number": 5},
    {"name": "Pervis Estupinan", "position": PlayerPosition.DEFENDER, "team": "Brighton", "price": 4.5, "shirt_number": 30},
    {"name": "Alexis Mac Allister", "position": PlayerPosition.MIDFIELDER, "team": "Brighton", "price": 5.5, "shirt_number": 10},
    {"name": "Solly March", "position": PlayerPosition.MIDFIELDER, "team": "Brighton", "price": 5.0, "shirt_number": 7},
]

def create_admin_user(db: Session):
    """Create an admin user for managing the system"""
    from models import User, UserRole
    from auth import get_password_hash
    
    # Check if admin already exists
    admin = db.query(User).filter(User.email == "admin@fantasyfootball.com").first()
    if not admin:
        admin_user = User(
            name="System Admin",
            email="admin@fantasyfootball.com",
            password_hash=get_password_hash("admin123"),  # Change this in production!
            role=UserRole.ADMIN
        )
        db.add(admin_user)
        db.commit()
        logger.info("Created admin user: admin@fantasyfootball.com")
    else:
        logger.info("Admin user already exists")

def seed_real_players(db: Session):
    """Populate database with real Premier League players"""
    
    logger.info("Starting to seed real players...")
    
    # Check if players already exist
    existing_count = db.query(Player).count()
    if existing_count > 0:
        logger.info(f"Database already has {existing_count} players. Skipping seed.")
        return
    
    # Add all real players
    added_count = 0
    for player_data in REAL_PLAYERS_DATA:
        # Check if player already exists (by name and team)
        existing = db.query(Player).filter(
            Player.name == player_data["name"],
            Player.team == player_data["team"]
        ).first()
        
        if not existing:
            player = Player(
                name=player_data["name"],
                position=player_data["position"],
                team=player_data["team"],
                price=player_data["price"],
                shirt_number=player_data.get("shirt_number"),
                status=PlayerStatus.AVAILABLE,
                total_points=0  # Will be updated as season progresses
            )
            db.add(player)
            added_count += 1
    
    db.commit()
    logger.info(f"Successfully added {added_count} real players to the database")
    
    # Log position summary
    positions = db.query(Player.position, func.count(Player.id)).group_by(Player.position).all()
    logger.info("Player position breakdown:")
    for position, count in positions:
        logger.info(f"  {position.value}: {count} players")

def seed_sample_gameweeks(db: Session):
    """Create sample gameweeks for the season"""
    from models import Gameweek, GameweekStatus
    from datetime import datetime, timedelta
    
    logger.info("Creating sample gameweeks...")
    
    # Check if gameweeks already exist
    existing_gw = db.query(Gameweek).first()
    if existing_gw:
        logger.info("Gameweeks already exist. Skipping.")
        return
    
    # Create 38 gameweeks (standard Premier League season)
    start_date = datetime(2024, 8, 17)  # Season start
    
    for week_num in range(1, 39):
        # Each gameweek deadline is typically Friday before the weekend
        deadline = start_date + timedelta(days=(week_num - 1) * 7, hours=18, minutes=30)
        
        # Determine status based on current date
        current_date = datetime.utcnow()
        if deadline > current_date + timedelta(days=7):
            status = GameweekStatus.UPCOMING
        elif deadline > current_date:
            status = GameweekStatus.ACTIVE
        else:
            status = GameweekStatus.COMPLETED
        
        gameweek = Gameweek(
            number=week_num,
            deadline=deadline,
            status=status
        )
        db.add(gameweek)
    
    db.commit()
    logger.info("Successfully created 38 gameweeks")

def main():
    """Main seeding function"""
    logger.info("Starting database seeding...")
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Seed data in order
        create_admin_user(db)
        seed_real_players(db)
        seed_sample_gameweeks(db)
        
        logger.info("Database seeding completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
