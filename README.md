# 🏈 NFL Stat Agent

An interactive AI-powered agent that answers questions about NFL team and play statistics using a local SQLite database derived from [nflfastR](https://github.com/nflverse/nflfastR). It uses an LLM agent to translate natural language questions into SQL queries and return intelligent, grounded responses. Now features blazing-fast web search, caching, and optimized hybrid routing.

## 🔍 Use Cases

### Historical Statistics (Database)
Ask questions like:
- "Which teams had the highest win percentage in 2023?"
- "How did the Eagles perform against the spread in the last 8 weeks?"
- "Compare Patrick Mahomes and Josh Allen by WPA in clutch time."
- "What was the most common play type in the 2023 season?"
- "Who were the top 5 rushers in 2022?"

### Current Information (Web Search)
Ask questions like:
- "What are the latest NFL injury updates?"
- "Who won the most recent NFL game?"
- "What are the current playoff standings?"
- "What trades happened this week?"
- "What's the latest news about [player name]?"

## ✨ Features

- **Dual Data Sources**: Combines historical database with real-time web search
- **Smart Query Routing**: Automatically chooses database or web search based on question type, with direct routing for clear web queries
- **Web Search Caching**: Caches web search results for repeated queries (blazing fast)
- **Natural Language to SQL**: Converts questions to SQL queries using LangChain
- **Current NFL News**: Access to latest injury updates, trades, and game results via DuckDuckGo (`ddgs`)
- **Interactive Web Interface**: Beautiful Streamlit UI with query history and response time display
- **Real-time Debug Output**: See the agent's reasoning process
- **Schema-Aware Queries**: Uses comprehensive database schema context
- **Query History**: Save and reuse previous queries
- **Error Handling**: Graceful fallbacks and timeout protection
- **Optimized LLM**: Uses Together AI's `meta-llama/Llama-3-8b-chat-hf` for fast, reliable inference

## 🧠 Tech Stack

- **LangChain** - SQL agent orchestration and tool management
- **Together AI** (`meta-llama/Llama-3-8b-chat-hf`) - LLM for natural language processing
- **ddgs (DuckDuckGo Search)** - Web search for current NFL information (fast, modern)
- **Streamlit** - Interactive web interface
- **SQLite** - Local database with NFL play-by-play data
- **nflfastR** - Source of comprehensive NFL statistics

## 📁 Project Structure

```
nflStatsAgent/
├── agent.py              # Core agent logic with LangChain integration
├── app.py                # Streamlit web interface
├── explore.py            # Database schema extraction utility
├── schema_context.txt    # Database schema documentation
├── requirements.txt      # Python dependencies
├── setup.py              # Automated setup script
├── test_agent.py         # Agent testing utility
├── test_routing.py       # Query routing logic testing
├── query_examples.md     # Query examples and routing guide
├── config.example        # Example configuration file
├── data/
│   └── pbp_db           # SQLite database (2GB)
└── README.md            # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Together AI API key
- 2GB+ free disk space for the database

### Installation

#### Option 1: Automated Setup (Recommended)
```bash
git clone <your-repo-url>
cd nflStatsAgent
python setup.py
```

#### Option 2: Manual Setup
1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd nflStatsAgent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Copy `config.example` to `.env` and add your API key:
   ```bash
   cp config.example .env
   # Edit .env and add your Together AI API key
   ```

4. **Test the agent**
   ```bash
   python test_agent.py
   python test_routing.py  # Test query routing logic
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:8501`

## 📊 Database Schema

The application uses a comprehensive NFL database with the following main tables:

### `nflfastR_pbp` (Play-by-Play Data)
- **Game Information**: `game_id`, `home_team`, `away_team`, `week`, `season_type`
- **Play Details**: `play_type`, `desc`, `yards_gained`, `down`, `distance`
- **Player Stats**: `passer_player_name`, `rusher_player_name`, `receiver_player_name`
- **Advanced Metrics**: `epa`, `wpa`, `air_yards`, `yards_after_catch`
- **Situational Data**: `quarter`, `time`, `score_differential`

### `team_stats` (Aggregated Team Statistics)
- Team-level aggregations for easier analysis
- Win/loss records, scoring, and performance metrics

## 🎯 Example Queries

### Team Performance
- "Which team had the most passing yards in 2023?"
- "Show me the top 5 teams by rushing yards in 2022"
- "What was the Eagles' win percentage in 2023?"

### Player Analysis
- "Who were the top 10 quarterbacks by passing yards in 2023?"
- "Compare Patrick Mahomes and Josh Allen by EPA"
- "Which running back had the most touchdowns in 2022?"

### Game Situations
- "What's the success rate on 4th down attempts in the 4th quarter?"
- "How often do teams score when starting from their own 20-yard line?"
- "What's the average EPA on 3rd and long situations?"

### Advanced Analytics
- "Which teams had the highest WPA (Win Probability Added) in clutch situations?"
- "What's the correlation between air yards and completion percentage?"
- "Show me the most efficient red zone offenses in 2023"

### Current Events & News
- "What are the latest injury updates for key players?"
- "Who won the most recent Monday Night Football game?"
- "What trades happened during the recent trade deadline?"
- "What's the current status of the playoff race?"
- "What are the latest rumors about free agent signings?"

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TOGETHER_API_KEY` | Your Together AI API key | Required |
| `DB_PATH` | Path to SQLite database | `data/pbp_db` |
| `SCHEMA_FILE` | Path to schema context file | `schema_context.txt` |

### Agent Settings

The agent is optimized for speed and reliability:

```python
self._llm = Together(
    model="meta-llama/Llama-3-8b-chat-hf",  # Fast, serverless LLM
    temperature=0.2,                        # Creativity level (0-1)
    max_tokens=2048,
    together_api_key=os.getenv("TOGETHER_API_KEY")
)
```

- **Web search** uses the `ddgs` package for fast, reliable DuckDuckGo results.
- **Caching** is enabled for web search queries.
- **Tool routing** is optimized: clear web queries bypass the agent for instant answers.

## ⚡ Performance

- **Web search**: ~0.3s (cached or direct)
- **Database queries**: ~2s (LLM + SQL)
- **Hybrid/complex queries**: ~2-5s

## 🛠️ Development

### Adding New Features

1. **Custom Tools**: Add new LangChain tools in `agent.py`
2. **UI Enhancements**: Modify the Streamlit interface in `app.py`
3. **Schema Updates**: Run `python explore.py` to regenerate schema context

### Database Exploration

Use the `explore.py` script to extract and update the database schema:

```bash
python explore.py
```

This will regenerate `schema_context.txt` with the current database structure.

### Debugging

The application provides comprehensive debug output:
- **Agent Reasoning**: See the step-by-step thought process
- **SQL Queries**: View the generated SQL statements
- **Error Logs**: Detailed error messages and stack traces

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [nflfastR](https://github.com/nflverse/nflfastR) for the comprehensive NFL data
- [LangChain](https://langchain.com/) for the agent framework
- [Together AI](https://together.ai/) for the LLM infrastructure
- [Streamlit](https://streamlit.io/) for the web interface

## 📞 Support

For questions or issues:
1. Check the debug output for error details
2. Review the schema context for database structure
3. Open an issue on GitHub with your query and error details

---

**Happy analyzing! 🏈📊** 