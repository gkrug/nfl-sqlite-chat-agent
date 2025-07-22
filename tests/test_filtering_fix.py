#!/usr/bin/env python3
"""
Test the question validation filter for both relevant and irrelevant queries.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent import run_query_hybrid

class FilteringTestSuite:
    def __init__(self):
        print("🔧 Initializing Filtering Test Suite...")
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'total': 0
        }
        print("✅ Test suite initialized successfully")

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
        print("📊 FILTERING TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {self.test_results['total']}")
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        if self.test_results['total'] > 0:
            success_rate = (self.test_results['passed'] / self.test_results['total']) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        if self.test_results['failed'] > 0:
            print(f"\n⚠️  Issues Found:")
            print(f"   - {self.test_results['failed']} tests failed (filtering/logic issues)")
        else:
            print(f"\n🎉 All filtering tests passed successfully!")
        print(f"{'='*60}")

    def test_filtering(self):
        should_pass = [
            "Which quarterback had the most passing yards in the last two years?",
            "What team scored the most points in the 2024 season?",
            "Which quarterback had the most interceptions in the 2024 season?",
            "Who had the most rushing touchdowns in the 2024 season?",
            "What's the difference between 2023 and 2024 stats?",
            "Who has the most wins this year?",
            "Which team had the best red zone efficiency in 2023?",
            "Who led the league in sacks in 2022?",
            "Which team covered the spread the most in 2024?",
            "Who had the most field goals in 2021?"
        ]
        should_be_filtered = [
            "What's the weather like in New York?",
            "Who won the NBA championship last year?",
            "How do I cook lasagna?",
            "What is the capital of France?",
            "Tell me a joke about cats.",
            "Who is the president of the United States?",
            "What is the stock price of Apple?",
            "How to fix a flat tire?",
            "What is the best movie of 2023?",
            "How do I learn Python programming?"
        ]
        print("\nTesting NFL/statistics questions that should NOT be filtered")
        print("=" * 60)
        for i, question in enumerate(should_pass, 1):
            test_name = f"Should Pass #{i}: {question}"
            print(f"\n🔍 {test_name}")
            try:
                answer, error, reasoning = run_query_hybrid(question, show_reasoning=True)
                if error:
                    self.log_test_result(test_name, False, f"Error: {error}")
                elif "sorry" in answer.lower() or "only answer" in answer.lower():
                    self.log_test_result(test_name, False, "❌ STILL BEING FILTERED")
                    print(f"Answer: {answer[:150]}...")
                    print(f"Reasoning: {reasoning}")
                else:
                    self.log_test_result(test_name, True, "✅ NO LONGER FILTERED - Processing correctly")
                    print(f"Answer: {answer[:150]}...")
                    print(f"Reasoning: {reasoning}")
            except Exception as e:
                self.log_test_result(test_name, False, f"EXCEPTION: {str(e)}")
        print("\nTesting irrelevant/non-NFL questions that SHOULD be filtered")
        print("=" * 60)
        for i, question in enumerate(should_be_filtered, 1):
            test_name = f"Should Filter #{i}: {question}"
            print(f"\n🔍 {test_name}")
            try:
                answer, error, reasoning = run_query_hybrid(question, show_reasoning=True)
                if error:
                    self.log_test_result(test_name, True, f"Correctly filtered (error): {error}")
                elif "sorry" in answer.lower() or "only answer" in answer.lower():
                    self.log_test_result(test_name, True, "✅ Correctly filtered")
                    print(f"Answer: {answer[:150]}...")
                    print(f"Reasoning: {reasoning}")
                else:
                    self.log_test_result(test_name, False, "❌ NOT FILTERED - Should have been filtered")
                    print(f"Answer: {answer[:150]}...")
                    print(f"Reasoning: {reasoning}")
            except Exception as e:
                self.log_test_result(test_name, False, f"EXCEPTION: {str(e)}")
        self.print_summary()

if __name__ == "__main__":
    suite = FilteringTestSuite()
    suite.test_filtering() 