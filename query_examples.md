# 🏈 NFL Stat Agent - Query Examples

This document shows how the agent intelligently routes different types of queries to either the historical database or real-time web search.

## 📊 Database Queries (Historical Statistics)

These queries use the local SQLite database with nflfastR data and are intelligently routed to the appropriate table:

### 🏈 Team Statistics (team_stats table)
- "Which team had the most passing yards in 2023?"
- "Show me the top 5 teams by rushing yards in 2022"
- "What was the Eagles' win percentage in 2023?"
- "Compare quarterbacks by EPA"
- "Which teams had the best rolling win percentage over 16 games?"

### 🎯 Play-by-Play Analysis (nflfastR_pbp table)
- "What is the most common play type in the database?"
- "How many touchdowns did Mahomes throw in 2023?"
- "What's the success rate on 4th down attempts in the 4th quarter?"
- "Show me plays with the highest EPA"
- "How often do teams score when starting from their own 20-yard line?"
- "What's the average EPA on 3rd and long situations?"

### ⚔️ Game Matchups (pregame_matchups table)
- "What was the Vegas spread for Chiefs vs Bills in 2023?"
- "What was the win probability for the home team in that game?"
- "Show me head-to-head matchups between the Eagles and Cowboys"
- "What were the betting odds for the Super Bowl?"
- "Which team was favored in the most games?"

### Advanced Analytics
- "Which teams had the highest WPA (Win Probability Added) in clutch situations?"
- "What's the correlation between air yards and completion percentage?"
- "Show me the most efficient red zone offenses in 2023"

## 🌐 Web Search Queries (Current Information)

These queries use real-time web search for up-to-date information:

### Current Events
- "What are the latest NFL injury updates?"
- "Who won the most recent NFL game?"
- "What are the current playoff standings?"

### Breaking News
- "What trades happened this week?"
- "What's the latest news about Aaron Rodgers?"
- "What are the current free agent rumors?"

### Recent Games
- "What was the score of last night's game?"
- "Who won the most recent Monday Night Football game?"
- "What happened in the latest playoff game?"

### Player Status
- "Is Patrick Mahomes injured?"
- "What's the status of [player name]?"
- "Who is questionable for this week's games?"

## 🤖 How Query Routing Works

The agent uses intelligent keyword analysis to determine the best data source:

### Database vs Web Search
- **Database Triggers**: Statistical terms, historical references, performance metrics
- **Web Search Triggers**: Time indicators, current events, live information

### Database Table Routing
The agent also intelligently routes database queries to the most appropriate table:

#### 🏈 team_stats Table
- **Keywords**: team, win, loss, record, rolling, cumulative, season, quarterback
- **Use for**: Team performance, season records, quarterback stats, rolling averages

#### 🎯 nflfastR_pbp Table  
- **Keywords**: play, individual, player, down, distance, yard, touchdown, quarter
- **Use for**: Individual plays, player stats, game situations, play analysis

#### ⚔️ pregame_matchups Table
- **Keywords**: matchup, spread, vegas, win probability, pregame, betting
- **Use for**: Game predictions, odds, head-to-head matchups, betting analysis

### Examples of Smart Routing

| Query | Data Source | Table | Reason |
|-------|-------------|-------|---------|
| "Who had the most passing yards in 2023?" | Database | team_stats | Team statistics |
| "What's the latest injury news?" | Web Search | - | Current events |
| "Compare Mahomes and Allen by EPA" | Database | team_stats | Quarterback comparison |
| "Who won last night's game?" | Web Search | - | Recent game result |
| "What's the success rate on 4th down?" | Database | nflfastR_pbp | Play-by-play analysis |
| "What was the Vegas spread?" | Database | pregame_matchups | Betting/odds data |
| "Show me individual plays" | Database | nflfastR_pbp | Granular play data |
| "What trades happened today?" | Web Search | - | Breaking news |

## 🎯 Best Practices

### For Database Queries
- Ask about historical statistics and trends
- Use specific years or seasons
- Request comparisons and rankings
- Ask about performance metrics and analytics

### For Web Search Queries
- Ask about current events and news
- Request recent game results
- Inquire about player status and injuries
- Ask about trades, signings, and roster moves

The agent automatically chooses the best approach, but you can also be explicit:
- "Search the web for..." (forces web search)
- "Look up in the database..." (forces database query) 