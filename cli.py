"""
SQL Query Analyzer CLI Tool

A simple CLI tool that accepts SQL queries and provides analysis insights.
"""

from tokenizer import tokenize, TokenType, tokenize_ignore_whitespace
from parser import parse_query
from analyzer import analyze_query as analyze_parsed_query, SEVERITY_PENALTY


def calculate_score(issues: list[dict]) -> tuple[int, str]:
    """
    Calculates performance score and risk level from issues.
    
    Args:
        issues: List of issue dictionaries with 'severity' field
        
    Returns:
        Tuple of (score 0-100, risk level string)
    """
    total_penalty = 0
    for issue in issues:
        severity = issue.get("severity", "medium")
        total_penalty += SEVERITY_PENALTY.get(severity, 10)
    
    score = max(0, 100 - total_penalty)
    
    # Determine risk level
    if score >= 85:
        risk = "Low"
    elif score >= 60:
        risk = "Medium"
    elif score >= 30:
        risk = "High"
    else:
        risk = "Critical"
    
    return score, risk


def format_parsed_structure(parsed) -> str:
    """
    Formats the parsed query structure for display.
    
    Args:
        parsed: A ParsedQuery object
        
    Returns:
        Formatted JSON-like string representation
    """
    result_dict = parsed.to_dict()
    
    lines = []
    lines.append("\n{")
    
    # Query type
    lines.append(f'  "query_type": {repr(result_dict.get("query_type"))},')
    
    # SELECT columns
    if "select" in result_dict:
        select_cols = result_dict["select"]
        if select_cols:
            lines.append(f'  "select": {select_cols},')
        else:
            lines.append('  "select": [],')
    
    # FROM table
    if "from" in result_dict:
        from_table = result_dict["from"]
        lines.append(f'  "from": {repr(from_table)},')
    
    # WHERE conditions
    if "where" in result_dict:
        where_conds = result_dict["where"]
        if where_conds:
            lines.append(f'  "where": {where_conds}')
        else:
            lines.append('  "where": []')
    
    lines.append("}")
    
    return "\n".join(lines)


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
        'tokens', and 'parsed' keys
    """
    # Tokenize the query
    all_tokens = tokenize(query)
    meaningful_tokens = tokenize_ignore_whitespace(query)
    
    # Parse the query structure
    parsed = parse_query(query)
    
    # Analyze the parsed query for issues and suggestions (pass tokens for typo detection)
    analysis = analyze_parsed_query(parsed, meaningful_tokens)
    
    return {
        "issues": analysis["issues"],
        "suggestions": analysis["suggestions"],
        "tokens": all_tokens,
        "token_count": len(meaningful_tokens),
        "parsed": parsed
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
    lines.append("\n" + "=" * 60)
    lines.append("SQL QUERY ANALYSIS RESULTS")
    lines.append("=" * 60)
    
    # Token stats
    lines.append(f"\n📊 Token Count: {results.get('token_count', 0)} (excluding whitespace)")
    
    # Calculate and display score
    issues = results.get("issues", [])
    score, risk = calculate_score(issues)
    lines.append(f"\n🎯 Performance Score: {score}/100  |  Risk Level: {risk}")
    
    # Issues section
    lines.append("\n📋 Issues Found:")
    if issues:
        for i, issue in enumerate(issues, 1):
            sev = issue.get("severity", "medium").upper()
            lines.append(f"\n  {i}. [{sev}] {issue['issue']}")
            lines.append(f"     Confidence: {issue['confidence']:.0%}")
            lines.append(f"     {issue['explanation']}")
    else:
        lines.append("  ✓ No issues detected")
    
    # Suggestions section
    lines.append("\n\n💡 Suggestions:")
    suggestions = results.get("suggestions", [])
    if suggestions:
        for i, suggestion in enumerate(suggestions, 1):
            lines.append(f"\n  {i}. {suggestion['suggestion']}")
            lines.append(f"     Confidence: {suggestion['confidence']:.0%}")
            lines.append(f"     {suggestion['explanation']}")
    else:
        lines.append("  ✓ No suggestions at this time")
    
    lines.append("\n" + "=" * 60)
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
    
    # Display parsed structure
    print("\n" + "=" * 50)
    print("PARSED STRUCTURE:")
    print("=" * 50)
    print(format_parsed_structure(results["parsed"]))
    
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
