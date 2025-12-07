# main.py (Free Version with Google Gemini)

import os
import shutil
import git
import stat
import io
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# --- SWAP: Use Google Gemini instead of OpenAI ---
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import SKLearnVectorStore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

app = FastAPI(title="Unspaghetti Platform", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CLONE_DIR = "temp_clones"

# 1. SETUP GOOGLE KEY
# Paste your AIza... key here OR set it in Render Environment Variables
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", None)

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

@app.get("/")
def read_root(): return {"message": "Unspaghetti Platform (Gemini Edition)"}

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
        return {"status": "Success", "repo": repo_name, "chunks": len(chunks), "mode": "Active" if GOOGLE_API_KEY else "Mock"}
    except Exception as e: raise HTTPException(500, str(e))

@app.post("/ask-question")
def ask_question(question: str):
    if not GOOGLE_API_KEY:
        return {"answer": "MOCK MODE: Please add GOOGLE_API_KEY to use the free AI.", "sources": []}
    try:
        repo_name = os.listdir(CLONE_DIR)[0]
        chunks = load_and_split_code(os.path.join(CLONE_DIR, repo_name))
        
        # 2. Use Google Embeddings (Free)
        vector_store = SKLearnVectorStore.from_documents(
            documents=chunks, 
            embedding=GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        )
        
        docs = vector_store.similarity_search(question, k=3)
        context = "\n".join([d.page_content for d in docs])
        
        # 3. Use Google Gemini Pro (Free)
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
        
        response = llm.invoke(f"Context:\n{context}\n\nQuestion: {question}")
        return {"answer": response.content, "sources": [d.metadata['source'] for d in docs]}
    except Exception as e: return {"error": str(e)}

# ... (Keep analyze-data and unspaghetti-it routes exactly the same) ...
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