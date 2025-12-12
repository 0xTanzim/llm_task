"""Database tools for querying PostgreSQL."""

import os

import psycopg2
from langchain.tools import tool
from psycopg2.extras import RealDictCursor

DB_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
)


def get_db_connection():
    """
    Create PostgreSQL database connection.

    Returns:
        psycopg2 connection with RealDictCursor
    """
    connection = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    return connection


@tool()
def query_database(sql_query: str) -> str:
    """
    Execute read-only SQL queries on PostgreSQL database.

    Use this for:
    - SELECT queries to get customer data
    - Get order information
    - Check product details
    - Any database lookups

    IMPORTANT: Only SELECT queries are allowed for safety.

    Args:
        sql_query: SQL SELECT query to execute

    Returns:
        Formatted query results or error message

    Example queries:
    - "SELECT * FROM customers LIMIT 5"
    - "SELECT * FROM orders WHERE status = 'delivered'"
    - "SELECT name, price FROM products WHERE category = 'Electronics'"
    """
    try:
        sql = (sql_query or "").strip()
        sql_lower = sql.lower()

        # Safety guardrail: allow read-only queries only
        disallowed = (
            "drop ",
            "delete ",
            "truncate ",
            "alter ",
            "update ",
            "insert ",
            "create ",
        )

        if any(tok in sql_lower for tok in disallowed):
            return "❌ Unsafe SQL blocked. Only read-only queries are allowed (SELECT/WITH/EXPLAIN)."

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Execute query
        cur.execute(sql)
        results = cur.fetchall()

        limit = 10  # Limit results displayed

        if results:
            output = f"✅ Query successful! Found {len(results)} rows:\n\n"
            for row in results[:limit]:
                output += f"• {dict(row)}\n"
            if len(results) > limit:
                output += f"\n... and {len(results) - limit} more rows"
        else:
            output = "✅ Query executed but found no results"

        cur.close()
        conn.close()

        return output

    except psycopg2.Error as e:
        return f"❌ Database error: {e}"
    except Exception as e:
        return f"❌ Error: {e}"


@tool
def get_database_schema() -> str:
    """
    Get the database schema - list all tables and their columns.

    Use this when you're not sure what tables exist or their structure.

    Returns:
        A formatted string listing all tables and their columns in the public schema.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get all tables
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        tables = cur.fetchall()

        if not tables:
            return "No tables found in public schema."

        output = "📌 Database Schema (public schema):\n\n"

        for table in tables:
            table_name = table["table_name"]
            output += f"=== {table_name} ===\n"

            # Get columns for this table
            cur.execute(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """,
                (table_name,),
            )

            columns = cur.fetchall()

            for col in columns:
                nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
                default = (
                    ""
                    if col["column_default"] is None
                    else f"DEFAULT {col['column_default']}"
                )
                output += f"  - {col['column_name']} ({col['data_type']}) {nullable} {default}\n"

            output += "\n"

        cur.close()
        conn.close()

        return output

    except psycopg2.Error as e:
        return f"❌ Database error: {e}"
    except Exception as e:
        return f"❌ Schema error: {e}"


# Tool list for database operations
database_tools = [query_database, get_database_schema]
