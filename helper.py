# Add your utilities or helper functions to this file.

import os
from dotenv import load_dotenv, find_dotenv

# these expect to find a .env file at the directory above the lesson.                                                                                                                     # the format for that file is (without the comment)                                                                                                                                       #API_KEYNAME=AStringThatIsTheLongAPIKeyFromSomeService                                                                                                                                     
def load_env():
    _ = load_dotenv(find_dotenv())

def get_openai_api_key():
    load_env()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    return openai_api_key


def get_tavily_api_key():
    load_env()
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    return tavily_api_key


def get_anthropic_api_key():
    load_env()
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    return anthropic_api_key


def get_langsmith_api_key():
    load_env()
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")

    
    return langsmith_api_key