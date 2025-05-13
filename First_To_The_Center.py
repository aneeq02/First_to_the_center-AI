import pygame
import chess
import time
import math
import sys
import os
import traceback


WIDTH, HEIGHT = 640, 640
INFO_HEIGHT = 80
SQUARE_SIZE = WIDTH // 8
FPS = 60
CENTER_SQUARES = [chess.D4, chess.D5, chess.E4, chess.E5]
PIECES = {}
AI_DEPTH = 3


WHITE_SQ = (240, 217, 181)
BROWN_SQ = (181, 136, 99)
YELLOW_HL = (255, 255, 0, 100)
GREEN_HL = (0, 255, 0, 100)
RED_CHECK = (255, 0, 0, 120)
LAST_MOVE_HL = (255, 255, 0, 80)
BLACK = (0, 0, 0)
WHITE_TXT = (255, 255, 255)
DARK_GREY_BG = (40, 40, 40)
LIGHT_GREY_BTN = (200, 200, 200)
BLUE_BTN = (0, 120, 255)
GREEN_BTN = (0, 200, 0)
DARK_GREY_TXT = (100, 100, 100)
GAME_OVER_BG = (0, 0, 0, 180)


TIME_OPTIONS = [1, 3, 5, 10]


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT + INFO_HEIGHT))
pygame.display.set_caption("First to the Centre")
clock = pygame.time.Clock()
try:
    font_small = pygame.font.SysFont(None, 24)
    font_medium = pygame.font.SysFont(None, 36)
    font_large = pygame.font.SysFont(None, 48)
    font_xlarge = pygame.font.SysFont(None, 72)
except pygame.error as e:
    print(f"Font loading error: {e}. Using default font.")
    font_small = pygame.font.Font(None, 24)
    font_medium = pygame.font.Font(None, 36)
    font_large = pygame.font.Font(None, 48)
    font_xlarge = pygame.font.Font(None, 72)



def load_images():
    """Loads piece images, handling potential errors."""
    global PIECES
    pieces_symbols = ["P", "R", "N", "B", "Q", "K"]
    loaded_count = 0
    PIECES = {}
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        asset_folder = os.path.join(script_dir, "assets")
        if not os.path.isdir(asset_folder):
            asset_folder = "assets"
        if not os.path.isdir(asset_folder):
            raise FileNotFoundError(f"Asset folder '{asset_folder}' not found.")

        for color in ["w", "b"]:
            for p in pieces_symbols:
                image_path = os.path.join(asset_folder, f"{color}{p}.png")
                if not os.path.exists(image_path):
                    print(f"Warning: Image file not found - {image_path}")
                    continue
                image = pygame.image.load(image_path).convert_alpha()
                PIECES[color + p] = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))
                loaded_count += 1
        if loaded_count < 12:
            print("Warning: Not all piece images loaded.")
        elif loaded_count > 0:
            print("Piece images loaded successfully.")
        if loaded_count == 0:
            raise RuntimeError("No piece images could be loaded.")
    except (pygame.error, FileNotFoundError, RuntimeError) as e:
        print(f"Error loading images: {e}")
        pygame.quit()
        sys.exit()


def draw_board(board, selected_square=None, legal_move_squares=[], last_move=None):
    """Draws the board, pieces, highlights, and check indicator."""
    colors = [WHITE_SQ, BROWN_SQ]
    for rank in range(8):
        for file in range(8):
            square = chess.square(file, 7 - rank)
            color = colors[(file + rank) % 2]
            rect = pygame.Rect(file * SQUARE_SIZE, rank * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(screen, color, rect)

            
            if square in CENTER_SQUARES:
                highlight_surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                highlight_surf.fill(YELLOW_HL)
                screen.blit(highlight_surf, rect.topleft)

            
            if square == selected_square:
                sel_surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                sel_surf.fill(GREEN_HL)
                screen.blit(sel_surf, rect.topleft)
            
            if legal_move_squares:
                try:
                    if any(move.to_square == square for move in legal_move_squares):
                        target_piece = board.piece_at(square)
                        circle_surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                        if target_piece:
                            pygame.draw.circle(circle_surf, GREEN_HL, (SQUARE_SIZE//2, SQUARE_SIZE//2), SQUARE_SIZE//2 - 2, 4)
                        else:
                            pygame.draw.circle(circle_surf, GREEN_HL, (SQUARE_SIZE//2, SQUARE_SIZE//2), 15)
                        screen.blit(circle_surf, rect.topleft)
                except TypeError:
                    pass

    
    if last_move:
        for square in [last_move.from_square, last_move.to_square]:
            rect = pygame.Rect(chess.square_file(square) * SQUARE_SIZE,
                               (7 - chess.square_rank(square)) * SQUARE_SIZE,
                               SQUARE_SIZE, SQUARE_SIZE)
            border_surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(border_surf, LAST_MOVE_HL, border_surf.get_rect(), 4)
            screen.blit(border_surf, rect.topleft)

    
    for rank in range(8):
        for file in range(8):
            square = chess.square(file, 7 - rank)
            piece = board.piece_at(square)
            if piece:
                rect = pygame.Rect(file * SQUARE_SIZE, rank * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                img_key = ("w" if piece.color == chess.WHITE else "b") + piece.symbol().upper()
                if img_key in PIECES:
                    screen.blit(PIECES[img_key], rect.topleft)
                else:
                    placeholder_text = font_medium.render(piece.symbol(), True, BLACK)
                    screen.blit(placeholder_text, placeholder_text.get_rect(center=rect.center))

    
    if board.is_check():
        king_square = board.king(board.turn)
        if king_square is not None:
            king_rect = pygame.Rect(chess.square_file(king_square) * SQUARE_SIZE,
                                    (7 - chess.square_rank(king_square)) * SQUARE_SIZE,
                                    SQUARE_SIZE, SQUARE_SIZE)
            if int(time.time() * 3) % 2 == 0:
                flash_surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                flash_surf.fill(RED_CHECK)
                screen.blit(flash_surf, king_rect.topleft)

def draw_info_panel(turn, white_time_elapsed, black_time_elapsed, time_limit_secs, white_name, black_name):
    """Draws the bottom panel with timers and turn indicator."""
    pygame.draw.rect(screen, DARK_GREY_BG, (0, HEIGHT, WIDTH, INFO_HEIGHT))
    white_time_left = max(0, time_limit_secs - white_time_elapsed)
    black_time_left = max(0, time_limit_secs - black_time_elapsed)
    
    wt_str = f"{white_name}: {int(white_time_left // 60)}:{int(white_time_left % 60):02d}"
    bt_str = f"{black_name}: {int(black_time_left // 60)}:{int(black_time_left % 60):02d}"
    wt_render = font_small.render(wt_str, True, WHITE_TXT)
    bt_render = font_small.render(bt_str, True, WHITE_TXT)
    screen.blit(wt_render, (15, HEIGHT + 10))
    screen.blit(bt_render, (WIDTH - bt_render.get_width() - 15, HEIGHT + 10))
    
    turn_player_name = white_name if turn == chess.WHITE else black_name
    turn_text = f"{turn_player_name}'s Turn"
    turn_render = font_medium.render(turn_text, True, WHITE_TXT)
    turn_rect = turn_render.get_rect(center=(WIDTH // 2, HEIGHT + INFO_HEIGHT // 2))
    screen.blit(turn_render, turn_rect)

def draw_game_over(message):
    """Draws the game over message centered on the screen."""
    overlay = pygame.Surface((WIDTH, HEIGHT + INFO_HEIGHT), pygame.SRCALPHA)
    overlay.fill(GAME_OVER_BG)
    screen.blit(overlay, (0, 0))
    lines = message.split('\n')
    line_renders = [font_large.render(line, True, WHITE_TXT) for line in lines]
    total_height = sum(r.get_height() for r in line_renders) + (len(lines) - 1) * 10
    start_y = (HEIGHT + INFO_HEIGHT - total_height) // 2
    current_y = start_y
    for render in line_renders:
        rect = render.get_rect(center=(WIDTH // 2, current_y + render.get_height() // 2))
        screen.blit(render, rect)
        current_y += render.get_height() + 10
    prompt = font_small.render("Click anywhere to return to menu", True, LIGHT_GREY_BTN)
    prompt_rect = prompt.get_rect(center=(WIDTH // 2, current_y + 30))
    screen.blit(prompt, prompt_rect)



def choose_promotion(player_color):
    """Displays promotion options and returns the chosen piece type."""
    options = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
    option_map = {chess.QUEEN: 'q', chess.ROOK: 'r', chess.BISHOP: 'b', chess.KNIGHT: 'n'}
    option_rects = []
    popup_width = 220
    popup_height = 60
    start_x = (WIDTH - popup_width) // 2
    start_y = (HEIGHT - popup_height) // 2
    piece_prefix = 'w' if player_color == chess.WHITE else 'b'

    for i, piece_type in enumerate(options):
        rect = pygame.Rect(start_x + 10 + i * 50, start_y + 10, 40, 40)
        option_rects.append((rect, piece_type))

    while True:
        pygame.draw.rect(screen, DARK_GREY_BG, (start_x, start_y, popup_width, popup_height), border_radius=5)
        pygame.draw.rect(screen, LIGHT_GREY_BTN, (start_x, start_y, popup_width, popup_height), 2, border_radius=5)
        promo_label = font_small.render("Promote to:", True, WHITE_TXT)
        screen.blit(promo_label, (start_x + (popup_width - promo_label.get_width()) // 2, start_y - 25))

        for rect, piece_type in option_rects:
            pygame.draw.rect(screen, LIGHT_GREY_BTN, rect, border_radius=3)
            pygame.draw.rect(screen, BLACK, rect, 1, border_radius=3)
            piece_char = option_map[piece_type]
            img_key = piece_prefix + piece_char.upper()
            if img_key in PIECES:
                screen.blit(pygame.transform.scale(PIECES[img_key], (36, 36)), rect.inflate(-4, -4).topleft)
            else:
                txt = font_medium.render(piece_char.upper(), True, BLACK)
                screen.blit(txt, txt.get_rect(center=rect.center))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for rect, piece_type in option_rects:
                    if rect.collidepoint(event.pos):
                        return piece_type


def menu_screen():
    """Displays the setup menu and returns game settings."""
    input_boxes = [pygame.Rect(WIDTH//2 - 110, 150, 220, 40), pygame.Rect(WIDTH//2 - 110, 210, 220, 40)]
    time_buttons = [(pygame.Rect(120 + i*100, 300, 80, 40), t) for i, t in enumerate(TIME_OPTIONS)]
    mode_buttons = [(pygame.Rect(WIDTH//2 - 110, 370, 100, 40), 'human'), (pygame.Rect(WIDTH//2 + 10, 370, 100, 40), 'ai')]
    color_buttons = [(pygame.Rect(WIDTH//2 - 110, 460, 100, 40), chess.WHITE), (pygame.Rect(WIDTH//2 + 10, 460, 100, 40), chess.BLACK)]
    player1_default, player2_default = "Player 1", "Player 2"
    player1, player2 = player1_default, player2_default
    time_choice, mode_choice, player_color_choice = 5, 'human', chess.WHITE
    active_box, cleared_on_click = None, [False, False]

    while True:
        screen.fill(DARK_GREY_BG)
        title = font_large.render("First to the Centre", True, WHITE_TXT)
        screen.blit(title, title.get_rect(center=(WIDTH//2, 60)))
        subtitle = font_small.render("(Rooks move like Bishops, Bishops move like Rooks!)", True, YELLOW_HL[:3])
        screen.blit(subtitle, subtitle.get_rect(center=(WIDTH//2, 95)))

        
        p1_box = input_boxes[0]
        pygame.draw.rect(screen, WHITE_SQ, p1_box, border_radius=3)
        border_color_p1 = BLUE_BTN if active_box == 0 else LIGHT_GREY_BTN
        pygame.draw.rect(screen, border_color_p1, p1_box, 2, border_radius=3)
        txt1_color = BLACK if player1 and player1 != player1_default else DARK_GREY_TXT
        txt1_display = player1 if (player1 and player1 != player1_default) or cleared_on_click[0] else "Enter P1 Name..."
        txt1_surface = font_medium.render(txt1_display, True, txt1_color)
        screen.blit(txt1_surface, (p1_box.x + 5, p1_box.y + (p1_box.height - txt1_surface.get_height()) // 2))

        p2_box = input_boxes[1]
        if mode_choice == 'human':
            pygame.draw.rect(screen, WHITE_SQ, p2_box, border_radius=3)
            border_color_p2 = BLUE_BTN if active_box == 1 else LIGHT_GREY_BTN
            pygame.draw.rect(screen, border_color_p2, p2_box, 2, border_radius=3)
            txt2_color = BLACK if player2 and player2 != player2_default else DARK_GREY_TXT
            txt2_display = player2 if (player2 and player2 != player2_default) or cleared_on_click[1] else "Enter P2 Name..."
            txt2_surface = font_medium.render(txt2_display, True, txt2_color)
            screen.blit(txt2_surface, (p2_box.x + 5, p2_box.y + (p2_box.height - txt2_surface.get_height()) // 2))
        else:
            ai_label_text = font_medium.render("AI Opponent", True, DARK_GREY_TXT)
            screen.blit(ai_label_text, (p2_box.x + 5, p2_box.y + (p2_box.height - ai_label_text.get_height()) // 2))

        
        t_label = font_small.render("Select Time Control (minutes):", True, WHITE_TXT)
        screen.blit(t_label, (WIDTH//2 - t_label.get_width()//2, 275))
        for rect, time_val_mins in time_buttons:
            button_color = GREEN_BTN if time_val_mins == time_choice else LIGHT_GREY_BTN
            pygame.draw.rect(screen, button_color, rect, border_radius=3)
            pygame.draw.rect(screen, BLACK, rect, 1, border_radius=3)
            time_text_render = font_small.render(str(time_val_mins), True, BLACK)
            screen.blit(time_text_render, time_text_render.get_rect(center=rect.center))

        
        m_label = font_small.render("Select Mode:", True, WHITE_TXT)
        screen.blit(m_label, (WIDTH//2 - m_label.get_width()//2, 345))
        for rect, mode_str in mode_buttons:
            button_color = GREEN_BTN if mode_str == mode_choice else LIGHT_GREY_BTN
            pygame.draw.rect(screen, button_color, rect, border_radius=3)
            pygame.draw.rect(screen, BLACK, rect, 1, border_radius=3)
            mode_text_render = font_small.render(mode_str.capitalize(), True, BLACK)
            screen.blit(mode_text_render, mode_text_render.get_rect(center=rect.center))

        
        if mode_choice == 'ai':
            c_label = font_small.render("Choose Your Color (vs AI):", True, WHITE_TXT)
            screen.blit(c_label, (WIDTH//2 - c_label.get_width()//2, 425))
            for rect, color_const in color_buttons:
                 button_color = GREEN_BTN if color_const == player_color_choice else LIGHT_GREY_BTN
                 pygame.draw.rect(screen, button_color, rect, border_radius=3)
                 pygame.draw.rect(screen, BLACK, rect, 1, border_radius=3)
                 color_name = "White" if color_const == chess.WHITE else "Black"
                 color_text_render = font_small.render(color_name, True, BLACK)
                 screen.blit(color_text_render, color_text_render.get_rect(center=rect.center))

        
        start_btn = pygame.Rect(WIDTH//2 - 70, 520, 140, 40)
        pygame.draw.rect(screen, BLUE_BTN, start_btn, border_radius=3)
        pygame.draw.rect(screen, BLACK, start_btn, 1, border_radius=3)
        start_text_render = font_medium.render("Start Game", True, WHITE_TXT)
        screen.blit(start_text_render, start_text_render.get_rect(center=start_btn.center))
        pygame.display.flip()

        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                new_active_box = None
                if input_boxes[0].collidepoint(event.pos):
                    new_active_box = 0
                    if player1 == player1_default and not cleared_on_click[0]: player1 = ""; cleared_on_click[0] = True
                elif mode_choice == 'human' and input_boxes[1].collidepoint(event.pos):
                    new_active_box = 1
                    if player2 == player2_default and not cleared_on_click[1]: player2 = ""; cleared_on_click[1] = True
                active_box = new_active_box
                for rect, time_val_mins in time_buttons:
                    if rect.collidepoint(event.pos): time_choice = time_val_mins; active_box = None
                for rect, mode_str in mode_buttons:
                    if rect.collidepoint(event.pos):
                        if mode_choice != mode_str:
                            mode_choice = mode_str
                            if mode_choice == 'ai': player2 = "AI"; cleared_on_click[1] = True;
                            elif player2 == "AI": player2 = player2_default; cleared_on_click[1] = False
                            if active_box == 1 and mode_choice == 'ai': active_box = None 
                        active_box = None
                if mode_choice == 'ai':
                    for rect, color_const in color_buttons:
                         if rect.collidepoint(event.pos): player_color_choice = color_const; active_box = None
                if start_btn.collidepoint(event.pos):
                    final_p1 = player1.strip() if player1.strip() and player1 != player1_default else player1_default
                    final_p2 = (player2.strip() if player2.strip() and player2 != player2_default else player2_default) if mode_choice == 'human' else "AI"
                    
                    if mode_choice == 'ai': final_p2 = "AI"
                    return final_p1, final_p2, time_choice * 60, player_color_choice, mode_choice
            elif event.type == pygame.KEYDOWN and active_box is not None:
                is_p1_box = (active_box == 0)
                target_player = player1 if is_p1_box else player2
                
                if not is_p1_box and mode_choice != 'human': continue

                if event.key == pygame.K_BACKSPACE:
                    default_check = player1_default if is_p1_box else player2_default
                    if target_player != default_check or cleared_on_click[active_box]:
                        target_player = target_player[:-1]
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER: active_box = None; continue
                else:
                    char = event.unicode
                    if char.isprintable() and len(target_player) < 15:
                        default_check = player1_default if is_p1_box else player2_default
                        if target_player == default_check and not cleared_on_click[active_box]:
                            target_player = ""
                            cleared_on_click[active_box] = True
                        target_player += char
                
                if is_p1_box:
                     player1 = target_player
                     cleared_on_click[0] = bool(player1) 
                else: 
                     player2 = target_player
                     cleared_on_click[1] = bool(player2)





def custom_legal_moves(board):
    """
    Generates legal moves including custom R/B swap and explicit pawn checks.
    """
    valid_custom_moves = []
    current_turn = board.turn
    opponent_color = not current_turn

    
    try:
        for move in board.pseudo_legal_moves:
            piece_type = board.piece_type_at(move.from_square)
            if piece_type is None or board.color_at(move.from_square) != current_turn:
                 continue 

            is_standard_piece = piece_type in [chess.PAWN, chess.KNIGHT, chess.KING, chess.QUEEN]

            if is_standard_piece:
                
                if piece_type == chess.PAWN:
                    from_rank = chess.square_rank(move.from_square)
                    to_rank = chess.square_rank(move.to_square)
                    from_file = chess.square_file(move.from_square)
                    to_file = chess.square_file(move.to_square)

                    
                    if from_rank == to_rank and from_file != to_file:
                        
                        continue 

                
                try:
                    if board.is_legal(move):
                        valid_custom_moves.append(move)
                except (AssertionError, ValueError):
                    
                    pass 

    except Exception as e:
        print(f"Error getting standard pseudo-legal moves: {e}")
        traceback.print_exc()

    
    try:
        for from_sq in chess.SQUARES:
            piece = board.piece_at(from_sq)
            if not piece or piece.color != current_turn: continue

            original_type = piece.piece_type
            is_custom_rook = original_type == chess.ROOK
            is_custom_bishop = original_type == chess.BISHOP

            if not (is_custom_rook or is_custom_bishop): continue

            directions = [7, 9, -7, -9] if is_custom_rook else [8, -8, 1, -1]
            start_file = chess.square_file(from_sq)
            start_rank = chess.square_rank(from_sq)

            for direction in directions:
                target_sq = from_sq
                while True:
                    target_sq += direction
                    if not (0 <= target_sq < 64): break 

                    target_file = chess.square_file(target_sq)
                    target_rank = chess.square_rank(target_sq)
                    file_change = abs(target_file - start_file)
                    rank_change = abs(target_rank - start_rank)

                    
                    if is_custom_rook: 
                        if file_change != rank_change: break
                    else: 
                        if file_change > 0 and rank_change > 0: break
                        if file_change == 0 and rank_change == 0: break 

                    target_piece = board.piece_at(target_sq)
                    can_move_to = False
                    stop_ray = False

                    if target_piece is None: can_move_to = True
                    elif target_piece.color == opponent_color: can_move_to = True; stop_ray = True
                    else: stop_ray = True 

                    if can_move_to:
                        move = chess.Move(from_sq, target_sq)
                        
                        is_safe_move = False
                        try:
                            board.push(move)
                            try:
                                king_square = board.king(current_turn)
                                if king_square is not None and not board.is_attacked_by(opponent_color, king_square):
                                    is_safe_move = True
                            finally: board.pop()
                        except (ValueError, AssertionError): pass 
                        except Exception as e:
                             print(f"Unexpected error checking king safety for {move}: {e}"); traceback.print_exc()
                        if is_safe_move: valid_custom_moves.append(move)

                    if stop_ray: break

    except Exception as e:
        print(f"Error generating custom R/B moves: {e}")
        traceback.print_exc()

    return list(set(valid_custom_moves))



def king_dist_to_center(square):
    """Calculates Manhattan distance from square to nearest center square."""
    fx, fy = chess.square_file(square), chess.square_rank(square)
    center_coords = [(3, 3), (3, 4), (4, 3), (4, 4)]
    if not center_coords or fx is None or fy is None: return 7
    return min(abs(fx - cx) + abs(fy - cy) for cx, cy in center_coords)

def evaluate(board):
    """Evaluation function for the AI."""
    try:
        outcome = board.outcome(claim_draw=True)
        if outcome:
            if outcome.winner == chess.WHITE: return 99999
            if outcome.winner == chess.BLACK: return -99999
            return 0
    except Exception as e:
        print(f"Error checking board outcome in evaluate: {e}"); return 0

    
    opponent_color = not board.turn
    try:
        opponent_king_square = board.king(opponent_color)
        if opponent_king_square in CENTER_SQUARES: 
            if not board.is_attacked_by(board.turn, opponent_king_square):
                return 99999 if opponent_color == chess.WHITE else -99999
    except Exception as e: print(f"Error during center win check in evaluate: {e}")

    
    score = 0
    piece_values = {'p': 100, 'n': 320, 'b': 500, 'r': 330, 'q': 900, 'k': 0}
    try:
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece:
                val = piece_values[piece.symbol().lower()]
                if piece.piece_type == chess.KING:
                    val += max(0, (6 - king_dist_to_center(sq))) * 5
                score += val if piece.color == chess.WHITE else -val
        if board.is_check(): score += 20 if board.turn == chess.BLACK else -20
    except Exception as e: print(f"Error during material/positional eval: {e}"); return 0
    return score


def minimax(board, depth, alpha, beta, maximizing_player):
    """Minimax algorithm with alpha-beta pruning."""
    try:
        
        outcome = board.outcome(claim_draw=True)
        if outcome is not None:
            if outcome.winner == chess.WHITE: return 99999, None
            if outcome.winner == chess.BLACK: return -99999, None
            return 0, None 

        opponent_color = not board.turn
        king_sq = board.king(opponent_color) 
        if king_sq in CENTER_SQUARES and not board.is_attacked_by(board.turn, king_sq):
             return (99999, None) if opponent_color == chess.WHITE else (-99999, None)

        if depth == 0: return evaluate(board), None

    except Exception as e:
        print(f"Error checking terminal state in minimax depth {depth}: {e}"); traceback.print_exc(); return 0, None

    
    best_move_found = None
    try: legal_moves_for_node = custom_legal_moves(board)
    except Exception as e: print(f"Error getting moves in minimax depth {depth}: {e}"); traceback.print_exc(); return evaluate(board), None

    if not legal_moves_for_node: return evaluate(board), None 

    best_move_found = legal_moves_for_node[0] 

    if maximizing_player: 
        max_eval = -math.inf
        for move in legal_moves_for_node:
            current_eval = -math.inf
            try:
                board.push(move); current_eval, _ = minimax(board, depth - 1, alpha, beta, False); board.pop()
            except Exception as e:
                print(f"Error in MAX recurse {move} d{depth}: {e}"); traceback.print_exc()
                try: 
                    if board.move_stack and board.peek() == move: board.pop()
                except Exception: pass
                continue
            if current_eval > max_eval: max_eval = current_eval; best_move_found = move
            alpha = max(alpha, current_eval)
            if beta <= alpha: break
        return max_eval, best_move_found
    else: 
        min_eval = math.inf
        for move in legal_moves_for_node:
            current_eval = math.inf
            try:
                board.push(move); current_eval, _ = minimax(board, depth - 1, alpha, beta, True); board.pop()
            except Exception as e:
                print(f"Error in MIN recurse {move} d{depth}: {e}"); traceback.print_exc()
                try: 
                    if board.move_stack and board.peek() == move: board.pop()
                except Exception: pass
                continue
            if current_eval < min_eval: min_eval = current_eval; best_move_found = move
            beta = min(beta, current_eval)
            if beta <= alpha: break
        return min_eval, best_move_found



def game_loop():
    """Runs the main game loop."""
    player1_name, player2_name, time_limit_seconds, player_color, game_mode = menu_screen()
    print(f"Starting Game: P1={player1_name}, P2={player2_name}, Mode={game_mode}, Time={time_limit_seconds/60:.1f}m, HumanColor={'W' if player_color == chess.WHITE else 'B'}")

    board = chess.Board()
    try: load_images()
    except SystemExit: return

    
    if game_mode == 'human':
        white_player_name = player1_name
        black_player_name = player2_name
    else: 
        
        
        if player_color == chess.WHITE:
            white_player_name = player1_name 
            black_player_name = player2_name 
        else: 
            white_player_name = player2_name 
            black_player_name = player1_name 
    


    white_time, black_time = 0.0, 0.0
    selected_square, legal_moves_for_selected = None, []
    last_move, winner_message = None, ""
    last_frame_time = time.time()
    game_over, ai_is_thinking = False, False
    running = True

    while running:
        current_time = time.time()
        delta_time = current_time - last_frame_time
        last_frame_time = current_time

        
        if not game_over and not ai_is_thinking:
            try:
                if board.turn == chess.WHITE: white_time += delta_time
                else: black_time += delta_time
                if white_time >= time_limit_seconds: game_over = True; winner_message = f"Time Up!\n{black_player_name} (Black) Wins!"
                elif black_time >= time_limit_seconds: game_over = True; winner_message = f"Time Up!\n{white_player_name} (White) Wins!"
            except Exception as e: print(f"Timer error: {e}")

        
        is_ai_turn = (game_mode == 'ai' and board.turn != player_color)
        if not game_over and is_ai_turn and not ai_is_thinking:
            ai_is_thinking = True
            try: 
                screen.fill(BLACK)
                draw_board(board, None, [], last_move)
                draw_info_panel(board.turn, white_time, black_time, time_limit_seconds, white_player_name, black_player_name)
                thinking_text = font_small.render("AI is thinking...", True, WHITE_TXT)
                screen.blit(thinking_text, (WIDTH // 2 - thinking_text.get_width() // 2, HEIGHT + INFO_HEIGHT // 2 + 25))
                pygame.display.flip()
            except Exception as e: print(f"Error drawing AI thinking state: {e}")

            
            ai_start_time = time.time()
            eval_score, ai_move = None, None
            validated_ai_move = None
            try:
                maximizing = (board.turn == chess.WHITE)
                eval_score, ai_move = minimax(board.copy(), AI_DEPTH, -math.inf, math.inf, maximizing)
                ai_end_time = time.time()
                print(f"AI done: {ai_end_time - ai_start_time:.2f}s. Move: {ai_move}, Eval: {eval_score}")

                
                if ai_move:
                    current_custom_legal_moves = custom_legal_moves(board)
                    for legal_move in current_custom_legal_moves:
                        if legal_move.from_square == ai_move.from_square and \
                           legal_move.to_square == ai_move.to_square and \
                           legal_move.promotion == ai_move.promotion:
                            validated_ai_move = legal_move; break
                    if not validated_ai_move:
                        print(f"ERROR: AI suggested move {ai_move} NOT currently legal.")
                        print(f"Available: {[str(m) for m in current_custom_legal_moves]}")
                        if current_custom_legal_moves: 
                            validated_ai_move = current_custom_legal_moves[0]
                            print(f"Fallback to: {validated_ai_move}")
                        else: validated_ai_move = None
            except Exception as e:
                print(f"Critical error during AI minimax/validation: {e}"); traceback.print_exc()
                game_over = True; winner_message = "Error during AI calculation!"; validated_ai_move = None

            
            if validated_ai_move:
                try: board.push(validated_ai_move); last_move = validated_ai_move
                except Exception as e: print(f"Error pushing AI move {validated_ai_move}: {e}"); traceback.print_exc(); game_over = True; winner_message = "Error pushing AI move!"; last_move = None
            elif not game_over and ai_move is None: pass 
            elif not game_over: game_over = True; winner_message = "Error: Invalid AI move state!" 

            
            if not game_over:
                
                try:
                    outcome = board.outcome(claim_draw=True)
                    if outcome:
                        game_over = True
                        term = outcome.termination.name.replace("_", " ").title()
                        if outcome.winner == chess.WHITE: winner_message = f"{term}!\n{white_player_name} (White) Wins!"
                        elif outcome.winner == chess.BLACK: winner_message = f"{term}!\n{black_player_name} (Black) Wins!"
                        else: winner_message = f"{term}!\nIt's a Draw!"
                    elif validated_ai_move: 
                        ai_player_color = not board.turn
                        ai_king_square = board.king(ai_player_color)
                        if ai_king_square in CENTER_SQUARES and not board.is_attacked_by(board.turn, ai_king_square):
                             game_over = True
                             winner = white_player_name if ai_player_color == chess.WHITE else black_player_name
                             w_color = "(White)" if ai_player_color == chess.WHITE else "(Black)"
                             winner_message = f"King Reached Center!\n{winner} {w_color} Wins!"
                except Exception as e: print(f"Error checking win conditions post AI: {e}")

            ai_is_thinking = False

        
        try:
            is_human_turn = not is_ai_turn if game_mode == 'ai' else True
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if game_over:
                    if event.type == pygame.MOUSEBUTTONDOWN: running = False
                    continue
                if ai_is_thinking or not is_human_turn: continue

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = event.pos
                    if mouse_y >= HEIGHT: continue
                    file_idx, rank_idx = mouse_x // SQUARE_SIZE, 7 - (mouse_y // SQUARE_SIZE)
                    clicked_square = chess.square(file_idx, rank_idx)

                    if selected_square is None: 
                        piece = board.piece_at(clicked_square)
                        if piece and piece.color == board.turn:
                            potential_moves = [m for m in custom_legal_moves(board) if m.from_square == clicked_square]
                            if potential_moves: selected_square = clicked_square; legal_moves_for_selected = potential_moves
                            else: selected_square = None; legal_moves_for_selected = []
                        else: selected_square = None; legal_moves_for_selected = []
                    else: 
                        move_to_make = None
                        for move in legal_moves_for_selected:
                            if move.to_square == clicked_square: move_to_make = move; break

                        if move_to_make: 
                            is_promotion = (board.piece_type_at(selected_square) == chess.PAWN and chess.square_rank(clicked_square) in [0, 7])
                            if is_promotion:
                                draw_board(board, selected_square, legal_moves_for_selected, last_move)
                                draw_info_panel(board.turn, white_time, black_time, time_limit_seconds, white_player_name, black_player_name)
                                pygame.display.flip()
                                promo_piece = choose_promotion(board.turn)
                                move_to_make = chess.Move(selected_square, clicked_square, promotion=promo_piece)
                                if move_to_make not in custom_legal_moves(board): move_to_make = None 

                            if move_to_make:
                                try:
                                    board.push(move_to_make); last_move = move_to_make
                                    
                                    if not game_over:
                                         try:
                                             outcome = board.outcome(claim_draw=True)
                                             if outcome:
                                                  game_over = True; term = outcome.termination.name.replace("_", " ").title()
                                                  if outcome.winner == chess.WHITE: winner_message = f"{term}!\n{white_player_name} (White) Wins!"
                                                  elif outcome.winner == chess.BLACK: winner_message = f"{term}!\n{black_player_name} (Black) Wins!"
                                                  else: winner_message = f"{term}!\nIt's a Draw!"
                                             else: 
                                                  human_color = not board.turn
                                                  king_sq = board.king(human_color)
                                                  if king_sq in CENTER_SQUARES and not board.is_attacked_by(board.turn, king_sq):
                                                       game_over = True; winner = white_player_name if human_color == chess.WHITE else black_player_name
                                                       w_color = "(White)" if human_color == chess.WHITE else "(Black)"
                                                       winner_message = f"King Reached Center!\n{winner} {w_color} Wins!"
                                         except Exception as e: print(f"Error checking win conditions post Player: {e}")
                                except Exception as e: print(f"Error pushing player move {move_to_make}: {e}"); traceback.print_exc(); game_over = True; winner_message = "Error pushing player move!"; last_move = None
                            selected_square = None; legal_moves_for_selected = [] 
                        else: 
                            new_piece = board.piece_at(clicked_square)
                            if new_piece and new_piece.color == board.turn:
                                potential_moves = [m for m in custom_legal_moves(board) if m.from_square == clicked_square]
                                if potential_moves: selected_square = clicked_square; legal_moves_for_selected = potential_moves
                                else: selected_square = None; legal_moves_for_selected = [] 
                            else: selected_square = None; legal_moves_for_selected = [] 
        except pygame.error as e: print(f"Pygame event error: {e}")
        except Exception as e: print(f"Unexpected event error: {e}"); traceback.print_exc()

        
        try:
            screen.fill(BLACK)
            current_legal_highlight = legal_moves_for_selected if selected_square is not None else []
            draw_board(board, selected_square, current_legal_highlight, last_move)
            draw_info_panel(board.turn, white_time, black_time, time_limit_seconds, white_player_name, black_player_name)
            if game_over: draw_game_over(winner_message)
            pygame.display.flip()
        except pygame.error as e: print(f"Pygame draw error: {e}")
        except Exception as e: print(f"Unexpected draw error: {e}"); traceback.print_exc()

        clock.tick(FPS)
    
    print("Game loop ended.")


def main():
    print("Welcome to First to the Centre!")
    while True:
        print("\nStarting new game session...")
        try: game_loop()
        except (pygame.error, SystemExit): print("Pygame closed or sys exit."); break
        except Exception as e:
            print(f"\nUnexpected error during game session: {e}"); traceback.print_exc()
            try:
                if pygame.display.get_init() and pygame.display.get_active(): pass
                choice = input("Error occurred. Return to menu (m) or quit (q)? ").lower()
                if choice == 'q': break
            except EOFError: print("Input error, exiting."); break
            except Exception as input_err: print(f"Input failed: {input_err}. Exiting."); break
        print("Returning to menu...")


if __name__ == "__main__":
    if not pygame.get_init(): pygame.init()
    main()
    print("Exiting game.")
    if pygame.get_init(): pygame.quit()
    sys.exit()