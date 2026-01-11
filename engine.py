import bulletchess as bc
import threading, sys, time

MATE_SCORE = 30000
PIECE_VALUES = {
    bc.PAWN: 100,
    bc.KNIGHT: 320,
    bc.BISHOP: 330,
    bc.ROOK: 500,
    bc.QUEEN: 900,
    bc.KING: 0
}
PST_TABLES = {
    bc.PAWN: [
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
         5,  5, 10, 25, 25, 10,  5,  5,
         0,  0,  0, 20, 20,  0,  0,  0,
         5, -5,-10,  0,  0,-10, -5,  5,
         5, 10, 10,-20,-20, 10, 10,  5,
         0,  0,  0,  0,  0,  0,  0,  0
    ],
    bc.KNIGHT: [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ],
    bc.BISHOP: [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ],
    bc.ROOK: [
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10, 10, 10, 10, 10,  5,
       -5,  0,  0,  0,  0,  0,  0, -5,
       -5,  0,  0,  0,  0,  0,  0, -5,
       -5,  0,  0,  0,  0,  0,  0, -5,
       -5,  0,  0,  0,  0,  0,  0, -5,
       -5,  0,  0,  0,  0,  0,  0, -5,
        0,  0,  0,  5,  5,  0,  0,  0
    ],
    bc.QUEEN: [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
         -5,  0,  5,  5,  5,  5,  0, -5,
          0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ],
    bc.KING: [
        -40,-40,-35,-35,-35,-35,-40,-40,
        -30,-30,-25,-25,-25,-25,-30,-30,
        -30,-25,-10,-10,-10,-10,-25,-30,
        -30,-25, -5, 0,  0,  -5,-25,-30,
        -25,-20, -5, 0,  0,  -5,-20,-25,
        -20,-15, 0,  5,  5,  0, -15,-20,
         -5, -5, 0,  0,  0,  0, -5, -5,
        -15,  0, -10,-15,-15,-10, 0, -15
    ]
}

class Engine:
    def __init__(self):
        self.main_board = bc.Board()
        self.stop_signal = False
        self.is_searching = False
        self.nodes = 0
        self.time_limit = 0
        self.start_time = 0
        self.tt = {} # table de transposition via zobrist hashing
        
    def send(self, msg):
        print(msg, flush=True)

    def get_tt(self, board, depth, alpha, beta):
        res = self.tt.get(hash(board))
        if res and res["depth"] >= depth:
            if res['flag'] == 'EXACT': return res['score']
            if res['flag'] == 'LOWER' and res['score'] >= beta: return beta # borne inférieure trop grande ? on coupe
            if res['flag'] == 'UPPER' and res['score'] <= alpha: return alpha # borne supérieure trop petite ? on n'aurait jamais choisi ça
        return None

    def save_tt(self, board, depth, score, flag):
        self.tt[hash(board)] = {'depth': depth, 'score': score, 'flag': flag}
    
    def set_pos(self, args):
        try:
            if "startpos" in args:
                self.main_board = bc.Board()
            elif "fen" in args:
                fen_start = args.index("fen") + 1
                fen_end = args.index("moves") if "moves" in args else len(args)
                self.main_board = bc.Board.from_fen(" ".join(args[fen_start:fen_end]))

            if "moves" in args:
                moves_start = args.index("moves") + 1
                for move in args[moves_start:]:
                    self.main_board.apply(bc.Move.from_uci(move))
        except Exception as e:
            self.send(f"info string error: {e}")

    def evaluate(self, board):
        white_score = 0

        for square in bc.SQUARES:
            piece = board[square]
            if piece:
                val = PIECE_VALUES.get(piece.piece_type, 0)
                pst_val = 0
                if piece.piece_type in PST_TABLES:
                    idx = square.index()
                    if piece.color == bc.BLACK:
                         idx ^= 56
                    pst_val = PST_TABLES[piece.piece_type][idx]
                    
                if piece.color == bc.WHITE:
                    white_score += (val + pst_val)
                else:
                    white_score -= (val + pst_val)

        return white_score if board.turn == bc.WHITE else -white_score

    def get_mvv_lva(self, board, move):
        score = 0
        if move.is_capture(board):
            captured_piece = board[move.destination]
            victim_type = captured_piece.piece_type if captured_piece else bc.PAWN
            
            attacker_piece = board[move.origin]
            attacker_type = attacker_piece.piece_type if attacker_piece else bc.PAWN
            
            score = (PIECE_VALUES.get(victim_type, 0) * 10) - PIECE_VALUES.get(attacker_type, 0)
        if move.promotion:
            score += PIECE_VALUES.get(move.promotion, 0)
        return score
        
    def search(self, board, depth, alpha, beta, ply):
        self.nodes += 1

        cached_score = self.get_tt(board, depth, alpha, beta)
        if cached_score is not None:
            return cached_score
        
        # vérification temps toutes les 2000 nodes!
        if self.nodes%2000==0:
            if time.time() - self.start_time > self.time_limit:
                self.stop_signal = True
        
        if self.stop_signal: return 0
        if board in bc.CHECKMATE: return -MATE_SCORE+ply
        if board in bc.DRAW: return 0
        if depth <= 0: return self.quiescence(board, alpha, beta, ply)

        moves = list(board.legal_moves())
        moves.sort(key=lambda m: self.get_mvv_lva(board, m), reverse=True)

        best_score = float("-inf")
        old_alpha = alpha
        
        for move in moves:
            board.apply(move)
            score = -self.search(board, depth-1, -beta, -alpha, ply+1)
            board.undo()

            if self.stop_signal: return 0
            best_score = max(score, best_score)
            alpha = max(score, alpha)
            if alpha >= beta: break

        flag = "EXACT"
        if best_score <= old_alpha: flag = 'UPPER'
        elif best_score >= beta: flag = 'LOWER'
        self.save_tt(board, depth, best_score, flag)
    
        return best_score

    def quiescence(self, board, alpha, beta, ply):
        self.nodes += 1
        
        stand_pat = self.evaluate(board)
        
        if ply > 20: return stand_pat # pour ne pas aller trop loin non plus
        if stand_pat >= beta: return beta # position trop bonne ? on coupe, l'adversaire évitera
        if alpha < stand_pat: alpha = stand_pat
            
        if self.nodes%2000==0:
            if time.time() - self.start_time > self.time_limit:
                self.stop_signal = True
        if self.stop_signal: return alpha

        moves = [m for m in board.legal_moves() if m.is_capture(board) or m.is_promotion()]
        moves.sort(key = lambda m: self.get_mvv_lva(board, m), reverse=True)

        for move in moves:
            board.apply(move)
            score = -self.quiescence(board, -beta, -alpha, ply+1)
            board.undo()

            if score >= beta: return beta # coupure beta
            alpha = max(alpha, score) # alpha étant score maximum qu'on peut espérer

        return alpha
        
    def search_worker(self, board_snapshot, max_depth):
        self.is_searching = True
        self.nodes = 0
        self.stop_signal = False
        self.start_time = time.time()

        legal_moves = list(board_snapshot.legal_moves())
        if not legal_moves:
            self.send("bestmove 0000")
            self.is_searching = False
            return
            
        last_best_move = legal_moves[0]

        for d in range(1, max_depth+1):
            if d>1 and self.stop_signal: break
            
            moves = list(board_snapshot.legal_moves())
            moves.sort(key=lambda m: (m == last_best_move, self.get_mvv_lva(board_snapshot, m)), reverse=True)

            current_best_move = None
            current_best_val = float("-inf")
            alpha = float("-inf")
            beta = float("inf")

            for move in moves:
                board_snapshot.apply(move)
                score = -self.search(board_snapshot, d-1, -beta, -alpha, 1)
                board_snapshot.undo()
                alpha = max(alpha, score)
                
                # si stop_signal durant search, alors score incorrect
                if d>1 and self.stop_signal: break
                if score > current_best_val:
                    current_best_val = score
                    current_best_move = move

            if (d == 1 or not self.stop_signal) and current_best_move:
                last_best_move = current_best_move
                elapsed = time.time() - self.start_time
                nps = int(self.nodes/elapsed) if elapsed > 0.0001 else 0
                
                if current_best_val > 20000:
                    score_str = f"mate {(MATE_SCORE - current_best_val + 1) // 2}"
                elif current_best_val < -20000:
                    score_str = f"mate {-(MATE_SCORE + current_best_val + 1) // 2}"
                else:
                    score_str = f"cp {current_best_val}"

                self.send(f"info depth {d} score {score_str} nodes {self.nodes} nps {nps} time {int(elapsed*1000)} pv {current_best_move.uci()}")

        self.send(f"bestmove {last_best_move.uci()}")
        self.is_searching = False

    def start_search(self, args):
        wtime = int(args[args.index("wtime") + 1]) if "wtime" in args else 10000
        btime = int(args[args.index("btime") + 1]) if "btime" in args else 10000
        winc = int(args[args.index("winc") + 1]) if "winc" in args else 0
        binc = int(args[args.index("binc") + 1]) if "binc" in args else 0
        max_depth = int(args[args.index("depth") + 1]) if "depth" in args else 5

        if self.main_board.turn == bc.WHITE:
            allowed_ms = (wtime / 20.0) + (winc / 2.0)
        else:
            allowed_ms = (btime / 20.0) + (binc / 2.0)
        self.time_limit = max(allowed_ms/1000.0, 0.030)
        board_copy = self.main_board.copy()
        threading.Thread(target=self.search_worker, args=(board_copy, max_depth), daemon=True).start()
