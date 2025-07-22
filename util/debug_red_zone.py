#!/usr/bin/env python3
"""
Debug script for red zone efficiency inconsistency issue
"""

import sqlite3
import time
from agent import NFLStatAgent

def debug_red_zone_efficiency():
    """Debug the red zone efficiency inconsistency"""
    print("🔍 Debugging Red Zone Efficiency Inconsistency")
    print("=" * 60)
    
    # Initialize agent and database
    agent = NFLStatAgent()
    conn = sqlite3.connect('data/pbp_db')
    cursor = conn.cursor()
    
    # Direct database query to get the correct answer
    print("\n📊 Step 1: Get correct database result")
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
    LIMIT 5
    """
    
    cursor.execute(direct_query)
    db_results = cursor.fetchall()
    
    print("Database Results (Top 5):")
    for team, plays, tds, pct in db_results:
        print(f"  {team}: {tds}/{plays} = {pct}%")
    
    correct_team = db_results[0][0]
    correct_percentage = db_results[0][3]
    print(f"\n✅ Correct Answer: {correct_team} with {correct_percentage}%")
    
    # Test agent multiple times
    print(f"\n🧪 Step 2: Test agent multiple times")
    test_question = "which team had the best red zone touchdown percentage in 2024"
    
    results = []
    for i in range(5):
        print(f"\n--- Test #{i+1} ---")
        start_time = time.time()
        
        answer, error = agent._run_database_query(test_question)
        response_time = time.time() - start_time
        
        print(f"Response Time: {response_time:.2f}s")
        print(f"Answer: {answer}")
        
        if error:
            print(f"❌ Error: {error}")
            results.append({"test": i+1, "error": error, "time": response_time})
        else:
            # Extract team and percentage from answer
            answer_lower = answer.lower()
            
            # Look for team names
            team_found = None
            if correct_team.lower() in answer_lower or "baltimore" in answer_lower:
                team_found = correct_team
            elif "tampa" in answer_lower or "tb" in answer_lower:
                team_found = "TB"
            elif "buffalo" in answer_lower or "buf" in answer_lower:
                team_found = "BUF"
            
            # Look for percentage
            import re
            percentage_match = re.search(r'(\d+\.?\d*)%', answer)
            percentage_found = float(percentage_match.group(1)) if percentage_match else None
            
            results.append({
                "test": i+1,
                "team": team_found,
                "percentage": percentage_found,
                "time": response_time,
                "full_answer": answer
            })
            
            print(f"Extracted: Team={team_found}, Percentage={percentage_found}")
    
    # Analyze results
    print(f"\n📈 Step 3: Analyze Results")
    print("=" * 60)
    
    print("Test Results Summary:")
    for result in results:
        if "error" in result:
            print(f"  Test #{result['test']}: ❌ ERROR - {result['error']}")
        else:
            team_correct = result['team'] == correct_team
            percentage_correct = result['percentage'] == correct_percentage
            both_correct = team_correct and percentage_correct
            
            status = "✅ PERFECT" if both_correct else "⚠️ PARTIAL" if team_correct else "❌ WRONG"
            print(f"  Test #{result['test']}: {status}")
            print(f"    Team: {result['team']} (expected: {correct_team}) - {'✅' if team_correct else '❌'}")
            print(f"    Percentage: {result['percentage']}% (expected: {correct_percentage}%) - {'✅' if percentage_correct else '❌'}")
            print(f"    Time: {result['time']:.2f}s")
    
    # Count consistency
    correct_answers = [r for r in results if "error" not in r and r['team'] == correct_team and r['percentage'] == correct_percentage]
    team_correct = [r for r in results if "error" not in r and r['team'] == correct_team]
    
    print(f"\n📊 Consistency Analysis:")
    print(f"  Total Tests: {len(results)}")
    print(f"  Perfect Matches: {len(correct_answers)}/{len(results)} ({len(correct_answers)/len(results)*100:.1f}%)")
    print(f"  Team Correct: {len(team_correct)}/{len(results)} ({len(team_correct)/len(results)*100:.1f}%)")
    
    if len(correct_answers) < len(results):
        print(f"\n🔍 Inconsistency Detected!")
        print(f"  - {len(results) - len(correct_answers)} tests returned different results")
        print(f"  - This suggests LLM hallucination or inconsistent SQL generation")
        
        # Show different answers
        unique_answers = {}
        for result in results:
            if "error" not in result:
                key = f"{result['team']}_{result['percentage']}"
                if key not in unique_answers:
                    unique_answers[key] = []
                unique_answers[key].append(result['test'])
        
        print(f"\n📝 Unique Answers Found:")
        for answer_key, test_numbers in unique_answers.items():
            team, pct = answer_key.split('_')
            print(f"  {team} with {pct}%: Tests {test_numbers}")
    
    conn.close()
    return results

def debug_sql_generation():
    """Debug the SQL generation process"""
    print(f"\n🔍 Step 4: Debug SQL Generation Process")
    print("=" * 60)
    
    agent = NFLStatAgent()
    
    # Let's look at the debug output from the agent
    print("Running query with debug output...")
    
    question = "which team had the best red zone touchdown percentage in 2024"
    
    # Run the query and capture debug info
    answer, error = agent._run_database_query(question)
    
    print(f"\nFinal Answer: {answer}")
    if error:
        print(f"Error: {error}")
    
    # Get debug logs
    debug_logs = agent.get_debug_logs()
    print(f"\nDebug Logs:")
    print(debug_logs)

if __name__ == "__main__":
    print("🏈 Red Zone Efficiency Debug Session")
    print("=" * 60)
    
    # Run the main debug
    results = debug_red_zone_efficiency()
    
    # Run SQL generation debug
    debug_sql_generation()
    
    print(f"\n🎯 Debug Session Complete!")
    print("=" * 60) 