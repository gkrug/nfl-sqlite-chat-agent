#!/usr/bin/env python3
"""
Quick test script for NFL Stat Agent Hybrid Approach
Run this to quickly verify the hybrid approach is working.
"""

import os
import time
from dotenv import load_dotenv
from agent import run_query_hybrid, get_debug_logs

def test_hybrid_quick():
    """Quick test of the hybrid approach with key examples."""
    
    # Load environment variables
    load_dotenv()
    
    # Check if API key is set
    if not os.getenv("TOGETHER_API_KEY"):
        print("❌ Error: TOGETHER_API_KEY not found in environment variables")
        return False
    
    # Quick test queries
    test_queries = [
        {
            "query": "What are the latest NFL injury updates?",
            "expected": "web",
            "description": "Current events - should use web search"
        },
        {
            "query": "How many games are in the database?",
            "expected": "database", 
            "description": "Database query - should use database"
        }
    ]
    
    print("🚀 Quick Hybrid Approach Test")
    print("=" * 50)
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {test['description']}")
        print(f"Query: {test['query']}")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            answer, error, reasoning = run_query_hybrid(test['query'], show_reasoning=False)
            response_time = time.time() - start_time
            
            # Determine actual data source
            debug_logs = get_debug_logs()
            if "web_search" in debug_logs.lower():
                actual_source = "web"
                source_icon = "🌐 Web Search"
            elif "sql" in debug_logs.lower() or "database" in debug_logs.lower():
                actual_source = "database"
                source_icon = "📊 Database"
            else:
                actual_source = "hybrid"
                source_icon = "🔄 Hybrid"
            
            print(f"🔍 Expected: {test['expected']}")
            print(f"🔍 Actual: {source_icon}")
            print(f"⏱️  Time: {response_time:.2f}s")
            
            if actual_source == test['expected']:
                print("✅ Source routing correct!")
            else:
                print("⚠️  Source routing different than expected")
            
            if error:
                print(f"❌ Error: {error}")
            else:
                print(f"✅ Answer: {answer[:200]}{'...' if len(answer) > 200 else ''}")
                
        except Exception as e:
            response_time = time.time() - start_time
            print(f"❌ Exception: {str(e)}")
            print(f"⏱️  Time: {response_time:.2f}s")
    
    print("\n" + "=" * 50)
    print("✅ Quick test complete!")

if __name__ == "__main__":
    test_hybrid_quick() 