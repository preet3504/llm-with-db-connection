import streamlit as st
from pathlib import Path
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_classic.agents import AgentType
from sqlalchemy import create_engine
from langchain_groq import ChatGroq
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()


st.title("Chat with SQL Database using Groq")

LOCALDB='USE_LOCAL_DB'
MYSQLDB='USE_MYSQL_DB'

radio_option = st.sidebar.radio("Select Database Type", (LOCALDB, MYSQLDB))

if radio_option == MYSQLDB:
    db_uri=MYSQLDB
    host = st.sidebar.text_input("MySQL Host", "localhost")
    port = st.sidebar.text_input("MySQL Port", "3306")
    username = st.sidebar.text_input("MySQL Username", "root")
    password = st.sidebar.text_input("MySQL Password", "password", type="password")
    database = st.sidebar.text_input("MySQL Database Name", "testdb")
else:
    db_uri=LOCALDB


API_KEY = os.getenv("GROQ_API_KEY")

model = ChatGroq(model='llama-3.3-70b-versatile', groq_api_key=API_KEY, streaming=True)

@st.cache_resource(ttl=7200)
def configure_db(db_uri, db_host=None, db_port=None, db_username=None, db_password=None, db_name=None):
    try:
        if db_uri == MYSQLDB:
            connection_string = f'mysql+pymysql://{db_username}:{quote_plus(db_password)}@{db_host}:{db_port}/{db_name}'
            engine = create_engine(connection_string)
        else:
            db_path = (Path(__file__).parent / "user.db").absolute()
            creator = lambda: sqlite3.connect(f"file:{db_path}?mode=rw", uri=True)
            engine = create_engine('sqlite://', creator=creator)
        return engine
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        st.stop()
        return None


# Connect to database and display success message
if radio_option == MYSQLDB:
    if not all([host, port, username, password, database]):
        st.error("Please fill in all MySQL connection details")
        st.stop()
    db_engine = configure_db(db_uri, db_host=host, db_port=port, db_username=username, db_password=password, db_name=database)
else:
    db_engine = configure_db(db_uri)

if db_engine is not None:
    st.success("✅ Database connected successfully!")
    # Convert engine to SQLDatabase instance
    db = SQLDatabase(engine=db_engine)
    SqlToolkit = SQLDatabaseToolkit(db=db, llm=model)
else:
    st.error("Failed to initialize database toolkit")
    st.stop()

agent = create_sql_agent(
    llm=model,
    toolkit=SqlToolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION
    )

if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "Assistant",
        "content": "Hello! How can I assist you with the database today?"
    }]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])


user_input = st.chat_input("Ask a question about the database...")

if user_input:
    st.session_state.messages.append({"role": "User", "content": user_input})
    st.chat_message("User").write(user_input)

    with st.chat_message("Assistant"):
        streamlit_callback = StreamlitCallbackHandler(st.container())
        response = agent.run(user_input, callbacks=[streamlit_callback])
        st.session_state.messages.append({"role": "Assistant", "content": response})
        st.write(response)
