import os
import sqlite3
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# LangChain imports (unchanged logic)
from langchain.agents import initialize_agent, Tool, AgentType
from langchain_openai import ChatOpenAI

# --- PDF (RAG) pieces
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import SystemMessagePromptTemplate

# --- SQL pieces
from langchain_community.utilities import SQLDatabase
from langchain.agents.agent_toolkits import create_sql_agent

# ------------------------------------------------------------------------------------
# Config (unchanged)
# ------------------------------------------------------------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Get the directory where main.py is located
BASE_DIR = Path(__file__).parent.absolute()

# Use absolute paths for data files
DB_PATH = BASE_DIR / "data" / "healthcare.db"
FAISS_PATH = BASE_DIR / "data" / "faiss_index_notice_privacy"  # folder containing index.faiss + index.pkl
MODEL_PATH = BASE_DIR / "models" / "all-MiniLM-L6-v2"  # Local vendored model

# ------------------------------------------------------------------------------------
# Database setup functions
# ------------------------------------------------------------------------------------
def create_database():
    """Create the SQLite database from CSV files"""
    print(f"Creating database at: {DB_PATH}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Ensure data directory exists
    data_dir = BASE_DIR / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Create database connection
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Read CSV files
        csv_dir = BASE_DIR / "csv"
        print(f"Reading CSV files from: {csv_dir}")
        
        # Check if CSV files exist
        csv_files = {
            'patients': csv_dir / 'patients.csv',
            'visits': csv_dir / 'visits.csv',
            'prescriptions': csv_dir / 'prescriptions.csv',
            'medications': csv_dir / 'medications.csv'
        }
        
        for table_name, csv_file in csv_files.items():
            if csv_file.exists():
                print(f"Processing {table_name} from {csv_file}")
                df = pd.read_csv(csv_file)
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                print(f"✅ Created table {table_name} with {len(df)} rows")
            else:
                print(f"⚠️  CSV file not found: {csv_file}")
        
        # Verify tables were created
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✅ Database tables: {[table[0] for table in tables]}")
        
        # Check table contents
        for table_name in ['patients', 'visits', 'prescriptions', 'medications']:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"📊 Table {table_name}: {count} rows")
        
        conn.commit()
        print("✅ Database created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        raise
    finally:
        conn.close()

def verify_database():
    """Verify database exists and has correct schema"""
    print(f"Verifying database at: {DB_PATH}")
    
    if not DB_PATH.exists():
        print(f"❌ Database file not found: {DB_PATH}")
        return False
    
    file_size = DB_PATH.stat().st_size
    print(f"📁 Database file size: {file_size} bytes")
    
    if file_size == 0:
        print("❌ Database file is empty")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        print(f"📋 Available tables: {table_names}")
        
        required_tables = ['patients', 'visits', 'prescriptions', 'medications']
        missing_tables = [table for table in required_tables if table not in table_names]
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        # Check table contents
        for table in required_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"📊 Table {table}: {count} rows")
            
            if count == 0:
                print(f"⚠️  Table {table} is empty")
        
        conn.close()
        print("✅ Database verification successful!")
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

# ------------------------------------------------------------------------------------
# App init
# ------------------------------------------------------------------------------------
app = FastAPI(title="Unified Multi-Source Agent (PDF + SQL)")

# Static + Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Globals initialized on startup
agent = None  # router agent

# ------------------------------------------------------------------------------------
# Startup: build EXACT SAME agent/tools as your CLI script (logic unchanged)
# ------------------------------------------------------------------------------------
@app.on_event("startup")
def build_agent_on_startup():
    global agent
    
    print("🚀 Starting application setup...")
    print(f"📍 Base directory: {BASE_DIR}")
    print(f"📍 Current working directory: {os.getcwd()}")
    
    # Check if OpenAI API key is set
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
        print("ERROR: OPENAI_API_KEY not set. Please set your OpenAI API key in the environment variables.")
        print("You can get an API key from: https://platform.openai.com/api-keys")
        return
    
    try:
        # Database setup and verification
        print("🔍 Checking database...")
        if not verify_database():
            print("🔄 Creating database from CSV files...")
            create_database()
            if not verify_database():
                print("❌ Failed to create/verify database")
                return
        
        # 1) Shared LLM
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

        # 2) PDF Tool (RAG over FAISS)
        print("Loading FAISS index and embeddings...")
        # Use local model for offline operation
        embedding = HuggingFaceEmbeddings(
            model_name=str(MODEL_PATH),
            model_kwargs={'device': 'cpu'}
        )
        vectorstore = FAISS.load_local(
            FAISS_PATH,
            embeddings=embedding,
            allow_dangerous_deserialization=True,  # needed to load index.pkl
        )
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})

        pdf_qa = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            return_source_documents=True,   # show which PDF & page
            chain_type="stuff",
        )

        def run_pdf_tool(question: str) -> str:
            result = pdf_qa.invoke({"query": question})
            sources = result.get("source_documents", [])
            if sources:
                unique_srcs = []
                for doc in sources:
                    src = f"{doc.metadata.get('source','PDF')} (p.{doc.metadata.get('page','?')})"
                    if src not in unique_srcs:
                        unique_srcs.append(src)
                src_line = ", ".join(unique_srcs[:5])
            else:
                src_line = "PDF index (no page metadata)"

            return (
                f"Source: PDF • Files: {src_line}\n"
                f"Tool Used: PDF_RetrievalQA\n"
                f"Answer: {result['result']}"
            )

        pdf_tool = Tool(
            name="PDF_RetrievalQA",
            func=run_pdf_tool,
            description=(
                "Use for questions about content in the PDFs (privacy policy, patient rights, website policy, "
                "pharmacy coverage, user guide, etc.). INPUT MUST BE THE ORIGINAL NATURAL-LANGUAGE QUESTION."
            ),
        )

        # 3) SQL Tool (Healthcare DB) — robust wrapper
        print(f"🔗 Connecting to database: {DB_PATH}")
        db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")

        # ---- capture generated SQL by monkey-patching db.run (minimal, local)
        sql_queries = []  # will hold last executed SQL

        _orig_db_run = db.run  # keep original

        def _capturing_run(query: str, *args, **kwargs):
            sql_queries.append(query)
            return _orig_db_run(query, *args, **kwargs)

        db.run = _capturing_run  # patch

        sql_agent = create_sql_agent(
            llm=llm,
            db=db,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            verbose=False,
            prefix="""
You are a helpful medical data assistant.

Database schema:
- patients(patient_id PK, name, age, gender)
- visits(visit_id PK, patient_id FK->patients.patient_id, date, reason)
- prescriptions(id PK, visit_id FK->visits.visit_id, med_id FK->medications.med_id, dosage)
- medications(med_id PK, name, category)

Rules:
- Conditions (e.g., 'hypertension', 'chest pain') live in visits.reason (string match; use LOWER() when needed).
- For patient 'summary', join patients -> visits -> prescriptions -> medications and order by date.
- Prefer DISTINCT to avoid duplicates where it makes sense.
- Return concise, faithful results. Do not invent data.

When summarizing, output a short clinical-style paragraph (no bullets).
"""
        )

        SQL_PREFIX_FORCED = """You MUST accept a NATURAL LANGUAGE question and generate SQL yourself.
Do NOT expect the input to be SQL. If the input looks like SQL anyway, execute it directly and then summarize the results."""

        def run_sql_tool(question: str) -> str:
            q = question.strip()
            looks_like_sql = q.lower().startswith(
                ("select", "with", "pragma", "explain", "insert", "update", "delete")
            )
            try:
                if looks_like_sql:
                    rows = db.run(q)  # executes SQL directly (also captured)
                    return (
                        "Source: Database (SQLite: healthcare.db)\n"
                        "Tool Used: SQL_Agent (direct SQL execution)\n"
                        f"SQL: {q}\n"
                        f"Answer: {rows}"
                    )
                # clear previous captured SQLs for a clean grab
                sql_queries.clear()
                answer = sql_agent.run(SQL_PREFIX_FORCED + "\n\nUser question:\n" + q)
                generated_sql = sql_queries[-1] if sql_queries else "N/A"
                return (
                    "Source: Database (SQLite: healthcare.db)\n"
                    "Tool Used: SQL_Agent\n"
                    f"SQL: {generated_sql}\n"
                    f"Answer: {answer}"
                )
            except Exception as e:
                return (
                    "Source: Database (SQLite: healthcare.db)\n"
                    "Tool Used: SQL_Agent\n"
                    f"Answer: Error while querying database: {e}"
                )

        sql_tool = Tool(
            name="SQL_Agent",
            func=run_sql_tool,
            description=(
                "Use for questions about patients, visits, prescriptions, medications, counts or summaries in the SQLite database. "
                "INPUT MUST BE THE ORIGINAL NATURAL-LANGUAGE QUESTION. Do NOT pass SQL; the tool will generate SQL."
            ),
        )

        # 4) Router Agent — strict routing instructions
        tools = [pdf_tool, sql_tool]

        ROUTER_SYSTEM_PROMPT = """You are a routing assistant that decides which tool to use.

TOOLS
- PDF_RetrievalQA: For policy/rights/privacy/coverage/website policy/user guide content that lives in PDFs.
- SQL_Agent: For patients/visits/medications/prescriptions/summaries/counts/demographics in the SQLite database.

CRITICAL:
- ALWAYS pass the user's ORIGINAL NATURAL-LANGUAGE question to the chosen tool.
- NEVER translate the question into SQL yourself.
- NEVER pass SQL text as tool input. The SQL_Agent generates (or executes) SQL internally if needed.

OUTPUT:
Return the chosen tool's raw output only. It already includes:
- Source: <PDF or Database>
- Tool Used: <name>
- Answer: <final answer>
"""

        router_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        agent_local = initialize_agent(
            tools=tools,
            llm=router_llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
            agent_kwargs={
                "extra_prompt_messages": [
                    SystemMessagePromptTemplate.from_template(ROUTER_SYSTEM_PROMPT)
                ]
            },
            return_intermediate_steps=True,  # <-- ensure we can read tool observations
        )

        agent = agent_local  # set global
        print("✅ Agent initialization completed successfully!")
        
    except Exception as e:
        print(f"ERROR: Failed to initialize agent: {e}")
        print("Please check your OpenAI API key and ensure all dependencies are installed.")
        agent = None


# ------------------------------------------------------------------------------------
# Pydantic model for chat request
# ------------------------------------------------------------------------------------
class ChatRequest(BaseModel):
    query: str


# ------------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------------
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chatbot")
def chatbot(request: Request):
    return templates.TemplateResponse("chatbot.html", {"request": request})

@app.get("/about")
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.post("/chat")
def chat(req: ChatRequest):
    print(f"Received chat request: {req.query}")
    if agent is None:
        print("Agent not ready")
        raise HTTPException(status_code=503, detail="Agent not ready yet.")
    try:
        # invoke to get intermediate steps (tool observation)
        res = agent.invoke({"input": req.query})
        print(f"Agent response: {res}")

        steps = res.get("intermediate_steps", [])
        if steps:
            last_action, last_observation = steps[-1]  # (AgentAction, observation)
            
            # Parse the observation to extract clean answer and tool details
            clean_answer = ""
            tool_details = ""
            
            if last_action.tool == "SQL_Agent":
                # Extract clean answer (after "Answer: ")
                if "Answer:" in last_observation:
                    clean_answer = last_observation.split("Answer:")[-1].strip()
                else:
                    clean_answer = last_observation
                
                # Extract SQL query (between "SQL: " and "Answer: ")
                if "SQL:" in last_observation and "Answer:" in last_observation:
                    sql_start = last_observation.find("SQL:") + 4
                    sql_end = last_observation.find("Answer:")
                    tool_details = last_observation[sql_start:sql_end].strip()
                elif "SQL:" in last_observation:
                    sql_start = last_observation.find("SQL:") + 4
                    tool_details = last_observation[sql_start:].strip()
                    
            elif last_action.tool == "PDF_RetrievalQA":
                # Extract clean answer (after "Answer: ")
                if "Answer:" in last_observation:
                    clean_answer = last_observation.split("Answer:")[-1].strip()
                else:
                    clean_answer = last_observation
                
                # Extract PDF files and pages (between "Files: " and "Tool Used: ")
                if "Files:" in last_observation and "Tool Used:" in last_observation:
                    files_start = last_observation.find("Files:") + 6
                    files_end = last_observation.find("Tool Used:")
                    tool_details = last_observation[files_start:files_end].strip()
                elif "Files:" in last_observation:
                    files_start = last_observation.find("Files:") + 6
                    tool_details = last_observation[files_start:].strip()
            
            else:
                # Fallback for other tools
                clean_answer = last_observation
                tool_details = "No additional details available"
            
            response_data = {
                "clean_answer": clean_answer,
                "tool": last_action.tool,
                "tool_details": tool_details,
                "raw_output": res.get("output", ""),
            }
            print(f"Returning response: {response_data}")
            return JSONResponse(response_data)

        # Fallback to final output if no tools were used
        fallback_response = {
            "clean_answer": res.get("output", "(no output)"),
            "tool": "None",
            "tool_details": "No tool used",
            "raw_output": res.get("output", "")
        }
        print(f"Returning fallback response: {fallback_response}")
        return JSONResponse(fallback_response)

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    """Enhanced health check with database information"""
    health_info = {
        "status": "healthy",
        "message": "Application is running",
        "timestamp": str(pd.Timestamp.now()),
        "base_dir": str(BASE_DIR),
        "working_dir": os.getcwd(),
        "database": {
            "path": str(DB_PATH),
            "exists": DB_PATH.exists(),
            "size_bytes": DB_PATH.stat().st_size if DB_PATH.exists() else 0
        },
        "agent_ready": agent is not None
    }
    
    # Add database schema information if database exists
    if DB_PATH.exists() and DB_PATH.stat().st_size > 0:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            health_info["database"]["tables"] = table_names
            
            # Get row counts for each table
            table_counts = {}
            for table in table_names:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_counts[table] = count
            
            health_info["database"]["table_counts"] = table_counts
            conn.close()
            
        except Exception as e:
            health_info["database"]["error"] = str(e)
    
    if agent is None:
        health_info["status"] = "degraded"
        health_info["message"] = "Application is running but agent is not initialized"
    
    return health_info

@app.get("/debug/database")
def debug_database():
    """Debug endpoint to check database status and recreate if needed"""
    debug_info = {
        "timestamp": str(pd.Timestamp.now()),
        "base_dir": str(BASE_DIR),
        "working_dir": os.getcwd(),
        "csv_files": {},
        "database_status": {}
    }
    
    # Check CSV files
    csv_dir = BASE_DIR / "csv"
    csv_files = {
        'patients': csv_dir / 'patients.csv',
        'visits': csv_dir / 'visits.csv',
        'prescriptions': csv_dir / 'prescriptions.csv',
        'medications': csv_dir / 'medications.csv'
    }
    
    for table_name, csv_file in csv_files.items():
        debug_info["csv_files"][table_name] = {
            "exists": csv_file.exists(),
            "size_bytes": csv_file.stat().st_size if csv_file.exists() else 0
        }
    
    # Check database
    debug_info["database_status"] = {
        "path": str(DB_PATH),
        "exists": DB_PATH.exists(),
        "size_bytes": DB_PATH.stat().st_size if DB_PATH.exists() else 0
    }
    
    if DB_PATH.exists() and DB_PATH.stat().st_size > 0:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            debug_info["database_status"]["tables"] = table_names
            
            # Check table contents
            table_counts = {}
            for table in table_names:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_counts[table] = count
            
            debug_info["database_status"]["table_counts"] = table_counts
            conn.close()
            
        except Exception as e:
            debug_info["database_status"]["error"] = str(e)
    
    return debug_info

@app.post("/debug/recreate-database")
def recreate_database():
    """Force recreate the database from CSV files"""
    try:
        create_database()
        if verify_database():
            return {"status": "success", "message": "Database recreated successfully"}
        else:
            return {"status": "error", "message": "Database recreation failed verification"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to recreate database: {str(e)}"}
