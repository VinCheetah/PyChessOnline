import pygame
from pieces import Piece, Color, Pawn, Rook, Bishop, Knight, King, Queen

Case = tuple[int, int]


class ChessBoard:

    length = 8
    height = 8

    def __init__(self, game):
        self.game = game
        self.cell_width = self.game.win_width // self.length
        self.cell_height = self.game.win_height // self.height
        self.board: list[list[Piece | None]] = [[None] * self.length for _ in range(self.height)]
        self.pieces: dict[Color, list[Piece]] = {Color.WHITE: [], Color.BLACK: []}
        self.coups = 0
        self.en_passant = None
        self.demi_coups = 0
        self.init_piece_config()

    def accessible(self, piece, case):
        return 0 <= case[0] < self.length and 0 <= case[1] < self.height and not self.has_same_color(piece.case, case)

    def has_same_color(self, case1, case2):
        p1 = self.select_case(case1)
        p2 = self.select_case(case2)
        if p1 is not None and p2 is not None:
            return p1.color == p2.color
        return False

    def has_opposite_color(self, case1, case2):
        p1 = self.select_case(case1)
        p2 = self.select_case(case2)
        if p1 is not None and p2 is not None:
            return p1.color != p2.color
        return False

    def find_king(self, color) -> King:
        for piece in self.pieces[color]:
            if piece.is_king(color):
                return piece

    def init_piece_config(self):
        for h, i, fd, rd, color in [(0, 0, 1, 1, Color.WHITE), (self.length-1, 0, -1, 1, Color.BLACK)]:
            self.lign_init(h+fd, i, rd, [Pawn] * self.length, color)
            self.lign_init(h, i, rd, [Rook, Knight, Bishop, King, Queen, Bishop, Knight, Rook], color)

    def create_piece(self, piece_class, case, color):
        new_piece = piece_class(self, case, color)
        self.place_piece(new_piece, case)

    def will_check(self, piece, case):
        old_case = piece.case
        target_piece = self.select_case(case)
        self.set_piece(piece, case, False)
        for rd_piece in self.pieces[self.game.op_color(piece.color)]:
            if rd_piece.is_checking():
                self.set_piece(piece, old_case, False)
                self.set_piece(target_piece, case, False)
                return True
        self.set_piece(piece, old_case, False)
        self.set_piece(target_piece, case, False)
        return False

    def lign_init(self, lign, i, fd, pieces_classes, color):
        for k, piece_class in enumerate(pieces_classes):
            self.create_piece(piece_class, (lign, i+fd*k), color)

    def select_case(self, case) -> Piece | None:
        return self.board[case[0]][case[1]]

    def place_piece(self, piece, case):
        if piece is not None:
            piece.case = case
        self.board[case[0]][case[1]] = piece

    def is_occupied(self, case: Case) -> bool:
        return self.select_case(case) is not None

    def piece_color(self, case: Case) -> Color:
        assert self.is_occupied(case)
        return self.select_case(case).color

    def set_piece(self, piece: Piece | None, case: Case, effective=True) -> None:
        if piece is not None:
            self.place_piece(None, piece.case)
        if self.is_occupied(case) and effective:
            # print(f"Placing : {piece} / Destroyed : {case}")
            self.game.destroy(self.select_case(case))
        self.place_piece(piece, case)

    def display(self):
        for i in range(self.length):
            for j in range(self.height):
                self.display_case((i,j))

    def display_case(self, case, add_color=None):
        color = Color.BLACK if (case[1] + case[0]) % 2 else Color.WHITE
        if add_color is not None:
            color = [(color[i] + add_color[i]) / 2 for i in range(len(color))]
        pygame.draw.rect(self.game.screen, color,
                         pygame.Rect([case[1] * self.cell_width, case[0] * self.cell_height, self.cell_width, self.cell_height]))
        if self.is_occupied(case):
            self.select_case(case).display()

    def translate(self, case):
        return {i : chr(i + ord('a')) for i in range(self.length)}[case[1]] + str(int(case[0] + 1))

    def untranslate(self, string):
        return int(string[1]) - 1, 7 - (ord(string[0]) - ord('a'))

    def get_fen_notation(self):
        fen_notation = ""
        k = 0
        for i in range(self.length-1, -1, -1):
            for j in range(self.height-1, -1, -1):
                if self.is_occupied((i, j)):
                    if k > 0:
                        fen_notation += str(k)
                        k = 0
                    fen_notation += self.select_case((i, j)).fen_notation()
                else:
                    k += 1
            if k > 0:
                fen_notation += str(k)
                k = 0
            fen_notation += "/"
        fen_notation = fen_notation[:-1]
        fen_notation += " "
        fen_notation += "w" if self.game.turn == Color.WHITE else "b"
        fen_notation += " "
        for col in (Color.WHITE, Color.BLACK):
            king = self.find_king(col)
            if king.roque_allow("small"):
                fen_notation += "K" if col == Color.WHITE else "k"
            if king.roque_allow("big"):
                fen_notation += "Q" if col == Color.WHITE else "q"
        if fen_notation[-1] == " ":
            fen_notation += "-"
        if self.en_passant is None:
            fen_notation += " - "
        else:
            fen_notation += " " + self.translate(self.en_passant) + " "
        fen_notation += str(self.demi_coups)
        fen_notation += " "
        fen_notation += str(self.coups)
        return fen_notation

