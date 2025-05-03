# ... (Keep all code before update_display the same) ...

def update_display(self):
        """Updates the board display, last move, selection, and captured pieces."""
        piece_symbols = {'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
                         'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'}
        piece_colors = {'white': '#FFFFFF', 'black': '#000000'}

        # Ensure widgets and board exist before updating
        if not self.squares or not self.squares[0][0] or not self.board:
             # print("Warning: Attempted update_display before full initialization.") # Optional debug
             return

        # 1. Reset backgrounds
        for r in range(8):
            for c in range(8):
                if self.squares[r][c]:
                    original_bg = self.light_color if (r + c) % 2 == 0 else self.dark_color
                    try: self.squares[r][c].config(bg=original_bg)
                    except tk.TclError: pass

        # 2. Highlight last move
        if self.last_move:
            from_r, from_c, to_r, to_c, _ = self.last_move
            # Check if squares exist before accessing them
            if 0 <= from_r < 8 and 0 <= from_c < 8 and self.squares[from_r][from_c]:
                try: self.squares[from_r][from_c].config(bg=self.last_move_from_color)
                except tk.TclError: pass
            if 0 <= to_r < 8 and 0 <= to_c < 8 and self.squares[to_r][to_c]:
                 try: self.squares[to_r][to_c].config(bg=self.last_move_to_color)
                 except tk.TclError: pass

        # 3. Highlight selection
        if self.selected_piece:
            sel_r, sel_c = self.selected_piece
            if 0 <= sel_r < 8 and 0 <= sel_c < 8 and self.squares[sel_r][sel_c]:
                try: self.squares[sel_r][sel_c].config(bg=self.highlight_color)
                except tk.TclError: pass

        # 4. Set piece symbols
        for row in range(8):
            for col in range(8):
                square_button = self.squares[row][col]
                if not square_button: continue
                piece = self.board[row][col] # Read from self.board
                text_symbol = ''
                text_color = 'black'
                if piece:
                    color, piece_type = piece
                    symbol_key = piece_type.upper() if color == 'white' else piece_type.lower()
                    text_symbol = piece_symbols.get(symbol_key, '?')
                    text_color = piece_colors.get(color, 'black')
                try:
                    square_button.config(font=self.piece_font, text=text_symbol, fg=text_color)
                except tk.TclError: pass

        # 5. Update Captured Pieces
        white_captures_text = ""
        value_diff_white = 0
        black_captures_text = ""
        value_diff_black = 0

        # Ensure captured_pieces is initialized
        if self.captured_pieces:
            # White captures (black pieces)
            for cap_color, cap_type in self.captured_pieces.get('white', []):
                symbol_key = cap_type.lower()
                white_captures_text += piece_symbols.get(symbol_key, '?') + " "
                value_diff_white += self.piece_values.get(cap_type, 0)

            # Black captures (white pieces)
            for cap_color, cap_type in self.captured_pieces.get('black', []):
                symbol_key = cap_type.upper()
                black_captures_text += piece_symbols.get(symbol_key, '?') + " "
                value_diff_black += self.piece_values.get(cap_type, 0)

            # Calculate and add material difference
            diff = value_diff_white - value_diff_black
            if diff > 0: white_captures_text += f"\n+{diff}"
            elif diff < 0: black_captures_text += f"\n+{-diff}"

            # Update labels (with try-except for safety)
            if self.white_captured_label:
                 try:
                     self.white_captured_label.config(text=white_captures_text.strip())
                 except tk.TclError:
                     pass
            if self.black_captured_label:
                 try:
                     self.black_captured_label.config(text=black_captures_text.strip())
                 except tk.TclError:
                     pass
        else:
             # Clear capture labels if captured_pieces is None (e.g., during initial setup)
             # --- CORRECTED SYNTAX ---
             if self.white_captured_label:
                 try:
                     self.white_captured_label.config(text="")
                 except tk.TclError:
                     pass # Ignore if widget destroyed during reset/close
             if self.black_captured_label:
                 try:
                     self.black_captured_label.config(text="")
                 except tk.TclError:
                     pass # Ignore if widget destroyed during reset/close
             # --- END CORRECTION ---

# ... (Keep all code after update_display the same) ...

# Full corrected class (only update_display changed significantly from last version)

import tkinter as tk
from tkinter import messagebox
import tkinter.font as tkFont
import random
import time # For debouncing resize
import copy # For deep copying board state during simulation

class ChessGame:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Resizable Elegant Chess Game")
        self.window.minsize(360, 300)

        # --- Visual Enhancements ---
        self.initial_font_size = 16
        self.piece_font = tkFont.Font(family="Arial Unicode MS", size=self.initial_font_size, weight="bold")
        self.capture_font = tkFont.Font(family="Arial Unicode MS", size=max(8, self.initial_font_size - 4), weight="normal")

        self.light_color = '#E8E8E8'
        self.dark_color = '#7C9A7C'
        self.highlight_color = '#FFFF99'
        self.last_move_from_color = '#AEC6CF'
        self.last_move_to_color = '#B3E0B3'
        self.capture_bg_color = '#F0F0F0'

        # --- Piece Values ---
        self.piece_values = { 'P': 100, 'N': 300, 'B': 310, 'R': 500, 'Q': 900, 'K': 10000 }
        self.CHECKMATE_SCORE = 20000
        self.CHECK_SCORE = 50
        self.CASTLE_SCORE = 40

        # --- Initial Game State Setup ---
        self.board = None
        self.selected_piece = None
        self.is_player_turn = True
        self.last_move = None
        self.castling_rights = None
        self.captured_pieces = None
        self.squares = [] # Initialize squares list

        # --- Window and Frame Setup ---
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)

        self.main_frame = tk.Frame(self.window, padx=5, pady=5)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=0, minsize=40)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(2, weight=0, minsize=40)

        # --- Capture Display Areas ---
        self.left_capture_frame = tk.Frame(self.main_frame, bg=self.capture_bg_color, padx=3, pady=3)
        self.left_capture_frame.grid(row=0, column=0, sticky="ns", padx=(0, 3))
        self.white_captured_label = tk.Label(self.left_capture_frame, text="", font=self.capture_font,
                                             justify=tk.LEFT, anchor='nw', wraplength=35,
                                             bg=self.capture_bg_color)
        self.white_captured_label.pack(fill=tk.BOTH, expand=True)

        self.right_capture_frame = tk.Frame(self.main_frame, bg=self.capture_bg_color, padx=3, pady=3)
        self.right_capture_frame.grid(row=0, column=2, sticky="ns", padx=(3, 0))
        self.black_captured_label = tk.Label(self.right_capture_frame, text="", font=self.capture_font,
                                              justify=tk.LEFT, anchor='nw', wraplength=35,
                                              bg=self.capture_bg_color)
        self.black_captured_label.pack(fill=tk.BOTH, expand=True)

        # --- Board Frame ---
        self.board_frame = tk.Frame(self.main_frame)
        self.board_frame.grid(row=0, column=1, sticky="nsew")
        for i in range(8):
            self.board_frame.grid_rowconfigure(i, weight=1, uniform="group1")
            self.board_frame.grid_columnconfigure(i, weight=1, uniform="group1")

        self.create_board_widgets() # Create the button widgets
        self.reset_game()          # Initialize game state and display

        # --- Resize Handling ---
        self._resize_job = None
        self.board_frame.bind("<Configure>", self.schedule_resize)

        self.window.mainloop()

    def reset_game(self):
        """Resets the game to the initial state."""
        print("Resetting game...")
        self.board = self.initialize_board()
        self.selected_piece = None
        self.is_player_turn = True
        self.last_move = None
        self.castling_rights = {
            'white': {'kingside': True, 'queenside': True},
            'black': {'kingside': True, 'queenside': True}
        }
        self.captured_pieces = {'white': [], 'black': []}

        # Re-enable all squares if they exist
        if self.squares:
            for r in range(8):
                for c in range(8):
                    if self.squares[r][c]:
                        try:
                            self.squares[r][c].config(state=tk.NORMAL)
                        except tk.TclError: pass # Ignore if widget destroyed

        self.update_display() # Update display with the new board state

    def create_board_widgets(self):
        """Creates the Tkinter Button widgets for the board squares."""
        if not self.squares:
            self.squares = [[None for _ in range(8)] for _ in range(8)]
            colors = [self.light_color, self.dark_color]
            for row in range(8):
                for col in range(8):
                    color = colors[(row + col) % 2]
                    square = tk.Button(self.board_frame, bg=color, font=self.piece_font,
                                     borderwidth=0, relief="flat",
                                     command=lambda r=row, c=col: self.square_clicked(r, c))
                    square.grid(row=row, column=col, sticky="nsew")
                    self.squares[row][col] = square

    def initialize_board(self):
        board = [[None for _ in range(8)] for _ in range(8)]
        piece_order = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        for col in range(8):
            board[0][col] = ('black', piece_order[col])
            board[1][col] = ('black', 'P')
        for col in range(8):
            board[6][col] = ('white', 'P')
            board[7][col] = ('white', piece_order[col])
        return board

    def schedule_resize(self, event):
        if self._resize_job:
            self.window.after_cancel(self._resize_job)
        self._resize_job = self.window.after(150, lambda e=event: self.on_resize(e))

    def on_resize(self, event):
        self._resize_job = None
        new_size = min(event.width, event.height) // 8
        if new_size < 8: return

        new_font_size = max(6, int(new_size * 0.6))
        new_capture_font_size = max(5, int(new_font_size * 0.75))

        try:
            self.piece_font.configure(size=new_font_size)
            self.capture_font.configure(size=new_capture_font_size)
        except tk.TclError as e:
            print(f"Error configuring font: {e}")
            return
        self.update_display()

    def update_display(self):
        """Updates the board display, last move, selection, and captured pieces."""
        piece_symbols = {'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
                         'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'}
        piece_colors = {'white': '#FFFFFF', 'black': '#000000'}

        # Ensure widgets and board exist before updating
        if not self.squares or not self.squares[0][0] or not self.board:
             # print("Warning: Attempted update_display before full initialization.") # Optional debug
             return

        # 1. Reset backgrounds
        for r in range(8):
            for c in range(8):
                if self.squares[r][c]:
                    original_bg = self.light_color if (r + c) % 2 == 0 else self.dark_color
                    try: self.squares[r][c].config(bg=original_bg)
                    except tk.TclError: pass

        # 2. Highlight last move
        if self.last_move:
            from_r, from_c, to_r, to_c, _ = self.last_move
            # Check if squares exist before accessing them
            if 0 <= from_r < 8 and 0 <= from_c < 8 and self.squares[from_r][from_c]:
                try: self.squares[from_r][from_c].config(bg=self.last_move_from_color)
                except tk.TclError: pass
            if 0 <= to_r < 8 and 0 <= to_c < 8 and self.squares[to_r][to_c]:
                 try: self.squares[to_r][to_c].config(bg=self.last_move_to_color)
                 except tk.TclError: pass

        # 3. Highlight selection
        if self.selected_piece:
            sel_r, sel_c = self.selected_piece
            if 0 <= sel_r < 8 and 0 <= sel_c < 8 and self.squares[sel_r][sel_c]:
                try: self.squares[sel_r][sel_c].config(bg=self.highlight_color)
                except tk.TclError: pass

        # 4. Set piece symbols
        for row in range(8):
            for col in range(8):
                square_button = self.squares[row][col]
                if not square_button: continue
                piece = self.board[row][col] # Read from self.board
                text_symbol = ''
                text_color = 'black'
                if piece:
                    color, piece_type = piece
                    symbol_key = piece_type.upper() if color == 'white' else piece_type.lower()
                    text_symbol = piece_symbols.get(symbol_key, '?')
                    text_color = piece_colors.get(color, 'black')
                try:
                    square_button.config(font=self.piece_font, text=text_symbol, fg=text_color)
                except tk.TclError: pass

        # 5. Update Captured Pieces
        white_captures_text = ""
        value_diff_white = 0
        black_captures_text = ""
        value_diff_black = 0

        # Ensure captured_pieces is initialized
        if self.captured_pieces:
            # White captures (black pieces)
            for cap_color, cap_type in self.captured_pieces.get('white', []):
                symbol_key = cap_type.lower()
                white_captures_text += piece_symbols.get(symbol_key, '?') + " "
                value_diff_white += self.piece_values.get(cap_type, 0)

            # Black captures (white pieces)
            for cap_color, cap_type in self.captured_pieces.get('black', []):
                symbol_key = cap_type.upper()
                black_captures_text += piece_symbols.get(symbol_key, '?') + " "
                value_diff_black += self.piece_values.get(cap_type, 0)

            # Calculate and add material difference
            diff = value_diff_white - value_diff_black
            if diff > 0: white_captures_text += f"\n+{diff}"
            elif diff < 0: black_captures_text += f"\n+{-diff}"

            # Update labels (with try-except for safety)
            if self.white_captured_label:
                 try:
                     self.white_captured_label.config(text=white_captures_text.strip())
                 except tk.TclError:
                     pass
            if self.black_captured_label:
                 try:
                     self.black_captured_label.config(text=black_captures_text.strip())
                 except tk.TclError:
                     pass
        else:
             # Clear capture labels if captured_pieces is None (e.g., during initial setup)
             # --- CORRECTED SYNTAX ---
             if self.white_captured_label:
                 try:
                     self.white_captured_label.config(text="")
                 except tk.TclError:
                     pass # Ignore if widget destroyed during reset/close
             if self.black_captured_label:
                 try:
                     self.black_captured_label.config(text="")
                 except tk.TclError:
                     pass # Ignore if widget destroyed during reset/close
             # --- END CORRECTION ---


    def square_clicked(self, row, col):
        if not self.is_player_turn: return
        try:
            if self.squares[row][col].cget('state') == tk.DISABLED:
                return
        except (tk.TclError, IndexError, AttributeError):
             return

        current_piece = self.board[row][col]

        if self.selected_piece:
            old_row, old_col = self.selected_piece
            if (row, col) == (old_row, old_col):
                self.selected_piece = None
                self.update_display()
                return

            if self.is_valid_move(old_row, old_col, row, col):
                self.make_move(old_row, old_col, row, col)
                self.selected_piece = None
                self.update_display()
                if not self.check_game_over(): # Check game over *after* player move
                    self.is_player_turn = False
                    self.window.after(250, self.make_bot_move) # Schedule bot move
            elif current_piece and current_piece[0] == 'white':
                self.selected_piece = (row, col)
                self.update_display()
            else:
                 self.selected_piece = None
                 self.update_display()

        elif current_piece and current_piece[0] == 'white':
            self.selected_piece = (row, col)
            self.update_display()

    def make_move(self, from_row, from_col, to_row, to_col, is_simulation=False):
        piece = self.board[from_row][from_col]
        if not piece: return None
        color, piece_type = piece
        moving_color = color

        captured_piece = self.board[to_row][to_col]

        original_castling_rights = copy.deepcopy(self.castling_rights) if is_simulation else None
        original_last_move = self.last_move if is_simulation else None
        en_passant_capture_details = None
        castling_rook_move_details = None

        if piece_type == 'K':
            self.castling_rights[color]['kingside'] = False; self.castling_rights[color]['queenside'] = False
        elif piece_type == 'R':
            start_row = 7 if color == 'white' else 0
            if from_row == start_row:
                if from_col == 0: self.castling_rights[color]['queenside'] = False
                elif from_col == 7: self.castling_rights[color]['kingside'] = False
        if captured_piece:
             cap_color, cap_type = captured_piece; cap_start_row = 7 if cap_color == 'white' else 0
             if cap_type == 'R' and to_row == cap_start_row:
                 if to_col == 0: self.castling_rights[cap_color]['queenside'] = False
                 elif to_col == 7: self.castling_rights[cap_color]['kingside'] = False

        en_passant_capture_made = False
        if piece_type == 'P' and abs(from_col - to_col) == 1 and captured_piece is None:
            potential_ep_pawn_row = from_row
            potential_ep_pawn_col = to_col

            if 0 <= potential_ep_pawn_row < 8 and 0 <= potential_ep_pawn_col < 8:
                 ep_captured_pawn = self.board[potential_ep_pawn_row][potential_ep_pawn_col]
                 if self.last_move and ep_captured_pawn and ep_captured_pawn[0] != color and ep_captured_pawn[1] == 'P':
                     lm_from_r, lm_from_c, lm_to_r, lm_to_c, lm_piece = self.last_move
                     pawn_adv_two_row = 4 if color == 'white' else 3
                     if (lm_piece == ep_captured_pawn and
                         abs(lm_from_r - lm_to_r) == 2 and lm_to_r == potential_ep_pawn_row and
                         lm_to_c == potential_ep_pawn_col and from_row == pawn_adv_two_row):
                         captured_piece = ep_captured_pawn
                         en_passant_capture_made = True
                         if is_simulation: en_passant_capture_details = (captured_piece, (potential_ep_pawn_row, potential_ep_pawn_col))
                         self.board[potential_ep_pawn_row][potential_ep_pawn_col] = None

        is_castling_move = False
        if piece_type == 'K' and abs(to_col - from_col) == 2:
            is_castling_move = True; rook_from_col = 7 if to_col > from_col else 0; rook_to_col = 5 if to_col > from_col else 3
            if 0 <= from_row < 8 and 0 <= rook_from_col < 8 and 0 <= rook_to_col < 8:
                 rook_piece = self.board[from_row][rook_from_col]
                 if is_simulation: castling_rook_move_details = (rook_piece, (from_row, rook_from_col), (from_row, rook_to_col))
                 self.board[from_row][rook_to_col] = rook_piece; self.board[from_row][rook_from_col] = None

        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None

        promoted_to = None
        promote_row = 0 if color == 'white' else 7
        if piece_type == 'P' and to_row == promote_row:
            promoted_to = 'Q'; self.board[to_row][to_col] = (color, promoted_to)

        if captured_piece and not is_simulation:
            # Ensure captured_pieces exists before appending
            if self.captured_pieces is not None:
                 self.captured_pieces[moving_color].append(captured_piece)

        if not is_simulation:
            self.last_move = (from_row, from_col, to_row, to_col, piece)

        if is_simulation:
            undo_info = { "from_pos": (from_row, from_col), "to_pos": (to_row, to_col),
                          "moved_piece": piece, "captured_piece": captured_piece if not en_passant_capture_made else None,
                          "en_passant_details": en_passant_capture_details,
                          "castling_details": castling_rook_move_details, "promoted_to": promoted_to,
                          "original_castling_rights": original_castling_rights,
                          "original_last_move": original_last_move }
            return undo_info
        else:
            return None

    def undo_move(self, undo_info):
        if not undo_info: return
        from_r, from_c = undo_info["from_pos"]; to_r, to_c = undo_info["to_pos"]
        self.board[from_r][from_c] = undo_info["moved_piece"]
        self.board[to_r][to_c] = undo_info["captured_piece"]
        if undo_info["promoted_to"]:
             color = undo_info["moved_piece"][0]; self.board[from_r][from_c] = (color, 'P')
        if undo_info["en_passant_details"]:
            ep_pawn_captured, (r_ep, c_ep) = undo_info["en_passant_details"]
            self.board[r_ep][c_ep] = ep_pawn_captured
            self.board[to_r][to_c] = None
        if undo_info["castling_details"]:
            rook_piece, (r_from, c_from), (r_to, c_to) = undo_info["castling_details"]
            self.board[r_from][c_from] = rook_piece; self.board[r_to][c_to] = None
        self.castling_rights = undo_info["original_castling_rights"]
        self.last_move = undo_info["original_last_move"]

    def evaluate_move(self, from_row, from_col, to_row, to_col):
        score = 0; bot_color = 'black'; opponent_color = 'white'
        moving_piece = self.board[from_row][from_col]
        target_piece = self.board[to_row][to_col]

        piece_to_be_captured = target_piece
        if not piece_to_be_captured and moving_piece and moving_piece[1] == 'P' and abs(from_col - to_col) == 1: # Check moving_piece exists
             ep_row, ep_col = from_row, to_col
             if 0 <= ep_row < 8 and 0 <= ep_col < 8:
                possible_ep_pawn = self.board[ep_row][ep_col]
                if possible_ep_pawn and possible_ep_pawn[0] == opponent_color and possible_ep_pawn[1] == 'P':
                     if self.last_move:
                         lm_from_r, lm_from_c, lm_to_r, lm_to_c, lm_piece = self.last_move
                         if lm_piece == possible_ep_pawn and abs(lm_from_r - lm_to_r) == 2 and lm_to_r == ep_row and lm_to_c == ep_col:
                             piece_to_be_captured = possible_ep_pawn

        if piece_to_be_captured and piece_to_be_captured[0] == opponent_color:
             score += self.piece_values.get(piece_to_be_captured[1], 0)

        undo_info = self.make_move(from_row, from_col, to_row, to_col, is_simulation=True)
        if undo_info is None: return -99999

        if self.is_checkmate(opponent_color): score += self.CHECKMATE_SCORE
        elif self.is_in_check(opponent_color): score += self.CHECK_SCORE
        # Need moving_piece again as it might have been altered by simulation (promotion)
        sim_moving_piece = self.board[to_row][to_col] # Get piece after simulation
        if sim_moving_piece and sim_moving_piece[1] == 'K' and abs(to_col - from_col) == 2:
             score += self.CASTLE_SCORE

        self.undo_move(undo_info)
        score += random.randint(0, 5)
        return score

    def make_bot_move(self):
        if self.is_player_turn: return

        possible_moves = []
        bot_color = 'black'
        for r1 in range(8):
            for c1 in range(8):
                piece = self.board[r1][c1]
                if piece and piece[0] == bot_color:
                    for r2 in range(8):
                        for c2 in range(8):
                            if self.is_valid_move(r1, c1, r2, c2):
                                possible_moves.append(((r1, c1), (r2, c2)))
        if not possible_moves:
            self.check_game_over()
            return

        scored_moves = []
        for move in possible_moves:
            (r1, c1), (r2, c2) = move
            score = self.evaluate_move(r1, c1, r2, c2)
            scored_moves.append((score, move))

        if not scored_moves:
             chosen_move = random.choice(possible_moves) if possible_moves else None
             best_score = "N/A (Fallback)"
        else:
            scored_moves.sort(key=lambda item: item[0], reverse=True)
            best_score = scored_moves[0][0]
            # Filter potentially multiple best moves
            best_score_threshold = best_score - 1 # Allow for small random variations
            best_moves = [item[1] for item in scored_moves if item[0] >= best_score_threshold]
            # Ensure best_moves is not empty
            if not best_moves:
                best_moves = [scored_moves[0][1]] # Fallback to the absolute highest score if filter is too strict
            chosen_move = random.choice(best_moves)


        if chosen_move:
            (from_row, from_col), (to_row, to_col) = chosen_move
            moving_piece = self.board[from_row][from_col] # Get piece before move
            if not moving_piece: # Should not happen if logic is correct
                print("Error: Bot chose move for empty square?")
                self.is_player_turn = True # Prevent infinite loop
                return

            moving_piece_type = moving_piece[1]
            target_desc = f"({to_row},{to_col})"
            target_piece = self.board[to_row][to_col]
            is_ep = False
            if not target_piece and moving_piece_type == 'P' and abs(from_col - to_col) == 1:
                # Check if it's a valid EP square based on last move
                if self.last_move:
                    lm_from_r, lm_from_c, lm_to_r, lm_to_c, lm_piece = self.last_move
                    if (lm_piece[1] == 'P' and abs(lm_from_r - lm_to_r) == 2 and
                        lm_to_r == from_row and lm_to_c == to_col and
                        to_row == from_row + (1 if bot_color == 'black' else -1)):
                        is_ep = True

            if target_piece: target_desc = f"x{target_piece[1]} at ({to_row},{to_col})"
            elif is_ep: target_desc += " (EP)"
            print(f"Bot moves: {moving_piece_type} ({from_row},{from_col})->{target_desc} (Score: {best_score})")

            self.make_move(from_row, from_col, to_row, to_col)
            self.update_display()
            self.is_player_turn = True
            # Check game over *after* bot move completes and turn switches
            self.check_game_over()
        else:
            self.check_game_over()


    # --- Validation/Utility/Game State functions ---
    def is_valid_move(self, from_row, from_col, to_row, to_col):
        piece_data = self.board[from_row][from_col];
        if not piece_data: return False
        color, piece_type = piece_data;
        if not (0 <= to_row < 8 and 0 <= to_col < 8): return False
        target = self.board[to_row][to_col];
        if target and target[0] == color:
             # Allow targeting rook square during castling validation
             if not (piece_type == 'K' and abs(to_col - from_col) == 2 and target[1] == 'R'):
                  return False
        valid_basic_move = False;
        if piece_type == 'P': valid_basic_move = self.is_valid_pawn_move(from_row, from_col, to_row, to_col, color)
        elif piece_type == 'R': valid_basic_move = self.is_valid_rook_move(from_row, from_col, to_row, to_col)
        elif piece_type == 'N': valid_basic_move = self.is_valid_knight_move(from_row, from_col, to_row, to_col)
        elif piece_type == 'B': valid_basic_move = self.is_valid_bishop_move(from_row, from_col, to_row, to_col)
        elif piece_type == 'Q': valid_basic_move = self.is_valid_queen_move(from_row, from_col, to_row, to_col)
        elif piece_type == 'K': valid_basic_move = self.is_valid_king_move(from_row, from_col, to_row, to_col, color)
        if not valid_basic_move: return False
        undo_info = self.make_move(from_row, from_col, to_row, to_col, is_simulation=True)
        king_in_check_after_move = False
        if undo_info:
            king_in_check_after_move = self.is_in_check(color)
            self.undo_move(undo_info)
        else: return False
        return not king_in_check_after_move

    def is_basic_move_valid(self, from_row, from_col, to_row, to_col, piece_type, color):
        target = self.board[to_row][to_col]
        if piece_type == 'P':
             direction = 1 if color == 'black' else -1
             if from_col == to_col and to_row == from_row + direction: return True
             start_row = 1 if color == 'black' else 6
             if from_row == start_row and from_col == to_col and to_row == from_row + 2 * direction: return True
             if to_row == from_row + direction and abs(to_col - from_col) == 1: return True
             return False
        elif piece_type == 'R': return from_row == to_row or from_col == to_col
        elif piece_type == 'N':
            row_diff = abs(to_row - from_row); col_diff = abs(to_col - from_col)
            return (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)
        elif piece_type == 'B': return abs(to_row - from_row) == abs(to_col - from_col)
        elif piece_type == 'Q': return (from_row==to_row or from_col==to_col) or (abs(to_row-from_row)==abs(to_col-from_col))
        elif piece_type == 'K':
             if abs(to_row - from_row) <= 1 and abs(to_col - from_col) <= 1: return True
             king_start_row = 7 if color == 'white' else 0
             if from_row == king_start_row and to_row == king_start_row and abs(to_col - from_col) == 2: return True
             return False
        return False

    def is_valid_pawn_move(self, from_row, from_col, to_row, to_col, color):
        direction = 1 if color == 'black' else -1; start_row = 1 if color == 'black' else 6
        if not (0 <= to_row < 8 and 0 <= to_col < 8): return False

        if from_col == to_col and to_row == from_row + direction:
            return self.board[to_row][to_col] is None

        if from_row == start_row and from_col == to_col and to_row == from_row + 2 * direction:
            path_clear = self.board[from_row + direction][from_col] is None
            destination_clear = self.board[to_row][to_col] is None
            return path_clear and destination_clear

        if to_row == from_row + direction and abs(to_col - from_col) == 1:
            target = self.board[to_row][to_col]
            # Standard capture
            if target is not None and target[0] != color: return True
            # En Passant check
            if target is None and self.last_move:
                 lm_from_r, lm_from_c, lm_to_r, lm_to_c, lm_piece = self.last_move
                 if (lm_piece[0] != color and lm_piece[1] == 'P' and abs(lm_from_r - lm_to_r) == 2 and
                     lm_to_r == from_row and lm_to_c == to_col): # Check adjacent pawn was the one that just moved two steps
                     return True
        return False

    def _is_path_clear(self, from_row, from_col, to_row, to_col):
        row_step = 0 if from_row == to_row else (1 if to_row > from_row else -1); col_step = 0 if from_col == to_col else (1 if to_col > from_col else -1)
        current_row, current_col = from_row + row_step, from_col + col_step
        while (current_row, current_col) != (to_row, to_col):
            if not (0 <= current_row < 8 and 0 <= current_col < 8): return False
            if self.board[current_row][current_col] is not None: return False
            current_row += row_step; current_col += col_step
        return True

    def is_valid_rook_move(self, from_row, from_col, to_row, to_col):
        if from_row != to_row and from_col != to_col: return False
        return self._is_path_clear(from_row, from_col, to_row, to_col)

    def is_valid_knight_move(self, from_row, from_col, to_row, to_col):
        row_diff = abs(to_row - from_row); col_diff = abs(to_col - from_col)
        return (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)

    def is_valid_bishop_move(self, from_row, from_col, to_row, to_col):
        if abs(to_row - from_row) != abs(to_col - from_col): return False
        return self._is_path_clear(from_row, from_col, to_row, to_col)

    def is_valid_queen_move(self, from_row, from_col, to_row, to_col):
        is_rook_like=(from_row==to_row or from_col==to_col);is_bishop_like=(abs(to_row-from_row)==abs(to_col-from_col))
        if not (is_rook_like or is_bishop_like): return False
        return self._is_path_clear(from_row, from_col, to_row, to_col)

    def is_valid_king_move(self, from_row, from_col, to_row, to_col, color):
        if abs(to_row - from_row) <= 1 and abs(to_col - from_col) <= 1:
             target = self.board[to_row][to_col]
             return target is None or target[0] != color

        if from_row == to_row and abs(to_col - from_col) == 2: # Castling attempt
            if self.is_in_check(color): return False
            king_start_row = 7 if color == 'white' else 0
            if from_row != king_start_row: return False

            opponent_color = 'black' if color == 'white' else 'white'
            if to_col == 6: # Kingside
                rook_col = 7
                if not self.castling_rights[color]['kingside']: return False
                if self.board[from_row][5] is not None or self.board[from_row][6] is not None: return False
                if self.is_square_attacked(from_row,5,opponent_color) or self.is_square_attacked(from_row,6,opponent_color): return False
                # Ensure rook is present and correct type/color
                rook = self.board[from_row][rook_col]
                if not rook or rook != (color, 'R'): return False
                return True
            elif to_col == 2: # Queenside
                rook_col = 0
                if not self.castling_rights[color]['queenside']: return False
                if self.board[from_row][1] is not None or self.board[from_row][2] is not None or self.board[from_row][3] is not None: return False
                if self.is_square_attacked(from_row,2,opponent_color) or self.is_square_attacked(from_row,3,opponent_color): return False
                rook = self.board[from_row][rook_col]
                if not rook or rook != (color, 'R'): return False
                return True
        return False

    def find_king(self, color):
        if not self.board: return None
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c];
                if piece and piece == (color, 'K'): return (r, c)
        print(f"Warning: King not found for {color}") # Should not happen
        return None

    def is_square_attacked(self, row, col, attacker_color):
        if not self.board: return False
        for r in range(8):
            for c in range(8):
                piece_data = self.board[r][c]
                if piece_data and piece_data[0] == attacker_color:
                    # Simplified check: Can the piece make the basic move *ignoring checks/path for non-pawns/knights*?
                    # Pawns attack diagonally
                    if piece_data[1] == 'P':
                        direction = 1 if attacker_color == 'black' else -1
                        if row == r + direction and abs(col - c) == 1:
                            return True
                    # Use basic geometry check, then path check only if needed
                    elif self.is_basic_move_valid(r, c, row, col, piece_data[1], attacker_color):
                         if piece_data[1] != 'N' and piece_data[1] != 'P': # Knights jump, pawn handled above
                              if self._is_path_clear(r, c, row, col):
                                   return True
                         elif piece_data[1] == 'N': # Knight check
                              return True
        return False

    def is_in_check(self, color):
        king_pos = self.find_king(color);
        if not king_pos: return False
        opponent_color = 'black' if color == 'white' else 'white';
        return self.is_square_attacked(king_pos[0], king_pos[1], opponent_color)

    def has_legal_moves(self, color):
        if not self.board: return False
        for r1 in range(8):
            for c1 in range(8):
                piece = self.board[r1][c1];
                if piece and piece[0] == color:
                    for r2 in range(8):
                        for c2 in range(8):
                            if self.is_valid_move(r1, c1, r2, c2):
                                 return True
        return False

    def is_checkmate(self, color):
        if not self.is_in_check(color): return False
        return not self.has_legal_moves(color)

    def is_stalemate(self, color):
         if self.is_in_check(color): return False
         return not self.has_legal_moves(color)

    def check_game_over(self):
        """ Checks for checkmate or stalemate and asks to play again."""
        player_whose_move_it_is = 'white' if self.is_player_turn else 'black'

        mate = self.is_checkmate(player_whose_move_it_is)
        stale = self.is_stalemate(player_whose_move_it_is)

        if mate or stale:
            if mate:
                winner = 'Black' if player_whose_move_it_is == 'white' else 'White'
                message = f"Checkmate! {winner} wins!"
            else: # stale
                message = "Stalemate! It's a draw."

            # Disable board immediately
            for r in range(8):
                for c in range(8):
                    if self.squares[r][c]:
                        try: self.squares[r][c].config(state=tk.DISABLED)
                        except tk.TclError: pass

            # Schedule the ask_play_again dialog
            self.window.after(50, lambda m=message: self.ask_play_again(m))

            return True # Indicate game is over

        return False # Game is not over

    def ask_play_again(self, message):
        """Shows the game over message and asks the user if they want to play again."""
        # Ensure the main window is still responsive before showing the dialog
        try:
            self.window.update_idletasks() # Process pending events
        except tk.TclError:
            return # Window likely closed

        play_again = messagebox.askyesno(
            title="Game Over",
            message=f"{message}\n\nDo you want to play again?"
        )

        if play_again:
            self.reset_game()
        else:
            print("Exiting.")
            # Use destroy() for cleaner exit than quit() in some cases
            try:
                 self.window.destroy()
            except tk.TclError:
                 pass # Ignore if already destroyed

# ==================================================================

if __name__ == "__main__":
    game = ChessGame()