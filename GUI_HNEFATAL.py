"""
Hnefatafl GUI - Python (tkinter)
Full game logic mirrors the Prolog code exactly.
Supports: Human vs CPU (easy/medium/hard) and Multiplayer
"""

import tkinter as tk
from tkinter import messagebox, ttk
import threading
import copy
import math

# ══════════════════════════════════════════════
#  BOARD LOGIC  (mirrors the Prolog predicates)
# ══════════════════════════════════════════════

BOARD_SIZE = 9
THRONE = (5, 5)
CORNERS = {(1,1),(1,9),(9,1),(9,9)}

INITIAL_PIECES = [
    ("king",     5, 5),
    ("defender", 5, 3), ("defender", 5, 4),
    ("defender", 5, 6), ("defender", 5, 7),
    ("defender", 3, 5), ("defender", 4, 5),
    ("defender", 6, 5), ("defender", 7, 5),
    ("defender", 4, 4), ("defender", 4, 6),
    ("defender", 6, 4), ("defender", 6, 6),
    # Attackers
    ("attacker", 1, 3), ("attacker", 1, 4),
    ("attacker", 1, 5), ("attacker", 1, 6),
    ("attacker", 1, 7), ("attacker", 2, 5),
    ("attacker", 9, 3), ("attacker", 9, 4),
    ("attacker", 9, 5), ("attacker", 9, 6),
    ("attacker", 9, 7), ("attacker", 8, 5),
    ("attacker", 3, 1), ("attacker", 4, 1),
    ("attacker", 5, 1), ("attacker", 6, 1),
    ("attacker", 7, 1), ("attacker", 5, 2),
    ("attacker", 3, 9), ("attacker", 4, 9),
    ("attacker", 5, 9), ("attacker", 6, 9),
    ("attacker", 7, 9), ("attacker", 5, 8),
]

def initial_board():
    return [list(p) for p in INITIAL_PIECES]

def inside_board(r, c):
    return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE

def king_position(board):
    for p in board:
        if p[0] == "king":
            return p[1], p[2]
    return None, None

def piece_at(board, r, c):
    for p in board:
        if p[1] == r and p[2] == c:
            return p[0]
    return None

def empty_cell(board, r, c):
    return inside_board(r, c) and piece_at(board, r, c) is None

def player_pieces(board, player):
    if player == "attacker":
        return [(p[1], p[2]) for p in board if p[0] == "attacker"]
    else:
        return [(p[1], p[2]) for p in board if p[0] in ("defender", "king")]

def clear_path(board, r1, c1, r2, c2):
    sr = 0 if r1 == r2 else (1 if r2 > r1 else -1)
    sc = 0 if c1 == c2 else (1 if c2 > c1 else -1)
    r, c = r1 + sr, c1 + sc
    while (r, c) != (r2, c2):
        if not empty_cell(board, r, c):
            return False
        r += sr
        c += sc
    return True

def valid_moves_for(board, player):
    moves = []
    for r1, c1 in player_pieces(board, player):
        for r2 in range(1, BOARD_SIZE+1):
            if r2 != r1 and empty_cell(board, r2, c1) and clear_path(board, r1, c1, r2, c1):
                moves.append((r1, c1, r2, c1))
        for c2 in range(1, BOARD_SIZE+1):
            if c2 != c1 and empty_cell(board, r1, c2) and clear_path(board, r1, c1, r1, c2):
                moves.append((r1, c1, r1, c2))
    return moves

def is_anvil(board, r, c, enemy):
    t = piece_at(board, r, c)
    if enemy == "attacker":
        return t in ("defender", "king") or (r, c) == THRONE or (r, c) in CORNERS
    else:
        return t == "attacker" or (r, c) == THRONE or (r, c) in CORNERS

def apply_move(board, r1, c1, r2, c2):
    board = copy.deepcopy(board)
    moving = None
    for p in board:
        if p[1] == r1 and p[2] == c1:
            moving = p
            break
    moving[1], moving[2] = r2, c2
    mover_type = moving[0]
    enemy = "defender" if mover_type == "attacker" else "attacker"
    to_remove = []
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r2+dr, c2+dc
        ep = piece_at(board, nr, nc)
        if ep is None:
            continue
        if (enemy == "defender" and ep in ("defender","king")) or (enemy == "attacker" and ep == "attacker"):
            or_, oc = nr+(nr-r2), nc+(nc-c2)
            if inside_board(or_, oc) and is_anvil(board, or_, oc, enemy):
                to_remove.append((nr, nc))
    board = [p for p in board if (p[1], p[2]) not in to_remove]
    return board

def is_wall(r, c):
    return r == 1 or r == BOARD_SIZE or c == 1 or c == BOARD_SIZE

def is_corner_adjacent(r, c):
    return (r in (1, BOARD_SIZE)) and (c in (1, BOARD_SIZE))

def king_surrounded(board):
    kr, kc = king_position(board)
    if kr is None: return False
    if is_corner_adjacent(kr, kc):
        required = 2
    elif is_wall(kr, kc):
        required = 3
    else:
        required = 4
    blocked = sum(
        1 for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
        if piece_at(board, kr+dr, kc+dc) == "attacker"
    )
    return blocked >= required

def terminal(board):
    kr, kc = king_position(board)
    if kr is None:
        return "attacker"
    if (kr, kc) in CORNERS:
        return "defender"
    if king_surrounded(board):
        return "attacker"
    return None

# ══════════════════════════════════════════════
#  UTILITY + ALPHA-BETA
# ══════════════════════════════════════════════

DEPTH_MAP = {"easy": 1, "medium": 3, "hard": 5}

def nearest_corner_dist(kr, kc):
    return min(abs(kr-r)+abs(kc-c) for r,c in [(1,1),(1,9),(9,1),(9,9)])

def utility(board):
    w = terminal(board)
    if w == "attacker": return 10000
    if w == "defender": return -10000
    num_a = sum(1 for p in board if p[0] == "attacker")
    num_d = sum(1 for p in board if p[0] in ("defender","king"))
    kr, kc = king_position(board)
    dist = nearest_corner_dist(kr, kc) if kr else 16
    adj_a = sum(1 for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)] if piece_at(board,kr+dr,kc+dc)=="attacker") if kr else 0
    adj_d = sum(1 for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)] if piece_at(board,kr+dr,kc+dc) in ("defender","king")) if kr else 0
    piece_score  = (num_a * 10) - (num_d * 15)
    dist_score   = dist * 5
    protect_score = (adj_a * 20) - (adj_d * 10)
    return piece_score + dist_score + protect_score

def alphabeta(board, depth, alpha, beta, player):
    w = terminal(board)
    if w or depth == 0:
        return None, utility(board)
    opponent = "defender" if player == "attacker" else "attacker"
    moves = valid_moves_for(board, player)
    if not moves:
        return None, utility(board)
    best_move = None
    if player == "attacker":
        best_val = -99999
        for m in moves:
            nb = apply_move(board, *m)
            _, val = alphabeta(nb, depth-1, alpha, beta, opponent)
            if val > best_val:
                best_val, best_move = val, m
            alpha = max(alpha, best_val)
            if alpha >= beta:
                break
    else:
        best_val = 99999
        for m in moves:
            nb = apply_move(board, *m)
            _, val = alphabeta(nb, depth-1, alpha, beta, opponent)
            if val < best_val:
                best_val, best_move = val, m
            beta = min(beta, best_val)
            if beta <= alpha:
                break
    return best_move, best_val

def best_move(board, depth, player):
    move, _ = alphabeta(board, depth, -99999, 99999, player)
    return move

# ══════════════════════════════════════════════
#  GUI
# ══════════════════════════════════════════════

# Palette
BG          = "#1a1a2e"
PANEL_BG    = "#16213e"
BOARD_DARK  = "#2d1b69"
BOARD_LIGHT = "#1a1258"
CELL_NORMAL = "#1e1e4a"
THRONE_CLR  = "#4a0e8f"
CORNER_CLR  = "#0d3d6e"
HIGHLIGHT   = "#00d4ff"
VALID_CLR   = "#00ff88"
ATTACKER    = "#e63946"
DEFENDER    = "#4cc9f0"
KING_CLR    = "#ffd60a"
TEXT_CLR    = "#e0e0ff"
ACCENT      = "#7b2fff"
BTN_BG      = "#2d2d6e"
BTN_HOVER   = "#4a4aaa"

CELL_SIZE = 62
PADDING   = 40

class HnefataflGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hnefatafl")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.board       = initial_board()
        self.current     = "attacker"
        self.selected    = None
        self.valid_dests = []
        self.mode        = None   # "cpu" or "multiplayer"
        self.human_side  = None
        self.depth       = 1
        self.game_over   = False
        self.thinking    = False

        self._build_menu()

    # ── Menu Screen ─────────────────────────────────
    def _build_menu(self):
        self._clear_window()
        f = tk.Frame(self.root, bg=BG, padx=60, pady=40)
        f.pack(expand=True, fill="both")

        tk.Label(f, text="HNEFATAFL", font=("Georgia", 38, "bold"),
                 fg=KING_CLR, bg=BG).pack(pady=(0,4))
        tk.Label(f, text="The Viking Board Game", font=("Georgia", 14, "italic"),
                 fg=ACCENT, bg=BG).pack(pady=(0,30))

        tk.Label(f, text="Game Mode", font=("Helvetica", 13, "bold"),
                 fg=TEXT_CLR, bg=BG).pack()

        self._btn(f, "⚔  Human vs Computer", self._show_cpu_opts)
        self._btn(f, "⚔  Multiplayer (2 Players)", self._start_multiplayer)

        tk.Label(f, text="", bg=BG).pack()
        tk.Label(f, text="Attackers (A) surround the King.\nDefenders (D) escort the King to a corner.",
                 font=("Helvetica", 10), fg="#8888aa", bg=BG, justify="center").pack()

    def _show_cpu_opts(self):
        self._clear_window()
        f = tk.Frame(self.root, bg=BG, padx=60, pady=40)
        f.pack(expand=True, fill="both")

        tk.Label(f, text="Choose Difficulty", font=("Georgia", 22, "bold"),
                 fg=KING_CLR, bg=BG).pack(pady=(0,20))

        for d in ("easy","medium","hard"):
            label = {"easy":"🟢  Easy","medium":"🟡  Medium","hard":"🔴  Hard"}[d]
            self._btn(f, label, lambda d=d: self._show_side_opts(d))

        self._btn(f, "← Back", self._build_menu, color="#555577")

    def _show_side_opts(self, difficulty):
        self.depth = DEPTH_MAP[difficulty]
        self._clear_window()
        f = tk.Frame(self.root, bg=BG, padx=60, pady=40)
        f.pack(expand=True, fill="both")

        tk.Label(f, text="Choose Your Side", font=("Georgia", 22, "bold"),
                 fg=KING_CLR, bg=BG).pack(pady=(0,20))

        self._btn(f, "🔴  Attackers  (go first)", lambda: self._start_cpu("attacker"))
        self._btn(f, "🔵  Defenders  (King's side)", lambda: self._start_cpu("defender"))
        self._btn(f, "← Back", lambda: self._show_cpu_opts())

    def _btn(self, parent, text, cmd, color=BTN_BG):
        b = tk.Button(parent, text=text, command=cmd,
                      bg=color, fg=TEXT_CLR, font=("Helvetica", 12, "bold"),
                      relief="flat", bd=0, padx=20, pady=10,
                      activebackground=BTN_HOVER, activeforeground="white",
                      cursor="hand2")
        b.pack(fill="x", pady=5)
        return b

    def _clear_window(self):
        for w in self.root.winfo_children():
            w.destroy()

    # ── Start Game ───────────────────────────────────
    def _start_cpu(self, human_side):
        self.mode       = "cpu"
        self.human_side = human_side
        self._start_game()

    def _start_multiplayer(self):
        self.mode       = "multiplayer"
        self.human_side = None
        self.depth      = 0
        self._start_game()

    def _start_game(self):
        self.board       = initial_board()
        self.current     = "attacker"
        self.selected    = None
        self.valid_dests = []
        self.game_over   = False
        self.thinking    = False
        self._build_game_ui()
        if self.mode == "cpu" and self.human_side != self.current:
            self.root.after(400, self._cpu_move)

    # ── Game UI ──────────────────────────────────────
    def _build_game_ui(self):
        self._clear_window()
        W = CELL_SIZE * BOARD_SIZE + PADDING * 2
        H = CELL_SIZE * BOARD_SIZE + PADDING * 2 + 120

        self.root.geometry(f"{W + 220}x{H}")

        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True)

        # Canvas
        canvas_frame = tk.Frame(main, bg=BG)
        canvas_frame.pack(side="left", padx=(20,0), pady=20)

        self.canvas = tk.Canvas(canvas_frame,
                                width=CELL_SIZE*BOARD_SIZE+PADDING*2,
                                height=CELL_SIZE*BOARD_SIZE+PADDING*2,
                                bg=BG, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_click)

        # Side panel
        side = tk.Frame(main, bg=PANEL_BG, width=200, padx=15, pady=20)
        side.pack(side="left", fill="y", padx=15, pady=20)
        side.pack_propagate(False)

        tk.Label(side, text="HNEFATAFL", font=("Georgia", 14, "bold"),
                 fg=KING_CLR, bg=PANEL_BG).pack(pady=(0,5))

        self.turn_label = tk.Label(side, text="", font=("Helvetica", 11, "bold"),
                                   fg=TEXT_CLR, bg=PANEL_BG, wraplength=170)
        self.turn_label.pack(pady=5)

        tk.Frame(side, bg=ACCENT, height=1).pack(fill="x", pady=8)

        tk.Label(side, text="LEGEND", font=("Helvetica", 9, "bold"),
                 fg="#8888aa", bg=PANEL_BG).pack()

        legend = [
            (ATTACKER, "A", "Attacker"),
            (DEFENDER, "D", "Defender"),
            (KING_CLR, "K", "King"),
            (THRONE_CLR, "T", "Throne"),
            (CORNER_CLR, "*", "Corner"),
            (VALID_CLR, "●", "Valid move"),
            (HIGHLIGHT, "■", "Selected"),
        ]
        for color, sym, desc in legend:
            row = tk.Frame(side, bg=PANEL_BG)
            row.pack(anchor="w", pady=1)
            tk.Label(row, text=sym, font=("Helvetica", 11, "bold"),
                     fg=color, bg=PANEL_BG, width=3).pack(side="left")
            tk.Label(row, text=desc, font=("Helvetica", 9),
                     fg="#aaaacc", bg=PANEL_BG).pack(side="left")

        tk.Frame(side, bg=ACCENT, height=1).pack(fill="x", pady=8)

        self.score_label = tk.Label(side, text="", font=("Helvetica", 9),
                                    fg="#aaaacc", bg=PANEL_BG, justify="left")
        self.score_label.pack()

        tk.Frame(side, bg=PANEL_BG).pack(expand=True)

        self._btn(side, "🏠 Menu", self._build_menu, "#333355")
        self._btn(side, "↺ Restart", self._start_game, "#333355")

        self.status_label = tk.Label(side, text="", font=("Helvetica", 10),
                                     fg="#ffcc00", bg=PANEL_BG, wraplength=170)
        self.status_label.pack(pady=5)

        self._draw_board()
        self._update_labels()

    def _draw_board(self):
        self.canvas.delete("all")
        p = PADDING

        # Board background
        self.canvas.create_rectangle(p-4, p-4,
                                     p+CELL_SIZE*BOARD_SIZE+4,
                                     p+CELL_SIZE*BOARD_SIZE+4,
                                     fill="#0d0d2e", outline=ACCENT, width=2)

        # Column / Row labels
        for i in range(BOARD_SIZE):
            x = p + i*CELL_SIZE + CELL_SIZE//2
            y = p - 16
            self.canvas.create_text(x, y, text=str(i+1),
                                    font=("Helvetica", 9), fill="#666688")
            y2 = p + BOARD_SIZE*CELL_SIZE + 16
            self.canvas.create_text(x, y2, text=str(i+1),
                                    font=("Helvetica", 9), fill="#666688")
        for i in range(BOARD_SIZE):
            y = p + i*CELL_SIZE + CELL_SIZE//2
            self.canvas.create_text(p-16, y, text=str(i+1),
                                    font=("Helvetica", 9), fill="#666688")
            self.canvas.create_text(p+BOARD_SIZE*CELL_SIZE+16, y, text=str(i+1),
                                    font=("Helvetica", 9), fill="#666688")

        # Cells
        for r in range(1, BOARD_SIZE+1):
            for c in range(1, BOARD_SIZE+1):
                x1 = p + (c-1)*CELL_SIZE
                y1 = p + (r-1)*CELL_SIZE
                x2, y2 = x1+CELL_SIZE, y1+CELL_SIZE
                cx, cy = x1+CELL_SIZE//2, y1+CELL_SIZE//2

                # Cell background
                if self.selected == (r,c):
                    fill = HIGHLIGHT
                elif (r,c) in self.valid_dests:
                    fill = "#1a3a1a"
                elif (r,c) in CORNERS:
                    fill = CORNER_CLR
                elif (r,c) == THRONE:
                    fill = THRONE_CLR
                else:
                    fill = CELL_NORMAL

                self.canvas.create_rectangle(x1+1, y1+1, x2-1, y2-1,
                                             fill=fill, outline="#2a2a5a", width=1)

                # Valid move dots
                if (r,c) in self.valid_dests and self.selected:
                    self.canvas.create_oval(cx-8, cy-8, cx+8, cy+8,
                                            fill=VALID_CLR, outline="", stipple="")

                # Special square labels
                if (r,c) in CORNERS:
                    self.canvas.create_text(cx, cy, text="✦",
                                            font=("Helvetica", 14), fill="#6ab4ff")
                elif (r,c) == THRONE and not piece_at(self.board, r, c):
                    self.canvas.create_text(cx, cy, text="⊕",
                                            font=("Helvetica", 16), fill="#bb88ff")

        # Pieces
        for piece in self.board:
            typ, r, c = piece[0], piece[1], piece[2]
            x1 = p + (c-1)*CELL_SIZE
            y1 = p + (r-1)*CELL_SIZE
            cx = x1 + CELL_SIZE//2
            cy = y1 + CELL_SIZE//2

            if typ == "king":
                # Crown shape
                rad = CELL_SIZE//2 - 6
                self.canvas.create_oval(cx-rad, cy-rad, cx+rad, cy+rad,
                                        fill="#aa8800", outline=KING_CLR, width=3)
                self.canvas.create_text(cx, cy, text="♛",
                                        font=("Helvetica", 20), fill=KING_CLR)
            elif typ == "defender":
                rad = CELL_SIZE//2 - 8
                self.canvas.create_oval(cx-rad, cy-rad, cx+rad, cy+rad,
                                        fill="#1a4a6a", outline=DEFENDER, width=2)
                self.canvas.create_text(cx, cy, text="D",
                                        font=("Helvetica", 11, "bold"), fill=DEFENDER)
            elif typ == "attacker":
                rad = CELL_SIZE//2 - 8
                self.canvas.create_rectangle(cx-rad, cy-rad, cx+rad, cy+rad,
                                             fill="#5a1a1a", outline=ATTACKER, width=2)
                self.canvas.create_text(cx, cy, text="A",
                                        font=("Helvetica", 11, "bold"), fill=ATTACKER)

    def _update_labels(self):
        side_name = {"attacker":"⚔ Attackers (A)", "defender":"🛡 Defenders (D)"}
        if self.game_over:
            return
        if self.mode == "cpu":
            human_tag = "(YOU)" if self.current == self.human_side else "(CPU)"
        else:
            human_tag = ""
        self.turn_label.config(
            text=f"Turn: {side_name[self.current]}\n{human_tag}"
        )
        num_a = sum(1 for p in self.board if p[0]=="attacker")
        num_d = sum(1 for p in self.board if p[0] in ("defender","king"))
        self.score_label.config(
            text=f"Attackers:  {num_a}\nDefenders: {num_d}"
        )

    # ── Click Handler ────────────────────────────────
    def _on_click(self, event):
        if self.game_over or self.thinking:
            return
        if self.mode == "cpu" and self.current != self.human_side:
            return

        p = PADDING
        c = (event.x - p) // CELL_SIZE + 1
        r = (event.y - p) // CELL_SIZE + 1
        if not inside_board(r, c):
            return

        if self.selected:
            if (r, c) in self.valid_dests:
                self._make_move(self.selected[0], self.selected[1], r, c)
                return
            # deselect or reselect
            self.selected    = None
            self.valid_dests = []

        # Try to select
        typ = piece_at(self.board, r, c)
        if typ and self._belongs_to(typ, self.current):
            self.selected    = (r, c)
            self.valid_dests = self._calc_valid_dests(r, c)
        self._draw_board()

    def _belongs_to(self, typ, player):
        if player == "attacker":
            return typ == "attacker"
        return typ in ("defender", "king")

    def _calc_valid_dests(self, r, c):
        dests = []
        for r2 in range(1, BOARD_SIZE+1):
            if r2 != r and empty_cell(self.board, r2, c) and clear_path(self.board, r, c, r2, c):
                dests.append((r2, c))
        for c2 in range(1, BOARD_SIZE+1):
            if c2 != c and empty_cell(self.board, r, c2) and clear_path(self.board, r, c, r, c2):
                dests.append((r, c2))
        return dests

    def _make_move(self, r1, c1, r2, c2):
        self.board       = apply_move(self.board, r1, c1, r2, c2)
        self.selected    = None
        self.valid_dests = []
        self._draw_board()

        winner = terminal(self.board)
        if winner:
            self._announce(winner)
            return

        # Switch turn
        self.current = "defender" if self.current == "attacker" else "attacker"
        self._update_labels()

        if self.mode == "cpu" and self.current != self.human_side:
            self.root.after(300, self._cpu_move)

    def _cpu_move(self):
        if self.game_over:
            return
        self.thinking = True
        self.status_label.config(text="🤖 CPU thinking...")
        self.root.update()

        def run():
            move = best_move(self.board, self.depth, self.current)
            self.root.after(0, lambda: self._apply_cpu_move(move))

        threading.Thread(target=run, daemon=True).start()

    def _apply_cpu_move(self, move):
        self.thinking = False
        self.status_label.config(text="")
        if move:
            r1, c1, r2, c2 = move
            self._make_move(r1, c1, r2, c2)
        else:
            # No moves — opponent wins
            w = "defender" if self.current == "attacker" else "attacker"
            self._announce(w)

    def _announce(self, winner):
        self.game_over = True
        if winner == "defender":
            msg = "🏆 Defenders WIN!\nThe King reached a corner!"
            self.turn_label.config(text="👑 Defenders WIN!", fg=DEFENDER)
        else:
            msg = "⚔ Attackers WIN!\nThe King was captured!"
            self.turn_label.config(text="⚔ Attackers WIN!", fg=ATTACKER)
        self.root.after(200, lambda: messagebox.showinfo("Game Over", msg))


def main():
    root = tk.Tk()
    root.configure(bg=BG)
    # Center window roughly
    root.geometry("540x480")
    root.update_idletasks()
    x = (root.winfo_screenwidth()  - root.winfo_reqwidth())  // 2
    y = (root.winfo_screenheight() - root.winfo_reqheight()) // 2
    root.geometry(f"+{x}+{y}")

    app = HnefataflGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()