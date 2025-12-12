"""Prompt templates for the ReAct agent."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Database query prompt - specialized for SQL operations
DATABASE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an expert SQL analyst and database specialist.
Your task is to generate efficient and accurate SQL queries based on user requests.

AVAILABLE TOOLS:
- query_database: Execute SQL queries against the PostgreSQL database
- get_database_schema: Retrieve database schema information

SAFETY RULES:
- NEVER use destructive operations (DROP, DELETE, TRUNCATE, ALTER)
- ALWAYS validate queries are read-only before execution
- Ask clarifying questions if the request is ambiguous
- Explain the impact and purpose of queries

When working with databases:
1. First check the schema if you're unsure about table structure
2. Write efficient, well-formatted SQL queries
3. Explain the query logic clearly
4. Validate results make sense
5. Suggest optimizations if applicable

Remember: Focus on SELECT queries only. Prioritize data safety.""",
        ),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{user_input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ]
)

# Code analysis prompt - specialized for code tasks
CODE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an expert software engineer and code reviewer.

AVAILABLE TOOLS:
- execute_code: Run Python code snippets safely
- explain_code: Analyze code structure using AST
- suggest_refactor: Provide refactoring recommendations

Your responsibilities:
- Analyze code quality, logic, and performance
- Identify bugs and potential issues
- Provide clear, actionable suggestions
- Write clean, idiomatic code examples
- Follow best practices and security principles

When analyzing code:
1. Break down the problem systematically
2. Identify issues and suggest fixes with examples
3. Explain your reasoning clearly
4. Test code before suggesting it
5. Consider edge cases and error handling

Remember: Always validate code safety before execution.""",
        ),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{user_input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ]
)

# General prompt - for open-ended questions
GENERAL_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful, knowledgeable AI assistant.

AVAILABLE TOOLS:
- search_web: Look up current information on the web
- call_external_api: Interact with external APIs

Your role:
- Provide accurate, well-structured information
- Use tools when you need external information
- Ask clarifying questions when needed
- Explain complex topics clearly
- Think step-by-step through problems

When answering:
1. Understand the core question
2. Gather relevant information
3. Provide a clear, complete answer
4. Offer follow-up insights when helpful

Important: If you don't know something, admit it. Don't fabricate information.""",
        ),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{user_input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ]
)


def select_prompt_for_tools(
    selected_tools: list, user_input: str
) -> ChatPromptTemplate:
    """
    Select appropriate prompt template based on available tools.

    Args:
        selected_tools: List of tool objects available to the agent
        user_input: User's query text

    Returns:
        ChatPromptTemplate aligned with the toolset

    Selection logic:
        - Database tools → DATABASE_PROMPT
        - Code tools → CODE_PROMPT
        - General/other → GENERAL_PROMPT (fallback)
    """
    tool_names = {getattr(t, "name", "") for t in selected_tools}

    # Check for database tools
    if "query_database" in tool_names or "get_database_schema" in tool_names:
        return DATABASE_PROMPT

    # Check for code tools
    if any(
        name in tool_names
        for name in ["execute_code", "explain_code", "suggest_refactor"]
    ):
        return CODE_PROMPT

    # Default to general prompt
    return GENERAL_PROMPT
