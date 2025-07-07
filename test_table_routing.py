#!/usr/bin/env python3
"""
Test script for table routing logic
This demonstrates how queries are routed to the appropriate database tables.
"""

from agent import get_agent

def test_table_routing():
    """Test the table routing logic."""
    
    agent = get_agent()
    
    # Test queries with expected table routing
    test_cases = [
        # Team stats queries
        ("Which team had the best win percentage in 2023?", "team_stats"),
        ("Show me the top 5 teams by offensive EPA", "team_stats"),
        ("What was the Eagles' win streak in 2023?", "team_stats"),
        ("Compare quarterbacks by EPA", "team_stats"),
        
        # Play-by-play queries
        ("What is the most common play type?", "nflfastR_pbp"),
        ("How many touchdowns did Mahomes throw in 2023?", "nflfastR_pbp"),
        ("What's the success rate on 4th down attempts?", "nflfastR_pbp"),
        ("Show me plays with the highest EPA", "nflfastR_pbp"),
        
        # Matchup queries
        ("What was the Vegas spread for Chiefs vs Bills?", "pregame_matchups"),
        ("What was the win probability for the home team?", "pregame_matchups"),
        ("Show me head-to-head matchups between teams", "pregame_matchups"),
        ("What were the betting odds for the game?", "pregame_matchups"),
    ]
    
    print("🧪 Testing Table Routing Logic")
    print("=" * 60)
    
    for query, expected_table in test_cases:
        table_context = agent._get_appropriate_table_context(query)
        
        # Determine which table was selected based on context
        if "team_stats" in table_context.lower():
            actual_table = "team_stats"
        elif "play-by-play" in table_context.lower():
            actual_table = "nflfastR_pbp"
        elif "pregame_matchups" in table_context.lower() or "matchup" in table_context.lower():
            actual_table = "pregame_matchups"
        else:
            actual_table = "unknown"
        
        status = "✅" if actual_table == expected_table else "❌"
        
        print(f"{status} Query: {query[:50]}{'...' if len(query) > 50 else ''}")
        print(f"   Expected: {expected_table}")
        print(f"   Actual:   {actual_table}")
        print(f"   Context:  {table_context[:100]}{'...' if len(table_context) > 100 else ''}")
        print()

def show_table_guidance():
    """Show guidance on which table to use for different types of queries."""
    
    print("📊 Table Selection Guidance")
    print("=" * 60)
    
    print("\n🏈 team_stats table - Use for:")
    print("  • Team season performance and records")
    print("  • Rolling averages and trends (16-game, 8-game, 4-game)")
    print("  • Quarterback statistics and performance")
    print("  • Team rankings and comparisons")
    print("  • Win/loss records and streaks")
    print("  • Against-the-spread records")
    
    print("\n🎯 nflfastR_pbp table - Use for:")
    print("  • Individual plays and play types")
    print("  • Player-specific statistics")
    print("  • Game situations and scenarios")
    print("  • Detailed play analysis")
    print("  • Specific game moments and drives")
    print("  • Down/distance situations")
    
    print("\n⚔️  pregame_matchups table - Use for:")
    print("  • Game predictions and odds")
    print("  • Head-to-head matchups")
    print("  • Pre-game analysis")
    print("  • Betting lines and spreads")
    print("  • Team performance leading into specific games")
    print("  • Vegas spreads and win probabilities")

if __name__ == "__main__":
    show_table_guidance()
    print("\n" + "=" * 60)
    test_table_routing() 