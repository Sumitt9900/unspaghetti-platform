# main.py (Final Version: CORS Enabled)

import os
import shutil
import git
import stat
import io
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware # <--- NEW IMPORT

# AI Libraries
from langchain_community.vectorstores import SKLearnVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

app = FastAPI(title="Unspaghetti Platform", version="3.0")

# --- NEW: ENABLE CORS (Allow React to talk to Python) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (POST, GET, etc.)
    allow_headers=["*"],
)

# --- CONFIGURATION ---
CLONE_DIR = "temp_clones"
OPENAI_API_KEY = None # Paste key here if you have one: "sk-..."
if OPENAI_API_KEY: os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

def remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def load_and_split_code(repo_path):
    docs = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        docs.append(Document(page_content=f.read(), metadata={"source": rel_path}))
                except: continue
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    return splitter.split_documents(docs)

# --- ROUTES ---
@app.get("/")
def read_root(): return {"message": "Unspaghetti Platform Ready"}

@app.post("/analyze-repo")
def analyze_repo(repo_url: str):
    if os.path.exists(CLONE_DIR):
        shutil.rmtree(CLONE_DIR, onerror=remove_readonly)
    try:
        if not os.path.exists(CLONE_DIR): os.makedirs(CLONE_DIR)
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        local_path = os.path.join(CLONE_DIR, repo_name)
        git.Repo.clone_from(repo_url, local_path)
        chunks = load_and_split_code(local_path)
        return {"status": "Success", "repo": repo_name, "chunks": len(chunks), "mode": "Active" if OPENAI_API_KEY else "Mock"}
    except Exception as e: raise HTTPException(500, str(e))

@app.post("/ask-question")
def ask_question(question: str):
    if not OPENAI_API_KEY:
        return {"answer": "MOCK ANSWER: I see you are asking about '" + question + "'. (Add API Key for real AI)", "sources": ["mock_file.py"]}
    try:
        repo_name = os.listdir(CLONE_DIR)[0]
        chunks = load_and_split_code(os.path.join(CLONE_DIR, repo_name))
        vector_store = SKLearnVectorStore.from_documents(chunks, OpenAIEmbeddings())
        docs = vector_store.similarity_search(question, k=3)
        context = "\n".join([d.page_content for d in docs])
        llm = ChatOpenAI(model="gpt-4", temperature=0)
        return {"answer": llm.invoke(f"Context:\n{context}\n\nQuestion: {question}").content, "sources": [d.metadata['source'] for d in docs]}
    except Exception as e: return {"error": str(e)}

@app.post("/analyze-data")
async def analyze_data(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))
    return {"filename": file.filename, "missing": int(df.isnull().sum().sum()), "status": "Spaghetti" if df.isnull().sum().sum() > 0 else "Clean"}

@app.post("/unspaghetti-it")
async def unspaghetti_it(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))
    stream = io.StringIO()
    df.fillna(0).to_csv(stream, index=False)
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=clean_data.csv"
    return response