# 🏈 NFL Stat Agent

An intelligent AI-powered agent that answers questions about NFL statistics and current events using a hybrid approach combining historical play-by-play data and real-time web search. The agent uses advanced filtering, parallel execution, and smart answer selection to provide accurate, up-to-date responses.

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

- **Hybrid Data Sources**: Combines historical nflfastR play-by-play database with real-time web search
- **Intelligent Filtering**: Two-stage filtering system (keyword pre-screening + LLM validation) for NFL relevance
- **Parallel Execution**: Simultaneous database and web search for optimal performance
- **Smart Answer Selection**: Comprehensive scoring system to select the best answer from multiple sources
- **Natural Language to SQL**: Converts questions to SQL queries using LangChain with enhanced schema context
- **Current NFL News**: Access to latest injury updates, trades, and game results via DuckDuckGo (`ddgs`)
- **Interactive Web Interface**: Beautiful Streamlit UI with query history and response time display
- **Real-time Debug Output**: See the agent's reasoning process and answer scoring
- **Enhanced Schema Context**: Comprehensive field descriptions with data types for better SQL generation
- **Query History**: Save and reuse previous queries
- **Error Handling**: Graceful fallbacks and timeout protection
- **Optimized LLMs**: Uses Together AI's Mixtral-8x7B for database queries and Llama-3-70B for web synthesis

## 🧠 Tech Stack

- **LangChain** - Agent orchestration and tool management
- **Together AI** - Multiple LLMs for different tasks:
  - **Mixtral-8x7B** - Database queries and SQL generation
  - **Llama-3-70B** - Web search synthesis and complex reasoning
- **ddgs (DuckDuckGo Search)** - Web search for current NFL information
- **Streamlit** - Interactive web interface
- **SQLite** - Local database with nflfastR play-by-play data
- **nflfastR** - Source of comprehensive NFL statistics

## 🏗️ Agent Architecture

### Flow Overview

The agent uses a sophisticated multi-stage approach to provide accurate answers:

```
1. Keyword Filter (Stage 1)
   ↓
2. LLM Query Classifier (Stage 2) - Only if Stage 1 inconclusive
   ↓
3. Parallel SQL and Web Execution
   ↓
4. Rating and Selecting Best Answer
```

### Detailed Flow

#### **Stage 1: Keyword Pre-screening**
- **Purpose**: Fast filtering for obvious NFL vs non-NFL cases
- **Method**: `_stage1_keyword_pre_screen()`
- **Logic**: Checks for core NFL terms (team names, players, football terms) vs obvious non-NFL terms
- **Output**: `(is_relevant, reason, is_conclusive)`

#### **Stage 2: LLM Classifier**
- **Purpose**: Only used when Stage 1 is inconclusive
- **Method**: `_stage2_llm_classifier()`
- **Logic**: Minimal LLM call with simple Y/N response for edge cases
- **Output**: `(is_relevant, reason)`

#### **Stage 3: Parallel Execution**
- **Purpose**: Run both database and web search simultaneously
- **Method**: `run_query_hybrid()` with `ThreadPoolExecutor`
- **Database**: `_run_database_query()` - SQL queries against nflfastR_pbp table
- **Web Search**: `_run_web_search()` - Web search for current NFL information

#### **Stage 4: Answer Selection**
- **Purpose**: Score and select the best answer
- **Method**: `_score_answer()`
- **Scoring Factors**:
  - Base score (10 points)
  - Length bonus (5 points for 50-500 chars)
  - Specificity bonus (3 points for NFL terms)
  - Number presence (2 points for stats)
  - Source credibility (5 points for database, 3 for reputable web sources)
  - Penalties for implausible numbers, coaching questions, low confidence phrases

## 📁 Project Structure

```
nflStatsAgent/
├── agent.py                    # Core agent logic with hybrid architecture
├── app.py                      # Streamlit web interface
├── landing_page.py             # Landing page for the application
├── sunday_spread.py            # Sunday spread analysis utility
├── explore.py                  # Database exploration utility
├── getDescriptions.R           # R script to generate field descriptions
├── requirements.txt            # Python dependencies
├── setup.py                    # Automated setup script
├── config.example              # Example configuration file
├── query_examples.md           # Query examples and usage guide
├── schema/
│   ├── schema_nflfastR_pbp.txt # nflfastR play-by-play schema
│   ├── field_descriptions.json # Enhanced field descriptions with data types
│   ├── schema_team_stats.txt   # Team stats schema (legacy)
│   └── schema_pregame_matchups.txt # Pregame matchups schema (legacy)
├── data/
│   └── pbp_db                  # SQLite database (2GB)
└── README.md                   # This file
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

The application uses the comprehensive nflfastR play-by-play database with enhanced field descriptions:

### `nflfastR_pbp` (Play-by-Play Data)
- **Game Information**: `game_id`, `home_team`, `away_team`, `week`, `season_type`
- **Play Details**: `play_type`, `desc`, `yards_gained`, `down`, `distance`
- **Player Stats**: `passer_player_name`, `rusher_player_name`, `receiver_player_name`
- **Advanced Metrics**: `epa`, `wpa`, `air_yards`, `yards_after_catch`
- **Situational Data**: `quarter`, `time`, `score_differential`
- **Enhanced Context**: Complete field descriptions with data types in `schema/field_descriptions.json`

### Schema Context
The agent uses comprehensive schema context including:
- **Original Schema**: `schema/schema_nflfastR_pbp.txt` with example queries and important notes
- **Field Descriptions**: `schema/field_descriptions.json` with detailed descriptions and data types for all 200+ fields
- **SQL Rules**: Built-in critical SQL rules for quarterback queries, time-based filtering, and team statistics

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

The agent uses multiple optimized LLMs for different tasks:

```python
# Database queries and SQL generation
self._llm = Together(
    model="mistralai/Mixtral-8x7B-Instruct-v0.1",
    temperature=0.2,
    max_tokens=2048,
    together_api_key=api_key
)

# Web search synthesis and complex reasoning
self._web_llm = Together(
    model="meta-llama/Llama-3-70b-chat-hf",
    temperature=0.2,
    max_tokens=2048,
    together_api_key=api_key
)

# Fast classification (minimal tokens)
self._classifier_llm = Together(
    model="mistralai/Mixtral-8x7B-Instruct-v0.1",
    temperature=0.1,
    max_tokens=3,  # Very small for Y/N responses
    together_api_key=api_key
)
```

- **Parallel execution** runs database and web search simultaneously
- **Smart filtering** uses two-stage approach for NFL relevance
- **Answer scoring** selects the best response from multiple sources

## ⚡ Performance

- **Keyword filtering**: ~0.01s (instant pre-screening)
- **LLM classification**: ~0.5s (only for inconclusive cases)
- **Parallel execution**: ~2-3s (both database and web search simultaneously)
- **Answer scoring**: ~0.1s (comprehensive quality assessment)
- **Total response time**: ~2-4s for most queries

## 🛠️ Development

### Adding New Features

1. **Custom Tools**: Add new LangChain tools in `agent.py`
2. **UI Enhancements**: Modify the Streamlit interface in `app.py`
3. **Schema Updates**: Run `python explore.py` to regenerate schema context
4. **Field Descriptions**: Run `Rscript getDescriptions.R` to update field descriptions

### Database Exploration

Use the `explore.py` script to extract and update the database schema:

```bash
python explore.py
```

### Field Descriptions

Generate enhanced field descriptions with data types:

```bash
Rscript getDescriptions.R
```

This creates `schema/field_descriptions.json` with comprehensive field documentation.

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