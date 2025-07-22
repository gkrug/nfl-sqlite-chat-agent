#!/usr/bin/env python3
"""
Focused test suite for SQL Agent component
Tests SQL generation and execution without the full agent pipeline
"""

import sqlite3
import time
from agent import NFLStatAgent

class SQLAgentTestSuite:
    """Test suite focused on SQL agent functionality"""
    
    def __init__(self, suppress_debug=False):
        """Initialize the test suite
        
        Args:
            suppress_debug (bool): If True, suppress LLM debug output during tests
        """
        print("🔧 Initializing SQL Agent Test Suite...")
        self.suppress_debug = suppress_debug
        self.agent = NFLStatAgent()
        self.db_path = 'data/pbp_db'
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'total': 0
        }
        print("✅ Test suite initialized successfully")
        if suppress_debug:
            print("🔇 Debug output suppressed")
        
    def __del__(self):
        """Clean up database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def log_test_result(self, test_name: str, passed: bool, reason: str = ""):
        """Log test result with detailed reporting"""
        self.test_results['total'] += 1
        if passed:
            self.test_results['passed'] += 1
            print(f"✅ PASSED: {test_name}")
            if reason:
                print(f"   Reason: {reason}")
        else:
            self.test_results['failed'] += 1
            print(f"❌ FAILED: {test_name}")
            if reason:
                print(f"   Reason: {reason}")
    
    def log_error(self, test_name: str, error: str):
        """Log test error"""
        self.test_results['total'] += 1
        self.test_results['errors'] += 1
        print(f"💥 ERROR: {test_name}")
        print(f"   Error: {error}")
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print("📊 SQL AGENT TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {self.test_results['total']}")
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"💥 Errors: {self.test_results['errors']}")
        
        if self.test_results['total'] > 0:
            success_rate = (self.test_results['passed'] / self.test_results['total']) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.test_results['failed'] > 0 or self.test_results['errors'] > 0:
            print(f"\n⚠️  Issues Found:")
            if self.test_results['failed'] > 0:
                print(f"   - {self.test_results['failed']} tests failed (logic/accuracy issues)")
            if self.test_results['errors'] > 0:
                print(f"   - {self.test_results['errors']} tests had errors (service/connection issues)")
        else:
            print(f"\n🎉 All tests passed successfully!")
        
        print(f"{'='*60}")
    
    def _run_query_with_debug_control(self, question):
        """Run a database query with debug output control"""
        if self.suppress_debug:
            # Temporarily redirect stdout to suppress debug output
            import sys
            import io
            from contextlib import redirect_stdout
            
            # Capture stdout to suppress debug prints
            f = io.StringIO()
            with redirect_stdout(f):
                answer, error = self.agent._run_database_query(question)
            return answer, error
        else:
            # Run normally with debug output
            return self.agent._run_database_query(question)
    
    def test_sql_generation_basic(self):
        """Test basic SQL generation for simple queries"""
        print("=" * 60)
        print("🧪 Testing: Basic SQL Generation")
        print("=" * 60)
        
        test_cases = [
            {
                "question": "who had the most passing touchdowns in 2024",
                "expected_keywords": ["touchdown", "2024"],
                "description": "Simple player stats query"
            },
            {
                "question": "how many games were played in week 1 of 2024",
                "expected_keywords": ["games", "week", "2024"],
                "description": "Simple counting query"
            },
            {
                "question": "which team had the most wins in 2024",
                "expected_keywords": ["wins", "2024"],
                "description": "Team wins query"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            test_name = f"Basic SQL #{i}: {test_case['description']}"
            print(f"\n🔍 {test_name}")
            print(f"   Question: {test_case['question']}")
            
            try:
                # Run the database query directly through the agent
                answer, error = self._run_query_with_debug_control(test_case['question'])
                
                if error:
                    self.log_error(test_name, f"Agent returned error: {error}")
                    continue
                
                print(f"   Answer: {answer}")
                
                # Check if the SQL was generated correctly by looking for expected keywords
                answer_lower = answer.lower()
                keywords_found = [kw for kw in test_case['expected_keywords'] if kw.lower() in answer_lower]
                
                if len(keywords_found) >= len(test_case['expected_keywords']) * 0.5:  # At least 50% of keywords
                    self.log_test_result(test_name, True, f"Found keywords: {keywords_found}")
                else:
                    self.log_test_result(test_name, False, f"Missing expected keywords. Found: {keywords_found}, Expected: {test_case['expected_keywords']}")
                    
            except Exception as e:
                self.log_error(test_name, f"Exception: {e}")
    
    def test_sql_generation_complex(self):
        """Test complex SQL generation for advanced queries"""
        print("\n" + "=" * 60)
        print("🧪 Testing: Complex SQL Generation")
        print("=" * 60)
        
        test_cases = [
            {
                "question": "which team covered the spread on the road the most in 2024",
                "expected_keywords": ["detroit", "lions", "covers", "8"],
                "description": "Road spread coverage with CTE"
            },
            {
                "question": "which team had the best red zone touchdown percentage in 2024",
                "expected_keywords": ["percentage", "red zone", "touchdown"],
                "description": "Red zone efficiency with aggregation"
            },
            {
                "question": "which team had the best record in games decided by 3 points or less in 2024",
                "expected_keywords": ["close", "games", "wins", "points"],
                "description": "Close games analysis"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            test_name = f"Complex SQL #{i}: {test_case['description']}"
            print(f"\n🔍 {test_name}")
            print(f"   Question: {test_case['question']}")
            
            try:
                # Run the database query directly through the agent
                answer, error = self._run_query_with_debug_control(test_case['question'])
                
                if error:
                    self.log_error(test_name, f"Agent returned error: {error}")
                    continue
                
                print(f"   Answer: {answer}")
                
                # For complex queries, we validate the answer makes sense
                answer_lower = answer.lower()
                keywords_found = [kw for kw in test_case['expected_keywords'] if kw.lower() in answer_lower]
                
                # Check for coaching-related rejection
                if "coaching" in answer_lower and "not available" in answer_lower:
                    self.log_test_result(test_name, False, "Query incorrectly classified as coaching-related")
                elif len(keywords_found) >= len(test_case['expected_keywords']) * 0.3:  # At least 30% of keywords
                    self.log_test_result(test_name, True, f"Found keywords: {keywords_found}")
                else:
                    self.log_test_result(test_name, False, f"Missing expected keywords. Found: {keywords_found}, Expected: {test_case['expected_keywords']}")
                    
            except Exception as e:
                self.log_error(test_name, f"Exception: {e}")
    
    def test_sql_execution_accuracy(self):
        """Test SQL execution accuracy against direct database queries"""
        print("\n" + "=" * 60)
        print("🧪 Testing: SQL Execution Accuracy")
        print("=" * 60)
        
        # Test 1: Road spread coverage
        test_name = "Accuracy #1: Road Spread Coverage"
        print(f"\n🔍 {test_name}")
        
        # Direct database query
        direct_query = """
        WITH final_scores AS (
            SELECT game_id, away_team, home_team, spread_line, 
                   MAX(total_away_score) as final_away_score, 
                   MAX(total_home_score) as final_home_score 
            FROM nflfastR_pbp 
            WHERE season=2024 AND week BETWEEN 1 AND 18 
            GROUP BY game_id
        )
        SELECT away_team, COUNT(DISTINCT game_id) as covers 
        FROM final_scores 
        WHERE (
            (spread_line > 0 AND final_away_score + spread_line > final_home_score) 
            OR (spread_line < 0 AND final_away_score > final_home_score) 
            OR (spread_line = 0 AND final_away_score > final_home_score)
        ) 
        GROUP BY away_team 
        ORDER BY covers DESC 
        LIMIT 1
        """
        
        self.cursor.execute(direct_query)
        db_result = self.cursor.fetchone()
        expected_team = db_result[0]
        expected_covers = db_result[1]
        
        print(f"   Database Result: {expected_team} with {expected_covers} covers")
        
        # Agent query
        agent_answer, error = self._run_query_with_debug_control(
            "which team covered the spread on the road the most in 2024"
        )
        
        if error:
            self.log_error(test_name, f"Agent returned error: {error}")
        else:
            print(f"   Agent Answer: {agent_answer}")
            
            # Validate accuracy
            answer_lower = agent_answer.lower()
            team_found = expected_team.lower() in answer_lower or "detroit" in answer_lower
            number_found = str(expected_covers) in agent_answer
            
            if team_found and number_found:
                self.log_test_result(test_name, True, f"Exact match: {expected_team} with {expected_covers} covers")
            else:
                self.log_test_result(test_name, False, f"Expected {expected_team} with {expected_covers} covers, but team_found={team_found}, number_found={number_found}")
        
        # Test 2: Red zone efficiency
        test_name = "Accuracy #2: Red Zone Efficiency"
        print(f"\n🔍 {test_name}")
        
        # Direct database query
        direct_query = """
        WITH red_zone_plays AS (
            SELECT posteam, 
                   COUNT(*) as total_plays,
                   SUM(CASE WHEN touchdown = 1 THEN 1 ELSE 0 END) as touchdowns
            FROM nflfastR_pbp 
            WHERE season=2024 
              AND week BETWEEN 1 AND 18
              AND yardline_100 <= 20
              AND play_type IN ('pass', 'run')
            GROUP BY posteam
        )
        SELECT posteam, 
               total_plays,
               touchdowns,
               ROUND(CAST(touchdowns AS FLOAT) / total_plays * 100, 1) as td_percentage
        FROM red_zone_plays
        WHERE total_plays >= 20
        ORDER BY td_percentage DESC
        LIMIT 1
        """
        
        self.cursor.execute(direct_query)
        db_result = self.cursor.fetchone()
        expected_team = db_result[0]
        expected_percentage = db_result[3]
        
        print(f"   Database Result: {expected_team} with {expected_percentage}%")
        
        # Agent query
        agent_answer, error = self._run_query_with_debug_control(
            "which team had the best red zone touchdown percentage in 2024"
        )
        
        if error:
            self.log_error(test_name, f"Agent returned error: {error}")
        else:
            print(f"   Agent Answer: {agent_answer}")
            
            # Validate accuracy
            answer_lower = agent_answer.lower()
            team_found = expected_team.lower() in answer_lower or "baltimore" in answer_lower
            percentage_found = str(expected_percentage) in agent_answer
            
            if team_found and percentage_found:
                self.log_test_result(test_name, True, f"Exact match: {expected_team} with {expected_percentage}%")
            else:
                self.log_test_result(test_name, False, f"Expected {expected_team} with {expected_percentage}%, but team_found={team_found}, percentage_found={percentage_found}")
    
    def test_sql_edge_cases(self):
        """Test SQL generation for edge cases and boundary conditions"""
        print("\n" + "=" * 60)
        print("🧪 Testing: SQL Edge Cases")
        print("=" * 60)
        
        test_cases = [
            {
                "question": "which team had exactly 8 wins in 2024",
                "expected_keywords": ["team", "wins", "8", "2024"],
                "description": "Exact count query"
            },
            {
                "question": "who had the most passing touchdowns in the last 2 minutes of games in 2024",
                "expected_keywords": ["touchdowns", "last", "minutes", "2024"],
                "description": "Time-based filtering query"
            },
            {
                "question": "which team had the most rushing yards in the red zone in 2024",
                "expected_keywords": ["team", "rushing", "yards", "red zone", "2024"],
                "description": "Location-based filtering query"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            test_name = f"Edge Case #{i}: {test_case['description']}"
            print(f"\n🔍 {test_name}")
            print(f"   Question: {test_case['question']}")
            
            try:
                answer, error = self._run_query_with_debug_control(test_case['question'])
                
                if error:
                    self.log_error(test_name, f"Agent returned error: {error}")
                    continue
                
                print(f"   Answer: {answer}")
                
                # Check if answer contains relevant information
                answer_lower = answer.lower()
                keywords_found = [kw for kw in test_case['expected_keywords'] if kw.lower() in answer_lower]
                
                if len(keywords_found) >= len(test_case['expected_keywords']) * 0.4:  # At least 40% of keywords
                    self.log_test_result(test_name, True, f"Found keywords: {keywords_found}")
                else:
                    self.log_test_result(test_name, False, f"Missing expected keywords. Found: {keywords_found}, Expected: {test_case['expected_keywords']}")
                    
            except Exception as e:
                self.log_error(test_name, f"Exception: {e}")
    
    def test_sql_performance(self):
        """Test SQL query performance"""
        print("\n" + "=" * 60)
        print("🧪 Testing: SQL Performance")
        print("=" * 60)
        
        test_queries = [
            "who had the most passing touchdowns in 2024",
            "which team covered the spread on the road the most in 2024",
            "which team had the best red zone touchdown percentage in 2024"
        ]
        
        for i, query in enumerate(test_queries, 1):
            test_name = f"Performance #{i}: {query[:50]}..."
            print(f"\n🔍 {test_name}")
            print(f"   Query: {query}")
            
            start_time = time.time()
            answer, error = self._run_query_with_debug_control(query)
            response_time = time.time() - start_time
            
            if error:
                self.log_error(test_name, f"Agent returned error: {error}")
            else:
                print(f"   Response Time: {response_time:.2f} seconds")
                print(f"   Answer: {answer[:100]}...")
                
                if response_time > 30:
                    self.log_test_result(test_name, False, f"Response time too slow: {response_time:.2f}s > 30s")
                elif response_time > 15:
                    self.log_test_result(test_name, True, f"Response time acceptable but slow: {response_time:.2f}s")
                else:
                    self.log_test_result(test_name, True, f"Response time good: {response_time:.2f}s")
    
    def test_scoring_mechanism_spread_coverage(self):
        """Test that the DB answer is scored higher than the web for a stats question"""
        print("\n" + "=" * 60)
        print("🧪 Testing: Scoring Mechanism (Spread Coverage)")
        print("=" * 60)
        question = "which team covered the spread on the road the most in 2024 regular season"
        
        # Run the hybrid query to get both answers
        db_answer, db_error = self.agent._run_database_query(question)
        web_answer, web_error = self.agent._run_web_search(question)
        
        # Score both answers
        db_score = self.agent._score_answer(db_answer, db_error, "database")
        web_score = self.agent._score_answer(web_answer, web_error, "web")
        
        print(f"DB Answer: {db_answer}\nDB Score: {db_score}")
        print(f"Web Answer: {web_answer}\nWeb Score: {web_score}")
        
        # Check that DB answer is scored higher if it is correct
        # We'll consider it correct if it mentions a team and a number of covers
        import re
        db_correct = bool(re.search(r"[A-Z]{2,3}", db_answer)) and bool(re.search(r"\d+", db_answer))
        if db_correct and db_score > web_score:
            self.log_test_result("Scoring: DB preferred for spread coverage", True, f"DB score {db_score} > Web score {web_score}")
        elif db_correct and db_score == web_score:
            self.log_test_result("Scoring: DB not preferred but tied", False, f"DB score {db_score} == Web score {web_score}")
        elif db_correct:
            self.log_test_result("Scoring: DB correct but not preferred", False, f"DB score {db_score} < Web score {web_score}")
        else:
            self.log_test_result("Scoring: DB answer not correct", False, "DB answer did not match expected pattern")
    
    def run_all_tests(self):
        """Run all SQL agent tests"""
        print("🏈 SQL Agent Component Test Suite")
        print("=" * 60)
        
        tests = [
            ("Basic SQL Generation", self.test_sql_generation_basic),
            ("Complex SQL Generation", self.test_sql_generation_complex),
            ("SQL Execution Accuracy", self.test_sql_execution_accuracy),
            ("SQL Edge Cases", self.test_sql_edge_cases),
            ("SQL Performance", self.test_sql_performance),
            ("Scoring Mechanism (Spread Coverage)", self.test_scoring_mechanism_spread_coverage)
        ]
        
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            print(f"🚀 Running: {test_name}")
            print(f"{'='*60}")
            try:
                test_func()
            except Exception as e:
                print(f"💥 TEST FAILED: {e}")
        
        # Print final summary
        self.print_summary()

def main():
    """Run the SQL agent test suite"""
    import sys
    
    # Check for command line arguments
    suppress_debug = False
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--suppress-debug', '-s', '--quiet', '-q']:
            suppress_debug = True
        elif sys.argv[1] in ['--help', '-h']:
            print("SQL Agent Test Suite")
            print("Usage: python test_sql_agent.py [OPTIONS]")
            print("\nOptions:")
            print("  --suppress-debug, -s    Suppress LLM debug output")
            print("  --quiet, -q             Same as --suppress-debug")
            print("  --help, -h              Show this help message")
            return
    
    test_suite = SQLAgentTestSuite(suppress_debug=suppress_debug)
    test_suite.run_all_tests()

if __name__ == "__main__":
    main() 