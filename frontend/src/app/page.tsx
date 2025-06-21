'use client';

import { useEffect, useRef, useState } from 'react';
import { createClient } from '@supabase/supabase-js';
import { User } from '../types/User';
import './chat.css';

const supabase = createClient(
  'https://suqfupehkzxtpqqghpaq.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN1cWZ1cGVoa3p4dHBxcWdocGFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA1MzY3NjcsImV4cCI6MjA2NjExMjc2N30.Vt3iK170uwYfI7PwlA17S8lvhrcSCiuXpQVEo2XE2Z4'
);

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  created_at: string;
}

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [generatedCode, setGeneratedCode] = useState<string | null>(null);
  const [view, setView] = useState<'chat' | 'code'>('chat');
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const getUser = async () => {
      const { data } = await supabase.auth.getUser();
      if (data.user) {
        setUser({
          id: data.user.id,
          email: data.user.email!,
          full_name: data.user.user_metadata.full_name,
          avatar_url: data.user.user_metadata.avatar_url,
        });
      }
    };

    const subscribeToMessages = async () => {
      const { data } = await supabase
        .from('messages')
        .select('*')
        .order('created_at', { ascending: true });
      setMessages(data || []);
      supabase
        .channel('public:messages')
        .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'messages' }, (payload) => {
          setMessages((prev) => [...prev, payload.new as Message]);
        })
        .subscribe();
    };

    getUser();
    subscribeToMessages();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSignIn = async () => {
    await supabase.auth.signInWithOAuth({ provider: 'google' });
  };

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    setUser(null);
  };

  const handleIterate = async (type: string) => {
    try {
      const res = await fetch('http://localhost:5001/iterate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type }),
      });
      const data = await res.json();
      const reply = data.reply || `No reply for ${type}`;
      const botMsg: Message = {
        id: crypto.randomUUID(),
        text: reply,
        sender: 'bot',
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, botMsg]);

      if (type === 'example' || type === 'code') {
        setGeneratedCode(reply);
        setView('code');
      }

      await supabase.from('messages').insert([{ text: reply, sender: 'bot' }]);
    } catch (err) {
      console.error('Iterate failed:', err);
    }
  };

  const handleSendMessage = async () => {
    const trimmed = message.trim();
    if (!trimmed) return;
    const userMsg: Message = {
      id: crypto.randomUUID(),
      text: trimmed,
      sender: 'user',
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setMessage('');

    try {
      const res = await fetch('http://localhost:5001/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed }),
      });
      const data = await res.json();
      const reply = data.reply || 'No reply';
      const botMsg: Message = {
        id: crypto.randomUUID(),
        text: reply,
        sender: 'bot',
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, botMsg]);
      await supabase.from('messages').insert([
        { text: trimmed, sender: 'user' },
        { text: reply, sender: 'bot' },
      ]);
    } catch (err) {
      console.error('Send failed:', err);
    }
  };

  return (
    <div className="app">
      {!user ? (
        <div className="center">
          <button className="signin-button" onClick={handleSignIn}>
            Sign in with Google
          </button>
        </div>
      ) : (
        <>
          <div className="header">
            <h1>Welcome, {user.full_name}</h1>
            <button onClick={handleSignOut}>Sign Out</button>
          </div>

          <div className="iteration-buttons">
            <button onClick={() => handleIterate('idea')}>Generate Idea</button>
            <button className="green" onClick={() => handleIterate('refine')}>Refine Thought</button>
            <button className="yellow" onClick={() => handleIterate('example')}>Give Example</button>
            {generatedCode && (
              <button onClick={() => setView(view === 'chat' ? 'code' : 'chat')}>
                Switch to {view === 'chat' ? 'Code' : 'Chat'}
              </button>
            )}
          </div>

          {view === 'chat' ? (
            <div className="chat-column">
              {messages.map((msg) => (
                <div key={msg.id} className={`message ${msg.sender}`}>
                  <div className="label">{msg.sender === 'bot' ? 'Bot' : 'You'}</div>
                  <div>{msg.text}</div>
                </div>
              ))}
              <div ref={bottomRef} />
              <div className="input-bar">
                <div className="input-inner">
                  <div className="input-box">
                    <textarea
                      value={message}
                      rows={1}
                      placeholder="Send a message"
                      onChange={(e) => setMessage(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage();
                        }
                      }}
                    />
                    <button onClick={handleSendMessage}>Send</button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="code-column" id="code-panel">
              <div className="code-title">Generated Code</div>
              <pre className="code-box">{generatedCode}</pre>
            </div>
          )}
        </>
      )}
    </div>
  );
}
