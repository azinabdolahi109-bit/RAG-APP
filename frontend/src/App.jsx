import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, Send, FileText, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

// Determine API base URL based on environment
const API_BASE_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:8000' 
  : '/api';

function App() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [indexReady, setIndexReady] = useState(false);
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const [chat, setChat] = useState([]);
  const [error, setError] = useState('');
  const [fileName, setFileName] = useState('');

  // Check health on load
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/health`);
        setIndexReady(res.data.index_ready);
      } catch (err) {
        console.error("Backend not reachable");
      }
    };
    checkHealth();
  }, []);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError('');
    }
  };

  const uploadFile = async () => {
    if (!file) return;
    setUploading(true);
    setError('');
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post(`${API_BASE_URL}/upload`, formData);
      setIndexReady(true);
      setFileName(res.data.filename);
      setChat([{ role: 'assistant', content: `Success! I've indexed "${res.data.filename}". You can now ask questions about its content.` }]);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to upload and index file.");
    } finally {
      setUploading(false);
    }
  };

  const askQuestion = async (e) => {
    e.preventDefault();
    if (!question.trim() || !indexReady) return;

    const userMsg = question;
    setChat(prev => [...prev, { role: 'user', content: userMsg }]);
    setQuestion('');
    setAsking(true);
    setError('');

    try {
      const res = await axios.post(`${API_BASE_URL}/ask`, { question: userMsg });
      setChat(prev => [...prev, { 
        role: 'assistant', 
        content: res.data.answer,
        sources: res.data.sources 
      }]);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to get an answer.");
    } finally {
      setAsking(false);
    }
  };

  return (
    <div className="container">
      <header>
        <h1>Excel RAG Assistant</h1>
        <div className="status-indicator">
          <div className={`status-dot ${indexReady ? 'active' : ''}`}></div>
          <span>{indexReady ? `Index Ready (${fileName || 'Loaded'})` : 'No Data Indexed'}</span>
        </div>
      </header>

      <main className="glass-card">
        {!indexReady && !uploading && (
          <div className="upload-section">
            <label className="dropzone">
              <input type="file" onChange={handleFileChange} accept=".xlsx,.xls" hidden />
              <div className="flex flex-col items-center">
                <Upload size={48} className="text-primary mb-4" />
                <p>{file ? file.name : "Click to select or drag & drop an Excel file"}</p>
              </div>
            </label>
            {file && (
              <button className="btn mt-4" onClick={uploadFile}>
                Process File
              </button>
            )}
          </div>
        )}

        {uploading && (
          <div className="flex flex-col items-center py-8">
            <Loader2 className="loading-spinner text-primary mb-4" size={48} />
            <p>Analyzing sheets and generating embeddings...</p>
          </div>
        )}

        {indexReady && (
          <div className="chat-interface">
            <div className="chat-container">
              {chat.map((msg, i) => (
                <div key={i} className={`message ${msg.role}`}>
                  <p>{msg.content}</p>
                  {msg.sources && (
                    <div className="sources">
                      <strong>Sources:</strong>
                      <div className="flex flex-wrap">
                        {msg.sources.map((s, j) => (
                          <span key={j} className="source-chip">{s.split('|')[0]}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
              {asking && (
                <div className="message assistant">
                  <Loader2 className="loading-spinner" size={20} />
                </div>
              )}
            </div>

            <form className="input-group" onSubmit={askQuestion}>
              <input 
                type="text" 
                placeholder="Ask something about your data..." 
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={asking}
              />
              <button className="btn" type="submit" disabled={asking || !question.trim()}>
                <Send size={18} />
                Send
              </button>
            </form>
            
            <div className="text-center mt-4">
              <button 
                className="text-muted text-sm hover:text-white transition-colors"
                onClick={() => {
                  setIndexReady(false);
                  setFile(null);
                  setFileName('');
                }}
              >
                Upload different file
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="error-message">
            <AlertCircle size={18} />
            <p>{error}</p>
          </div>
        )}
      </main>

      <footer className="mt-8 text-center text-muted text-sm">
        Powered by Groq & FAISS • Sentence Transformers
      </footer>
    </div>
  );
}

export default App;
