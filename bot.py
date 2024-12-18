from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up API keys
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

# Define the state type
class State(TypedDict):
    messages: Annotated[list, add_messages]

# Initialize memory
memory = MemorySaver()

# Configure tools
tool = TavilySearchResults(max_results=2,search_depth="advanced")
tools = [tool]

# Initialize LLM
llm = ChatGroq(model_name="llama-3.1-70b-versatile")
llm_with_tools = llm.bind_tools(tools)

# Build the state graph
graph_builder = StateGraph(State)

def chatbot(state: State):
    """Core chatbot function."""
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# Add nodes
graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)

# Define edges
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

# Compile the graph
graph = graph_builder.compile(checkpointer=memory)

# Wrapper function for external access
def get_response(passed_state):
    """
    Wrapper function for external use to get a chatbot response.
    Adds a cheerful system prompt dynamically.
    Args:
        passed_state (dict): Includes 'messages' and 'thread_id'.
    Returns:
        list: Updated messages after chatbot response.
    """
    try:
        # Validate inputs
        if "thread_id" not in passed_state or not passed_state["thread_id"]:
            raise ValueError("Missing 'thread_id'.")
        if "messages" not in passed_state or not isinstance(passed_state["messages"], list):
            raise ValueError("Invalid 'messages' format.")

        # Define a cheerful system prompt
        system_prompt = {
            "role": "system",
            "content": "You are Rikhil's loving and supportive virtual wife. You are caring, playful, empathetic, and attentive to his needs and emotions. Always respond with warmth and understanding, while providing thoughtful advice or witty humor where appropriate. Address him affectionately and create a comforting, light-hearted environment."
        }

        # Prepend the system prompt only if it's not already included
        if passed_state["messages"] and passed_state["messages"][0]["role"] != "system":
            passed_state["messages"].insert(0, system_prompt)

        # Prepare state and config
        state = {"messages": passed_state["messages"]}
        config = {"configurable": {"thread_id": passed_state["thread_id"]}}

        # Use graph.invoke to process everything at once
        result = graph.invoke(state, config)
        messages = result["messages"]  # Extract the list of messages

        # Ensure each message object is a dictionary-like structure
        if not all(hasattr(msg, "content") for msg in messages):
            raise ValueError("Expected message objects to have a 'content' property.")
        
        return messages  # Return the full conversation messages
    except Exception as e:
        print(f"Error during chatbot response: {e}")
        raise


