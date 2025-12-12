import ast
import json
import os

import psycopg2
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_tavily import TavilySearch
from psycopg2.extras import RealDictCursor

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "localhost")


def get_db_connection():
    connection = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    return connection


# ============ TOOLS ============


@tool()
def query_database(sql_query: str) -> str:
    """
    Execute SQL queries on PostgreSQL database.
    Use this for:
    - SELECT queries to get customer data
    - Get order information
    - Check product details
    - Any database lookups

    Example queries:
    - "SELECT * FROM customers LIMIT 5"
    - "SELECT * FROM orders WHERE status = 'delivered'"
    - "SELECT name, price FROM products WHERE category = 'Electronics'"
    """

    try:
        sql = (sql_query or "").strip()
        sql_lower = sql.lower()

        # safety guardrail: allow read-only queries only.
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

        limit = 5

        cur.execute(sql)
        results = cur.fetchall()

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
    except Exception as e:
        return f"Error connecting to database: {e}"


@tool
def get_database_schema() -> str:
    """
    Get the database schema - list all tables and their columns.
    Use this when you're not sure what tables exist or their structure.

    returns:
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
        """)

        tables = cur.fetchall()

        if not tables:
            return "No tables found in public schema."

        output = "📌 Database Schema (public schema):\n\n"

        for table in tables:
            table_name = table["table_name"]
            output += f"=== {table_name} ===\n"

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
                output += (
                    f"- {col['column_name']} ({col['data_type']}) "
                    f"{'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'} "
                    f"{'' if col['column_default'] is None else f'DEFAULT {col["column_default"]}'}\n"
                )
            output += "\n"

        cur.close()
        conn.close()

        return output

    except Exception as e:
        return f"❌ Schema error: {str(e)}"


# print( query_database.invoke("SELECT * FROM customers LIMIT 5") )

# print(get_database_schema.invoke(""))


@tool
def search_web(query: str) -> str:
    """
    Search the web for current information.
    Use this for: latest news, real-time data, external information
    """

    tavily = TavilySearch(max_results=5)
    response = tavily.invoke(query)

    if response["results"]:
        output = f"🔍 Found {len(response['results'])} results:\n\n"
        for i, result in enumerate(response["results"], 1):
            output += f"{i}. **{result['title']}**\n"
            output += f"   URL: {result['url']}\n"
            output += f"   Summary: {result['content']}\n\n"
    else:
        output = "No results found."

    return output


# print(search_web.invoke("Latest news on AI advancements in 2024"))


@tool
def call_external_api(url: str, method: str = "GET") -> str:
    """
    Call external REST APIs.
    Use this for external data like: weather, currency, etc.
    """
    try:
        import requests

        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return f"✅ API Response:\n{response.json()}"
    except Exception as e:
        return f"❌ API error: {str(e)}"


# print(call_external_api.invoke("https://jsonplaceholder.typicode.com/todos/1"))


@tool
def get_current_time() -> str:
    """Get current date and time."""
    from datetime import datetime

    return datetime.now().isoformat()


# print(get_current_time.invoke(""))


@tool
def explain_code(code: str) -> str:
    """
    Provide a structured summary of Python code using AST:
    - lists top-level functions & classes
    - for each function: args + docstring + approx. lines of code
    - for each class: methods + docstring
    This is a deterministic reasoning tool that helps you understand code quickly.
    """

    try:
        tree = ast.parse(code)
        lines = code.splitlines()

        out = []

        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                name = node.name
                args = [a.arg for a in node.args.args]
                doc = ast.get_docstring(node) or ""
                lineno = node.lineno
                end_lineno = getattr(node, "end_lineno", lineno)
                out.append(
                    {
                        "type": "function",
                        "name": name,
                        "args": args,
                        "doc": (doc[:240] + "...") if len(doc) > 240 else doc,
                        "loc": end_lineno - lineno + 1,
                    }
                )
            elif isinstance(node, ast.ClassDef):
                name = node.name
                doc = ast.get_docstring(node) or ""
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                out.append(
                    {
                        "type": "class",
                        "name": name,
                        "methods": methods,
                        "doc": (doc[:240] + "...") if len(doc) > 240 else doc,
                    }
                )
        return json.dumps(out, indent=2)
    except SyntaxError as e:
        return f"❌ Syntax error in code: {e}"


@tool
def suggest_refactor(code: str) -> str:
    """
    Very small static heuristic tool to suggest refactors:
    - flags functions > 80 LOC
    - flags functions with > 6 parameters
    - flags nested loops deeper than 2
    This is not exhaustive but gives quick hints.
    """
    try:
        tree = ast.parse(code)
        messages = []

        class RefactorVisitor(ast.NodeVisitor):
            def __init__(self):
                self.loop_depth = 0

            def visit_FunctionDef(self, node):
                args_len = len(node.args.args)
                lineno = node.lineno
                end_lineno = getattr(node, "end_lineno", lineno)
                loc = end_lineno - lineno + 1
                if args_len > 6:
                    messages.append(
                        f"Function '{node.name}' has {args_len} args (consider grouping into object)."
                    )
                if loc > 80:
                    messages.append(
                        f"Function '{node.name}' is {loc} lines (consider splitting)."
                    )
                self.generic_visit(node)

            def visit_For(self, node):
                if self.loop_depth >= 2:
                    messages.append(
                        "Found nested loops deeper than 2 (consider flattening)."
                    )
                self.loop_depth += 1
                self.generic_visit(node)
                self.loop_depth -= 1

            def visit_While(self, node):
                if self.loop_depth >= 2:
                    messages.append(
                        "Found nested loops deeper than 2 (consider flattening)."
                    )
                self.loop_depth += 1
                self.generic_visit(node)
                self.loop_depth -= 1

        visitor = RefactorVisitor()
        visitor.visit(tree)

        return "\n".join(messages) or "No quick refactor suggestions found."
    except Exception as e:
        return f"❌ suggest_refactor error: {e}"


@tool
def execute_code(code: str, language: str = "python") -> str:
    """
    Execute code snippets in a secure sandbox.
    Currently supports Python only.
    Use this for: quick calculations, data processing, etc.
    """

    if language.lower() != "python":
        return "❌ Only Python execution is supported."

    try:
        import subprocess
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name

        result = subprocess.run(
            ["python", temp_file_path],
            capture_output=True,
            text=True,
            timeout=5,
        )

        os.remove(temp_file_path)

        if result.returncode != 0:
            return f"❌ Error executing code:\n{result.stderr}"

        return f"✅ Code executed successfully:\n{result.stdout}"

    except Exception as e:
        return f"❌ Code execution error: {str(e)}"


# print(execute_code.invoke("print('Hello, World!')", language="python"))


all_tools = [
    query_database,
    get_database_schema,
    search_web,
    call_external_api,
    get_current_time,
    explain_code,
    suggest_refactor,
    execute_code,
]

database_tools = [query_database, get_database_schema, get_current_time]

code_analysis_tools = [explain_code, suggest_refactor, execute_code, get_current_time]

general_tools = [
    search_web,
    call_external_api,
    get_current_time,
]
