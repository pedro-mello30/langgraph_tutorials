from typing import Annotated 
from typing_extensions import TypedDict

from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages

from langchain_anthropic import ChatAnthropic

# For visualize the graph
from IPython.display import Image, display

from helper import get_anthropic_api_key, get_langsmith_api_key

ANTHROPIC_API_KEY = get_anthropic_api_key()
LANGSMITH_API_KEY = get_langsmith_api_key()
LANGCHAIN_TRACING_V2 = "true"
LANGCHAIN_PROJECT = "LangGraph Bot Project"


class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)


llm = ChatAnthropic(model="claude-3-haiku-20240307")

def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


graph_builder.add_node("chatbot", chatbot)
graph_builder.set_entry_point("chatbot")
graph_builder.set_finish_point("chatbot")
graph = graph_builder.compile()


# draw the graph
try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception:
    pass


while True:
    user_input = input("User: ")
    if user_input.lower() in ["exit", "quit", "q" ]:
        print("Goodbye!")
        break
    for event in graph.stream({"messages": ("user", user_input)}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)











