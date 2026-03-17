"""
SQL Query Analyzer Module

Analyzes parsed SQL queries to identify issues and provide improvement suggestions.
"""

from parser import ParsedQuery
from tokenizer import Token, TokenType, SQL_KEYWORDS


# Severity penalty points
SEVERITY_PENALTY = {
    "high": 25,
    "medium": 10,
    "low": 5
}

def create_issue(title: str, explanation: str, confidence: float, severity: str = "medium") -> dict:
    """
    Creates a structured issue dictionary.
    
    Args:
        title: Short issue title
        explanation: Detailed explanation
        confidence: Confidence score 0-1
        severity: Impact level - "high", "medium", or "low"
    """
    return {
        "issue": title,
        "explanation": explanation,
        "confidence": round(confidence, 2),
        "severity": severity
    }


def create_suggestion(title: str, explanation: str, confidence: float) -> dict:
    """Creates a structured suggestion dictionary."""
    return {
        "suggestion": title,
        "explanation": explanation,
        "confidence": round(confidence, 2)
    }


def find_closest_keyword(token_value: str) -> str | None:
    """
    Finds the closest matching SQL keyword for a potential typo.
    
    Uses simple character overlap and length similarity to find likely matches.
    
    Args:
        token_value: The identifier token value to check
        
    Returns:
        Closest keyword match or None if no close match found
    """
    token_upper = token_value.upper()
    
    if token_upper in SQL_KEYWORDS:
        return None  # It's already a valid keyword
    
    # Skip very short tokens (likely not typos)
    if len(token_upper) < 2:
        return None
    
    best_match = None
    best_score = 0
    
    for keyword in SQL_KEYWORDS:
        # Quick checks for common typo patterns
        
        # Check if it's a substring (e.g., "LIK" is substring of "LIKE")
        if token_upper in keyword and len(token_upper) >= len(keyword) - 2:
            score = len(token_upper) / len(keyword)
            if score > best_score:
                best_score = score
                best_match = keyword
        
        # Check if keyword is substring of token (extra chars added)
        elif keyword in token_upper and len(keyword) >= len(token_upper) - 2:
            score = len(keyword) / len(token_upper)
            if score > best_score:
                best_score = score
                best_match = keyword
        
        # Check character overlap for similar length tokens
        elif abs(len(token_upper) - len(keyword)) <= 2:
            common_chars = set(token_upper) & set(keyword)
            if len(common_chars) >= min(len(token_upper), len(keyword)) - 1:
                overlap_ratio = len(common_chars) / max(len(token_upper), len(keyword))
                if overlap_ratio >= 0.7 and overlap_ratio > best_score:
                    best_score = overlap_ratio
                    best_match = keyword
    
    return best_match if best_score >= 0.5 else None


def analyze_keyword_typos(tokens: list[Token]) -> tuple[list[dict], list[dict]]:
    """
    Checks for potential typos in SQL keywords.
    
    Scans IDENTIFIER tokens and compares them against known keywords.
    
    Returns:
        Tuple of (issues, suggestions)
    """
    issues = []
    suggestions = []
    
    for token in tokens:
        if token.type == TokenType.IDENTIFIER:
            closest = find_closest_keyword(token.value)
            if closest:
                issues.append(create_issue(
                    title=f"Potential typo: '{token.value}' might be '{closest}'",
                    explanation=f"The identifier '{token.value}' is not a recognized keyword but closely matches SQL keyword '{closest}'. This could be a typo that will cause a syntax error or unexpected behavior.",
                    confidence=0.85
                ))
                suggestions.append(create_suggestion(
                    title=f"Change '{token.value}' to '{closest}'",
                    explanation=f"Replace '{token.value}' with '{closest}' if you intended to use the SQL keyword. Verify the context to ensure this is the correct fix.",
                    confidence=0.85
                ))
    
    return issues, suggestions


def analyze_select_star(parsed: ParsedQuery) -> tuple[list[dict], list[dict]]:
    """
    Checks for SELECT * usage.
    
    Returns:
        Tuple of (issues, suggestions)
    """
    issues = []
    suggestions = []
    
    if parsed.select_columns and parsed.select_columns[0].strip() == '*':
        issues.append(create_issue(
            title="SELECT * retrieves all columns",
            explanation="Using SELECT * fetches every column from the table, which increases network overhead, memory usage, and can break application code if table schema changes. It also prevents the query optimizer from using covering indexes.",
            confidence=0.95,
            severity="high"
        ))
        suggestions.append(create_suggestion(
            title="Specify only the columns you need",
            explanation="List each column explicitly (e.g., SELECT id, name, email). This reduces data transfer, improves cache efficiency, and makes your query more resilient to schema changes.",
            confidence=0.95
        ))
    
    return issues, suggestions


def analyze_missing_where(parsed: ParsedQuery) -> tuple[list[dict], list[dict]]:
    """
    Checks for missing WHERE clause on SELECT/UPDATE/DELETE.
    
    Returns:
        Tuple of (issues, suggestions)
    """
    issues = []
    suggestions = []
    
    if parsed.query_type in ('SELECT', 'UPDATE', 'DELETE') and not parsed.where_conditions:
        if parsed.query_type == 'SELECT':
            issues.append(create_issue(
                title="SELECT without WHERE may scan entire table",
                explanation="Without a WHERE clause, the database must read every row in the table. This is slow for large tables and wastes I/O and memory resources.",
                confidence=0.90,
                severity="high"
            ))
            suggestions.append(create_suggestion(
                title="Add a WHERE clause to filter rows",
                explanation="Include conditions to limit results (e.g., WHERE status = 'active'). This allows the database to use indexes and significantly reduces rows processed.",
                confidence=0.90
            ))
        elif parsed.query_type == 'UPDATE':
            issues.append(create_issue(
                title="UPDATE without WHERE modifies all rows",
                explanation="This is a dangerous operation that will change every row in the table. In production, this could corrupt all your data.",
                confidence=1.0,
                severity="high"
            ))
            suggestions.append(create_suggestion(
                title="Add a WHERE clause to limit affected rows",
                explanation="Always specify which rows to update (e.g., WHERE id = 123). Test with a SELECT first to verify you're updating the right rows.",
                confidence=1.0
            ))
        elif parsed.query_type == 'DELETE':
            issues.append(create_issue(
                title="DELETE without WHERE removes all rows",
                explanation="This will delete every row in the table. Without a backup, this data loss may be unrecoverable.",
                confidence=1.0,
                severity="high"
            ))
            suggestions.append(create_suggestion(
                title="Add a WHERE clause to limit deletions",
                explanation="Specify which rows to delete (e.g., WHERE created_at < '2020-01-01'). Always run as SELECT first to verify the rows, and ensure backups exist.",
                confidence=1.0
            ))
    
    return issues, suggestions


def analyze_limit_clause(parsed: ParsedQuery) -> tuple[list[dict], list[dict]]:
    """
    Checks for missing LIMIT clause on SELECT queries.
    
    Returns:
        Tuple of (issues, suggestions)
    """
    issues = []
    suggestions = []
    
    if parsed.query_type == 'SELECT' and not parsed.where_conditions:
        issues.append(create_issue(
            title="Query may return large result set",
            explanation="Without a LIMIT clause, the query could return millions of rows if the table is large, causing memory issues in your application and database.",
            confidence=0.75
        ))
        suggestions.append(create_suggestion(
            title="Add a LIMIT clause to control result size",
            explanation="Use LIMIT (or TOP/FETCH FIRST depending on your database) to cap results (e.g., LIMIT 100). Combine with pagination for large datasets.",
            confidence=0.75
        ))
    
    return issues, suggestions


def analyze_like_patterns(parsed: ParsedQuery) -> tuple[list[dict], list[dict]]:
    """
    Checks for LIKE patterns that can't use indexes (leading wildcards).
    
    Returns:
        Tuple of (issues, suggestions)
    """
    issues = []
    suggestions = []
    
    for condition in parsed.where_conditions:
        condition_upper = condition.upper()
        if ' LIKE ' in condition_upper:
            # Check for leading wildcard patterns
            if '%' in condition or '_' in condition:
                # Extract the pattern part (after LIKE)
                parts = condition_upper.split(' LIKE ')
                if len(parts) > 1:
                    pattern = parts[1].strip()
                    # Check if pattern starts with % or _
                    if pattern.startswith("'%") or pattern.startswith('"%'):
                        issues.append(create_issue(
                            title="LIKE pattern with leading wildcard cannot use index",
                            explanation=f"The pattern '{pattern}' starts with a wildcard, forcing a full table scan. The database cannot use B-tree indexes for prefix wildcards.",
                            confidence=0.90,
                            severity="medium"
                        ))
                        suggestions.append(create_suggestion(
                            title="Remove leading wildcard or use full-text search",
                            explanation="If possible, use 'prefix%' instead of '%suffix'. For complex text search, consider database full-text search features or dedicated search engines like Elasticsearch.",
                            confidence=0.85
                        ))
    
    return issues, suggestions


def analyze_not_conditions(parsed: ParsedQuery) -> tuple[list[dict], list[dict]]:
    """
    Checks for NOT conditions that may be inefficient.
    
    Returns:
        Tuple of (issues, suggestions)
    """
    issues = []
    suggestions = []
    
    for condition in parsed.where_conditions:
        condition_upper = condition.upper()
        
        # Check for NOT IN
        if ' NOT IN ' in condition_upper:
            issues.append(create_issue(
                title="NOT IN can be slow and has NULL handling issues",
                explanation="NOT IN performs poorly on large lists and returns no results if the subquery contains NULL values, which can cause subtle bugs.",
                confidence=0.80,
                severity="medium"
            ))
            suggestions.append(create_suggestion(
                title="Use LEFT JOIN with IS NULL or NOT EXISTS instead",
                explanation="Replace 'WHERE x NOT IN (SELECT y FROM t)' with 'WHERE NOT EXISTS (SELECT 1 FROM t WHERE y = x)' or use a LEFT JOIN with 'WHERE t.y IS NULL'.",
                confidence=0.80
            ))
        
        # Check for != or <>
        if '!=' in condition or '<>' in condition:
            issues.append(create_issue(
                title="Inequality operators may not use indexes efficiently",
                explanation="The != and <> operators often prevent index usage or require scanning large portions of the index, especially for high-cardinality columns.",
                confidence=0.70
            ))
            suggestions.append(create_suggestion(
                title="Consider if equality or range conditions could work",
                explanation="If possible, restructure to use =, >, <, or BETWEEN. For excluding specific values, consider if the values can be filtered in application code instead.",
                confidence=0.60
            ))
    
    return issues, suggestions


def analyze_or_conditions(parsed: ParsedQuery) -> tuple[list[dict], list[dict]]:
    """
    Checks for OR conditions that may be inefficient.
    
    Returns:
        Tuple of (issues, suggestions)
    """
    issues = []
    suggestions = []
    
    # Placeholder for future OR condition analysis
    
    return issues, suggestions


def analyze_functions_in_where(parsed: ParsedQuery) -> tuple[list[dict], list[dict]]:
    """
    Checks for functions applied to columns in WHERE clause.
    
    Returns:
        Tuple of (issues, suggestions)
    """
    issues = []
    suggestions = []
    
    for condition in parsed.where_conditions:
        condition_upper = condition.upper()
        
        # Common functions that prevent index usage
        functions = ['UPPER(', 'LOWER(', 'SUBSTRING(', 'SUBSTR(', 'LEFT(', 'RIGHT(',
                    'DATE(', 'YEAR(', 'MONTH(', 'DAY(', 'CAST(', 'CONVERT(']
        
        for func in functions:
            if func in condition_upper:
                func_name = func.strip('(')
                issues.append(create_issue(
                    title=f"Function {func_name}() on column prevents index usage",
                    explanation=f"Applying {func_name}() to a column in the WHERE clause forces the database to evaluate the function for every row, preventing index lookups.",
                    confidence=0.85,
                    severity="medium"
                ))
                suggestions.append(create_suggestion(
                    title="Store pre-computed values or use a computed column",
                    explanation=f"Instead of 'WHERE {func_name}(column) = value', store the computed value in a separate column with an index, or use a function-based index if your database supports it.",
                    confidence=0.80
                ))
                break
    
    return issues, suggestions


def analyze_column_count(parsed: ParsedQuery) -> tuple[list[dict], list[dict]]:
    """
    Checks if too many columns are being selected.
    
    Returns:
        Tuple of (issues, suggestions)
    """
    issues = []
    suggestions = []
    
    if parsed.select_columns:
        col_count = len(parsed.select_columns)
        if col_count > 10:
            issues.append(create_issue(
                title=f"Query selects {col_count} columns",
                explanation="Selecting many columns increases memory usage, network transfer, and processing time. It also reduces the chance that a covering index can be used.",
                confidence=0.70
            ))
            suggestions.append(create_suggestion(
                title="Select only the columns your application needs",
                explanation="Review which columns are actually used in your application. Removing unused columns can significantly improve query performance and reduce resource usage.",
                confidence=0.75
            ))
    
    return issues, suggestions


def analyze_distinct_usage(parsed: ParsedQuery) -> tuple[list[dict], list[dict]]:
    """
    Checks for DISTINCT that might indicate data quality issues.
    
    Returns:
        Tuple of (issues, suggestions)
    """
    issues = []
    suggestions = []
    
    # Placeholder for future DISTINCT analysis
    
    return issues, suggestions


def analyze_query(parsed: ParsedQuery, tokens: list[Token] | None = None) -> dict:
    """
    Analyzes a parsed SQL query and returns issues and suggestions.
    
    Args:
        parsed: A ParsedQuery object containing the parsed query components
        tokens: Optional list of tokens for keyword typo detection
        
    Returns:
        A dictionary with 'issues' and 'suggestions' keys containing structured objects
    """
    all_issues = []
    all_suggestions = []
    
    # Run parsed-based analysis functions
    analyzers = [
        analyze_select_star,
        analyze_missing_where,
        analyze_limit_clause,
        analyze_like_patterns,
        analyze_not_conditions,
        analyze_or_conditions,
        analyze_functions_in_where,
        analyze_column_count,
        analyze_distinct_usage,
    ]
    
    for analyzer in analyzers:
        issues, suggestions = analyzer(parsed)
        all_issues.extend(issues)
        all_suggestions.extend(suggestions)
    
    # Run token-based analysis if tokens provided
    if tokens:
        typo_issues, typo_suggestions = analyze_keyword_typos(tokens)
        all_issues.extend(typo_issues)
        all_suggestions.extend(typo_suggestions)
    
    return {
        "issues": all_issues,
        "suggestions": all_suggestions
    }
