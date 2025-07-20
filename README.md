# Fantasy Football Web API

A robust, secure, and scalable Fantasy Football Web API built with FastAPI, PostgreSQL, and modern Python technologies. This API allows users to create and manage fantasy football teams, track player performance, and participate in competitive leagues.

## Features

### Core Functionality
- **User Management**: Registration, authentication, and profile management
- **Team Management**: Create teams, manage player rosters, set captains
- **Player Management**: Comprehensive player database with statistics
- **League System**: Create private leagues, join by codes, view leaderboards
- **Scoring System**: Real-time point calculations and leaderboards
- **Fixture Management**: Submit match results and player statistics
- **Transfer System**: Buy/sell players with budget management

### Technical Features
- **JWT Authentication**: Secure user authentication with role-based access
- **RESTful API**: Clean, standardized endpoints following REST conventions
- **Real-time Scoring**: Dynamic point calculations based on player performance
- **Database Integrity**: Normalized PostgreSQL schema with proper relationships
- **Comprehensive Testing**: PyTest-based testing suite
- **Docker Support**: Containerized deployment with Docker Compose
- **API Documentation**: Automatic OpenAPI/Swagger documentation

## Technologies Used

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with bcrypt password hashing
- **Validation**: Pydantic models for request/response validation
- **Testing**: PyTest with asyncio support
- **Containerization**: Docker and Docker Compose
- **API Documentation**: Automatic OpenAPI/Swagger generation

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Docker and Docker Compose (for containerized deployment)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fantasy_football
   ```

2. **Install dependencies**
   ```bash
   source venv/Scripts/activate  
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and secret key
   ```

4. **Set up PostgreSQL database**
   ```bash
   createdb fantasy_football
   ```

5. **Run the application**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Access the application**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Database Admin: http://localhost:8080

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user

### Users
- `GET /users/me` - Get current user profile
- `GET /users/{user_id}` - Get user by ID
- `PUT /users/{user_id}` - Update user profile
- `GET /users/{user_id}/budget` - Get user budget

### Players
- `GET /players/` - Get all players (with filtering)
- `POST /players/` - Create player (admin only)
- `GET /players/{player_id}` - Get player by ID
- `PUT /players/{player_id}` - Update player (admin only)
- `PATCH /players/{player_id}/status` - Update player status (admin only)
- `GET /players/{player_id}/history` - Get player performance history
- `GET /players/{player_id}/stats` - Get player statistics

### Teams
- `GET /teams/` - Get user's teams
- `POST /teams/` - Create new team
- `GET /teams/{team_id}` - Get team by ID
- `PUT /teams/{team_id}` - Update team
- `GET /teams/{team_id}/players` - Get team players
- `POST /teams/{team_id}/players` - Add player to team
- `DELETE /teams/{team_id}/players/{player_id}` - Remove player from team
- `PUT /teams/{team_id}/captain` - Set team captain
- `POST /teams/{team_id}/transfers` - Make player transfer

### Gameweeks
- `GET /gameweeks/` - Get all gameweeks
- `POST /gameweeks/` - Create gameweek (admin only)
- `GET /gameweeks/{gameweek_id}` - Get gameweek by ID
- `PUT /gameweeks/{gameweek_id}` - Update gameweek (admin only)
- `GET /gameweeks/current/active` - Get current active gameweek
- `PATCH /gameweeks/{gameweek_id}/activate` - Activate gameweek (admin only)

### Fixtures
- `GET /fixtures/` - Get all fixtures
- `POST /fixtures/` - Create fixture (admin only)
- `GET /fixtures/{fixture_id}` - Get fixture by ID
- `PUT /fixtures/{fixture_id}` - Update fixture (admin only)
- `POST /fixtures/{fixture_id}/results` - Submit fixture results (admin only)
- `GET /fixtures/{fixture_id}/stats` - Get fixture statistics

### Leagues
- `GET /leagues/` - Get user's leagues
- `POST /leagues/` - Create new league
- `GET /leagues/{league_id}` - Get league by ID
- `PUT /leagues/{league_id}` - Update league (owner only)
- `POST /leagues/{league_id}/join` - Join league by ID
- `POST /leagues/join` - Join league by code
- `GET /leagues/{league_id}/leaderboard` - Get league leaderboard
- `GET /leagues/{league_id}/members` - Get league members
- `DELETE /leagues/{league_id}/leave` - Leave league

### Admin
- `GET /admin/users/{user_id}/activity` - Get user activity logs
- `GET /admin/audit-logs` - Get system audit logs
- `GET /admin/stats/overview` - Get system statistics
- `GET /admin/leaderboard/global` - Get global leaderboard
- `POST /admin/users/{user_id}/promote` - Promote user to admin
- `POST /admin/users/{user_id}/demote` - Demote admin to user
- `POST /admin/recalculate-points` - Recalculate all points
- `POST /admin/reset-gameweek-points` - Reset weekly points

## Fantasy Football Rules

### Team Composition
- 11 players per team (maximum)
- 1 goalkeeper, 3-5 defenders, 3-5 midfielders, 1-3 forwards
- £100 million budget for transfers
- 1 captain per gameweek (earns double points)

### Scoring System
- **Playing Time**: 1 point (>0 minutes), 2 points (≥60 minutes)
- **Goals**: Goalkeeper/Defender (6 points), Midfielder (5 points), Forward (4 points)
- **Assists**: 3 points
- **Clean Sheets**: Goalkeeper/Defender (4 points), Midfielder (1 point)
- **Saves**: 1 point per 3 saves (goalkeepers only)
- **Penalty Saves**: 5 points
- **Penalties**: -2 points for misses
- **Cards**: Yellow (-1 point), Red (-3 points)
- **Own Goals**: -2 points

### Transfers
- Unlimited transfers before season starts
- Limited transfers during season
- Transfer costs based on price differences
- Transfer deadlines before each gameweek

## Testing

Run the test suite:
```bash
pytest test_main.py -v
```

Run with coverage:
```bash
pytest test_main.py --cov=. --cov-report=html
```

## API Documentation

When the application is running, you can access:
- **Interactive API Documentation**: http://localhost:8000/docs
- **Alternative API Documentation**: http://localhost:8000/redoc

## Data Models

### Core Models
- **User**: User accounts with authentication and profile data
- **Player**: Real football players with positions, teams, and pricing
- **Team**: User's fantasy teams with player selections
- **League**: Private leagues for competition
- **Gameweek**: Weekly periods with deadlines and fixtures
- **Fixture**: Football matches with results and statistics
- **PlayerStats**: Individual player performance data

### Relationships
- Users can have one team in each leauge 
- Teams belong to users and contain players
- Each player can be in one team in a leauge 
- Leagues contain multiple users
- Gameweeks contain multiple fixtures
- Fixtures contain player statistics

## Security Features

- **Password Hashing**: bcrypt for secure password storage
- **JWT Authentication**: Stateless authentication with expiration
- **Role-Based Access**: User and admin roles with appropriate permissions
- **Input Validation**: Pydantic models prevent injection attacks
- **CORS Protection**: Configurable cross-origin resource sharing
- **Rate Limiting**: Planned for future implementation

## Deployment

### Production Environment Variables
```bash
DATABASE_URL=postgresql://user:password@localhost/fantasy_football
SECRET_KEY=your-strong-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=False
```

### Docker Production Setup
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Future Enhancements

- **Real-time Notifications**: WebSocket support for live updates
- **External Data Integration**: Automatic player statistics from sports APIs
- **Mobile App Support**: React Native or Flutter mobile applications
- **Advanced Analytics**: Player performance predictions and recommendations
- **Social Features**: User messaging and league discussions
- **Payment Integration**: Premium leagues with entry fees
- **Machine Learning**: Injury prediction and player recommendations

## Support

For support, please create an issue in the GitHub repository or contact the development team.

---

Built with ❤️ using FastAPI and modern Python technologies. 