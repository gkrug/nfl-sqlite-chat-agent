import os
from langchain.agents import initialize_agent, AgentType
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
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

class NFLStatAgent:
    def __init__(self):
        self._debug_output = ""
        self._initialized = False
        self._agent_executor = None
        self._web_agent_executor = None
        self._schema_context = ""
        self._last_question = ""  # Track the current question for scoring
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

            # Only load the concise schema context file
            self._schema_context = ""
            schema_file = "schema/schema_nflfastR_pbp.txt"
            if os.path.exists(schema_file):
                with open(schema_file, "r") as f:
                    self._schema_context = f.read()

            # Corrected LLM setup with Together.ai
            api_key = os.getenv("TOGETHER_API_KEY")
            if not api_key:
                raise ValueError("TOGETHER_API_KEY not set in environment.")
            self._llm = Together(
                model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                temperature=0.2,
                max_tokens=2048,
                together_api_key=api_key
            )
            self._web_llm = Together(
                model="meta-llama/Llama-3-70b-chat-hf",
                temperature=0.2,
                max_tokens=2048,
                together_api_key=api_key
            )
            # Use a smaller, faster model for classification with minimal tokens
            self._classifier_llm = Together(
                model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                temperature=0.1,
                max_tokens=3,  # Very small for Y/N responses
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
            logger.error(f"Initialization error: {e}")
            raise

    def _stage1_keyword_pre_screen(self, question: str) -> Tuple[bool, str, bool]:
        """
        Stage 1: Fast keyword pre-screening for obvious cases.
        
        Args:
            question: The user's question
            
        Returns:
            Tuple of (is_relevant, reason, is_conclusive) where:
            - is_relevant: True if NFL-related, False if not
            - reason: Explanation of the decision
            - is_conclusive: True if we can make a confident decision, False if inconclusive
        """
        if not question or len(question.strip()) < 3:
            return False, "Query is too short", True
        
        question_lower = question.lower()
        
        # Core NFL terms that strongly indicate relevance
        core_nfl_terms = [
            'nfl', 'football', 'super bowl', 'mahomes', 'brady', 'allen', 'burrow',
            'patriots', 'bills', 'dolphins', 'jets', 'ravens', 'bengals', 'browns',
            'steelers', 'texans', 'colts', 'jaguars', 'titans', 'broncos', 'chiefs',
            'raiders', 'chargers', 'cowboys', 'giants', 'eagles', 'commanders',
            'bears', 'lions', 'packers', 'vikings', 'falcons', 'panthers', 'saints',
            'buccaneers', 'cardinals', 'rams', '49ers', 'seahawks'
        ]
        
        # Obvious non-NFL terms that strongly indicate irrelevance
        obvious_non_nfl_terms = [
            'basketball', 'nba', 'baseball', 'mlb', 'hockey', 'nhl', 'soccer',
            'tennis', 'golf', 'olympics', 'world cup', 'champions league',
            'politics', 'election', 'president', 'congress', 'government',
            'economy', 'stock', 'market', 'business', 'company', 'corporate',
            'technology', 'computer', 'software', 'programming', 'code',
            'science', 'research', 'study', 'medical', 'health', 'disease',
            'weather', 'climate', 'temperature', 'forecast',
            'music', 'movie', 'film', 'actor', 'actress', 'celebrity',
            'food', 'recipe', 'cooking', 'restaurant', 'cuisine',
            'travel', 'vacation', 'hotel', 'flight', 'destination',
            'education', 'school', 'university', 'college', 'student',
            'painting', 'sculpture', 'museum', 'gallery',
            'capital', 'france', 'python', 'learn'
        ]
        
        # Check for core NFL terms
        nfl_hits = [term for term in core_nfl_terms if term in question_lower]
        if nfl_hits:
            return True, f"Contains core NFL terms: {', '.join(nfl_hits[:3])}", True
        
        # Check for obvious non-NFL terms
        non_nfl_hits = [term for term in obvious_non_nfl_terms if term in question_lower]
        if non_nfl_hits:
            return False, f"Contains non-NFL terms: {', '.join(non_nfl_hits[:3])}", True
        
        # If neither clear NFL nor clear non-NFL terms, it's inconclusive
        return False, "No clear NFL or non-NFL terms detected", False

    def _stage2_llm_classifier(self, question: str) -> Tuple[bool, str]:
        """
        Stage 2: Minimal LLM classifier for inconclusive cases.
        Uses very small max_tokens and simple Y/N response.
        
        Args:
            question: The user's question
            
        Returns:
            Tuple of (is_relevant, reason) where reason explains the LLM decision
        """
        try:
            prompt = f"""Is this question about NFL (American football) statistics, players, teams, or current NFL news?

Question: "{question}"

Answer with ONLY "Y" for NFL-related or "N" for not NFL-related.

IMPORTANT: Answer "Y" if the question is about:
- NFL statistics, records, or performance
- NFL players, teams, or coaches
- NFL games, seasons, or current events
- Football-related queries that are clearly about American football

Answer "N" only if the question is clearly about:
- Other sports (basketball, baseball, soccer, etc.)
- Non-sports topics (weather, politics, cooking, etc.)
- Completely ambiguous questions with no context

Examples:
- "Who has the most passing touchdowns in the NFL?" → Y
- "Who has the most passing touchdowns?" → Y (context suggests NFL)
- "Which quarterback had the most yards?" → Y (quarterback = NFL)
- "What's the weather like?" → N
- "How did the Chiefs do?" → Y (NFL team)
- "Who won the NBA championship?" → N
- "What team scored the most points?" → Y (team + points = likely NFL)

Answer:"""

            # Use the classifier LLM with minimal tokens
            if not self._classifier_llm:
                return False, "LLM not available for classification"
            
            # Use the classifier LLM (already configured with max_tokens=3)
            response = self._classifier_llm.invoke(prompt)
            response_text = response.strip().upper()
            
            # Log for offline review
            logger.info(f"LLM classification - Question: '{question[:100]}...' | Response: '{response_text}'")
            
            # Handle empty or unclear responses
            if not response_text:
                logger.warning(f"Empty LLM response for question: '{question[:50]}...'")
                return False, "LLM returned empty response, defaulting to not NFL-related"
            
            # Clean up the response (remove quotes, extra whitespace)
            response_text = response_text.strip().strip('"').strip("'").strip()
            
            if response_text.startswith("Y"):
                return True, "LLM classified as NFL-related"
            elif response_text.startswith("N"):
                return False, "LLM classified as not NFL-related"
            else:
                # Fallback for unclear responses
                logger.warning(f"Unclear LLM response: '{response_text}' for question: '{question[:50]}...'")
                return False, "LLM response unclear, defaulting to not NFL-related"
                
        except Exception as e:
            logger.warning(f"LLM classification failed: {str(e)} for question: '{question[:50]}...'")
            return False, f"LLM classification failed: {str(e)}"

    def _is_nfl_relevant_hybrid(self, question: str) -> Tuple[bool, str]:
        """
        Two-stage hybrid filtering approach:
        Stage 1: Fast keyword pre-screening for obvious cases
        Stage 2: Minimal LLM classifier only for inconclusive cases
        
        Args:
            question: The user's question
            
        Returns:
            Tuple of (is_relevant, reason) where reason explains why it's relevant or not
        """
        # Stage 1: Fast keyword pre-screening
        is_relevant, reason, is_conclusive = self._stage1_keyword_pre_screen(question)
        
        if is_conclusive:
            # Stage 1 made a confident decision - use it
            return is_relevant, f"Stage 1 (keyword): {reason}"
        
        # Stage 2: LLM classifier for inconclusive cases
        logger.info(f"Stage 1 inconclusive for: '{question[:50]}...', using Stage 2 LLM classifier")
        llm_relevant, llm_reason = self._stage2_llm_classifier(question)
        
        return llm_relevant, f"Stage 2 (LLM): {llm_reason}"





    def _get_table_context(self, question: str) -> str:
        """Get the nflfastR_pbp table context with schema only."""
        if self._schema_context:
            return f"Use the nflfastR_pbp table with the following schema:\n\n{self._schema_context}"
        else:
            return "Use the nflfastR_pbp table (schema file not found)"

    def _run_database_query(self, question: str) -> Tuple[str, Optional[str]]:
        """Run a query against the NFL stats database using the nflfastR_pbp table."""
        try:
            table_context = self._get_table_context(question)
            
            full_prompt = f"""Answer this NFL question using the database: {question}

{table_context}

CRITICAL SQL RULES:
0. TABLE GRANULARITY:
   - Each row in the nflfastR_pbp table represents a single play, NOT a game.
   - For any question about games (e.g., wins, games covered, games played), you MUST aggregate by unique game_id for the relevant team.
   - Use COUNT(DISTINCT game_id) to count games, NOT COUNT(*), which counts plays.

1. QUARTERBACK QUERIES:
   - Use passer_player_name (NOT posteam_player_name or player_name)
   - For passing touchdowns: use pass_touchdown = 1 (NOT touchdown)
   - Group by passer_player_name for quarterback stats

2. TIME-BASED QUERIES:
   - Last 2 minutes: game_seconds_remaining BETWEEN 0 AND 120
   - Last 5 minutes: game_seconds_remaining BETWEEN 0 AND 300
   - Last quarter: game_seconds_remaining BETWEEN 0 AND 900

3. SEASON FILTERING:
   - Current season (2025): WHERE season = 2025 AND week BETWEEN 1 AND 18
   - Last season (2024): WHERE season = 2024 AND week BETWEEN 1 AND 18
   - Last two years: WHERE season IN (2023, 2024) AND week BETWEEN 1 AND 18
   - Last three years: WHERE season IN (2022, 2023, 2024) AND week BETWEEN 1 AND 18

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

7. TEAM SCORING (CRITICAL):
   - home_team_score, away_team_score, total_home_score, total_away_score are CUMULATIVE during the game
   - For final game scores, you MUST use MAX(total_home_score) and MAX(total_away_score) grouped by game_id
   - Example: SELECT game_id, MAX(total_away_score) as final_away_score, MAX(total_home_score) as final_home_score FROM nflfastR_pbp WHERE season=2024 GROUP BY game_id

8. SPREAD COVERAGE (CRITICAL):
   - spread_line: positive means home team favored, negative means away team favored, 0 means pick'em
   - For away team coverage, you MUST use final scores (MAX values):
     * If spread_line > 0: away covers if MAX(total_away_score) + spread_line > MAX(total_home_score)
     * If spread_line < 0: away covers if MAX(total_away_score) > MAX(total_home_score)  
     * If spread_line = 0: away covers if MAX(total_away_score) > MAX(total_home_score)
   - ALWAYS use WITH final_scores AS (SELECT game_id, away_team, home_team, spread_line, MAX(total_away_score) as final_away_score, MAX(total_home_score) as final_home_score FROM nflfastR_pbp WHERE season=2024 AND week BETWEEN 1 AND 18 GROUP BY game_id)

9. TEAM WINS QUERIES:
   - For team wins, you need to count GAMES won, not plays
   - Each team plays 17-18 games per season
   - A team wins a game if they have more points at the end
   - Use game_id to group by individual games, not plays
   - Example: SELECT home_team, COUNT(DISTINCT game_id) as wins FROM nflfastR_pbp WHERE season IN (2023, 2024) AND week BETWEEN 1 AND 18 AND home_team_score > away_team_score GROUP BY home_team, game_id

EXAMPLE QUERIES:
- QB passing TDs (current season): SELECT passer_player_name, COUNT(*) FROM nflfastR_pbp WHERE season=2025 AND week BETWEEN 1 AND 18 AND play_type='pass' AND pass_touchdown=1 GROUP BY passer_player_name
- QB passing TDs (last two years): SELECT passer_player_name, COUNT(*) FROM nflfastR_pbp WHERE season IN (2023, 2024) AND week BETWEEN 1 AND 18 AND play_type='pass' AND pass_touchdown=1 GROUP BY passer_player_name
- Team wins (last two years): SELECT home_team, COUNT(DISTINCT game_id) as wins FROM nflfastR_pbp WHERE season IN (2023, 2024) AND week BETWEEN 1 AND 18 AND home_team_score > away_team_score GROUP BY home_team
- Last 2 min TDs: SELECT passer_player_name, COUNT(*) FROM nflfastR_pbp WHERE season=2025 AND week BETWEEN 1 AND 18 AND game_seconds_remaining BETWEEN 0 AND 120 AND pass_touchdown=1 GROUP BY passer_player_name
- Road spread covers (2024): WITH final_scores AS (SELECT game_id, away_team, home_team, spread_line, MAX(total_away_score) as final_away_score, MAX(total_home_score) as final_home_score FROM nflfastR_pbp WHERE season=2024 AND week BETWEEN 1 AND 18 GROUP BY game_id) SELECT away_team, COUNT(DISTINCT game_id) as covers FROM final_scores WHERE ((spread_line > 0 AND final_away_score + spread_line > final_home_score) OR (spread_line < 0 AND final_away_score > final_home_score) OR (spread_line = 0 AND final_away_score > final_home_score)) GROUP BY away_team ORDER BY covers DESC LIMIT 1

CRITICAL: For team wins, use COUNT(DISTINCT game_id) to count games, not COUNT(*) which counts plays!

IMPORTANT: Execute your SQL query and provide the actual result with the player name and count. Include the raw data from the query result in your answer so it can be formatted properly. Do not just show the SQL - give the final answer with the data.

FORMAT: After executing the query, provide a clear summary with the key findings. For spread coverage questions, focus on the team with the most covers and the count. Do not include massive raw data arrays - just the essential information needed to answer the question.

CRITICAL: Provide a clear, concise answer based on the actual query results. For spread coverage, state which team covered the most times and how many times they covered.

IMPORTANT: If the question is about head coaches, coaching records, or team management, DO NOT attempt to answer it. The database contains play-by-play data, not coaching information. For coaching questions, return 'This question requires current coaching information not available in the play-by-play database. Please use web search for coaching-related queries.'
"""
            # Debug: print token length and prompt sample before sending to LLM
            try:
                import tiktoken
                enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
                token_length = len(enc.encode(full_prompt))
                print(f"[DEBUG] LLM prompt token length: {token_length}")
            except Exception as e:
                print(f"[DEBUG] Could not compute token length: {e}")
            print(f"[DEBUG] LLM prompt character length: {len(full_prompt)}")
            print(f"[DEBUG] LLM prompt first 500 chars:\n{full_prompt[:500]}")
            print(f"[DEBUG] LLM prompt last 500 chars:\n{full_prompt[-500:]}")
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

CRITICAL TIME PERIOD INTERPRETATION:
- "Last two years" means 2023 and 2024 (the last two completed seasons)
- "Last three years" means 2022, 2023, and 2024
- "This season" means the current 2025 season (ongoing)
- "Last season" means the 2024 season (completed)
- "Current season" means the 2025 season (ongoing)
- "Recent" means within the last 1-2 completed seasons
- We are currently in the 2025 offseason, so the last full season was 2024

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



    def run_query_hybrid(self, question: str, show_reasoning: bool = False) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Parallel approach: Query both database and web search simultaneously, then compare and select the best answer.
        Now uses the LLM scoring agent as the primary selector. Rule-based scoring is no longer used.
        """
        if not self._initialized:
            return "", "Agent not initialized", None

        try:
            # Pre-filter the question using two-stage hybrid approach
            is_relevant, reason = self._is_nfl_relevant_hybrid(question)
            if not is_relevant:
                logger.info(f"Question filtered out as irrelevant: '{question[:50]}...' - Reason: {reason}")
                return f"I'm sorry, but I can only answer questions about NFL statistics and current NFL information. {reason}", None, f"Filtered out: {reason}"

            logger.info(f"Question passed relevance filter: '{question[:50]}...' - Reason: {reason}")

            if not question or len(question.strip()) < 3:
                return "", "Query is too short", None

            self._debug_output = ""
            self._last_question = question  # Store the question for scoring

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

            # LLM scoring agent selection
            llm_choice, llm_rationale = self._llm_score_answers(question, db_answer_clean, web_answer_clean)
            logger.info(f"LLM scoring agent choice: {llm_choice} | Rationale: {llm_rationale}")
            if llm_choice == "Database":
                return db_answer_clean, None, f"LLM scoring agent selected database answer. Rationale: {llm_rationale}"
            elif llm_choice == "Web":
                return web_answer_clean, None, f"LLM scoring agent selected web answer. Rationale: {llm_rationale}"
            elif llm_choice == "Both equally good":
                # Prefer DB if both are equally good
                return db_answer_clean, None, f"LLM scoring agent found both equally good. Defaulting to database. Rationale: {llm_rationale}"
            else:
                # If LLM is unclear or fails, return a message
                return "Unable to determine the best answer at this time. Please try rephrasing your question or try again later.", None, f"LLM scoring agent was unclear or failed. Rationale: {llm_rationale}"
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
        
        # Loosened length bonus (concise answers are good)
        if 30 <= len(answer) <= 500:
            score += 5.0
        elif len(answer) > 500:
            score += 2.0  # Penalty for very long answers
        elif len(answer) < 30:
            score += 2.0  # Small bonus for very concise answers
        
        # Specificity bonus
        if any(word in answer.lower() for word in ["quarterback", "team", "player", "touchdown", "yard", "game", "season", "cover", "percentage"]):
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
        
        # STRONG BONUS: DB answer matches team+stat pattern for stats queries
        if source == "database":
            # Look for a team (2-3 uppercase letters or a known team name) and a number
            team_pattern = r"([A-Z]{2,3}|lions|eagles|bears|ravens|chiefs|colts|vikings|packers|bills|cowboys|giants|jets|patriots|dolphins|browns|bengals|steelers|texans|jaguars|titans|broncos|raiders|chargers|rams|49ers|seahawks|saints|buccaneers|cardinals|falcons|panthers|commanders)"
            stat_pattern = r"\d+"
            if re.search(team_pattern, answer, re.IGNORECASE) and re.search(stat_pattern, answer):
                score += 10.0  # Strong bonus for matching expected pattern
        
        # Heavy penalty for implausible numbers in any source
        numbers = re.findall(r'\d+', answer)
        for num in numbers:
            num_int = int(num)
            if num_int > 1000:  # Very high numbers that are clearly wrong
                score -= 50.0  # Heavy penalty
            elif num_int > 100 and "wins" in answer.lower():  # Unrealistic win counts
                score -= 30.0
            elif num_int > 50 and "wins" in answer.lower() and "years" in answer.lower():  # Unrealistic wins per year
                score -= 25.0
        
        # Penalty for database trying to answer coaching questions
        if source == "database":
            coaching_keywords = ["head coach", "coach", "coaching", "fired", "hired", "resigned", "retired"]
            if any(keyword in answer.lower() for keyword in coaching_keywords):
                # Check if the question was about coaching
                if hasattr(self, '_last_question'):
                    question_lower = self._last_question.lower()
                    if any(keyword in question_lower for keyword in coaching_keywords):
                        score -= 20.0  # Penalty for database answering coaching questions
        
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

    def _llm_score_answers(self, question: str, db_answer: str, web_answer: str) -> (str, str):
        """
        Use an LLM to select the better answer between DB and web for a given question.
        Returns (choice, rationale):
            choice: 'Database', 'Web', or 'Both equally good'
            rationale: one-sentence explanation
        """
        prompt = f"""
You are an expert NFL stats assistant. Given a question and two answers (one from a database, one from a web search), select the answer that best and most directly answers the question. Consider accuracy, relevance, and specificity. If both are equally good, say so.

Question: {question}

Database Answer: {db_answer}

Web Answer: {web_answer}

Which answer is better? Reply with "Database", "Web", or "Both equally good", and provide a one-sentence rationale.
"""
        try:
            llm = self._llm if hasattr(self, '_llm') and self._llm else None
            if not llm:
                return "Unknown", "No LLM available for scoring."
            response = llm.invoke(prompt)
            # Parse response: look for the first line as the choice, rest as rationale
            lines = response.strip().splitlines()
            if not lines:
                return "Unknown", "No response from LLM."
            choice = None
            rationale = None
            for line in lines:
                if line.strip().lower().startswith("database"):
                    choice = "Database"
                    rationale = line[len("Database"):].strip(" :-")
                    break
                elif line.strip().lower().startswith("web"):
                    choice = "Web"
                    rationale = line[len("Web"):].strip(" :-")
                    break
                elif line.strip().lower().startswith("both"):
                    choice = "Both equally good"
                    rationale = line[len("Both equally good"):].strip(" :-")
                    break
            if not choice:
                # Fallback: look for keywords in the first line
                first = lines[0].lower()
                if "database" in first:
                    choice = "Database"
                elif "web" in first:
                    choice = "Web"
                elif "both" in first:
                    choice = "Both equally good"
                else:
                    choice = "Unknown"
                rationale = lines[0]
            # If rationale is empty, use the next line if available
            if (not rationale or rationale == "") and len(lines) > 1:
                rationale = lines[1].strip()
            return choice, rationale
        except Exception as e:
            return "Unknown", f"LLM scoring error: {e}"

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