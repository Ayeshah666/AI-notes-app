import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [notes, setNotes] = useState([]);
  const [corrected, setCorrected] = useState('');
  const [assistPrompt, setAssistPrompt] = useState('');
  const [assistOutput, setAssistOutput] = useState('');
  const [assistMode, setAssistMode] = useState('default');

  const authHeaders = {
    headers: { Authorization: `Bearer ${token}` }
  };

  const signup = async () => {
    try {
      await axios.post('http://localhost:8080/signup', { email, password });
      alert('Signup successful. You can now log in.');
    } catch {
      alert('Signup failed');
    }
  };

  const login = async () => {
    try {
      const res = await axios.post('http://localhost:8080/login', { email, password });
      const token = res.data.access_token;
      setToken(token);
      localStorage.setItem('token', token);
      alert('Login successful');
    } catch {
      alert('Login failed');
    }
  };

  const fetchNotes = async () => {
    try {
      const res = await axios.get('http://localhost:8080/notes/', authHeaders);
      setNotes(res.data);
    } catch (err) {
      alert('Could not fetch notes');
      console.error(err);
    }
  };

  const deleteNote = async (id) => {
    try {
      await axios.delete(`http://localhost:8080/notes/${id}`, authHeaders);
      await fetchNotes(); // Refresh notes after delete
    } catch (err) {
      alert("Delete failed");
      console.error("Error deleting note:", err);
    }
  };

  const submitNote = async () => {
    try {
      await axios.post('http://localhost:8080/notes/', { title, content }, authHeaders);
      await fetchNotes();
      setTitle('');
      setContent('');
    } catch (err) {
      alert('Note creation failed');
    }
  };

  const correctGrammar = async () => {
    try {
      const res = await axios.post('http://localhost:8080/correct/', { text: content }, authHeaders);
      setCorrected(res.data.corrected_text);
    } catch {
      alert('Grammar correction failed');
    }
  };

  const getAICompletion = async () => {
    try {
      const res = await axios.post('http://localhost:8080/assist/', {
        prompt: assistPrompt,
        mode: assistMode
      }, authHeaders);
      setAssistOutput(res.data.completion);
    } catch {
      alert('AI assist failed');
    }
  };

  useEffect(() => {
    if (token) fetchNotes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]); // ignore fetchNotes warning

  return (
    <div className="container">
      <h1>🧠 AI Notes Assistant</h1>

      <section className="auth">
        <h2>🔐 Login or Signup</h2>
        <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
        <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
        <div className="btn-row">
          <button onClick={login}>Login</button>
          <button onClick={signup}>Signup</button>
        </div>
      </section>

      {token && (
        <>
          <section>
            <h2>📝 Create a Note</h2>
            <input placeholder="Note Title" value={title} onChange={e => setTitle(e.target.value)} />
            <textarea placeholder="Write your note..." rows={4} value={content} onChange={e => setContent(e.target.value)} />
            <div className="btn-row">
              <button onClick={submitNote}>💾 Save</button>
              <button onClick={correctGrammar}>✒️ Grammar Check</button>
            </div>
            {corrected && <div className="card"><strong>Corrected:</strong> <p>{corrected}</p></div>}
          </section>

          <section>
            <h2>✍️ AI Writing Assistant</h2>
            <textarea rows={3} placeholder="How can I help?" value={assistPrompt} onChange={e => setAssistPrompt(e.target.value)} />
            <select value={assistMode} onChange={e => setAssistMode(e.target.value)}>
              <option value="default">Default</option>
              <option value="email">Polite Email</option>
              <option value="idea">Idea Brainstorm</option>
              <option value="casual">Casual</option>
            </select>
            <button onClick={getAICompletion}>Generate</button>
            {assistOutput && <div className="card"><strong>AI Output:</strong><p>{assistOutput}</p></div>}
          </section>

          <section>
            <h2>📚 Your Notes</h2>
            <div className="notes-grid">
              {notes.map(note => (
                <div key={note.id} className="note-card">
                  <h4>{note.title}</h4>
                  <p>{note.content}</p>
                  <button onClick={() => deleteNote(note.id)}>🗑️ Delete</button>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}

export default App;









