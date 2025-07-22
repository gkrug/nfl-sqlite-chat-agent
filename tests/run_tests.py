#!/usr/bin/env python3
"""
Test runner for NFL Stats Agent tests.
"""

import sys
import os
import argparse

# Add parent directory to path so we can import agent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test suites
from test_filtering_fix import FilteringTestSuite
from test_scoring import ScoringTestSuite
from test_sql_agent import SQLAgentTestSuite

def main():
    parser = argparse.ArgumentParser(description='Run NFL Stats Agent tests')
    parser.add_argument('--test', choices=['filtering', 'scoring', 'sql', 'all'], 
                       default='all', help='Which test to run')
    args = parser.parse_args()

    if args.test == 'filtering' or args.test == 'all':
        print("\n================ FILTERING TEST SUITE ================")
        suite = FilteringTestSuite()
        suite.test_filtering()
        print()

    if args.test == 'scoring' or args.test == 'all':
        print("\n================ SCORING TEST SUITE ================")
        suite = ScoringTestSuite(suppress_debug=True)
        suite.run_all_tests()
        print()

    if args.test == 'sql' or args.test == 'all':
        print("\n================ SQL AGENT TEST SUITE ================")
        suite = SQLAgentTestSuite(suppress_debug=True)
        suite.run_all_tests()
        print()

if __name__ == "__main__":
    main() 