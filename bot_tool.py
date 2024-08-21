import json # Tool Node

from langchain_community.tools.tavily_search import TavilySearchResults


from typing import Annotated

from typing_extensions import TypedDict
from langchain_anthropic import ChatAnthropic

from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages


from langchain_core.messages import ToolMessage # Tool Node

from typing import Literal # Route tools

from IPython.display import Image, display # For visualize the graph

from langchain_core.messages import BaseMessage # 

from helper import get_tavily_api_key, get_anthropic_api_key

TAVILY_API_KEY = get_tavily_api_key()
ANTHROPIC_API_KEY = get_anthropic_api_key()



tool = TavilySearchResults(max_results=2)
tools = [tool]
# tool.invoke("What is the capital of France?")


# State Graph
class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

llm_with_tools = ChatAnthropic(model="claude-3-haiku-20240307")

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)


# Tool Node // This can be reply by ToolNode
class BasicToolNode:
    """A node that runs the tools requested in the last AIMessage."""
    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No messages in inputs")
        
        outputs = []
        for tool_call in message.tools_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(tool_call["args"])
            
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        
        return {"messages": outputs}


tool_node = BasicToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)


# Route tools // This can be reply by tool_condition
def route_tools(
    state: State
) -> Literal["tools", "__end__"]:
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")

    if hasattr(ai_message, "tools_calls") and len(ai_message.tool_calls) > 0:
        return "tools"

    return "__end__"

# The `tools_condition` function returns "tools" if the chatbot asks to use a tool, and "__end__" if
# it is fine directly responding. This conditional routing defines the main agent loop.
graph_builder.add_conditional_edges(
    "chatbot",
    route_tools,
    # The following dictionary lets you tell the graph to interpret the condition's outputs as a specific node
    # It defaults to the identity function, but if you
    # want to use a node named something else apart from "tools",
    # You can update the value of the dictionary to something else
    # e.g., "tools": "my_tools"
    {"tools": "tools", "__end__": "__end__"}
)

# Any time a tool is called, we return to the chatbot to decide the next step
graph_builder.add_edge("tools", "chatbot")
graph_builder.set_entry_point("chatbot")
graph = graph_builder.compile()


try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception:
    # This requires some extra dependencies and is optional
    pass


while True:
    user_input = input("User: ")
    if user_input.lower() in ["exit", "quit", "q"]:
        print("Goodbye!")
        break
    for event in graph.stream({"messages": ["user", user_input]}):
        for value in event.values():
            if isinstance(value["messages"][-1], BaseMessage):
                print("Assistant:", value["messages"][-1].content)