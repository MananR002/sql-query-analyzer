"""
SQL Parser Module

Parses SQL tokens into structured components like SELECT, FROM, WHERE clauses.
"""

from tokenizer import Token, TokenType, tokenize_ignore_whitespace


class ParsedQuery:
    """Represents a parsed SQL query with its components."""
    
    def __init__(self):
        self.select_columns = []
        self.from_table = None
        self.where_conditions = []
        self.query_type = None  # SELECT, INSERT, UPDATE, DELETE, etc.
    
    def to_dict(self) -> dict:
        """Converts the parsed query to a dictionary representation."""
        result = {
            "query_type": self.query_type
        }
        
        if self.select_columns:
            result["select"] = self.select_columns
        if self.from_table:
            result["from"] = self.from_table
        if self.where_conditions:
            result["where"] = self.where_conditions
            
        return result
    
    def __repr__(self) -> str:
        return f"ParsedQuery({self.to_dict()})"


def parse_select_columns(tokens: list[Token], start_idx: int) -> tuple[list[str], int]:
    """
    Parses SELECT column list from tokens.
    
    Args:
        tokens: List of tokens
        start_idx: Index to start parsing from (after SELECT keyword)
        
    Returns:
        Tuple of (list of column names, next index after columns)
    """
    columns = []
    i = start_idx
    current_column = []
    
    while i < len(tokens):
        token = tokens[i]
        
        # Stop at FROM keyword
        if token.type == TokenType.KEYWORD and token.value.upper() == "FROM":
            # Save any pending column
            if current_column:
                columns.append(" ".join(current_column))
            break
        
        # Handle comma - end of current column
        if token.type == TokenType.PUNCTUATION and token.value == ",":
            if current_column:
                columns.append(" ".join(current_column))
                current_column = []
            i += 1
            continue
        
        # Skip whitespace (shouldn't be here with ignore_whitespace, but be safe)
        if token.type == TokenType.WHITESPACE:
            i += 1
            continue
        
        # Build column expression (handles table.column, functions, etc.)
        if token.type in (TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.OPERATOR, 
                         TokenType.LITERAL_STRING, TokenType.LITERAL_NUMBER, 
                         TokenType.PUNCTUATION):
            if token.type == TokenType.LITERAL_STRING:
                current_column.append(f"'{token.value}'")
            else:
                current_column.append(token.value)
        
        i += 1
    
    # Handle case where query ends without FROM
    if current_column and (i >= len(tokens) or 
                          not (tokens[i].type == TokenType.KEYWORD and 
                               tokens[i].value.upper() == "FROM")):
        columns.append(" ".join(current_column))
    
    return columns, i


def parse_table_name(tokens: list[Token], start_idx: int) -> tuple[str | None, int]:
    """
    Parses table name from tokens.
    
    Args:
        tokens: List of tokens
        start_idx: Index to start parsing from (should be at FROM keyword)
        
    Returns:
        Tuple of (table name or None, next index after table name)
    """
    i = start_idx
    
    # Skip the FROM keyword
    if i < len(tokens) and tokens[i].type == TokenType.KEYWORD and tokens[i].value.upper() == "FROM":
        i += 1
    
    # Find the table name (identifier)
    while i < len(tokens):
        token = tokens[i]
        
        # Stop at next keyword (like WHERE, JOIN, etc.)
        if token.type == TokenType.KEYWORD:
            break
        
        # Skip whitespace
        if token.type == TokenType.WHITESPACE:
            i += 1
            continue
        
        # Return the table name
        if token.type == TokenType.IDENTIFIER:
            return token.value, i + 1
        
        i += 1
    
    return None, i


def parse_where_conditions(tokens: list[Token], start_idx: int) -> tuple[list[str], int]:
    """
    Parses WHERE conditions from tokens.
    
    Args:
        tokens: List of tokens
        start_idx: Index to start parsing from (should be at WHERE keyword)
        
    Returns:
        Tuple of (list of condition strings, next index after conditions)
    """
    conditions = []
    i = start_idx
    current_condition = []
    
    # Skip the WHERE keyword
    if i < len(tokens) and tokens[i].type == TokenType.KEYWORD and tokens[i].value.upper() == "WHERE":
        i += 1
    
    while i < len(tokens):
        token = tokens[i]
        
        # Stop at keywords that end WHERE clause (ORDER BY, GROUP BY, LIMIT, etc.)
        if token.type == TokenType.KEYWORD and token.value.upper() in (
            "ORDER", "GROUP", "HAVING", "LIMIT", "OFFSET", "UNION", "INTERSECT", "EXCEPT"
        ):
            if current_condition:
                conditions.append(" ".join(current_condition).strip())
            break
        
        # Handle AND/OR - split conditions
        if token.type == TokenType.KEYWORD and token.value.upper() in ("AND", "OR"):
            if current_condition:
                conditions.append(" ".join(current_condition).strip())
                current_condition = []
            i += 1
            continue
        
        # Skip whitespace
        if token.type == TokenType.WHITESPACE:
            i += 1
            continue
        
        # Build condition expression
        if token.type in (TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.OPERATOR,
                         TokenType.LITERAL_STRING, TokenType.LITERAL_NUMBER,
                         TokenType.PUNCTUATION):
            if token.type == TokenType.LITERAL_STRING:
                current_condition.append(f"'{token.value}'")
            else:
                current_condition.append(token.value)
        
        i += 1
    
    # Handle remaining condition
    if current_condition:
        conditions.append(" ".join(current_condition).strip())
    
    return conditions, i


def parse_query(sql: str) -> ParsedQuery:
    """
    Parses a SQL query string into its components.
    
    Args:
        sql: The SQL query string to parse
        
    Returns:
        A ParsedQuery object containing the extracted components
    """
    tokens = tokenize_ignore_whitespace(sql)
    result = ParsedQuery()
    
    if not tokens:
        return result
    
    # Identify query type from first token
    first_token = tokens[0]
    if first_token.type == TokenType.KEYWORD:
        result.query_type = first_token.value.upper()
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        # Handle SELECT
        if token.type == TokenType.KEYWORD and token.value.upper() == "SELECT":
            columns, i = parse_select_columns(tokens, i + 1)
            result.select_columns = columns
            continue
        
        # Handle FROM
        if token.type == TokenType.KEYWORD and token.value.upper() == "FROM":
            table_name, i = parse_table_name(tokens, i)
            result.from_table = table_name
            continue
        
        # Handle WHERE
        if token.type == TokenType.KEYWORD and token.value.upper() == "WHERE":
            conditions, i = parse_where_conditions(tokens, i)
            result.where_conditions = conditions
            continue
        
        i += 1
    
    return result
