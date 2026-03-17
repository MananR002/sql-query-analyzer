"""
SQL Query Analyzer CLI Tool

A simple CLI tool that accepts SQL queries and provides analysis insights.
"""

from tokenizer import tokenize, TokenType, tokenize_ignore_whitespace


def format_tokens(tokens: list) -> str:
    """
    Formats token list for display.
    
    Args:
        tokens: List of Token objects
        
    Returns:
        Formatted string representation of tokens
    """
    lines = []
    lines.append(f"\nTotal tokens: {len(tokens)}")
    lines.append("-" * 50)
    lines.append(f"{'Type':<20} {'Value':<25} {'Pos'}")
    lines.append("-" * 50)
    
    for token in tokens:
        value_display = repr(token.value) if len(token.value) > 20 else token.value
        lines.append(f"{token.type.name:<20} {value_display:<25} {token.position}")
    
    return "\n".join(lines)


def analyze_query(query: str) -> dict:
    """
    Analyzes a SQL query and returns structured insights.
    
    Args:
        query: The SQL query string to analyze
        
    Returns:
        A dictionary containing analysis results with 'issues', 'suggestions', 
        and 'tokens' keys
    """
    # Tokenize the query
    all_tokens = tokenize(query)
    meaningful_tokens = tokenize_ignore_whitespace(query)
    
    # Placeholder analysis - will be expanded
    issues = []
    suggestions = []
    
    return {
        "issues": issues,
        "suggestions": suggestions,
        "tokens": all_tokens,
        "token_count": len(meaningful_tokens)
    }


def format_results(results: dict) -> str:
    """
    Formats the analysis results into a human-readable string.
    
    Args:
        results: The dictionary containing analysis results
        
    Returns:
        A formatted string for terminal output
    """
    lines = []
    lines.append("\n" + "=" * 50)
    lines.append("SQL QUERY ANALYSIS RESULTS")
    lines.append("=" * 50)
    
    # Token stats
    lines.append(f"\n📊 Token Count: {results.get('token_count', 0)} (excluding whitespace)")
    
    # Issues section
    lines.append("\n📋 Issues Found:")
    if results.get("issues"):
        for i, issue in enumerate(results["issues"], 1):
            lines.append(f"  {i}. {issue}")
    else:
        lines.append("  ✓ No issues detected")
    
    # Suggestions section
    lines.append("\n💡 Suggestions:")
    if results.get("suggestions"):
        for i, suggestion in enumerate(results["suggestions"], 1):
            lines.append(f"  {i}. {suggestion}")
    else:
        lines.append("  ✓ No suggestions at this time")
    
    lines.append("\n" + "=" * 50)
    return "\n".join(lines)


def get_user_input() -> str:
    """
    Prompts the user to enter a SQL query.
    
    Returns:
        The SQL query string entered by the user
    """
    print("Enter your SQL query (press Enter twice to finish):")
    print("-" * 50)
    
    lines = []
    while True:
        try:
            line = input()
            if not line and lines:
                break
            lines.append(line)
        except (EOFError, KeyboardInterrupt):
            print("\nInput cancelled.")
            return ""
    
    return "\n".join(lines).strip()


def main():
    """
    Main entry point for the SQL Query Analyzer CLI.
    """
    print("🔍 SQL Query Analyzer")
    print("=" * 50)
    
    # Get query from user
    query = get_user_input()
    
    if not query:
        print("No query provided. Exiting.")
        return
    
    # Echo the query back to confirm flow
    print("\n" + "=" * 50)
    print("RAW QUERY RECEIVED:")
    print("=" * 50)
    print(query)
    
    # Analyze the query
    print("\nAnalyzing query...")
    results = analyze_query(query)
    
    # Display tokenization results
    print("\n" + "=" * 50)
    print("TOKENS:")
    print("=" * 50)
    print(format_tokens(results["tokens"]))
    
    # Display formatted analysis results
    formatted_output = format_results(results)
    print(formatted_output)


if __name__ == "__main__":
    main()
