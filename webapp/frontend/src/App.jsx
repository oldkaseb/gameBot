import React, { useEffect, useState } from 'react';

const BTN = {
  primary: "px-4 py-2.5 rounded-xl font-bold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-lg shadow-blue-600/30 active:scale-95 transition-all",
  success: "px-4 py-2.5 rounded-xl font-bold text-white bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-500 hover:to-green-500 shadow-lg shadow-emerald-600/30 active:scale-95 transition-all",
  danger: "px-4 py-2.5 rounded-xl font-bold text-white bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 shadow-lg shadow-rose-600/30 active:scale-95 transition-all",
};

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, info) {
    console.error("UI Error:", error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 text-center text-white">
          <h2 className="text-xl font-bold text-rose-500 mb-2">خطا در اجرای مینی‌اپ</h2>
          <p className="text-sm text-slate-300 mb-4">{this.state.error?.message}</p>
          <button className={BTN.primary} onClick={() => window.location.reload()}>تلاش مجدد</button>
        </div>
      );
    }
    return this.props.children;
  }
}

function MainHub({ onSelect }) {
  return (
    <div className="p-4 max-w-md mx-auto">
      <div className="bg-slate-900/80 p-5 rounded-2xl text-center mb-4 border border-white/10">
        <h1 className="text-2xl font-extrabold mb-1">مینی‌اپ بازی‌های راینو</h1>
        <p className="text-slate-300 text-sm">بازی مورد نظر خود را انتخاب کنید</p>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <button className={BTN.primary} onClick={() => onSelect('2048')}>پازل 2048</button>
        <button className={BTN.primary} onClick={() => onSelect('spuzzle')}>پازل کشویی</button>
        <button className={BTN.primary} onClick={() => onSelect('samegame')}>جفت‌ها</button>
        <button className={BTN.primary} onClick={() => onSelect('dooz')}>دوز ۲ نفره</button>
        <button className={BTN.primary} onClick={() => onSelect('doz4p')}>دوز ۴ نفره</button>
        <button className={BTN.success} onClick={() => onSelect('connect4')}>چهار در ردیف</button>
        <button className={BTN.primary} onClick={() => onSelect('rps')}>سنگ کاغذ قیچی</button>
        <button className={BTN.primary} onClick={() => onSelect('memory')}>بازی حافظه</button>
        <button className={BTN.primary} onClick={() => onSelect('typing')}>تایپ سرعتی</button>
        <button className={BTN.primary} onClick={() => onSelect('hangman')}>حدس کلمه</button>
        <button className={BTN.primary} onClick={() => onSelect('guess')}>حدس عدد</button>
      </div>
    </div>
  );
}

function App() {
  const [game, setGame] = useState('hub');

  useEffect(() => {
    try {
      const tg = window.Telegram?.WebApp;
      if (tg) { tg.ready(); tg.expand(); }
      const params = new URLSearchParams(window.location.search);
      const g = params.get('game');
      if (g) setGame(g);
    } catch (e) {
      console.error(e);
    }
  }, []);

  return (
    <ErrorBoundary>
      <div className="min-h-screen text-white font-sans flex flex-col items-center">
        {game === 'hub' ? (
          <MainHub onSelect={setGame} />
        ) : (
          <div className="p-4 max-w-md w-full">
            <button className={`${BTN.danger} mb-4 w-full`} onClick={() => setGame('hub')}>
              بازگشت به منوی بازی‌ها
            </button>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}

export default App;
