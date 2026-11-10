import { useEffect, useState } from 'react';
import HokmGame from './pages/HokmGame';
import ChatGame from './pages/ChatGame';

function App() {
  const [gameData, setGameData] = useState(null);

  useEffect(() => {
    // استخراج پارامترها از URL
    const params = new URLSearchParams(window.location.search);
    const game = params.get('game');
    const session = params.get('session');
    const uid = params.get('uid');
    
    setGameData({ game, session, uid });
  }, []);

  if (!gameData) return <div className="glass-bg h-screen text-white flex items-center justify-center">در حال بارگذاری...</div>;

  return (
    <div className="glass-bg min-h-screen text-white font-sans">
      {['hokm', 'dooz', 'connect4'].includes(gameData.game) && (
        <HokmGame session={gameData.session} uid={gameData.uid} />
      )}
      
      {['typing', 'hangman', 'guess'].includes(gameData.game) && (
        <ChatGame game={gameData.game} session={gameData.session} uid={gameData.uid} />
      )}
    </div>
  );
}

export default App;
