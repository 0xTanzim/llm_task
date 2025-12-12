"""Chat service implementation."""

import uuid
from typing import AsyncGenerator, Optional

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables.config import RunnableConfig

from core.agent.agent import create_agent


class ChatService:
    """Service for handling chat interactions with the agent."""

    def __init__(self):
        self.agent = create_agent()

    def chat(self, message: str, thread_id: Optional[str] = None) -> dict:
        """Send a message and get a response.

        Args:
            message: User message
            thread_id: Optional conversation thread ID

        Returns:
            dict: Response and thread_id
        """
        if not thread_id:
            thread_id = str(uuid.uuid4())

        input_state: dict[str, list] = {"messages": [HumanMessage(content=message)]}
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}  # type: ignore

        result = self.agent.invoke(input_state, config)  # type: ignore

        last_message = result["messages"][-1]
        response = (
            last_message.content
            if isinstance(last_message, AIMessage)
            else str(last_message)
        )

        return {"response": response, "thread_id": thread_id}

    async def stream(
        self, message: str, thread_id: Optional[str] = None
    ) -> AsyncGenerator[dict, None]:
        """Stream agent responses token by token.

        Args:
            message: User message
            thread_id: Optional conversation thread ID

        Yields:
            dict: Streaming tokens and metadata
        """
        if not thread_id:
            thread_id = str(uuid.uuid4())

        input_state: dict[str, list] = {"messages": [HumanMessage(content=message)]}
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}  # type: ignore

        async for event in self.agent.astream_events(
            input_state,
            config,  # type: ignore
            version="v2",
        ):
            kind = event.get("event")

            if kind == "on_chat_model_stream":
                data = event.get("data", {})
                if isinstance(data, dict):
                    chunk = data.get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        yield {
                            "token": chunk.content,
                            "thread_id": thread_id,
                            "done": False,
                        }

        yield {"token": "", "thread_id": thread_id, "done": True}
