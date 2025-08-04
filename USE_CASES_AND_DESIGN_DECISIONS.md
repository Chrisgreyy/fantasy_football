# Fantasy Football API - Use Cases and Design Decisions

## Overview
This document outlines the key use cases and design decisions for the Fantasy Football API

## Core System Concepts

### 1. User Roles and Authentication

#### Use Cases:
- **End Users**: Create fantasy teams, join leagues, manage their squad
- **Admins**: Manage the player database, create gameweeks, oversee system operations

#### Design Decisions:

**Why separate user and admin roles?**
- Security: Separates system management from user gameplay
- Data integrity: Only trusted admins can modify core game data (real players, prices, gameweeks)
- Scalability: Prevents users from accidentally corrupting the player database

**Admin Creation Process:**
- Initial admin created via database seeding or configuration
- Existing admins can create new admin users directly via `/admin/users/create-admin`
- Existing admins can promote regular users to admin status via `/admin/users/{id}/promote`
- Regular users cannot self-promote (security requirement)

**Why both create-admin and promote endpoints?**
- **Create Admin**: For creating new users who need admin access from the start (faster onboarding)
- **Promote User**: For existing users who have proven themselves and earned admin privileges
- **Different workflows**: New hire vs internal promotion scenarios
- **Audit trail**: Different reasons and processes for admin access

# 2. Player Management

# Use Cases:
- **Admins**: Add real football players (Salah, Rashford, etc.) to the database
- **Admins**: Update player information when transfers happen in real life
- **Admins**: Adjust player prices based on demand/performance
- **Users**: Browse and select players for their fantasy teams

# Design Decisions:

**Why separate player creation from player browsing?**
- **Admin endpoints** (`/admin/players`): For managing the master player database
- **User endpoints** (`/players`): For browsing available players to add to fantasy teams
- These serve different purposes and have different authorization requirements

**Why separate "update player" and "update player price" endpoints?**
- **Player Price Updates**: Happen frequently (weekly/daily) based on fantasy market dynamics
- **Player Information Updates**: Happen rarely (transfers, position changes, injuries)
- Separation allows for different validation rules and audit trails
- Price updates may need special logging for fantasy market transparency

# 3. Gameweek Management

# Use Cases:
- **Admins**: Create gameweeks with deadlines before real fixtures start
- **System**: Automatically activate gameweeks when deadline passes
- **Admins**: Manually complete gameweeks after all fixtures finish and stats are entered
- **Users**: Submit team changes before gameweek deadline

# Design Decisions:

**Why manual gameweek completion instead of automatic?**
1. **Data Verification**: Ensures all player stats and fixture results are entered correctly
2. **Error Correction Window**: Allows admins to fix any data entry mistakes before finalizing
3. **Audit Trail**: Clear record of when results were finalized
4. **User Transparency**: Users know exactly when their points are final

**Why gameweek activation/completion states?**
- **UPCOMING**: Gameweek created but not yet available for team changes
- **ACTIVE**: Deadline passed, no more team changes allowed, fixtures in progress
- **COMPLETED**: All fixtures finished, stats entered, points calculated and final

**Business Logic:**
- Once COMPLETED, no changes to that gameweek's data are allowed
- This prevents disputes and maintains data integrity
- If errors are found after completion, they must be corrected in future gameweeks

# 4. Team and League Management

# Use Cases:
- **Users**: Create fantasy teams within leagues
- **Users**: Join existing leagues
- **Users**: Select 15 players within budget constraints
- **Users**: Set captain and vice-captain for bonus points
- **System**: Calculate team scores based on real player performances

#### Design Decisions:

**Why 15-player squad limit?**
- Mirrors real fantasy football games (FPL standard)
- Forces strategic decisions about player selection
- Balances squad depth with budget constraints

**Why budget constraints?**
- Creates scarcity and strategic decision-making
- Prevents users from selecting all expensive players
- Adds trading/market dynamics to the game

## API Endpoint Design Rationale

### Authentication Endpoints (`/auth`)
- `POST /register`: Creates new users (not admins)
- `POST /login`: Returns JWT tokens for both users and admins

### User Management (`/users`)
- `GET /me`: User profile access
- `PUT /{user_id}`: Profile updates (own profile or admin)
- `GET /`: List all users (admin only)

### Admin Management (`/admin`)
- `GET /users`: List all users (admin only)
- `POST /users/create-admin`: Create new admin user (admin only)
- `PUT /users/{user_id}/promote`: Promote user to admin (admin only)
- `PUT /users/{user_id}/demote`: Demote admin to user (admin only)
- `POST /gameweeks`: Create new gameweeks (admin only)
- `PUT /gameweeks/{id}/status`: Change gameweek status - handles activation and completion (admin only)
- `PUT /gameweeks/{id}/emergency-correction`: Emergency corrections for completed gameweeks (admin only)
- `POST /player-stats`: Add player statistics (admin only)
- `POST /fixtures`: Create fixtures (admin only)

### Player Management (`/players`)
- `GET /`: Browse available players with filters (all users)
- `GET /{id}`: Get player details (all users)
- `GET /{id}/stats`: Get player performance history (all users)
- `POST /`: Create new real players (admin only)
- `PUT /{id}`: Update player information (admin only)
- `PATCH /{id}/price`: Update player price (admin only)

### Gameweek Browsing (`/gameweeks`)
- `GET /`: List gameweeks (all users)
- `GET /{id}`: Get gameweek details (all users)
- `GET /{id}/results`: Get gameweek results (all users)

## Data Consistency Rules

### Player Pricing
- Historical prices should be maintained for each gameweek
- Price changes affect new purchases but not existing team values
- This prevents manipulation and maintains fair play

### Gameweek Integrity
- Once a gameweek is COMPLETED, its data is immutable
- This ensures consistent scoring and prevents disputes
- Emergency corrections must be documented and applied to future gameweeks

### League Fairness
- All users in a league see the same player prices at the same time
- Gameweek deadlines are enforced consistently
- No retrospective changes that could affect league standings

## Security Considerations

### Role-Based Access
- Clear separation between user and admin capabilities
- Admin promotion requires existing admin authorization
- Sensitive operations (player management, gameweek control) restricted to admins

### Data Integrity
- Immutable gameweek results prevent tampering
- Audit trails for all admin actions
- Input validation on all user-submitted data

## Performance Considerations

### Database Design
- Indexed queries for common operations (player searches, league standings)
- Efficient relationships between teams, players, and gameweeks
- Pagination for large data sets

### Caching Strategy
- Player data cached between price updates
- League standings cached per gameweek
- Static data (positions, teams) cached long-term

This design balances user experience, data integrity, system security, and administrative control while maintaining the competitive fairness essential to fantasy football gameplay.
