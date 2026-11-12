# -*- coding: utf-8 -*-
"""webapp/backend/game_logic/hokm.py — موتور کامل حکم با تایمر ۱۲۰ ثانیه‌ای، چت/ری‌اکشن شفاف، چینش تیم و هوش مصنوعی"""

import random
import time

SUITS = {"S": "♠️", "H": "♥️", "D": "♦️", "C": "♣️"}
SUIT_NAMES_FA = {"S": "پیک ♠️", "H": "دل ♥️", "D": "خشت ♦️", "C": "گشنیز ♣️"}
RANK_DISPLAY = {11: "J", 12: "Q", 13: "K", 14: "A"}
SUIT_ORDER = {"C": 0, "D": 1, "S": 2, "H": 3}
TURN_TIMEOUT_SEC = 120  # ۲ دقیقه مهلت بازی هر کارت


def create_deck() -> list[str]:
    deck = [f"{s}{r}" for s in SUITS for r in range(2, 15)]
    random.shuffle(deck)
    return deck


def sort_hand(hand: list[str]) -> list[str]:
    return sorted(hand, key=lambda c: (SUIT_ORDER.get(c[0], 0), -int(c[1:])))


def card_value(card: str, trump: str, trick_suit: str) -> int:
    suit, rank = card[0], int(card[1:])
    if suit == trump:
        return rank + 200
    if suit == trick_suit:
        return rank + 100
    return rank


def format_card_obj(card: str) -> dict:
    suit = card[0]
    rank = int(card[1:])
    return {
        "code": card,
        "suit": suit,
        "suit_icon": SUITS.get(suit, "🃏"),
        "rank": str(RANK_DISPLAY.get(rank, rank)),
        "is_red": suit in ("H", "D"),
    }


class HokmGame:
    def __init__(self, session_id: str, mode: str = "4p", initial_players: list[dict] | None = None):
        self.session_id = session_id
        self.mode = "2p" if "2p" in str(mode).lower() else "4p"
        self.max_players = 2 if self.mode == "2p" else 4
        self.status = "joining"
        self.host_id: int | None = None
        self.players: list[dict] = []  # [{"id", "name", "username", "photo", "is_bot", "mic_on"}]
        self.hands: dict[int, list[str]] = {}
        self.deck: list[str] = []
        self.hakem_id: int | None = None
        self.hakem_name: str = ""
        self.turn_index: int = 0
        self.turn_started_at: float = time.time()
        self.hokm_suit: str | None = None
        self.current_trick: list[dict] = []
        self.last_trick_winner: str = ""
        self.last_winner_id: int | None = None
        self.trick_scores: dict = {}
        self.game_scores: dict = {}
        self.winner_display: str = ""
        self.bubbles: dict[int, dict] = {}  # {uid: {"text": str, "expires": float}}
        self.updated_at = time.time()

        if initial_players:
            for p in initial_players:
                self.join(int(p["id"]), p.get("name") or "Player", p.get("username") or "", p.get("photo") or "")

    def join(self, user_id: int, name: str = "بازیکن", username: str = "", photo: str = "", is_bot: bool = False) -> bool:
        user_id = int(user_id)
        if self.host_id is None and not is_bot and user_id > 0:
            self.host_id = user_id

        for p in self.players:
            if p["id"] == user_id:
                if name and not is_bot:
                    p["name"] = name
                if username:
                    p["username"] = username
                if photo:
                    p["photo"] = photo
                return True

        if len(self.players) >= self.max_players:
            return False

        self.players.append({
            "id": user_id,
            "name": name or f"بازیکن {len(self.players)+1}",
            "username": username,
            "photo": photo,
            "is_bot": is_bot,
            "mic_on": False,
        })
        self.hands[user_id] = []
        return True

    def swap_seats(self, requester_id: int, idx1: int, idx2: int) -> dict:
        """قابلیت تغییر هم‌تیمی‌ها توسط سازنده بازی قبل از شروع"""
        if self.status != "joining":
            return {"ok": False, "error": "فقط قبل از شروع بازی می‌توانید تیم‌ها را تغییر دهید."}
        if self.host_id and int(requester_id) != int(self.host_id):
            return {"ok": False, "error": "فقط سازنده میز می‌تواند یارها را جابه‌جا کند."}
        if 0 <= idx1 < len(self.players) and 0 <= idx2 < len(self.players):
            self.players[idx1], self.players[idx2] = self.players[idx2], self.players[idx1]
        return {"ok": True}

    def start_match(self, fill_bots: bool = True) -> dict:
        if fill_bots and len(self.players) < self.max_players:
            self.fill_with_bots()
        if len(self.players) < self.max_players:
            return {"ok": False, "error": "تعداد بازیکنان هنوز کامل نیست!"}
        if self.status == "joining":
            self.start_first_deal()
        return {"ok": True}

    def fill_with_bots(self):
        bot_names = ["هوش مصنوعی ۱", "یار هوشمند", "هوش مصنوعی ۲"] if self.mode == "4p" else ["حریف هوشمند"]
        idx = 0
        while len(self.players) < self.max_players:
            bot_id = -(idx + 1)
            seat_num = len(self.players)
            bname = bot_names[seat_num - 1] if seat_num - 1 < len(bot_names) else f"ربات {seat_num}"
            self.join(bot_id, bname, username="RhinoAI", is_bot=True)
            idx += 1
        if len(self.players) == self.max_players and self.status == "joining":
            self.start_first_deal()

    def post_bubble(self, user_id: int, text: str):
        """ارسال پیام یا ری‌اکشن سریع که بالای کارت بازیکن به صورت شفاف ظاهر می‌شود"""
        clean = (text or "").strip()[:45]
        if clean:
            self.bubbles[int(user_id)] = {"text": clean, "expires": time.time() + 5.5}

    def toggle_mic(self, user_id: int, mic_state: bool):
        for p in self.players:
            if p["id"] == int(user_id):
                p["mic_on"] = bool(mic_state)

    def start_first_deal(self, keep_game_scores: bool = False, next_hakem_idx: int | None = None):
        self.deck = create_deck()
        pids = [p["id"] for p in self.players]
        self.hands = {pid: [] for pid in pids}
        self.current_trick = []
        self.hokm_suit = None
        self.last_trick_winner = ""

        for _ in range(5):
            for p in self.players:
                self.hands[p["id"]].append(self.deck.pop(0))

        for pid in pids:
            self.hands[pid] = sort_hand(self.hands[pid])

        if next_hakem_idx is not None:
            hakem = self.players[next_hakem_idx]
        else:
            hakem = next(
                (p for p in self.players if "S14" in self.hands[p["id"]]),
                self.players[0],
            )

        self.hakem_id = hakem["id"]
        self.hakem_name = hakem["name"]
        self.turn_index = next(i for i, p in enumerate(self.players) if p["id"] == self.hakem_id)
        self.turn_started_at = time.time()

        if self.mode == "4p":
            self.trick_scores = {"A": 0, "B": 0}
            if not keep_game_scores or not self.game_scores:
                self.game_scores = {"A": 0, "B": 0}
        else:
            self.trick_scores = {str(pid): 0 for pid in pids}
            if not keep_game_scores or not self.game_scores:
                self.game_scores = {str(pid): 0 for pid in pids}

        self.status = "hakem_choosing"
        self.updated_at = time.time()

        if hakem.get("is_bot"):
            best_suit = max(SUITS.keys(), key=lambda s: sum(1 for c in self.hands[self.hakem_id] if c.startswith(s)))
            self.choose_trump(self.hakem_id, best_suit)

    def choose_trump(self, user_id: int, suit: str) -> dict:
        user_id = int(user_id)
        if self.status != "hakem_choosing":
            return {"ok": False, "error": "الان زمان انتخاب حکم نیست!"}
        if user_id != self.hakem_id:
            return {"ok": False, "error": "فقط حاکم می‌تواند خال حکم را انتخاب کند!"}
        if suit not in SUITS:
            return {"ok": False, "error": "خال نامعتبر است!"}

        self.hokm_suit = suit

        for p in self.players:
            while len(self.hands[p["id"]]) < 13 and self.deck:
                self.hands[p["id"]].append(self.deck.pop(0))

        for pid in self.hands:
            self.hands[pid] = sort_hand(self.hands[pid])

        self.status = "playing"
        self.turn_index = next(i for i, p in enumerate(self.players) if p["id"] == self.hakem_id)
        self.turn_started_at = time.time()
        self.current_trick = []
        self.updated_at = time.time()
        return {"ok": True}

    def _pick_best_card_for_player(self, pid: int) -> str | None:
        b_hand = self.hands.get(pid, [])
        if not b_hand:
            return None
        valid_cards = b_hand
        if self.current_trick:
            ts = self.current_trick[0]["card"][0]
            follow = [c for c in b_hand if c.startswith(ts)]
            if follow:
                valid_cards = follow

        if self.current_trick:
            ts = self.current_trick[0]["card"][0]
            best_so_far = max(self.current_trick, key=lambda x: card_value(x["card"], self.hokm_suit or "S", ts))
            p_seat = next((i for i, p in enumerate(self.players) if p["id"] == pid), 0)
            is_partner_winning = (self.mode == "4p" and (best_so_far["seat_idx"] % 2 == p_seat % 2))
            if is_partner_winning:
                return min(valid_cards, key=lambda c: card_value(c, self.hokm_suit or "S", ts))
            winning_options = [
                c for c in valid_cards
                if card_value(c, self.hokm_suit or "S", ts) > card_value(best_so_far["card"], self.hokm_suit or "S", ts)
            ]
            if winning_options:
                return min(winning_options, key=lambda c: card_value(c, self.hokm_suit or "S", ts))
            return min(valid_cards, key=lambda c: card_value(c, self.hokm_suit or "S", ts))
        return max(valid_cards, key=lambda c: int(c[1:]))

    def play_card(self, user_id: int, card_code: str) -> dict:
        user_id = int(user_id)
        if self.status == "trick_pause":
            self.collect_trick()

        if self.status != "playing":
            return {"ok": False, "error": "صبر کنید تا دست قبلی جمع شود!"}

        cur_player = self.players[self.turn_index]
        if user_id != cur_player["id"]:
            return {"ok": False, "error": f"نوبت شما نیست! نوبت {cur_player['name']} است."}

        hand = self.hands.get(user_id, [])
        if card_code not in hand:
            return {"ok": False, "error": "این کارت در دست شما نیست!"}

        if self.current_trick:
            trick_suit = self.current_trick[0]["card"][0]
            has_trick_suit = any(c.startswith(trick_suit) for c in hand)
            if has_trick_suit and not card_code.startswith(trick_suit):
                return {
                    "ok": False,
                    "error": f"باید از خال زمین ({SUIT_NAMES_FA[trick_suit]}) بازی کنید!",
                }

        hand.remove(card_code)
        self.hands[user_id] = sort_hand(hand)
        self.current_trick.append({
            "player_id": user_id,
            "seat_idx": self.turn_index,
            "name": cur_player["name"],
            "card": card_code,
        })
        self.updated_at = time.time()

        if len(self.current_trick) < self.max_players:
            self.turn_index = (self.turn_index + 1) % self.max_players
            self.turn_started_at = time.time()
            return {"ok": True}

        self._evaluate_trick_winner()
        return {"ok": True}

    def step_bot_once(self) -> dict:
        now = time.time()
        if self.status == "trick_pause":
            if now - self.updated_at >= 1.35:
                self.collect_trick()
            return {"ok": True}

        # اگر حاکم تا ۲ دقیقه حکم نکرد، ربات بهترین خال را انتخاب کند
        if self.status == "hakem_choosing" and self.hakem_id is not None:
            if now - self.turn_started_at >= TURN_TIMEOUT_SEC:
                best_suit = max(SUITS.keys(), key=lambda s: sum(1 for c in self.hands.get(self.hakem_id, []) if c.startswith(s)))
                self.post_bubble(self.hakem_id, "⏰ انتخاب خودکار حکم")
                self.choose_trump(self.hakem_id, best_suit)
                return {"ok": True}

        if self.status != "playing":
            return {"ok": True}

        cur_p = self.players[self.turn_index]
        elapsed = now - self.turn_started_at

        # اگر بازیکن بات است (مکث طبیعی ۱ ثانیه) یا اگر بازیکن انسانی تا ۱۲۰ ثانیه بازی نکرد
        if cur_p.get("is_bot") or elapsed >= TURN_TIMEOUT_SEC:
            chosen = self._pick_best_card_for_player(cur_p["id"])
            if chosen:
                if not cur_p.get("is_bot") and elapsed >= TURN_TIMEOUT_SEC:
                    self.post_bubble(cur_p["id"], "⏰ بازی خودکار (اتمام ۲ دقیقه)")
                return self.play_card(cur_p["id"], chosen)

        return {"ok": True}

    def _evaluate_trick_winner(self):
        trick_suit = self.current_trick[0]["card"][0]
        winner_play = max(
            self.current_trick,
            key=lambda play: card_value(play["card"], self.hokm_suit, trick_suit),
        )
        self.last_winner_id = winner_play["player_id"]
        self.last_trick_winner = f"{winner_play['name']} دست را گرفت"
        self.status = "trick_pause"
        self.updated_at = time.time()

    def collect_trick(self):
        if self.status != "trick_pause":
            return

        winner_id = self.last_winner_id
        if self.mode == "4p":
            team_a_ids = [self.players[0]["id"], self.players[2]["id"]]
            winner_team = "A" if winner_id in team_a_ids else "B"
            self.trick_scores[winner_team] += 1
            round_over = self.trick_scores[winner_team] >= 7
        else:
            self.trick_scores[str(winner_id)] = self.trick_scores.get(str(winner_id), 0) + 1
            round_over = any(s >= 7 for s in self.trick_scores.values())

        self.turn_index = next(i for i, p in enumerate(self.players) if p["id"] == winner_id)
        self.turn_started_at = time.time()
        self.current_trick = []
        self.status = "playing"
        self.updated_at = time.time()

        if not round_over:
            return

        cur_hakem_idx = next(i for i, p in enumerate(self.players) if p["id"] == self.hakem_id)

        if self.mode == "4p":
            winning_team = "A" if self.trick_scores["A"] >= 7 else "B"
            loser_team = "B" if winning_team == "A" else "A"
            hakem_team = "A" if cur_hakem_idx in (0, 2) else "B"
            pts = (3 if winning_team != hakem_team else 2) if self.trick_scores[loser_team] == 0 else 1
            self.game_scores[winning_team] += pts
            self.winner_display = "تیم ۱" if winning_team == "A" else "تیم ۲"
            game_over = self.game_scores[winning_team] >= 7
            next_hakem_idx = cur_hakem_idx if winning_team == hakem_team else (cur_hakem_idx + 1) % 4
        else:
            round_winner_id = next(int(pid) for pid, s in self.trick_scores.items() if s >= 7)
            loser_score = min(self.trick_scores.values())
            pts = 2 if loser_score == 0 else 1
            self.game_scores[str(round_winner_id)] += pts
            w_player = next(p for p in self.players if p["id"] == round_winner_id)
            self.winner_display = w_player["name"]
            game_over = any(s >= 7 for s in self.game_scores.values())
            next_hakem_idx = cur_hakem_idx if round_winner_id == self.hakem_id else (cur_hakem_idx + 1) % 2

        if game_over:
            self.status = "finished"
            return

        self.start_first_deal(keep_game_scores=True, next_hakem_idx=next_hakem_idx)

    def get_state_for_player(self, user_id: int) -> dict:
        now = time.time()
        user_id = int(user_id)
        my_seat = next((i for i, p in enumerate(self.players) if p["id"] == user_id), 0)
        my_cards = [format_card_obj(c) for c in sort_hand(self.hands.get(user_id, []))]

        rem_sec = max(0, int(TURN_TIMEOUT_SEC - (now - self.turn_started_at)))
        timer_pct = max(0, min(100, int((rem_sec / TURN_TIMEOUT_SEC) * 100)))

        seats_view = {}
        for idx, p in enumerate(self.players):
            rel = (idx - my_seat) % self.max_players
            pos_name = (["bottom", "right", "top", "left"][rel] if self.max_players == 4 else ["bottom", "top"][rel])
            bub = self.bubbles.get(p["id"])
            active_bubble = bub["text"] if (bub and bub["expires"] > now) else ""
            is_turn = (idx == self.turn_index and self.status in ("playing", "hakem_choosing"))
            seats_view[pos_name] = {
                "id": p["id"],
                "name": p["name"],
                "username": p.get("username") or "",
                "photo": p.get("photo") or "",
                "is_bot": p.get("is_bot", False),
                "mic_on": p.get("mic_on", False),
                "seat_idx": idx,
                "team": ("تیم ۱" if idx in (0, 2) else "تیم ۲") if self.mode == "4p" else "انفرادی",
                "cards_left": len(self.hands.get(p["id"], [])),
                "is_turn": is_turn,
                "timer_sec": rem_sec if is_turn else TURN_TIMEOUT_SEC,
                "timer_pct": timer_pct if is_turn else 100,
                "is_hakem": (p["id"] == self.hakem_id),
                "bubble": active_bubble,
            }

        trick_cards = []
        for t in self.current_trick:
            rel = (t["seat_idx"] - my_seat) % self.max_players
            pos_name = (["bottom", "right", "top", "left"][rel] if self.max_players == 4 else ["bottom", "top"][rel])
            trick_cards.append({
                "player_id": t["player_id"],
                "name": t["name"],
                "pos": pos_name,
                "card": format_card_obj(t["card"]),
            })

        turn_player = self.players[self.turn_index] if self.players and 0 <= self.turn_index < len(self.players) else None

        if self.mode == "4p":
            my_team = "A" if my_seat in (0, 2) else "B"
            opp_team = "B" if my_team == "A" else "A"
            our_tricks = self.trick_scores.get(my_team, 0)
            their_tricks = self.trick_scores.get(opp_team, 0)
            our_sets = self.game_scores.get(my_team, 0)
            their_sets = self.game_scores.get(opp_team, 0)
        else:
            opp_id = next((p["id"] for p in self.players if p["id"] != user_id), 0)
            our_tricks = self.trick_scores.get(str(user_id), 0)
            their_tricks = self.trick_scores.get(str(opp_id), 0)
            our_sets = self.game_scores.get(str(user_id), 0)
            their_sets = self.game_scores.get(str(opp_id), 0)

        return {
            "session_id": self.session_id,
            "host_id": self.host_id,
            "mode": self.mode,
            "max_players": self.max_players,
            "status": self.status,
            "players": [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "username": p.get("username") or "",
                    "is_bot": p.get("is_bot", False),
                    "seat_idx": i,
                    "team": ("تیم ۱" if i in (0, 2) else "تیم ۲") if self.mode == "4p" else f"نفر {i+1}",
                }
                for i, p in enumerate(self.players)
            ],
            "seats": seats_view,
            "hakem_id": self.hakem_id,
            "hakem_name": self.hakem_name,
            "trump": self.hokm_suit,
            "trump_icon": SUITS.get(self.hokm_suit, "❓") if self.hokm_suit else "❓",
            "turn_id": turn_player["id"] if turn_player else None,
            "turn_name": turn_player["name"] if turn_player else "—",
            "my_hand": my_cards,
            "trick": trick_cards,
            "last_trick_winner": self.last_trick_winner,
            "our_tricks": our_tricks,
            "their_tricks": their_tricks,
            "our_sets": our_sets,
            "their_sets": their_sets,
            "winner_display": self.winner_display,
        }
