import os
from langchain.agents import initialize_agent, AgentType
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_together import Together
from langchain.tools import Tool
from dotenv import load_dotenv
from io import StringIO
from contextlib import redirect_stdout
from functools import lru_cache
import logging
from typing import Optional, Tuple
import re
from ddgs import DDGS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

SCHEMA_FILES = {
    "team_stats": "schema/schema_team_stats.txt",
    "nflfastR_pbp": "schema/schema_nflfastR_pbp.txt",
    "pregame_matchups": "schema/schema_pregame_matchups.txt"
}

class NFLStatAgent:
    def __init__(self):
        self._debug_output = ""
        self._initialized = False
        self._agent_executor = None
        self._web_agent_executor = None
        self._schema_context = ""
        self._initialize_resources()

    def _ddgs_web_search(self, query: str) -> str:
        """Perform a DuckDuckGo web search using ddgs and return a formatted string of results."""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
            if not results:
                return "No relevant web results found."
            formatted = "\n".join(f"{r['title']}: {r['href']}\n{r['body']}" for r in results if 'title' in r and 'href' in r and 'body' in r)
            return formatted or "No relevant web results found."
        except Exception as e:
            return f"Web search error: {str(e)}"

    def _initialize_resources(self):
        """Initialize database connection and load schema."""
        try:
            # Path to your SQLite file
            db_path = os.getenv("DB_PATH", os.path.join("data", "pbp_db"))
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"Database not found at: {db_path}")

            self._db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

            # Load schema context
            schema_file = os.getenv("SCHEMA_FILE", "schema_context.txt")
            if os.path.exists(schema_file):
                with open(schema_file, "r") as f:
                    self._schema_context = f.read()

            # Corrected LLM setup with Together.ai
            api_key = os.getenv("TOGETHER_API_KEY")
            if not api_key:
                raise ValueError("TOGETHER_API_KEY environment variable is required")
            
            # Use Llama-3-8B for database (default)
            self._llm = Together(
                model="deepseek-ai/deepseek-coder-33b-instruct",
                temperature=0.2,
                max_tokens=2048,
                together_api_key=api_key
            )

            # Use Llama-3-70B for web search synthesis
            self._web_llm = Together(
                model="meta-llama/Llama-3-70b-chat-hf",
                temperature=0.2,
                max_tokens=2048,
                together_api_key=api_key
            )

            # Create SQL database toolkit and tools
            sql_toolkit = SQLDatabaseToolkit(db=self._db, llm=self._llm)
            sql_tools = sql_toolkit.get_tools()

            # Create web search tool using ddgs
            web_tools = [
                Tool(
                    name="web_search",
                    func=self._ddgs_web_search,
                    description="Useful for finding current NFL news, recent game results, player injuries, trades, and information not available in the historical database. Use this for questions about current events, recent games, or breaking news."
                )
            ]

            # Create database agent
            self._agent_executor = initialize_agent(
                tools=sql_tools,
                llm=self._llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=3,
                early_stopping_method="generate"
            )

            # Create web search agent with Llama-3-70B
            self._web_agent_executor = initialize_agent(
                tools=web_tools,
                llm=self._web_llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=3,
                early_stopping_method="generate"
            )

            self._initialized = True
            logger.info("NFLStatAgent initialized successfully with database and web search capabilities")
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            raise

    def _should_use_web_search(self, question: str) -> bool:
        """
        Determine if the question should use web search instead of database.
        
        Args:
            question: The user's question
            
        Returns:
            True if web search should be used, False for database
        """
        question_lower = question.lower()
        
        # Keywords that indicate current/recent information
        current_keywords = [
            'today', 'yesterday', 'this week', 'last week', 'recent', 'latest',
            'breaking', 'news', 'injury', 'trade', 'signing', 'draft', 'free agency',
            'playoff', 'super bowl', 'championship', 'current', 'now', 'live',
            'score', 'result', 'game', 'match', 'tonight', 'tomorrow'
        ]
        
        # Keywords that indicate historical/statistical data (use database)
        historical_keywords = [
            'statistics', 'stats', 'record', 'history', 'career', 'season',
            'average', 'total', 'percentage', 'ranking', 'top', 'most', 'least',
            'compare', 'performance', 'yards', 'touchdowns', 'passing', 'rushing',
            'database', 'in the database', 'team', 'teams', 'player', 'players'
        ]
        
        # Check for specific year patterns - if it's a statistical query with a year, use database
        year_pattern = re.search(r'\b(19[0-9]{2}|20[0-2][0-9])\b', question_lower)
        if year_pattern:
            # If it's a statistical query with a specific year, prefer database
            if any(keyword in question_lower for keyword in historical_keywords):
                return False
        
        # Check for current time indicators
        current_indicators = sum(1 for keyword in current_keywords if keyword in question_lower)
        historical_indicators = sum(1 for keyword in historical_keywords if keyword in question_lower)
        
        # If more current indicators than historical, use web search
        if current_indicators > historical_indicators:
            return True
            
        # Check for specific current event patterns
        if re.search(r'\b(injured|injury|out|questionable|doubtful)\b', question_lower):
            return True
            
        if re.search(r'\b(trade|signing|free agent|draft pick)\b', question_lower):
            return True
            
        # Check for database-specific keywords (force database use)
        if re.search(r'\b(database|in the database|from the database)\b', question_lower):
            return False
            
        # Check for statistical patterns that should use database
        if re.search(r'\b(most|least|top|bottom|highest|lowest|average|total|sum|count)\b', question_lower):
            return False  # Statistical queries should use database
        
        # Default to database for statistical questions
        return False

    def _get_appropriate_table_name(self, question: str) -> str:
        """Return the best table name for the query."""
        question_lower = question.lower()
        team_stats_keywords = [
            'team', 'teams', 'win', 'loss', 'record', 'win percentage', 'streak',
            'rolling', 'cumulative', 'season', 'yearly', 'offensive', 'defensive',
            'epa', 'wpa', 'elo', 'dominance', 'clutch', 'qb', 'quarterback'
        ]
        pbp_keywords = [
            'play', 'plays', 'play by play', 'individual', 'player', 'specific',
            'down', 'distance', 'yard', 'touchdown', 'field goal', 'punt',
            'interception', 'fumble', 'sack', 'pass', 'rush', 'reception',
            'quarter', 'drive', 'possession', 'game situation', 'clutch',
            'epa', 'wpa', 'air yards', 'yards after catch'
        ]
        matchup_keywords = [
            'matchup', 'match up', 'game prediction', 'spread', 'vegas',
            'win probability', 'pre game', 'pregame', 'before game',
            'head to head', 'versus', 'vs', 'against', 'home team', 'away team',
            'favorite', 'underdog', 'odds', 'betting'
        ]
        team_stats_score = sum(1 for keyword in team_stats_keywords if keyword in question_lower)
        pbp_score = sum(1 for keyword in pbp_keywords if keyword in question_lower)
        matchup_score = sum(1 for keyword in matchup_keywords if keyword in question_lower)
        if 'win probability' in question_lower:
            matchup_score += 2
        if 'head to head' in question_lower or 'matchup' in question_lower:
            matchup_score += 2
        if matchup_score > team_stats_score and matchup_score > pbp_score:
            return "pregame_matchups"
        elif pbp_score > team_stats_score:
            return "nflfastR_pbp"
        else:
            return "team_stats"

    def _get_appropriate_table_context(self, question: str) -> str:
        """Always use the nflfastR_pbp table for all queries."""
        try:
            with open("schema/schema_nflfastR_pbp.txt", 'r') as f:
                schema_content = f.read()
            return f"Use the nflfastR_pbp table with the following schema:\n\n{schema_content}"
        except FileNotFoundError:
            logger.error("Schema file schema/schema_nflfastR_pbp.txt not found")
            return "Use the nflfastR_pbp table (schema file not found)"

    def _run_database_query(self, question: str) -> Tuple[str, Optional[str]]:
        """Run a query against the NFL stats database using only the relevant table schema."""
        try:
            table_context = self._get_appropriate_table_context(question)
            
            full_prompt = f"""You are a helpful assistant that answers questions using the NFL play-by-play database.

{table_context}

CRITICAL RULES FOR nflfastR_pbp TABLE:

1. TEAM STATISTICS REQUIREMENT:
   - For offensive team stats (passing yards, rushing yards, touchdowns, etc.), use the posteam field
   - posteam indicates which team has possession and should be credited with offensive stats
   - DO NOT use home_team/away_team for offensive statistics - this will double-count
   - Use simple GROUP BY posteam for offensive team stats

2. REGULAR SEASON FILTERING:
   - Unless specifically asked about playoffs, ALWAYS filter for regular season games
   - Use WHERE week BETWEEN 1 AND 18 (NFL regular season is weeks 1-18)
   - This ensures you're not including playoff games in regular season stats
   - Example: WHERE season = 2023 AND week BETWEEN 1 AND 18

3. CORRECT PATTERN FOR OFFENSIVE TEAM STATS:
   ```sql
   SELECT posteam as team, SUM(stat_column) as total_stat
   FROM nflfastR_pbp 
   WHERE season = 2023 AND week BETWEEN 1 AND 18
   GROUP BY posteam
   ORDER BY total_stat DESC
   ```

4. SPECIFIC EXAMPLES:
   - Passing yards: SUM(passing_yards) WHERE posteam = team
   - Rushing yards: SUM(rushing_yards) WHERE posteam = team
   - Touchdowns: SUM(pass_touchdown + rush_touchdown) WHERE posteam = team
   - Interceptions: SUM(interception) WHERE posteam = team
   - Sacks: SUM(sack) WHERE defteam = team (defensive stat)

5. SEASON FILTERING:
   - Use WHERE season = 2023 (not year)
   - For multiple seasons: WHERE season IN (2022, 2023)
   - Always combine with week filter: WHERE season = 2023 AND week BETWEEN 1 AND 18

6. PLAYER STATS:
   - For player queries, use player_name column
   - Filter by posteam for offensive player stats
   - Filter by defteam for defensive player stats

7. GAME-LEVEL QUERIES:
   - For game results, use home_score and away_score
   - For specific games, use game_id
   - For playoff queries, use week > 18

8. DEFENSIVE STATS:
   - For defensive stats (sacks, interceptions against), use defteam field
   - defteam indicates the defensive team

Now answer the user's question:
{question}

Please show the SQL query you used to get your answer."""
            if not self._agent_executor:
                return "", "Database agent not initialized"
            buffer = StringIO()
            with redirect_stdout(buffer):
                result = self._agent_executor.invoke({"input": full_prompt})
            self._debug_output = buffer.getvalue()
            return result["output"], None
        except Exception as e:
            error_msg = f"Database query error: {str(e)}"
            logger.error(error_msg)
            return "", error_msg

    def run_query(self, question: str, show_reasoning: bool = False) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Execute a query using either database or web search based on the question type.
        
        Args:
            question: The question to answer about NFL stats or current events
            show_reasoning: If True, return the latest reasoning step
            
        Returns:
            Tuple of (answer, error, reasoning) where error is None if successful
        """
        if not self._initialized:
            return "", "Agent not initialized", None

        try:
            # Basic input validation
            if not question or len(question.strip()) < 3:
                return "", "Query is too short", None

            # Clear previous debug output
            self._debug_output = ""

            # Determine whether to use database or web search
            use_web_search = self._should_use_web_search(question)
            
            if use_web_search:
                logger.info(f"Using web search for query: {question[:50]}...")
                answer, error = self._run_web_search(question)
            else:
                logger.info(f"Using database for query: {question[:50]}...")
                answer, error = self._run_database_query(question)

            reasoning = self.get_debug_logs(latest_only=True) if show_reasoning else None
            return answer, error, reasoning
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            logger.error(error_msg)
            return "", error_msg, None

    def _run_web_search(self, question: str) -> Tuple[str, Optional[str]]:
        """Run a web search for current NFL information."""
        try:
            full_prompt = f"""You are a helpful assistant that answers questions about current NFL news, games, and events using web search.

SYNTHESIS INSTRUCTIONS:
- Synthesize information from multiple sources (StatMuse, ESPN, NFL.com, Pro-Football-Reference, etc.)
- Prefer answers that are consistent across multiple reputable sources
- If sources disagree, state the disagreement and show the most likely answer
- If the answer is not found, say so
- Do NOT hallucinate numbers or facts not present in the snippets
- Give a direct, factual answer first
- Cleanly cite sources (e.g., "According to ESPN and StatMuse") but do NOT include long URLs
- Keep the response concise, well-formatted, and focused on the most relevant information
- If the answer is ambiguous, explain why

Focus on providing accurate, up-to-date information about:
- Recent game results and scores
- Player injuries and status updates
- Trades, signings, and roster moves
- Current season standings and playoff races
- Breaking news and developments

Answer the user's question with current, factual information:
{question}
"""
            if not self._web_agent_executor:
                return "", "Web search agent not initialized"
                
            buffer = StringIO()
            with redirect_stdout(buffer):
                result = self._web_agent_executor.invoke({"input": full_prompt})
            
            self._debug_output = buffer.getvalue()
            return result["output"], None
        except Exception as e:
            error_msg = f"Web search error: {str(e)}"
            logger.error(error_msg)
            return "", error_msg

    def get_debug_logs(self, latest_only: bool = False) -> str:
        """Get the debug logs from the last query execution. If latest_only, return only the latest step."""
        if not latest_only:
            return self._debug_output
        # Extract the latest reasoning step (last non-empty line)
        lines = [line.strip() for line in self._debug_output.splitlines() if line.strip()]
        if not lines:
            return ""
        # Find the last line that looks like a reasoning/thought step
        for line in reversed(lines):
            # Heuristic: look for lines that start with 'Thought:' or 'Action:' or 'Observation:'
            if any(line.lower().startswith(prefix) for prefix in ["thought:", "action:", "observation:", "reasoning:", "step:", "intermediate step:"]):
                return line
        # Fallback: just return the last non-empty line
        return lines[-1]

    @lru_cache(maxsize=128)
    def _cached_ddgs_web_search(self, query: str) -> str:
        return self._ddgs_web_search(query)

    def run_query_hybrid(self, question: str, show_reasoning: bool = False) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Hybrid approach: Try web search first for a direct, high-confidence answer. If the web answer is missing nuance, is low confidence, or says 'not found', fall back to the database. If the database answer is also low confidence or missing, return the best related web answer with a disclaimer about limitations.
        """
        if not self._initialized:
            return "", "Agent not initialized", None

        try:
            if not question or len(question.strip()) < 3:
                return "", "Query is too short", None

            self._debug_output = ""

            # Try web search first and save the answer
            logger.info(f"Trying web search first for: {question[:50]}...")
            web_answer, web_error = self._run_web_search(question)
            web_answer_clean = web_answer.strip() if web_answer else ""

            # Heuristic: If web answer is direct, relevant, and matches nuance, use it
            low_conf_phrases = [
                "not found", "could not find", "no information", "no data", "not available", "couldn't find", "no answer"
            ]
            is_low_conf = (
                not web_answer_clean or web_error or len(web_answer_clean) < 50 or
                any(phrase in web_answer_clean.lower() for phrase in low_conf_phrases)
            )
            nuance_keywords = ["road", "away", "visitor", "on the road"]
            if not is_low_conf:
                if any(word in question.lower() for word in nuance_keywords):
                    if any(word in web_answer_clean.lower() for word in nuance_keywords):
                        logger.info("Web search provided nuanced answer, using it")
                        return web_answer_clean, None, "Used web search for nuanced stat lookup"
                else:
                    logger.info("Web search provided good answer, using it")
                    return web_answer_clean, None, "Used web search for quick stat lookup"

            # If web answer is low confidence or missing nuance, try database
            logger.info("Web search was low confidence or missing nuance, trying database...")
            db_answer, db_error = self._run_database_query(question)
            db_answer_clean = db_answer.strip() if db_answer else ""

            # Heuristic: If DB answer is plausible (not empty, not huge, not zero), use it
            plausible = db_answer_clean and not db_error and len(db_answer_clean) > 10 and not any(x in db_answer_clean for x in ["999", "1035", "0 road games", "no data"])
            if plausible:
                logger.info("Database provided plausible answer, using it")
                return db_answer_clean, None, "Used database for detailed analysis"

            # If DB answer is low confidence or missing, return best web answer with disclaimer
            if web_answer_clean:
                disclaimer = "No direct answer was found in the database. Here is the closest related stat from the web, but it may not exactly match your question:\n"
                return disclaimer + web_answer_clean, None, "DB fallback failed, using best web answer with disclaimer"
            else:
                return "No direct answer was found in the database or on the web.", None, "No answer found"

        except Exception as e:
            error_msg = f"Hybrid agent error: {str(e)}"
            logger.error(error_msg)
            return "", error_msg, None

@lru_cache(maxsize=1)
def get_agent() -> NFLStatAgent:
    return NFLStatAgent()

def run_query(question: str, show_reasoning: bool = False) -> Tuple[str, Optional[str], Optional[str]]:
    """Public interface to run a query."""
    return get_agent().run_query(question, show_reasoning=show_reasoning)

def get_debug_logs(latest_only: bool = False) -> str:
    """Public interface to get debug logs."""
    return get_agent().get_debug_logs(latest_only=latest_only)

def run_query_hybrid(question: str, show_reasoning: bool = False) -> Tuple[str, Optional[str], Optional[str]]:
    """Public interface to run the agent-based hybrid query."""
    return get_agent().run_query_hybrid(question, show_reasoning=show_reasoning)