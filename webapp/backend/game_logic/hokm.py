import random

SUITS = {"S": "♠️", "H": "♥️", "D": "♦️", "C": "♣️"}
RANKS = {11: "J", 12: "Q", 13: "K", 14: "A"}

class HokmGame:
    def __init__(self, session_id):
        self.session_id = session_id
        self.deck = []
        self.hands = {}
        self.trump_suit = None
        self.hakem = None
        self.turn = None
        self.players = [] # آیدی بازیکنان به ترتیب ورود
        self.trick = []
        self.scores = {"TeamA": 0, "TeamB": 0}

    def join(self, user_id):
        if len(self.players) < 4:
            self.players.append(user_id)
            self.hands[user_id] = []
            if len(self.players) == 4:
                self.start_round()

    def start_round(self):
        # 1. ساخت دسته
        self.deck = [(s, r) for s in SUITS for r in range(2, 15)]
        random.shuffle(self.deck)
        # 2. پخش ۵ کارت
        for _ in range(5):
            for p in self.players:
                self.hands[p].append(self.deck.pop())
        # 3. تعیین حاکم (آس پیک)
        for p in self.players:
            if ("S", 14) in self.hands[p]:
                self.hakem = p
                self.turn = p
                break
        
    def handle_action(self, user_id, msg):
        action = msg.get("action")
        if action == "choose_trump":
            self.trump_suit = msg.get("suit")
            # پخش ۸ کارت باقی مانده
            for _ in range(8):
                for p in self.players:
                    self.hands[p].append(self.deck.pop())
            # مرتب کردن دست‌ها
        elif action == "play_card":
            if user_id != self.turn:
                return {"error": "نوبت شما نیست"}
            # منطق بازی کارت...
            pass
        return {"status": "ok"}

    def get_state_for_player(self, user_id):
        # استیت رو طوری برمیگردونیم که هر کس فقط کارت‌های خودش رو ببینه
        return {
            "status": "playing",
            "hakem": self.hakem,
            "trump": self.trump_suit,
            "turn": self.turn,
            "my_hand": self.hands.get(user_id, []),
            "trick": self.trick,
            "scores": self.scores,
            "players_count": len(self.players)
        }
