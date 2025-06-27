### agent.py
import os
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_executor import AgentExecutor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to SQLite DB
db = SQLDatabase.from_uri("sqlite:///pbp_db.sqlite")

# LLM setup
llm = ChatOpenAI(
    temperature=0,
    model="gpt-4o",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Create agent
agent_executor: AgentExecutor = create_sql_agent(
    llm=llm,
    toolkit=SQLDatabaseToolkit(db=db, llm=llm),
    verbose=True
)

def run_query(question: str) -> str:
    try:
        return agent_executor.run(question)
    except Exception as e:
        return f"Error: {str(e)}"