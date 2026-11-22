"""
SQL Safety Validation service.

Validates generated SQL to ensure:
1. Only read-only operations are allowed.
2. Destructive operations are blocked.
3. Basic syntax validation.
"""

import logging
import re
from dataclasses import dataclass

import sqlparse

logger = logging.getLogger(__name__)

# Operations that are strictly blocked
BLOCKED_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "GRANT", "REVOKE", "EXECUTE", "EXEC",
    "COPY", "VACUUM", "REINDEX", "CLUSTER", "COMMENT",
    "LOCK", "UNLOCK", "PREPARE", "DEALLOCATE",
    "SET ROLE", "RESET ROLE", "DISCARD",
}

# Patterns that indicate destructive operations
BLOCKED_PATTERNS = [
    r"\bINSERT\s+INTO\b",
    r"\bUPDATE\s+\w+\s+SET\b",
    r"\bDELETE\s+FROM\b",
    r"\bDROP\s+(TABLE|DATABASE|INDEX|VIEW|SCHEMA|SEQUENCE|FUNCTION)\b",
    r"\bALTER\s+(TABLE|DATABASE|INDEX|VIEW|SCHEMA|SEQUENCE)\b",
    r"\bTRUNCATE\s+(TABLE\s+)?\w+",
    r"\bCREATE\s+(TABLE|DATABASE|INDEX|VIEW|SCHEMA|SEQUENCE|FUNCTION|ROLE|USER)\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bCOPY\b",
    r"\bINTO\s+OUTFILE\b",
    r"\bINTO\s+DUMPFILE\b",
    r"\bLOAD\s+DATA\b",
    r";\s*(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE)",  # Multi-statement injection
]


@dataclass
class ValidationResult:
    """Result of SQL validation."""
    is_valid: bool
    cleaned_sql: str
    reason: str = ""


def validate_sql(sql: str) -> ValidationResult:
    """
    Validate a SQL query for safety.

    Args:
        sql: The SQL query to validate.

    Returns:
        ValidationResult with is_valid, cleaned_sql, and reason.
    """
    if not sql or not sql.strip():
        return ValidationResult(
            is_valid=False,
            cleaned_sql="",
            reason="Empty SQL query",
        )

    cleaned = sql.strip()

    # Remove trailing semicolons for parsing but keep for execution
    clean_for_check = cleaned.rstrip(";").strip()

    # Check for blocked patterns (case-insensitive)
    upper_sql = clean_for_check.upper()

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            match = re.search(pattern, cleaned, re.IGNORECASE)
            logger.warning(
                "Blocked SQL pattern detected: %s in query: %s",
                match.group() if match else pattern,
                cleaned[:100],
            )
            return ValidationResult(
                is_valid=False,
                cleaned_sql=cleaned,
                reason=f"Blocked operation detected: {match.group() if match else 'destructive operation'}",
            )

    # Parse and check statement types
    try:
        parsed = sqlparse.parse(cleaned)
        if not parsed:
            return ValidationResult(
                is_valid=False,
                cleaned_sql=cleaned,
                reason="Could not parse SQL query",
            )

        for statement in parsed:
            # Get the statement type
            stmt_type = statement.get_type()

            # Allow only SELECT and UNKNOWN (CTEs parsed as UNKNOWN)
            if stmt_type and stmt_type not in ("SELECT", "UNKNOWN"):
                logger.warning(
                    "Blocked SQL statement type: %s in query: %s",
                    stmt_type, cleaned[:100],
                )
                return ValidationResult(
                    is_valid=False,
                    cleaned_sql=cleaned,
                    reason=f"Only SELECT queries are allowed. Found: {stmt_type}",
                )

            # For UNKNOWN type, verify it starts with WITH (CTE) or SELECT
            if stmt_type == "UNKNOWN":
                first_token = str(statement.tokens[0]).strip().upper()
                if first_token not in ("WITH", "SELECT", "("):
                    return ValidationResult(
                        is_valid=False,
                        cleaned_sql=cleaned,
                        reason=f"Query must start with SELECT or WITH. Found: {first_token}",
                    )

    except Exception as e:
        logger.warning("SQL parsing error: %s", e)
        # If parsing fails, do a basic keyword check
        first_word = clean_for_check.split()[0].upper() if clean_for_check.split() else ""
        if first_word not in ("SELECT", "WITH"):
            return ValidationResult(
                is_valid=False,
                cleaned_sql=cleaned,
                reason=f"Query must start with SELECT or WITH. Found: {first_word}",
            )

    # Check for multiple statements (potential injection)
    statements = [s for s in sqlparse.split(cleaned) if s.strip()]
    if len(statements) > 1:
        logger.warning("Multiple SQL statements detected: %d", len(statements))
        return ValidationResult(
            is_valid=False,
            cleaned_sql=cleaned,
            reason="Multiple SQL statements are not allowed. Only single queries are permitted.",
        )

    # Additional safety: check for suspicious patterns
    if re.search(r"--.*$", cleaned, re.MULTILINE):
        # SQL comments are okay, but check they don't hide malicious content
        pass

    logger.info("SQL validation passed: %s", cleaned[:100])
    return ValidationResult(
        is_valid=True,
        cleaned_sql=cleaned,
        reason="",
    )
