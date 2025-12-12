"""Chat service for handling LangGraph agent interactions."""

import uuid
from typing import Any, AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage

from core.agent.graph import create_graph
from core.checkpointer import create_thread_config, get_async_checkpointer


class ChatService:
    """Service for managing chat interactions with the LangGraph agent."""

    def __init__(self):
        """Initialize the chat service."""
        self._graph = None
        self._checkpointer = None

    async def _get_graph(self):
        """Get or create the compiled graph with checkpointer."""
        async with get_async_checkpointer() as checkpointer:
            graph = create_graph(checkpointer=checkpointer)
            return graph

    def _generate_thread_id(self) -> str:
        """Generate a unique thread ID for new conversations."""
        return f"thread_{uuid.uuid4().hex[:16]}"

    async def chat(self, message: str, thread_id: str | None = None) -> dict[str, Any]:
        """
        Send a message to the agent and get a response.

        Args:
            message: User message
            thread_id: Optional conversation thread ID

        Returns:
            Dict with response, thread_id, llm_calls, and tools_used
        """
        try:
            is_new_conversation = thread_id is None
            if is_new_conversation:
                thread_id = self._generate_thread_id()

            config = create_thread_config(thread_id)

            async with get_async_checkpointer() as checkpointer:
                graph = create_graph(checkpointer=checkpointer)

                input_state = {
                    "messages": [HumanMessage(content=message)],
                }

                result = await graph.ainvoke(input_state, config)
        except Exception as e:
            import traceback

            print(f"❌ Chat error: {e}")
            traceback.print_exc()
            raise

        final_response = "No response generated."
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
                final_response = msg.content
                break

        tools_used = []
        for msg in result["messages"]:
            if hasattr(msg, "name") and msg.name:
                tools_used.append(msg.name)

        selected_model = result.get("selected_model", "unknown")
        model_display_name = {
            "default": "Gemini 2.5 Flash Lite",
            "openai": "GPT-4o",
            "anthropic": "Claude Sonnet",
        }.get(selected_model, selected_model)

        return {
            "response": final_response,
            "thread_id": thread_id,
            "model_used": model_display_name,
            "llm_calls": result.get("llm_calls", 0),
            "tools_used": list(set(tools_used)) if tools_used else [],
        }

    async def stream(
        self, message: str, thread_id: str | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream agent responses in real-time with optimized performance.

        Optimizations:
        - Minimal per-chunk overhead
        - Truncate long tool outputs to reduce bandwidth
        - Skip empty/redundant events

        Args:
            message: User message
            thread_id: Optional conversation thread ID

        Yields:
            Dict chunks with type, content, and metadata
        """
        is_new_conversation = thread_id is None
        if is_new_conversation:
            thread_id = self._generate_thread_id()

        config = create_thread_config(thread_id)

        yield {
            "type": "thread_id",
            "thread_id": thread_id,
            "done": False,
        }

        llm_calls = 0
        try:
            async with get_async_checkpointer() as checkpointer:
                graph = create_graph(checkpointer=checkpointer)

                input_state = {
                    "messages": [HumanMessage(content=message)],
                }

                async for event in graph.astream(
                    input_state, config, stream_mode="values"
                ):
                    messages = event.get("messages", [])
                    llm_calls = event.get("llm_calls", 0)

                    if not messages:
                        continue

                    last_message = messages[-1]

                    # Handle AI messages
                    if isinstance(last_message, AIMessage):
                        # Check for tool calls
                        if (
                            hasattr(last_message, "tool_calls")
                            and last_message.tool_calls
                        ):
                            for tool_call in last_message.tool_calls:
                                yield {
                                    "type": "tool_call",
                                    "tool_name": tool_call.get("name"),
                                    "tool_args": tool_call.get("args"),
                                    "done": False,
                                }
                        # AI response content (skip empty chunks for performance)
                        elif last_message.content and last_message.content.strip():
                            yield {
                                "type": "response",
                                "content": last_message.content,
                                "done": False,
                            }

                    # Handle tool results (truncate long outputs)
                    elif hasattr(last_message, "name") and last_message.name:
                        content = str(last_message.content)
                        # Truncate to 300 chars for better streaming performance
                        truncated_content = (
                            content[:300] + "..." if len(content) > 300 else content
                        )
                        yield {
                            "type": "tool_result",
                            "tool_name": last_message.name,
                            "content": truncated_content,
                            "done": False,
                        }

                # Final message
                yield {
                    "type": "complete",
                    "thread_id": thread_id,
                    "llm_calls": llm_calls,
                    "done": True,
                }

        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "done": True,
            }

    async def get_history(self, thread_id: str) -> list[dict[str, Any]]:
        """
        Get conversation history for a thread.

        Args:
            thread_id: Conversation thread ID

        Returns:
            List of message dictionaries
        """
        config = create_thread_config(thread_id)

        try:
            async with get_async_checkpointer() as checkpointer:
                graph = create_graph(checkpointer=checkpointer)
                state = await graph.aget_state(config)

                messages = []
                for msg in state.values.get("messages", []):
                    if isinstance(msg, (HumanMessage, AIMessage)):
                        messages.append(
                            {
                                "role": "user"
                                if isinstance(msg, HumanMessage)
                                else "assistant",
                                "content": msg.content,
                            }
                        )

                return messages
        except Exception:
            return []

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup checkpointer."""
        # PostgresSaver manages its own connection cleanup
        pass
