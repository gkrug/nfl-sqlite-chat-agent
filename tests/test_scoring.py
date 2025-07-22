#!/usr/bin/env python3
"""
Test suite for answer scoring functionality: DB vs Web
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent import NFLStatAgent
import re

class ScoringTestSuite:
    def __init__(self, suppress_debug=True):
        print("🔧 Initializing Scoring Test Suite...")
        self.suppress_debug = suppress_debug
        self.agent = NFLStatAgent()
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'total': 0
        }
        print("✅ Test suite initialized successfully")
        if suppress_debug:
            print("🔇 Debug output suppressed")

    def log_test_result(self, test_name: str, passed: bool, reason: str = ""):
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

    def print_summary(self):
        print(f"\n{'='*60}")
        print("📊 SCORING TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {self.test_results['total']}")
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        if self.test_results['total'] > 0:
            success_rate = (self.test_results['passed'] / self.test_results['total']) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        if self.test_results['failed'] > 0:
            print(f"\n⚠️  Issues Found:")
            print(f"   - {self.test_results['failed']} tests failed (scoring/logic issues)")
        else:
            print(f"\n🎉 All scoring tests passed successfully!")
        print(f"{'='*60}")

    def _run_query_with_debug_control(self, method, question):
        if self.suppress_debug:
            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                answer, error = method(question)
            return answer, error
        else:
            return method(question)

    def test_spread_coverage_scoring(self):
        print("\n" + "=" * 60)
        print("🧪 Scoring: Spread Coverage DB vs Web")
        print("=" * 60)
        question = "which team covered the spread on the road the most in 2024 regular season"
        db_answer, db_error = self._run_query_with_debug_control(self.agent._run_database_query, question)
        web_answer, web_error = self._run_query_with_debug_control(self.agent._run_web_search, question)
        db_score = self.agent._score_answer(db_answer, db_error, "database")
        web_score = self.agent._score_answer(web_answer, web_error, "web")
        print(f"DB Answer: {db_answer}\nDB Score: {db_score}")
        print(f"Web Answer: {web_answer}\nWeb Score: {web_score}")
        db_correct = bool(re.search(r"[A-Z]{2,3}|lions|eagles|bears|ravens|chiefs|colts|vikings|packers|bills|cowboys|giants|jets|patriots|dolphins|browns|bengals|steelers|texans|jaguars|titans|broncos|raiders|chargers|rams|49ers|seahawks|saints|buccaneers|cardinals|falcons|panthers|commanders", db_answer, re.IGNORECASE)) and bool(re.search(r"\d+", db_answer))
        # LLM scoring agent
        llm_choice, llm_rationale = self.agent._llm_score_answers(question, db_answer, web_answer)
        print(f"LLM Scoring Agent Choice: {llm_choice}\nRationale: {llm_rationale}")
        # Log both rule-based and LLM-based results
        if db_correct and db_score > web_score:
            self.log_test_result("Spread Coverage: DB preferred (rule-based)", True, f"DB score {db_score} > Web score {web_score}")
        elif db_correct and db_score == web_score:
            self.log_test_result("Spread Coverage: DB not preferred but tied (rule-based)", False, f"DB score {db_score} == Web score {web_score}")
        elif db_correct:
            self.log_test_result("Spread Coverage: DB correct but not preferred (rule-based)", False, f"DB score {db_score} < Web score {web_score}")
        else:
            self.log_test_result("Spread Coverage: DB answer not correct (rule-based)", False, "DB answer did not match expected pattern")
        # LLM scoring agent result
        if llm_choice == "Database":
            self.log_test_result("Spread Coverage: LLM scoring agent preferred DB", True, llm_rationale)
        elif llm_choice == "Web":
            self.log_test_result("Spread Coverage: LLM scoring agent preferred Web", False, llm_rationale)
        elif llm_choice == "Both equally good":
            self.log_test_result("Spread Coverage: LLM scoring agent found both equally good", False, llm_rationale)
        else:
            self.log_test_result("Spread Coverage: LLM scoring agent unclear", False, llm_rationale)

    def test_red_zone_efficiency_scoring(self):
        print("\n" + "=" * 60)
        print("🧪 Scoring: Red Zone Efficiency DB vs Web")
        print("=" * 60)
        question = "which team had the best red zone touchdown percentage in 2024"
        db_answer, db_error = self._run_query_with_debug_control(self.agent._run_database_query, question)
        web_answer, web_error = self._run_query_with_debug_control(self.agent._run_web_search, question)
        db_score = self.agent._score_answer(db_answer, db_error, "database")
        web_score = self.agent._score_answer(web_answer, web_error, "web")
        print(f"DB Answer: {db_answer}\nDB Score: {db_score}")
        print(f"Web Answer: {web_answer}\nWeb Score: {web_score}")
        db_correct = bool(re.search(r"[A-Z]{2,3}|lions|eagles|bears|ravens|chiefs|colts|vikings|packers|bills|cowboys|giants|jets|patriots|dolphins|browns|bengals|steelers|texans|jaguars|titans|broncos|raiders|chargers|rams|49ers|seahawks|saints|buccaneers|cardinals|falcons|panthers|commanders", db_answer, re.IGNORECASE)) and bool(re.search(r"\d+\.?\d*%", db_answer))
        # LLM scoring agent
        llm_choice, llm_rationale = self.agent._llm_score_answers(question, db_answer, web_answer)
        print(f"LLM Scoring Agent Choice: {llm_choice}\nRationale: {llm_rationale}")
        # Log both rule-based and LLM-based results
        if db_correct and db_score > web_score:
            self.log_test_result("Red Zone Efficiency: DB preferred (rule-based)", True, f"DB score {db_score} > Web score {web_score}")
        elif db_correct and db_score == web_score:
            self.log_test_result("Red Zone Efficiency: DB not preferred but tied (rule-based)", False, f"DB score {db_score} == Web score {web_score}")
        elif db_correct:
            self.log_test_result("Red Zone Efficiency: DB correct but not preferred (rule-based)", False, f"DB score {db_score} < Web score {web_score}")
        else:
            self.log_test_result("Red Zone Efficiency: DB answer not correct (rule-based)", False, "DB answer did not match expected pattern")
        # LLM scoring agent result
        if llm_choice == "Database":
            self.log_test_result("Red Zone Efficiency: LLM scoring agent preferred DB", True, llm_rationale)
        elif llm_choice == "Web":
            self.log_test_result("Red Zone Efficiency: LLM scoring agent preferred Web", False, llm_rationale)
        elif llm_choice == "Both equally good":
            self.log_test_result("Red Zone Efficiency: LLM scoring agent found both equally good", False, llm_rationale)
        else:
            self.log_test_result("Red Zone Efficiency: LLM scoring agent unclear", False, llm_rationale)

    def test_mixed_queries_scoring(self):
        print("\n" + "=" * 60)
        print("🧪 Scoring: Mixed Web-Favored and DB-Favored Queries")
        print("=" * 60)
        # 5 likely web-favored queries (recent news, injuries, qualitative)
        web_queries = [
            {
                "question": "who won the super bowl last week?",
                "desc": "Recent event (web-favored)"
            },
            {
                "question": "is Patrick Mahomes injured right now?",
                "desc": "Current injury status (web-favored)"
            },
            {
                "question": "which team made the biggest trade this offseason?",
                "desc": "Recent trade (web-favored)"
            },
            {
                "question": "who is the current head coach of the New England Patriots?",
                "desc": "Current coach (web-favored)"
            },
            {
                "question": "what is the latest news on Aaron Rodgers?",
                "desc": "Recent player news (web-favored)"
            }
        ]
        # 5 likely db-favored queries (historical stats, season stats)
        db_queries = [
            {
                "question": "who had the most passing touchdowns in 2024?",
                "desc": "Season stat (db-favored)"
            },
            {
                "question": "which team had the most wins in 2023?",
                "desc": "Historical team stat (db-favored)"
            },
            {
                "question": "which player had the most rushing yards in 2022?",
                "desc": "Historical player stat (db-favored)"
            },
            {
                "question": "which team allowed the fewest points in 2021?",
                "desc": "Defensive stat (db-favored)"
            },
            {
                "question": "who had the most interceptions in the 2020 season?",
                "desc": "Turnover stat (db-favored)"
            }
        ]
        all_queries = web_queries + db_queries
        for q in all_queries:
            print(f"\n--- {q['desc']} ---\nQuestion: {q['question']}")
            db_answer, db_error = self._run_query_with_debug_control(self.agent._run_database_query, q['question'])
            web_answer, web_error = self._run_query_with_debug_control(self.agent._run_web_search, q['question'])
            db_score = self.agent._score_answer(db_answer, db_error, "database")
            web_score = self.agent._score_answer(web_answer, web_error, "web")
            print(f"DB Answer: {db_answer}\nDB Score: {db_score}")
            print(f"Web Answer: {web_answer}\nWeb Score: {web_score}")
            # LLM scoring agent
            llm_choice, llm_rationale = self.agent._llm_score_answers(q['question'], db_answer, web_answer)
            print(f"LLM Scoring Agent Choice: {llm_choice}\nRationale: {llm_rationale}")
            # Rule-based log
            if db_score > web_score:
                self.log_test_result(f"{q['desc']}: DB preferred (rule-based)", True, f"DB score {db_score} > Web score {web_score}")
            elif db_score == web_score:
                self.log_test_result(f"{q['desc']}: DB not preferred but tied (rule-based)", False, f"DB score {db_score} == Web score {web_score}")
            else:
                self.log_test_result(f"{q['desc']}: DB not preferred (rule-based)", False, f"DB score {db_score} < Web score {web_score}")
            # LLM scoring agent log
            if llm_choice == "Database":
                self.log_test_result(f"{q['desc']}: LLM scoring agent preferred DB", True, llm_rationale)
            elif llm_choice == "Web":
                self.log_test_result(f"{q['desc']}: LLM scoring agent preferred Web", True, llm_rationale)
            elif llm_choice == "Both equally good":
                self.log_test_result(f"{q['desc']}: LLM scoring agent found both equally good", False, llm_rationale)
            else:
                self.log_test_result(f"{q['desc']}: LLM scoring agent unclear", False, llm_rationale)

    def run_all_tests(self):
        print("\n🏈 Scoring Test Suite")
        print("=" * 60)
        self.test_spread_coverage_scoring()
        self.test_red_zone_efficiency_scoring()
        self.test_mixed_queries_scoring()
        self.print_summary()

if __name__ == "__main__":
    suite = ScoringTestSuite(suppress_debug=True)
    suite.run_all_tests() 