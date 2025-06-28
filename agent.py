### agent.py
import os
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv
from io import StringIO
import sys

# Load environment variables
load_dotenv()

# Path to your SQLite file
DB_PATH = os.path.join("data", "pbp_db")  # fixed path
if not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"Database not found at: {DB_PATH}")

db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")

# Load schema context
SCHEMA_FILE = "schema_context.txt"
schema_context = ""
if os.path.exists(SCHEMA_FILE):
    with open(SCHEMA_FILE, "r") as f:
        schema_context = f.read()

# LLM setup
llm = ChatOpenAI(
    temperature=0,
    model="gpt-4o",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Create agent
agent_executor = create_sql_agent(
    llm=llm,
    toolkit=SQLDatabaseToolkit(db=db, llm=llm),
    verbose=True,
    handle_parsing_errors=True
)

_debug_output = ""

def run_query(question: str) -> str:
    global _debug_output
    try:
        full_prompt = f"""You are a helpful assistant that answers questions using a football stats database. 
Here is the schema for your reference:

{schema_context}

Now answer the user's question:
{question}
"""
        buffer = StringIO()
        sys.stdout = buffer
        result = agent_executor.run(full_prompt)
        sys.stdout = sys.__stdout__
        _debug_output = buffer.getvalue()
        return result
    except Exception as e:
        sys.stdout = sys.__stdout__
        return f"Error: {str(e)}"

def get_debug_logs():
    return _debug_output