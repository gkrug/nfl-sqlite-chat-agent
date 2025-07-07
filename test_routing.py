#!/usr/bin/env python3
"""
Test script for query routing logic
This helps verify that queries are being routed to the correct data source.
"""

from agent import get_agent

def test_routing():
    """Test the query routing logic."""
    
    agent = get_agent()
    
    # Test queries with expected routing
    test_cases = [
        # Database queries
        ("What is the most common play type in the database?", False),
        ("How many games are in the database?", False),
        ("Which team had the most passing yards in 2023?", False),
        ("Show me the top 5 rushers in 2022", False),
        ("Compare Patrick Mahomes and Josh Allen by EPA", False),
        ("What's the success rate on 4th down attempts?", False),
        
        # Web search queries
        ("What are the latest NFL injury updates?", True),
        ("Who won the most recent NFL game?", True),
        ("What are the current NFL playoff standings?", True),
        ("What trades happened this week?", True),
        ("Is Patrick Mahomes injured?", True),
        ("What's the latest news about Aaron Rodgers?", True),
    ]
    
    print("🧪 Testing Query Routing Logic")
    print("=" * 50)
    
    correct = 0
    total = len(test_cases)
    
    for query, expected_web_search in test_cases:
        actual_web_search = agent._should_use_web_search(query)
        data_source = "🌐 Web Search" if actual_web_search else "📊 Database"
        expected_source = "🌐 Web Search" if expected_web_search else "📊 Database"
        
        status = "✅" if actual_web_search == expected_web_search else "❌"
        if actual_web_search == expected_web_search:
            correct += 1
            
        print(f"{status} Query: {query[:50]}{'...' if len(query) > 50 else ''}")
        print(f"   Expected: {expected_source}")
        print(f"   Actual:   {data_source}")
        print()
    
    print("=" * 50)
    print(f"📊 Results: {correct}/{total} correct ({correct/total*100:.1f}%)")
    
    if correct == total:
        print("🎉 All routing tests passed!")
    else:
        print("⚠️  Some routing tests failed. Check the logic.")

if __name__ == "__main__":
    test_routing() 