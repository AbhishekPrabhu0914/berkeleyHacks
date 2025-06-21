'use client';

import { useEffect, useRef, useState } from 'react';
import { createClient } from '@supabase/supabase-js';
import { User } from '../types/User';

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
  const bottomRef = useRef<HTMLDivElement | null>(null);

  // Get current user and load messages
  useEffect(() => {
    const getUser = async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser();

      if (user) {
        setUser({
          id: user.id,
          email: user.email!,
          full_name: user.user_metadata.full_name,
          avatar_url: user.user_metadata.avatar_url,
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
        .on(
          'postgres_changes',
          { event: 'INSERT', schema: 'public', table: 'messages' },
          (payload) => {
            setMessages((prev) => [...prev, payload.new as Message]);
          }
        )
        .subscribe();
    };

    getUser();
    subscribeToMessages();
  }, []);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auth
  const handleSignIn = async () => {
    const { error } = await supabase.auth.signInWithOAuth({ provider: 'google' });
    if (error) console.error('Login error:', error);
  };

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    setUser(null);
  };

  // Chat
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

      // Optionally save both to Supabase
      await supabase.from('messages').insert([
        { text: trimmed, sender: 'user' },
        { text: reply, sender: 'bot' },
      ]);
    } catch (err) {
      console.error('Message send failed:', err);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      {!user ? (
        <div className="m-auto">
          <button
            onClick={handleSignIn}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg text-lg hover:bg-blue-700 transition"
          >
            Sign in with Google
          </button>
        </div>
      ) : (
        <div className="flex flex-col flex-1 max-w-3xl mx-auto w-full">
          {/* Header */}
          <div className="flex justify-between items-center p-4 border-b bg-white shadow-sm">
            <h1 className="text-xl font-semibold">Welcome, {user.full_name}</h1>
            <button
              onClick={handleSignOut}
              className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 transition"
            >
              Sign Out
            </button>
          </div>

          {/* Chat messages */}
          <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4 bg-gray-50">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`max-w-[75%] px-4 py-3 rounded-lg shadow-sm ${
                  msg.sender === 'user'
                    ? 'bg-blue-100 self-end text-right'
                    : 'bg-gray-200 self-start text-left'
                }`}
              >
                <div className="text-sm font-semibold text-gray-600">
                  {msg.sender === 'bot' ? 'Bot' : 'You'}
                </div>
                <div className="mt-1 text-gray-900 whitespace-pre-wrap">{msg.text}</div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          {/* Input area */}
          <div className="sticky bottom-0 w-full bg-white border-t">
            <div className="max-w-3xl mx-auto p-4">
              <div className="flex items-end gap-2 border rounded-xl px-4 py-3 shadow bg-gray-50">
                <textarea
                  className="flex-1 resize-none outline-none text-base bg-transparent"
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
                <button
                  onClick={handleSendMessage}
                  className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition"
                >
                  Send
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
