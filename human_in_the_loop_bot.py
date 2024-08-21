from typing import Annotated

from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from helper import get_tavily_api_key, get_anthropic_api_key

ANTHROPIC_API_KEY = get_anthropic_api_key()
TAVILY_API_KEY = get_tavily_api_key()

memory = SqliteSaver.from_conn_string(":memory:")


class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

tool = TavilySearchResults(max_results=2)
tools = [tool]

llm = ChatAnthropic(model="claude-3-haiku-20240307")
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.set_entry_point("chatbot")

graph = graph_builder.compile(
    checkpointer=memory,
    interrupt_before=["tools"]
)


user_input = "I'm learning LangGraph. Could you do some research on it for me."
config = {"configurable": {"thread_id": "1"}}

events = graph.stream(
    {"messages": ("user", user_input)},
    config=config,
    stream_mode="values"
)
for event in events:
    if "messages" in event:
        event["messages"][-1].pretty_print()


snapshot = graph.get_state(config)
print(snapshot.next)

existing_messages = snapshot.values["messages"][-1]
print(existing_messages.tool_calls)

# `None` will append nothing new to the current state, letting it resume as if it had never been interrupted
events = graph.stream(None, config=config, stream_mode="values")
for event in events:
    if "messages" in event:
        event["messages"][-1].pretty_print()