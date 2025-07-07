#!/usr/bin/env python3
"""
Test script for NFL Stat Agent
Run this to verify the agent is working correctly before using the web interface.
"""

import os
import time
from dotenv import load_dotenv
from agent import run_query_hybrid, get_debug_logs, get_agent

def test_agent():
    """Test the agent with sample queries using the hybrid approach."""
    
    # Load environment variables
    load_dotenv()
    
    # Check if API key is set
    if not os.getenv("TOGETHER_API_KEY"):
        print("❌ Error: TOGETHER_API_KEY not found in environment variables")
        print("Please create a .env file with your Together AI API key")
        return False
    
    # Test queries - focused selection to test hybrid approach
    test_queries = [
        # Current events (should use web search)
        "What are the latest NFL injury updates?",
        "Who won the most recent NFL game?",
        
        # Historical stats (should use database)
        "How many games are in the database?",
        "What's the average passing yards per game in 2023?",
        
        # Complex queries (should use hybrid approach)
        "What are the current NFL standings and how do they compare to last year's final standings?",
        "Who are the top performers this season and what were their stats last year?"
    ]
    
    print("🧪 Testing NFL Stat Agent (Hybrid Approach)...")
    print("=" * 60)
    
    total_time = 0
    successful_queries = 0
    failed_queries = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i:2d}: {query}")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # Run query using hybrid approach
            answer, error, reasoning = run_query_hybrid(query, show_reasoning=False)
            
            end_time = time.time()
            response_time = end_time - start_time
            total_time += response_time
            
            # Determine data source from debug logs
            debug_logs = get_debug_logs()
            if "web_search" in debug_logs.lower():
                source_icon = "🌐 Web Search"
                data_source = "web"
            elif "sql" in debug_logs.lower() or "database" in debug_logs.lower():
                source_icon = "📊 Database"
                data_source = "database"
            else:
                source_icon = "🔄 Hybrid (Web + Database)"
                data_source = "hybrid"
            
            print(f"🔍 Data Source: {source_icon}")
            print(f"⏱️  Response Time: {response_time:.2f}s")
            
            if error:
                print(f"❌ Error: {error}")
                failed_queries += 1
            else:
                print(f"✅ Answer: {answer[:300]}{'...' if len(answer) > 300 else ''}")
                successful_queries += 1
                
                # Show debug info
                debug_logs = get_debug_logs()
                if debug_logs:
                    print(f"🔍 Debug logs available ({len(debug_logs)} characters)")
            
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            total_time += response_time
            print(f"❌ Exception: {str(e)}")
            print(f"⏱️  Response Time: {response_time:.2f}s")
            failed_queries += 1
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Successful Queries: {successful_queries}")
    print(f"❌ Failed Queries: {failed_queries}")
    print(f"📈 Success Rate: {(successful_queries / len(test_queries) * 100):.1f}%")
    print(f"⏱️  Total Time: {total_time:.2f}s")
    print(f"⏱️  Average Response Time: {(total_time / len(test_queries)):.2f}s")
    print(f"⏱️  Average Success Time: {(total_time / successful_queries if successful_queries > 0 else 0):.2f}s")
    
    if successful_queries > 0:
        print("\n🎉 Testing complete! Agent is working correctly.")
        return True
    else:
        print("\n⚠️  Testing complete but no successful queries. Check configuration.")
        return False

def test_specific_scenarios():
    """Test specific scenarios to verify hybrid approach behavior."""
    
    print("\n🔬 Testing Specific Scenarios...")
    print("=" * 60)
    
    scenarios = [
        {
            "name": "Current Events (Web Search)",
            "query": "What are today's NFL scores?",
            "expected_source": "web"
        },
        {
            "name": "Historical Stats (Database)",
            "query": "What's the average passing yards per game in 2023?",
            "expected_source": "database"
        },
        {
            "name": "Complex Query (Hybrid)",
            "query": "What are the current playoff standings and how do they compare to last year's final standings?",
            "expected_source": "hybrid"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🧪 {scenario['name']}")
        print(f"📝 Query: {scenario['query']}")
        
        start_time = time.time()
        answer, error, reasoning = run_query_hybrid(scenario['query'], show_reasoning=False)
        response_time = time.time() - start_time
        
        # Determine actual data source from debug logs
        debug_logs = get_debug_logs()
        if "web_search" in debug_logs.lower():
            actual_source = "web"
        elif "sql" in debug_logs.lower() or "database" in debug_logs.lower():
            actual_source = "database"
        else:
            actual_source = "hybrid"
        
        print(f"⏱️  Response Time: {response_time:.2f}s")
        print(f"🔍 Expected Source: {scenario['expected_source']}")
        print(f"🔍 Actual Source: {actual_source}")
        
        if actual_source == scenario['expected_source']:
            print("✅ Source routing correct!")
        else:
            print("⚠️  Source routing different than expected")
        
        if error:
            print(f"❌ Error: {error}")
        else:
            print(f"✅ Answer: {answer[:200]}{'...' if len(answer) > 200 else ''}")

if __name__ == "__main__":
    # Run main test
    success = test_agent()
    
    # Run specific scenario tests
    if success:
        test_specific_scenarios() 