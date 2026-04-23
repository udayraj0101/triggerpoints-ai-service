import { useState, useRef, useEffect } from 'react';
import './App.css';

// Use environment variable or fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || 'my-api-key';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [userId] = useState(() => `user_${Date.now()}`);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);

    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);

    // Add loading message
    setMessages(prev => [...prev, { role: 'assistant', content: '', isLoading: true }]);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
        },
        body: JSON.stringify({
          user_id: userId,
          query: userMessage,
        }),
      });

      if (!response.ok) {
        throw new Error(response.status === 401 ? 'Invalid API key' : 'Request failed');
      }

      const data = await response.json();

      // Update the loading message with actual response
      setMessages(prev => prev.map((msg, i) => 
        i === prev.length - 1 
          ? { role: 'assistant', content: data.answer || data.navigation || 'No response', isLoading: false }
          : msg
      ));
    } catch (error) {
      setMessages(prev => prev.map((msg, i) => 
        i === prev.length - 1 
          ? { role: 'assistant', content: `Error: ${error.message}`, isLoading: false, isError: true }
          : msg
      ));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="app-container">
      <header className="header">
        <div className="logo">
          <span className="logo-icon">💆</span>
          <h1>TriggerPoints AI</h1>
        </div>
        <button className="clear-btn" onClick={clearChat}>
          Clear Chat
        </button>
      </header>

      <main className="chat-container">
        <div className="messages">
          {messages.length === 0 && (
            <div className="welcome-message">
              <div className="welcome-icon">💆</div>
              <h2>Welcome to TriggerPoints AI</h2>
              <p>Ask me anything about trigger points, muscle pain, or related symptoms.</p>
              <div className="suggestions">
                <button onClick={() => setInput("What are trigger points?")}>
                  What are trigger points?
                </button>
                <button onClick={() => setInput("Help with neck pain")}>
                  Help with neck pain
                </button>
                <button onClick={() => setInput("List of muscles")}>
                  List of muscles
                </button>
              </div>
            </div>
          )}
          
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              <div className="message-avatar">
                {message.role === 'user' ? '👤' : '🤖'}
              </div>
              <div className="message-content">
                {message.isLoading ? (
                  <div className="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                ) : (
                  <p className={message.isError ? 'error' : ''}>{message.content}</p>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={isLoading}
          />
          <button 
            onClick={sendMessage} 
            disabled={isLoading || !input.trim()}
            className={isLoading ? 'loading' : ''}
          >
            {isLoading ? '⏳' : '➤'}
          </button>
        </div>
      </main>
    </div>
  );
}

export default App;