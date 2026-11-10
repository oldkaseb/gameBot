import { useEffect, useState } from 'react';
import HokmGame from './pages/HokmGame';
import ChatGame from './pages/ChatGame';

function App() {
  const [gameData, setGameData] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const game = params.get('game');
    const session = params.get('session');
    
    // ✅ گرفتن آیدی امن از تلگرام (نه از URL)
    const tg = window.Telegram?.WebApp;
    const uid = tg?.initDataUnsafe?.user?.id?.toString() || params.get('uid');
    
    setGameData({ game, session, uid });
  }, []);

  if (!gameData) return <div className="glass-bg h-screen text-white flex items-center justify-center">در حال بارگذاری...</div>;

  // بازی‌های چت‌محور
  const isChat = ['typing', 'hangman', 'guess'].includes(gameData.game);
  
  // بازی حکم (فعلاً تنها بازی چندنفره‌ای که فرانت‌اند کامل دارد)
  const isHokm = gameData.game === 'hokm';

  return (
    <div className="glass-bg min-h-screen text-white font-sans">
      {isHokm && <HokmGame session={gameData.session} uid={gameData.uid} />}
      {isChat && <ChatGame game={gameData.game} session={gameData.session} uid={gameData.uid} />}
      
      {/* بازی‌های دیگر که هنوز فرانت‌اند کامل ندارند */}
      {!isHokm && !isChat && (
         <div className="flex flex-col items-center justify-center h-screen text-center px-4">
            <h1 className="text-2xl font-bold mb-4">🎮 بازی در حال توسعه است</h1>
            <p className="text-gray-300">به زودی می‌توانید این بازی را در همین صفحه انجام دهید.</p>
         </div>
      )}
    </div>
  );
}

export default App;
