import { useEffect, useState } from 'react';

export default function HokmGame({ session, uid }) {
  const [state, setState] = useState(null);

  useEffect(() => {
    // اتصال به وب‌سوکت بک‌اند
    const ws = new WebSocket(`wss://games.rhinokaseb.abrdns.com/ws/hokm/${session}/${uid}`);
    
    ws.onmessage = (e) => {
      setState(JSON.parse(e.data));
    };

    return () => ws.close();
  }, [session, uid]);

  if (!state) return <div className="h-screen flex items-center justify-center">در حال اتصال به میز...</div>;

  return (
    <div className="h-screen flex flex-col justify-between p-4 relative overflow-hidden">
      {/* میز وسط */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="glass-panel w-64 h-64 rounded-full flex items-center justify-center">
          {/* کارت‌های روی میز */}
          <div className="flex gap-2">
             {state.trick?.map((card, i) => (
                <div key={i} className="w-12 h-16 bg-white text-black rounded flex flex-col items-center justify-center shadow-lg">
                  <span>{card.rank}</span>
                  <span>{card.suit}</span>
                </div>
             ))}
          </div>
        </div>
      </div>

      {/* حریف بالا */}
      <div className="flex justify-center mt-4">
         <div className="glass-panel px-4 py-2 rounded-full text-sm">
            حریف بالا ({state.hands_count || 0} کارت)
         </div>
      </div>

      {/* دست بازیکن (پایین) */}
      <div className="flex justify-center gap-2 mb-4 z-10">
        {state.my_hand?.map((card, i) => (
          <div 
            key={i} 
            className="w-14 h-20 bg-white text-black rounded-lg flex flex-col items-center justify-center cursor-pointer hover:-translate-y-4 transition-transform shadow-xl"
          >
            <span className="font-bold">{card.rank}</span>
            <span className="text-xl">{card.suit}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
