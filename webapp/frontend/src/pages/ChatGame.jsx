import { useEffect, useState, useRef } from 'react';

export default function ChatGame({ game, session, uid }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const ws = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    ws.current = new WebSocket(`wss://games.rhinokaseb.abrdns.com/ws/${game}/${session}/${uid}`);
    ws.current.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setMessages(prev => [...prev, data]);
    };
    return () => ws.current.close();
  }, [game, session, uid]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = () => {
    if (!input.trim()) return;
    ws.current.send(JSON.stringify({ text: input, name: "من" }));
    setInput("");
  };

  return (
    <div className="h-screen flex flex-col">
      <div className="glass-panel p-4 text-center text-lg font-bold">اتاق چت گروهی 💬</div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.user_id === parseInt(uid) ? 'justify-end' : 'justify-start'}`}>
            <div className={`glass-panel px-4 py-2 rounded-2xl max-w-[80%] ${m.user_id === parseInt(uid) ? 'bg-blue-600/40' : ''}`}>
              <div className="text-xs text-gray-300 mb-1">{m.name}</div>
              <div>{m.text}</div>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="glass-panel p-4 flex gap-2">
        <input 
          className="flex-1 bg-transparent border border-white/20 rounded-full px-4 py-2 outline-none"
          placeholder="تایپ کنید..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
        />
        <button onClick={send} className="glass-btn px-6 py-2 rounded-full font-bold">ارسال</button>
      </div>
    </div>
  );
}
