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

  const isMulti = ['hokm', 'dooz', 'connect4'].includes(gameData.game);
  const isChat = ['typing', 'hangman', 'guess'].includes(gameData.game);

  return (
    <div className="glass-bg min-h-screen text-white font-sans">
      {isMulti && <HokmGame session={gameData.session} uid={gameData.uid} />}
      {isChat && <ChatGame game={gameData.game} session={gameData.session} uid={gameData.uid} />}
      {!isMulti && !isChat && (
         <div className="flex items-center justify-center h-screen">بازی در حال توسعه است...</div>
      )}
    </div>
  );
}

export default App;
