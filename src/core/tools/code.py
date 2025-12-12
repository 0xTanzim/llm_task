"""Code analysis and execution tools."""

import ast
import json
import os
import subprocess
import tempfile

from langchain.tools import tool


@tool
def explain_code(code: str) -> str:
    """Provide structured summary of Python code using AST."""
    try:
        tree = ast.parse(code)
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
        return f"Syntax error: {e}"
    except Exception as e:
        return f"Analysis error: {e}"


@tool
def suggest_refactor(code: str) -> str:
    """Provide static refactor suggestions for Python code."""
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
                    messages.append(f"Function '{node.name}' has {args_len} args")
                if loc > 80:
                    messages.append(f"Function '{node.name}' is {loc} lines")
                self.generic_visit(node)

            def visit_For(self, node):
                if self.loop_depth >= 2:
                    messages.append("Found nested loops deeper than 2")
                self.loop_depth += 1
                self.generic_visit(node)
                self.loop_depth -= 1

            def visit_While(self, node):
                if self.loop_depth >= 2:
                    messages.append("Found nested loops deeper than 2")
                self.loop_depth += 1
                self.generic_visit(node)
                self.loop_depth -= 1

        visitor = RefactorVisitor()
        visitor.visit(tree)

        return "\n".join(messages) or "No refactor suggestions found."
    except Exception as e:
        return f"Refactor error: {e}"


@tool
def execute_code(code: str, language: str = "python") -> str:
    """Execute Python code snippets safely."""
    if language.lower() != "python":
        return "Only Python execution is supported."

    try:
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
            return f"Error: {result.stderr}"

        return f"Success: {result.stdout}"
    except subprocess.TimeoutExpired:
        return "Timeout (5 seconds limit)"
    except Exception as e:
        return f"Execution error: {e}"


code_analysis_tools = [explain_code, suggest_refactor, execute_code]
