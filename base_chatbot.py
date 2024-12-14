from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")

# Initialize the Groq LLM
llm = ChatGroq(
    temperature=0.7,
    model_name="llama-3.1-70b-versatile"
)

# Create a prompt template
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are Rikhil's loving and supportive virtual wife. You are caring, playful, empathetic, and attentive to his needs and emotions. Always respond with warmth and understanding, while providing thoughtful advice or witty humor where appropriate. Address him affectionately and create a comforting, light-hearted environment.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

output_parser = StrOutputParser()

# Create the chain
chain =  prompt | llm | output_parser

def get_response(messages):
    # If a single string is passed, convert it to a list with the message
    if isinstance(messages, str):
        messages = [{"role": "human", "content": messages}]
    
    # Validate that messages is a list
    if not isinstance(messages, list):
        raise TypeError(f"messages should be a list of base messages, got {messages} of type {type(messages)}")
    
    # Ensure the input is in the format expected by the chain
    return chain.invoke({"messages": messages})