"""
SQL Query Analyzer Module

Analyzes parsed SQL queries to identify issues and provide improvement suggestions.
"""

from parser import ParsedQuery


def analyze_select_star(parsed: ParsedQuery) -> tuple[list[str], list[str]]:
    """
    Checks for SELECT * usage.
    
    Returns:
        Tuple of (issues, suggestions)
    """
    issues = []
    suggestions = []
    
    if parsed.select_columns and parsed.select_columns[0].strip() == '*':
        issues.append("SELECT * retrieves all columns which can cause unnecessary data transfer")
        suggestions.append("Specify only the columns you need instead of SELECT *")
    
    return issues, suggestions


def analyze_missing_where(parsed: ParsedQuery) -> tuple[list[str], list[str]]:
    """
    Checks for missing WHERE clause on SELECT/UPDATE/DELETE.
    
    Returns:
        Tuple of (issues, suggestions)
    """
    issues = []
    suggestions = []
    
    if parsed.query_type in ('SELECT', 'UPDATE', 'DELETE') and not parsed.where_conditions:
        if parsed.query_type == 'SELECT':
            issues.append("SELECT without WHERE clause may perform a full table scan")
            suggestions.append("Add a WHERE clause to filter rows and reduce data scanned")
        elif parsed.query_type == 'UPDATE':
            issues.append("UPDATE without WHERE clause will modify ALL rows in the table")
            suggestions.append("Add a WHERE clause to limit which rows are updated")
        elif parsed.query_type == 'DELETE':
            issues.append("DELETE without WHERE clause will remove ALL rows from the table")
            suggestions.append("Add a WHERE clause to limit which rows are deleted")
    
    return issues, suggestions


def analyze_limit_clause(parsed: ParsedQuery, has_order_by: bool = False) -> tuple[list[str], list[str]]:
    """
    Checks for missing LIMIT clause on SELECT queries.
    
    Returns:
        Tuple of (issues, suggestions)
    """
    issues = []
    suggestions = []
    
    # This is a simplified check - in reality we'd parse LIMIT from the query
    # For now, we'll suggest LIMIT for queries without WHERE that return many rows
    if parsed.query_type == 'SELECT' and not parsed.where_conditions:
        issues.append("Query may return large result set without LIMIT")
        suggestions.append("Consider adding a LIMIT clause to control result size")
    
    return issues, suggestions


def analyze_like_patterns(parsed: ParsedQuery) -> tuple[list[str], list[str]]:
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
                        issues.append(f"LIKE pattern with leading wildcard cannot use index: {condition.strip()}")
                        suggestions.append("Consider removing leading wildcard or using full-text search")
                    elif pattern.startswith("'_") or pattern.startswith('"_'):
                        issues.append(f"LIKE pattern with leading underscore may not use index efficiently: {condition.strip()}")
    
    return issues, suggestions


def analyze_not_conditions(parsed: ParsedQuery) -> tuple[list[str], list[str]]:
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
            issues.append(f"NOT IN can be slow and may have NULL handling issues: {condition.strip()}")
            suggestions.append("Consider using LEFT JOIN with IS NULL or NOT EXISTS instead of NOT IN")
        
        # Check for != or <>
        if '!=' in condition or '<>' in condition:
            issues.append(f"Inequality operators (!=, <>) may not use indexes efficiently: {condition.strip()}")
            suggestions.append("Consider if an equality condition or range query could be used instead")
    
    return issues, suggestions


def analyze_or_conditions(parsed: ParsedQuery) -> tuple[list[str], list[str]]:
    """
    Checks for OR conditions that may be inefficient.
    
    Returns:
        Tuple of (issues, suggestions)
    """
    issues = []
    suggestions = []
    
    # Check if WHERE conditions contain OR
    # The parser splits by AND/OR, so we need to look at the original query
    # For now, check if there are multiple conditions that might use OR
    
    return issues, suggestions


def analyze_functions_in_where(parsed: ParsedQuery) -> tuple[list[str], list[str]]:
    """
    Checks for functions applied to columns in WHERE clause.
    
    Returns:
        Tuple of (issues, suggestions)
    """
    issues = []
    suggestions = []
    
    for condition in parsed.where_conditions:
        # Simple check for function patterns (word followed by opening paren)
        condition_upper = condition.upper()
        
        # Common functions that prevent index usage
        functions = ['UPPER(', 'LOWER(', 'SUBSTRING(', 'SUBSTR(', 'LEFT(', 'RIGHT(',
                    'DATE(', 'YEAR(', 'MONTH(', 'DAY(', 'CAST(', 'CONVERT(']
        
        for func in functions:
            if func in condition_upper:
                issues.append(f"Function on column in WHERE prevents index usage: {condition.strip()}")
                suggestions.append(f"Consider storing pre-computed values or using a computed column instead of applying {func.strip('(')}() in WHERE")
                break
    
    return issues, suggestions


def analyze_column_count(parsed: ParsedQuery) -> tuple[list[str], list[str]]:
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
            issues.append(f"Query selects {col_count} columns which may impact performance")
            suggestions.append("Select only the columns you actually need")
    
    return issues, suggestions


def analyze_distinct_usage(parsed: ParsedQuery) -> tuple[list[str], list[str]]:
    """
    Checks for DISTINCT that might indicate data quality issues.
    
    Returns:
        Tuple of (issues, suggestions)
    """
    issues = []
    suggestions = []
    
    # This would need access to the raw tokens or query string
    # For now, placeholder for future enhancement
    
    return issues, suggestions


def analyze_query(parsed: ParsedQuery) -> dict:
    """
    Analyzes a parsed SQL query and returns issues and suggestions.
    
    Args:
        parsed: A ParsedQuery object containing the parsed query components
        
    Returns:
        A dictionary with 'issues' and 'suggestions' keys
    """
    all_issues = []
    all_suggestions = []
    
    # Run all analysis functions
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
    
    return {
        "issues": all_issues,
        "suggestions": all_suggestions
    }
