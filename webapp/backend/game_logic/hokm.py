# -*- coding: utf-8 -*-
"""webapp/backend/game_logic/hokm.py — موتور واقعی حکم ۲ و ۴ نفره با اجرای گام‌به‌گام نوبت‌ها"""

import random
import time

SUITS = {"S": "♠️", "H": "♥️", "D": "♦️", "C": "♣️"}
SUIT_NAMES_FA = {"S": "پیک ♠️", "H": "دل ♥️", "D": "خشت ♦️", "C": "گشنیز ♣️"}
RANK_DISPLAY = {11: "J", 12: "Q", 13: "K", 14: "A"}
# ترتیب مرتب‌سازی دست: گشنیز، خشت، پیک، دل
SUIT_ORDER = {"C": 0, "D": 1, "S": 2, "H": 3}


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
        self.status = "joining"  # joining | hakem_choosing | playing | trick_pause | finished
        self.players: list[dict] = []  # [{"id": int, "name": str, "is_bot": bool}]
        self.hands: dict[int, list[str]] = {}
        self.deck: list[str] = []
        self.hakem_id: int | None = None
        self.hakem_name: str = ""
        self.turn_index: int = 0
        self.hokm_suit: str | None = None
        self.current_trick: list[dict] = []  # [{"player_id": int, "seat_idx": int, "name": str, "card": str}]
        self.last_trick_winner: str = ""
        self.last_winner_id: int | None = None
        self.trick_scores: dict = {}
        self.game_scores: dict = {}
        self.winner_display: str = ""
        self.updated_at = time.time()

        if initial_players:
            for p in initial_players:
                self.join(int(p["id"]), p.get("name") or f"Player {p['id']}")

    def join(self, user_id: int, name: str = "بازیکن", is_bot: bool = False) -> bool:
        user_id = int(user_id)
        for p in self.players:
            if p["id"] == user_id:
                if name and not is_bot:
                    p["name"] = name
                return True

        if len(self.players) >= self.max_players:
            return False

        self.players.append({"id": user_id, "name": name or f"بازیکن {len(self.players)+1}", "is_bot": is_bot})
        self.hands[user_id] = []

        if len(self.players) == self.max_players and self.status == "joining":
            self.start_first_deal()
        return True

    def fill_with_bots(self):
        if self.mode == "4p":
            # چیدمان صندلی‌ها: 0=کاربر، 1=حریف راست، 2=یار روبه‌رو، 3=حریف چپ
            bot_names = ["حریف راست", "یار خودی", "حریف چپ"]
        else:
            bot_names = ["حریف روبه‌رو"]

        idx = 0
        while len(self.players) < self.max_players:
            bot_id = -(idx + 1)
            seat_num = len(self.players)
            bname = bot_names[seat_num - 1] if seat_num - 1 < len(bot_names) else f"بازیکن {seat_num+1}"
            self.join(bot_id, bname, is_bot=True)
            idx += 1

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
        self.current_trick = []
        self.updated_at = time.time()
        return {"ok": True}

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
            return {"ok": True}

        # تمام بازیکنان کارت انداختند -> مکث روی فرش برای دیده شدن کارت‌ها
        self._evaluate_trick_winner()
        return {"ok": True}

    def step_bot_once(self) -> dict:
        """اجرای فقط یک نوبت بات در هر تیک تا کارت‌ها یکی‌یکی و طبیعی روی فرش انداخته شوند"""
        if self.status == "trick_pause":
            if time.time() - self.updated_at >= 1.3:
                self.collect_trick()
            return {"ok": True}

        if self.status != "playing":
            return {"ok": True}

        cur_p = self.players[self.turn_index]
        if not cur_p.get("is_bot"):
            return {"ok": True}

        b_hand = self.hands.get(cur_p["id"], [])
        if not b_hand:
            return {"ok": True}

        valid_cards = b_hand
        if self.current_trick:
            ts = self.current_trick[0]["card"][0]
            follow = [c for c in b_hand if c.startswith(ts)]
            if follow:
                valid_cards = follow

        # هوش مصنوعی: اگر یارش دست را برده، کارت کوچک رد کند؛ وگرنه بالاترین کارت را بزند
        chosen = valid_cards[0]
        if self.current_trick:
            ts = self.current_trick[0]["card"][0]
            best_so_far = max(self.current_trick, key=lambda x: card_value(x["card"], self.hokm_suit or "S", ts))
            is_partner_winning = (
                self.mode == "4p"
                and (best_so_far["seat_idx"] % 2 == self.turn_index % 2)
            )
            if is_partner_winning:
                chosen = min(valid_cards, key=lambda c: card_value(c, self.hokm_suit or "S", ts))
            else:
                winning_options = [
                    c for c in valid_cards
                    if card_value(c, self.hokm_suit or "S", ts) > card_value(best_so_far["card"], self.hokm_suit or "S", ts)
                ]
                if winning_options:
                    chosen = min(winning_options, key=lambda c: card_value(c, self.hokm_suit or "S", ts))
                else:
                    chosen = min(valid_cards, key=lambda c: card_value(c, self.hokm_suit or "S", ts))
        else:
            chosen = max(valid_cards, key=lambda c: int(c[1:]))

        return self.play_card(cur_p["id"], chosen)

    def _evaluate_trick_winner(self):
        trick_suit = self.current_trick[0]["card"][0]
        winner_play = max(
            self.current_trick,
            key=lambda play: card_value(play["card"], self.hokm_suit, trick_suit),
        )
        self.last_winner_id = winner_play["player_id"]
        self.last_trick_winner = f"{winner_play['name']} دست را برید/برد"
        self.status = "trick_pause"
        self.updated_at = time.time()

    def collect_trick(self):
        """جمع کردن ۴ کارت از روی فرش و اضافه کردن ۱ کارت برعکس به دست‌های تیم برنده"""
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
        self.current_trick = []
        self.status = "playing"
        self.updated_at = time.time()

        if not round_over:
            return

        # رسیدن به ۷ کارت برعکس (پایان دور)
        cur_hakem_idx = next(i for i, p in enumerate(self.players) if p["id"] == self.hakem_id)

        if self.mode == "4p":
            winning_team = "A" if self.trick_scores["A"] >= 7 else "B"
            loser_team = "B" if winning_team == "A" else "A"
            hakem_team = "A" if cur_hakem_idx in (0, 2) else "B"

            if self.trick_scores[loser_team] == 0:
                pts = 3 if winning_team != hakem_team else 2
            else:
                pts = 1
            self.game_scores[winning_team] += pts
            self.winner_display = "تیم شما و یارتان" if winning_team == "A" else "تیم حریف"
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
        user_id = int(user_id)
        my_seat = next((i for i, p in enumerate(self.players) if p["id"] == user_id), 0)
        my_cards = [format_card_obj(c) for c in sort_hand(self.hands.get(user_id, []))]

        # محاسبه جایگاه نسبی صندلی‌ها نسبت به بازیکن فعلی:
        # bottom: خود بازیکن (0) | right: حریف راست (1) | top: یار روبه‌رو (2) | left: حریف چپ (3)
        seats_view = {}
        for idx, p in enumerate(self.players):
            rel = (idx - my_seat) % self.max_players
            if self.max_players == 4:
                pos_name = ["bottom", "right", "top", "left"][rel]
            else:
                pos_name = ["bottom", "top"][rel]
            seats_view[pos_name] = {
                "id": p["id"],
                "name": p["name"],
                "seat_idx": idx,
                "cards_left": len(self.hands.get(p["id"], [])),
                "is_turn": (idx == self.turn_index and self.status == "playing"),
                "is_hakem": (p["id"] == self.hakem_id),
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

        # محاسبه دست‌های گرفته‌شده (تعداد کارت‌های برعکس برای چیدن تا ۷)
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
            "mode": self.mode,
            "max_players": self.max_players,
            "status": self.status,
            "players": [{"id": p["id"], "name": p["name"], "cards_left": len(self.hands.get(p["id"], []))} for p in self.players],
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
