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

            # Load the full nflfastR_pbp schema (not schema_context.txt or others)
            self._schema_context = ""
            schema_file = "schema/schema_nflfastR_pbp.txt"
            if os.path.exists(schema_file):
                with open(schema_file, "r") as f:
                    self._schema_context = f.read()

            # Corrected LLM setup with Together.ai
            api_key = os.getenv("TOGETHER_API_KEY")
            if not api_key:
                raise ValueError("TOGETHER_API_KEY environment variable is required")
            # Use a model with larger context window for database queries
            self._llm = Together(
                model="mistralai/Mixtral-8x7B-Instruct-v0.1",
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
        """Always use the nflfastR_pbp table for all queries with the full schema."""
        if self._schema_context:
            return f"Use the nflfastR_pbp table with the following schema:\n\n{self._schema_context}"
        else:
            return "Use the nflfastR_pbp table (schema file not found)"

    def _run_database_query(self, question: str) -> Tuple[str, Optional[str]]:
        """Run a query against the NFL stats database using only the relevant table schema."""
        try:
            table_context = self._get_appropriate_table_context(question)
            
            full_prompt = f"""Answer this NFL question using the database: {question}

{table_context}

CRITICAL SQL RULES:
1. QUARTERBACK QUERIES:
   - Use passer_player_name (NOT posteam_player_name or player_name)
   - For passing touchdowns: use pass_touchdown = 1 (NOT touchdown)
   - Group by passer_player_name for quarterback stats

2. TIME-BASED QUERIES:
   - Last 2 minutes: game_seconds_remaining BETWEEN 0 AND 120
   - Last 5 minutes: game_seconds_remaining BETWEEN 0 AND 300
   - Last quarter: game_seconds_remaining BETWEEN 0 AND 900

3. SEASON FILTERING:
   - 2024 regular season: WHERE season = 2024 AND week BETWEEN 1 AND 18
   - 2023 regular season: WHERE season = 2023 AND week BETWEEN 1 AND 18

4. PLAY TYPE FILTERING:
   - Passing plays: play_type = 'pass'
   - Rushing plays: play_type = 'run'
   - All plays: no play_type filter needed

5. TOUCHDOWN TYPES:
   - Passing touchdowns: pass_touchdown = 1
   - Rushing touchdowns: rush_touchdown = 1
   - All touchdowns: touchdown = 1

6. TEAM vs PLAYER STATS:
   - Team offensive stats: GROUP BY posteam
   - Player stats: GROUP BY passer_player_name (passing) or rusher_player_name (rushing)

EXAMPLE QUERIES:
- QB passing TDs: SELECT passer_player_name, COUNT(*) FROM nflfastR_pbp WHERE season=2024 AND week BETWEEN 1 AND 18 AND play_type='pass' AND pass_touchdown=1 GROUP BY passer_player_name
- Last 2 min TDs: SELECT passer_player_name, COUNT(*) FROM nflfastR_pbp WHERE season=2024 AND week BETWEEN 1 AND 18 AND game_seconds_remaining BETWEEN 0 AND 120 AND pass_touchdown=1 GROUP BY passer_player_name

IMPORTANT: Execute your SQL query and provide the actual result with the player name and count. Include the raw data from the query result in your answer so it can be formatted properly. Do not just show the SQL - give the final answer with the data.

FORMAT: After executing the query, include the raw result data in your answer like this:
"Query result: [('Player1', 5), ('Player2', 3), ...]"
Then provide your summary.

CRITICAL: You MUST include the actual query results in your answer. Do not make up generic responses like 'Player1 with X touchdowns'. Use the real data from the database."""
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
        Execute a query using the hybrid approach: try database first, fall back to web search if needed.
        
        Args:
            question: The question to answer about NFL stats or current events
            show_reasoning: If True, return the latest reasoning step
            
        Returns:
            Tuple of (answer, error, reasoning) where error is None if successful
        """
        return self.run_query_hybrid(question, show_reasoning=show_reasoning)

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
        Parallel approach: Query both database and web search simultaneously, then compare and select the best answer.
        """
        if not self._initialized:
            return "", "Agent not initialized", None

        try:
            if not question or len(question.strip()) < 3:
                return "", "Query is too short", None

            self._debug_output = ""

            # Run both agents in parallel
            logger.info(f"Running both database and web search in parallel for: {question[:50]}...")
            
            import concurrent.futures
            import time
            
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                # Submit both tasks
                web_future = executor.submit(self._run_web_search, question)
                db_future = executor.submit(self._run_database_query, question)
                
                # Get results
                web_answer, web_error = web_future.result()
                db_answer, db_error = db_future.result()
            
            execution_time = time.time() - start_time
            logger.info(f"Both agents completed in {execution_time:.2f} seconds")
            
            web_answer_clean = web_answer.strip() if web_answer else ""
            db_answer_clean = db_answer.strip() if db_answer else ""
            
            # Score and compare answers
            web_score = self._score_answer(web_answer_clean, web_error, "web")
            db_score = self._score_answer(db_answer_clean, db_error, "database")
            
            logger.info(f"Web score: {web_score}, Database score: {db_score}")
            
            # Select best answer
            if db_score > web_score and db_score > 0:
                logger.info("Database provided better answer, using it")
                return db_answer_clean, None, f"Used database (score: {db_score}) - better than web (score: {web_score})"
            elif web_score > 0:
                logger.info("Web search provided better answer, using it")
                return web_answer_clean, None, f"Used web search (score: {web_score}) - better than database (score: {db_score})"
            else:
                # Both failed, return best available with disclaimer
                if web_answer_clean:
                    disclaimer = "Neither source provided a high-confidence answer. Here is the best available information from the web:\n"
                    return disclaimer + web_answer_clean, None, "Both sources low confidence, using best web answer"
                elif db_answer_clean:
                    disclaimer = "Neither source provided a high-confidence answer. Here is the best available information from the database:\n"
                    return disclaimer + db_answer_clean, None, "Both sources low confidence, using best database answer"
                else:
                    return "No answer found from either database or web search.", None, "No answer found from either source"

        except Exception as e:
            error_msg = f"Parallel agent error: {str(e)}"
            logger.error(error_msg)
            return "", error_msg, None

    def _score_answer(self, answer: str, error: Optional[str], source: str) -> float:
        """
        Score an answer based on various quality metrics.
        Higher score = better answer.
        """
        if error or not answer:
            return 0.0
        
        score = 0.0
        
        # Base score for having an answer
        score += 10.0
        
        # Length bonus (but not too long)
        if 50 <= len(answer) <= 500:
            score += 5.0
        elif len(answer) > 500:
            score += 2.0  # Penalty for very long answers
        
        # Specificity bonus
        if any(word in answer.lower() for word in ["quarterback", "team", "player", "touchdown", "yard", "game", "season"]):
            score += 3.0
        
        # Number presence bonus (for statistical queries)
        if re.search(r'\d+', answer):
            score += 2.0
        
        # Source credibility bonus
        if source == "database":
            score += 5.0  # Database is generally more reliable for stats
        elif source == "web":
            if any(source in answer.lower() for source in ["espn", "nfl.com", "pro-football-reference", "statmuse"]):
                score += 3.0
        
        # Penalty for low confidence indicators
        low_conf_phrases = [
            "not found", "could not find", "no information", "no data", "not available", 
            "couldn't find", "no answer", "insert name here", "unknown"
        ]
        if any(phrase in answer.lower() for phrase in low_conf_phrases):
            score -= 10.0
        
        # Penalty for implausible numbers (very high stats that seem unrealistic)
        if source == "web":
            # Check for implausibly high numbers that might be misinterpreted
            numbers = re.findall(r'\d+', answer)
            for num in numbers:
                num_int = int(num)
                if num_int > 100:  # Very high numbers might be season totals, not specific stats
                    score -= 2.0
        
        return max(0.0, score)

    def _format_tabular_data(self, answer: str) -> str:
        """
        Convert tabular data in the answer to markdown table format.
        """
        # Look for patterns that indicate tabular data
        # Pattern 1: List of tuples like [("A.O'Connell", 2), ('A.Richardson', 2), ...]
        tuple_pattern = r'\[\(([^)]+)\),\s*\(([^)]+)\)(?:,\s*\(([^)]+)\))*\]'
        
        # Pattern 2: Multiple lines with | separators
        table_pattern = r'([^|]+\|[^|]+(?:\|[^|]+)*)'
        
        # Pattern 3: Data in parentheses format
        paren_pattern = r'\(([^)]+)\)'
        
        # Try to extract and format tuple data
        if '[' in answer and ']' in answer and '(' in answer and ')' in answer:
            # Extract the tuple data
            start = answer.find('[')
            end = answer.find(']')
            if start != -1 and end != -1:
                tuple_data = answer[start:end+1]
                
                # Parse the tuples
                import ast
                try:
                    data_list = ast.literal_eval(tuple_data)
                    if isinstance(data_list, list) and len(data_list) > 0:
                        # Create markdown table
                        table_lines = []
                        
                        # Determine headers based on first item
                        if len(data_list[0]) == 2:
                            headers = ["Player", "Count"]
                        elif len(data_list[0]) == 3:
                            headers = ["Player", "Stat1", "Stat2"]
                        else:
                            headers = [f"Column{i+1}" for i in range(len(data_list[0]))]
                        
                        # Add header
                        table_lines.append("| " + " | ".join(headers) + " |")
                        table_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                        
                        # Add data rows
                        for row in data_list:
                            formatted_row = []
                            for item in row:
                                if item is None:
                                    formatted_row.append("N/A")
                                else:
                                    formatted_row.append(str(item))
                            table_lines.append("| " + " | ".join(formatted_row) + " |")
                        
                        # Replace the tuple data with the markdown table
                        markdown_table = "\n".join(table_lines)
                        formatted_answer = answer.replace(tuple_data, f"\n\n{markdown_table}\n\n")
                        return formatted_answer
                        
                except (ValueError, SyntaxError):
                    pass
        
        return answer

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