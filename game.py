import pygame
from chessBoard import ChessBoard
from pieces import Piece, Color
import subprocess

class Game:

    win_width = 600
    win_height = 600

    def __init__(self):
        self.board: ChessBoard = ChessBoard(self)
        self.turn: Color = Color.WHITE
        self.game_over: bool = True
        self.running: bool = False
        self.selected: Piece | None = None
        self.selected_moves: list = []
        self.screen = pygame.display.set_mode((self.win_width, self.win_height))
        self.accessible_color_case = 110, 160, 150
        self.stockfish_process = None
        self.indication = None
        self.init_stockfish()

    def start(self):
        self.running = True
        while self.running:
            self.start_new_game()

    def start_new_game(self):
        self.game_over = False
        self.board = ChessBoard(self)
        print("New game started...")
        self.display()
        while not self.game_over and self.running:
            self.interact()

    def interact(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game_over = True
                elif event.key == pygame.K_s:
                    bm = self.get_best_move()
                    piece = self.board.select_case(self.board.untranslate(bm[:2]))
                    self.move(piece, self.board.untranslate(bm[2:]))
                elif event.key == pygame.K_h:
                    bm = self.get_best_move()
                    self.indication = self.board.untranslate(bm[:2]), self.board.untranslate(bm[2:])
                    self.display()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                case = (y // self.board.cell_width, x // self.board.cell_height)
                if self.selected is not None:
                    if case in self.selected_moves:
                        self.move(self.selected, case)
                    else:
                        self.select(case)
                else:
                    self.select(case)


    def select(self, case):
        if self.board.is_occupied(case) and self.board.select_case(case).color == self.turn and self.selected != self.board.select_case(case):
            self.unselect()
            self.selected = self.board.select_case(case)
            self.selected_moves = self.selected.valid_moves()
            for p_case in self.selected_moves:
                self.board.display_case(p_case, self.accessible_color_case)
            pygame.display.flip()
        else:
            self.unselect()

    def next_turn(self):
        self.board.demi_coups += 1
        if self.turn == Color.BLACK:
            self.board.coups += 1
        self.turn = self.op_color(self.turn)

    def destroy(self, piece):
        piece.taken()

    @staticmethod
    def op_color(color):
        return Color.WHITE if color == Color.BLACK else Color.BLACK

    def move(self, piece, case):
        old_case = piece.case
        self.board.set_piece(piece, case)
        piece.move(case, old_case)
        self.indication = None
        self.display()
        pygame.display.flip()
        self.check_game_over()
        self.next_turn()
        self.unselect()

    def unselect(self):
        self.selected = None
        for case in self.selected_moves:
            self.board.display_case(case)
        self.selected_moves = []
        pygame.display.flip()

    def check_game_over(self):
        moves = 0
        for piece in self.board.pieces[self.op_color(self.turn)]:
            moves += len(piece.valid_moves())
        if moves == 0:
            print(f"{self.turn} won by Checkmate !")
            # self.game_over = True

    def display(self):
        self.board.display()
        if self.indication is not None:
            self.board.display_case(self.indication[0], (255, 0 , 0))
            self.board.display_case(self.indication[1], (255, 0, 0))
        for color in self.board.pieces:
            for piece in self.board.pieces[color]:
                piece.display()
        pygame.display.flip()

    def init_stockfish(self):
        stockfish_path = "/usr/games/stockfish"
        self.stockfish_process = subprocess.Popen(stockfish_path, universal_newlines=True, stdin=subprocess.PIPE,
                                             stdout=subprocess.PIPE)
        command = "uci\n"  # Send the UCI command to initialize the engine
        self.stockfish_process.stdin.write(command)
        self.stockfish_process.stdin.flush()

    def get_best_move(self, depth=13):
        self.stockfish_process.stdin.write(f"position fen {self.board.get_fen_notation()}\n go depth {depth}\n")
        self.stockfish_process.stdin.flush()
        best_move = None
        for line in self.stockfish_process.stdout:
            if line.startswith("bestmove"):
                best_move = line.split()[1]
                break
        return best_move

    def end_stockfish(self):
        self.stockfish_process.stdin.close()
        self.stockfish_process.stdout.close()
        self.stockfish_process.terminate()
