// frontend/src/App.jsx

import { useState } from 'react'
import axios from 'axios'
import logo from './assets/logo.jpg' // Importing your new logo
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('data') 

  // --- DATA STATE ---
  const [file, setFile] = useState(null)
  const [dataReport, setDataReport] = useState(null)
  const [loadingData, setLoadingData] = useState(false)

  // --- CODE STATE ---
  const [repoUrl, setRepoUrl] = useState('')
  const [repoStatus, setRepoStatus] = useState(null)
  const [question, setQuestion] = useState('')
  const [chatAnswer, setChatAnswer] = useState(null)
  const [loadingCode, setLoadingCode] = useState(false)

  // --- HANDLERS ---
  const handleFileChange = (e) => setFile(e.target.files[0])

  const analyzeData = async () => {
    if(!file) return alert("Please select a file first!")
    setLoadingData(true)
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await axios.post('http://127.0.0.1:8000/analyze-data', formData)
      setDataReport(res.data)
    } catch (err) { alert("Error connecting to backend") }
    setLoadingData(false)
  }

  const downloadCleanData = async () => {
    if(!file) return alert("Please select a file!")
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await axios.post('http://127.0.0.1:8000/unspaghetti-it', formData, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'clean_data.csv')
      document.body.appendChild(link)
      link.click()
    } catch (err) { alert("Error downloading file") }
  }

  const analyzeRepo = async () => {
    setLoadingCode(true)
    try {
      const res = await axios.post(`http://127.0.0.1:8000/analyze-repo?repo_url=${repoUrl}`)
      setRepoStatus(res.data)
    } catch (err) { alert("Failed to clone. Is the URL public?") }
    setLoadingCode(false)
  }

  const askQuestion = async () => {
    if(!question) return
    setLoadingCode(true)
    try {
      const res = await axios.post(`http://127.0.0.1:8000/ask-question?question=${question}`)
      setChatAnswer(res.data)
    } catch (err) { alert("Error asking question") }
    setLoadingCode(false)
  }

  return (
    <div className="app-container">
      
      {/* HEADER SECTION */}
      <header className="main-header">
        <div className="logo-wrapper">
          <img src={logo} className="brand-logo" alt="Unspaghetti Logo" />
        </div>
        <p className="tagline">The AI Intelligence Layer for your messy Code & Data.</p>
      </header>

      {/* GLASS CARD CONTAINER */}
      <main className="glass-panel">
        
        {/* NAVIGATION TABS */}
        <div className="nav-tabs">
          <button 
            className={`nav-btn ${activeTab === 'data' ? 'active' : ''}`}
            onClick={() => setActiveTab('data')}
          >
            📊 Data Lab
          </button>
          <button 
            className={`nav-btn ${activeTab === 'code' ? 'active' : ''}`}
            onClick={() => setActiveTab('code')}
          >
            💻 Code Brain
          </button>
        </div>

        <div className="content-area">
          {/* --- TAB 1: DATA LAB --- */}
          {activeTab === 'data' && (
            <div className="tab-content fade-in">
              <div className="section-title">
                <h2>Data Untangler</h2>
                <p>Upload raw CSV files to detect errors and autofix missing values.</p>
              </div>
              
              <div className="upload-zone">
                <input type="file" onChange={handleFileChange} accept=".csv" className="file-input"/>
                <div className="upload-instruction">
                  📂 Drag & drop your messy CSV here, or click to browse
                </div>
              </div>

              <div className="action-row">
                <button className="btn-primary" onClick={analyzeData} disabled={loadingData}>
                  {loadingData ? 'Scanning...' : '🔍 Scan for Issues'}
                </button>
                <button className="btn-secondary" onClick={downloadCleanData}>
                  ✨ Unspaghetti It (Fix & Download)
                </button>
              </div>

              {dataReport && (
                <div className="result-card">
                  <div className="badge success">Diagnosis Complete</div>
                  <div className="info-grid">
                    <div className="info-item">
                      <label>Filename</label>
                      <span>{dataReport.filename}</span>
                    </div>
                    <div className="info-item">
                      <label>Status</label>
                      <span>{dataReport.status}</span>
                    </div>
                    <div className="info-item">
                      <label>Missing Values</label>
                      <span className="highlight-red">{dataReport.missing}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* --- TAB 2: CODE BRAIN --- */}
          {activeTab === 'code' && (
            <div className="tab-content fade-in">
               <div className="section-title">
                <h2>Repository Intelligence</h2>
                <p>Ingest any public GitHub repository and chat with its architecture.</p>
              </div>
              
              {/* STEP 1: INGEST */}
              <div className="search-bar">
                <input 
                  type="text" 
                  placeholder="https://github.com/username/repo" 
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                />
                <button className="btn-primary" onClick={analyzeRepo} disabled={loadingCode}>
                  {loadingCode ? 'Ingesting...' : '🚀 Ingest'}
                </button>
              </div>

              {repoStatus && (
                <div className="result-card success-border">
                  <div className="badge success">System Ready</div>
                  <p>
                    Successfully analyzed <strong>{repoStatus.repo}</strong>. 
                    AI Mode: <strong>{repoStatus.mode}</strong>
                  </p>
                </div>
              )}

              <div className="divider"></div>

              {/* STEP 2: CHAT */}
              <div className="search-bar">
                <input 
                  type="text" 
                  placeholder="Ask a question (e.g., How does login work?)" 
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && askQuestion()}
                />
                <button className="btn-secondary" onClick={askQuestion} disabled={loadingCode || !repoStatus}>
                  💬 Ask AI
                </button>
              </div>

              {chatAnswer && (
                <div className="chat-response">
                  <div className="ai-avatar">🤖</div>
                  <div className="response-text">
                    <h3>AI Answer:</h3>
                    <p>{chatAnswer.answer}</p>
                    {chatAnswer.sources && (
                      <div className="sources">
                        <strong>Source Files:</strong> {chatAnswer.sources.join(', ')}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default App