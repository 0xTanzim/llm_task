from typing import TypedDict, Any, List, Union, Annotated , Sequence
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from prompts import dynamic_template_selector
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage

from operator import add as add_messages




class AgentState(BaseModel):
    messages: Annotated[List[Sequence[BaseMessage]], add_messages]
    selected_model: Any
    selected_tools: List[Any]
    llm_calls: int = 0

