from enum import Enum
import pygame

# Color = Enum("Color", ("BLACK", "WHITE"))


class Color:
    BLACK = 50, 50, 50
    WHITE = 230, 200, 220


class Piece:
    value = 0
    type = "Piece"
    png_dir = "images/png/"

    def __init__(self, board, case, color):
        self.board = board
        self.color: Color = color
        self.case = case
        self.image = None
        self.unmoved = True
        self.init_png()

        self.board.pieces[color].append(self)

    def fen_notation(self):
        return self.type[0].lower() if self.color == Color.BLACK else self.type[0]

    def init_png(self):
        col = "w" if self.color == Color.WHITE else "b"
        self.image = pygame.transform.scale(pygame.image.load(self.png_dir + col + "_" + self.type + ".png"), (self.board.cell_width, self.board.cell_height))

    def dep(self, dx, dy, case=None):
        case = case or self.case
        return case[0] + dx, case[1] + dy

    def move(self, case, old_case) -> None:
        self.unmoved = False
        self.board.en_passant = None

    def is_king(self, color) -> bool:
        return False

    def is_rook(self, color) -> bool:
        return False

    def description(self):
        return f"{'White' if self.color == Color.WHITE else 'Black'} {self.type}"

    def possible_moves(self) -> list[tuple[int, int]]:
        return []

    def taken(self):
        self.board.demi_coups = 0
        self.board.pieces[self.color].remove(self)

    def is_checking(self):
        return self.board.find_king(self.board.game.op_color(self.color)).case in self.possible_moves()

    def valid_moves(self) -> list[tuple[int, int]]:
        return [move for move in self.possible_moves() if not self.board.will_check(self, move)]

    def display(self):
        self.board.game.screen.blit(self.image, (self.case[1] * self.board.cell_width, self.case[0] * self.board.cell_height))


class Pawn(Piece):
    value = 1
    type = "Pawn"

    def possible_moves(self) -> list[tuple[int, int]]:
        moves = []
        front_direction = 1 if self.color == Color.WHITE else -1
        next_case = self.dep(front_direction, 0)
        r_front = self.dep(0, 1, next_case)
        l_front = self.dep(0, -1, next_case)
        if self.board.accessible(self, next_case) and not self.board.is_occupied(next_case):
            moves.append(next_case)
            double_front = self.dep(front_direction, 0, next_case)
            if self.unmoved and self.board.accessible(self, double_front) and not self.board.is_occupied(double_front):
                moves.append(double_front)
        if (self.board.accessible(self, r_front) and self.board.is_occupied(r_front)) or r_front == self.board.en_passant:
            moves.append(r_front)
        if (self.board.accessible(self, l_front) and self.board.is_occupied(l_front)) or l_front == self.board.en_passant:
            moves.append(l_front)
        return moves

    def move(self, case, old_case):
        if case == self.board.en_passant:
            print("Take that shit")
            self.board.set_piece(None, (old_case[0], self.board.en_passant[1]))
        super().move(case, old_case)
        self.board.demi_coups = 0
        if abs(case[0] - old_case[0]) == 2:
            self.board.en_passant = (case[0] + old_case[0]) / 2, case[1]
        if case[0] == self.board.length-1 or case[0] == 0:
            self.promotion()

    def promotion(self):
        new_queen = Queen(self.board, self.case, self.color)
        self.board.place_piece(new_queen, self.case)
        self.board.pieces[self.color].remove(self)
        self.board.pieces[self.color].append(new_queen)

class Rook(Piece):
    value = 5
    type = "Rook"

    def possible_moves(self) -> list[tuple[int, int]]:
        moves = []
        for direction in [(0, 1), (-1, 0), (0, -1), (1, 0)]:
            next_case = self.case
            i = 1
            while True:
                next_case = self.dep(*direction, next_case)
                if self.board.accessible(self, next_case):
                    moves.append(next_case)
                else:
                    break
                if self.board.has_opposite_color(self.case, next_case):
                    break
                i += 1
        return moves

    def is_rook(self, color) -> bool:
        return self.color == color

class Knight(Piece):
    value = 3
    type = "Knight"

    def possible_moves(self) -> list[tuple[int, int]]:
        moves = []
        for direction in [(0, 2), (-2, 0), (0, -2), (2, 0)]:
            next_case = self.dep(*direction)
            n1 = self.dep(direction[0] == 0, direction[1] == 0, next_case)
            n2 = self.dep((- direction[0] == 0), - (direction[1] == 0), next_case)
            if self.board.accessible(self, n1):
                moves.append(n1)
            if self.board.accessible(self, n2):
                moves.append(n2)
        return moves

    def fen_notation(self):
        return "n" if self.color == Color.BLACK else "N"


class Bishop(Piece):
    value = 3
    type = "Bishop"

    def possible_moves(self) -> list[tuple[int, int]]:
        moves = []
        for direction in [(-1, 1), (-1, -1), (1, -1), (1, 1)]:
            next_case = self.case
            i = 1
            while True:
                next_case = self.dep(*direction, next_case)
                if self.board.accessible(self, next_case):
                    moves.append(next_case)
                else:
                    break
                if self.board.has_opposite_color(self.case, next_case):
                    break
                i += 1
        return moves


class Queen(Piece):
    value = 9
    type = "Queen"

    def possible_moves(self) -> list[tuple[int, int]]:
        moves = []
        for direction in [(0, 1), (-1, 0), (0, -1), (1, 0), (-1, 1), (-1, -1), (1, -1), (1, 1)]:
            next_case = self.case
            i = 1
            while True:
                next_case = self.dep(*direction, next_case)
                if self.board.accessible(self, next_case):
                    moves.append(next_case)
                else:
                    break
                if self.board.has_opposite_color(self.case, next_case):
                    break
                i += 1
        return moves


class King(Piece):
    value = 0
    type = "King"

    def is_king(self, color) -> bool:
        return self.color == color

    def possible_moves(self) -> list[tuple[int, int]]:
        moves = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    next_case = self.dep(dx, dy)
                    if self.board.accessible(self, next_case):
                        moves.append(next_case)
        if self.can_roque("small"):
            moves.append((self.case[0], 1))
        elif self.can_roque("big"):
            moves.append((self.case[0], 5))

        return moves

    def roque_allow(self, roque_type):
        if roque_type == "small":
            case = (self.case[0], 0)
        elif roque_type == "big":
            case = (self.case[0], self.board.height - 1)
        else:
            raise NotImplementedError
        return self.unmoved and self.board.is_occupied(case) and self.board.select_case(case).unmoved

    def can_roque(self, roque_type):
        if roque_type == "small":
            case = (self.case[0], 0)
        elif roque_type == "big":
            case = (self.case[0], self.board.height - 1)
        else:
            raise NotImplementedError
        if self.roque_allow(roque_type):
            piece = self.board.select_case(case)
            if piece.is_rook(self.color):
                for j in range(min(self.case[1], piece.case[1]) + 1, max(self.case[1], piece.case[1])):
                    if self.board.is_occupied((self.case[0], j)):
                        return False
                else:
                    return True

    def move(self, case, old_case):
        super().move(case, old_case)
        if abs(case[1] - old_case[1]) == 2:
            if case[1] == 1:
                self.board.set_piece(self.board.select_case((self.case[0], 0)), (self.case[0], 2))
            elif case[1] == 5:
                self.board.set_piece(self.board.select_case((self.case[0], self.board.length-1)), (self.case[0], 4))

