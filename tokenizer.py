"""
SQL Tokenizer Module

Converts raw SQL query strings into a list of structured tokens.
"""

from enum import Enum, auto


class TokenType(Enum):
    """Enumeration of SQL token types."""
    KEYWORD = auto()
    IDENTIFIER = auto()
    OPERATOR = auto()
    LITERAL_STRING = auto()
    LITERAL_NUMBER = auto()
    PUNCTUATION = auto()
    WHITESPACE = auto()
    COMMENT = auto()
    UNKNOWN = auto()


class Token:
    """Represents a single SQL token."""
    
    def __init__(self, token_type: TokenType, value: str, position: int = 0):
        self.type = token_type
        self.value = value
        self.position = position
    
    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, pos={self.position})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Token):
            return False
        return self.type == other.type and self.value == other.value


# SQL Keywords (common ones)
SQL_KEYWORDS = frozenset({
    'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP',
    'TABLE', 'INDEX', 'VIEW', 'INTO', 'VALUES', 'SET', 'JOIN', 'INNER', 'OUTER',
    'LEFT', 'RIGHT', 'FULL', 'ON', 'AND', 'OR', 'NOT', 'NULL', 'IS', 'AS',
    'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET', 'DISTINCT', 'ALL',
    'UNION', 'INTERSECT', 'EXCEPT', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
    'EXISTS', 'IN', 'BETWEEN', 'LIKE', 'ESCAPE', 'ASC', 'DESC'
})

# SQL Operators
SQL_OPERATORS = frozenset({
    '=', '<', '>', '<=', '>=', '<>', '!=', '+', '-', '*', '/', '%', '||',
    '&&', '!', '&', '|', '^', '~', '<<', '>>'
})

# Punctuation characters
PUNCTUATION_CHARS = frozenset({'(', ')', '[', ']', '{', '}', ',', ';', '.'})

# Whitespace characters
WHITESPACE_CHARS = frozenset({' ', '\t', '\n', '\r', '\v', '\f'})


def tokenize(sql: str) -> list[Token]:
    """
    Tokenizes a SQL query string into a list of tokens.
    
    Args:
        sql: The raw SQL query string to tokenize
        
    Returns:
        A list of Token objects representing the parsed query
    """
    tokens = []
    i = 0
    n = len(sql)
    
    while i < n:
        char = sql[i]
        start_pos = i
        
        # Handle whitespace
        if char in WHITESPACE_CHARS:
            while i < n and sql[i] in WHITESPACE_CHARS:
                i += 1
            tokens.append(Token(TokenType.WHITESPACE, sql[start_pos:i], start_pos))
            continue
        
        # Handle single-line comments (-- comment)
        if char == '-' and i + 1 < n and sql[i + 1] == '-':
            while i < n and sql[i] != '\n':
                i += 1
            tokens.append(Token(TokenType.COMMENT, sql[start_pos:i], start_pos))
            continue
        
        # Handle multi-line comments (/* comment */)
        if char == '/' and i + 1 < n and sql[i + 1] == '*':
            i += 2
            while i < n and not (sql[i] == '*' and i + 1 < n and sql[i + 1] == '/'):
                i += 1
            i += 2 if i < n else 0
            tokens.append(Token(TokenType.COMMENT, sql[start_pos:i], start_pos))
            continue
        
        # Handle string literals (single quotes)
        if char == "'":
            i += 1
            value = ""
            while i < n:
                if sql[i] == "'":
                    # Check for escaped quote ('')
                    if i + 1 < n and sql[i + 1] == "'":
                        value += "'"
                        i += 2
                    else:
                        i += 1
                        break
                else:
                    value += sql[i]
                    i += 1
            tokens.append(Token(TokenType.LITERAL_STRING, value, start_pos))
            continue
        
        # Handle string literals (double quotes - identifier in standard SQL, but treat as string)
        if char == '"':
            i += 1
            value = ""
            while i < n and sql[i] != '"':
                value += sql[i]
                i += 1
            i += 1 if i < n else 0
            tokens.append(Token(TokenType.IDENTIFIER, value, start_pos))
            continue
        
        # Handle backtick quoted identifiers (MySQL style)
        if char == '`':
            i += 1
            value = ""
            while i < n and sql[i] != '`':
                value += sql[i]
                i += 1
            i += 1 if i < n else 0
            tokens.append(Token(TokenType.IDENTIFIER, value, start_pos))
            continue
        
        # Handle bracket quoted identifiers (SQL Server style)
        if char == '[':
            i += 1
            value = ""
            while i < n and sql[i] != ']':
                value += sql[i]
                i += 1
            i += 1 if i < n else 0
            tokens.append(Token(TokenType.IDENTIFIER, value, start_pos))
            continue
        
        # Handle numbers (integers and decimals)
        if char.isdigit() or (char == '.' and i + 1 < n and sql[i + 1].isdigit()):
            has_dot = False
            while i < n:
                if sql[i].isdigit():
                    i += 1
                elif sql[i] == '.' and not has_dot and i + 1 < n and sql[i + 1].isdigit():
                    has_dot = True
                    i += 1
                else:
                    break
            tokens.append(Token(TokenType.LITERAL_NUMBER, sql[start_pos:i], start_pos))
            continue
        
        # Handle identifiers and keywords (letters, digits, underscore)
        if char.isalpha() or char == '_':
            while i < n and (sql[i].isalnum() or sql[i] == '_'):
                i += 1
            value = sql[start_pos:i]
            # Check if it's a keyword (case-insensitive)
            token_type = TokenType.KEYWORD if value.upper() in SQL_KEYWORDS else TokenType.IDENTIFIER
            tokens.append(Token(token_type, value, start_pos))
            continue
        
        # Handle operators (multi-character first)
        if char in '<>!=':
            if i + 1 < n:
                two_char = sql[i:i + 2]
                if two_char in ('<=', '>=', '<>', '!='):
                    tokens.append(Token(TokenType.OPERATOR, two_char, start_pos))
                    i += 2
                    continue
        
        # Handle single-character operators
        if char in '+-*/%=!&|^~':
            tokens.append(Token(TokenType.OPERATOR, char, start_pos))
            i += 1
            continue
        
        # Handle punctuation
        if char in PUNCTUATION_CHARS:
            tokens.append(Token(TokenType.PUNCTUATION, char, start_pos))
            i += 1
            continue
        
        # Unknown character - skip but record
        tokens.append(Token(TokenType.UNKNOWN, char, start_pos))
        i += 1
    
    return tokens


def tokenize_ignore_whitespace(sql: str) -> list[Token]:
    """
    Tokenizes a SQL query, filtering out whitespace and comments.
    
    Args:
        sql: The raw SQL query string to tokenize
        
    Returns:
        A list of Token objects with whitespace and comments removed
    """
    all_tokens = tokenize(sql)
    return [t for t in all_tokens if t.type not in (TokenType.WHITESPACE, TokenType.COMMENT)]
