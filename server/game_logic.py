"""
Logique du jeu Puissance 4 pour le serveur de matchmaking.
"""
from common.protocol import GameResult


class ConnectFourGame:
    """Implémentation de la logique du jeu Puissance 4."""

    def __init__(self):
        """Initialise un nouveau jeu de Puissance 4."""
        # Plateau 7 colonnes x 6 lignes (vide = 0, joueur 1 = 1, joueur 2 = 2)
        self.board = [[0 for _ in range(7)] for _ in range(6)]
        # Le joueur 1 commence
        self.current_player = 1
        self.is_game_over = False
        self.result = GameResult.IN_PROGRESS

    def load_board(self, board):
        """
        Charge un plateau existant.

        Args:
            board (list): Le plateau à charger
        """
        self.board = board
        # Détermine le joueur actuel en fonction du nombre de pièces
        pieces_count = sum(row.count(1) for row in board) + sum(row.count(2) for row in board)
        self.current_player = 1 if pieces_count % 2 == 0 else 2
        # Vérifie si le jeu est terminé
        self.check_game_over()

    def is_valid_move(self, column):
        """
        Vérifie si un mouvement est valide.

        Args:
            column (int): La colonne où placer la pièce (0-6)

        Returns:
            bool: True si le mouvement est valide
        """
        # Vérifier si la colonne est dans les limites
        if not 0 <= column < 7:
            return False

        # Vérifier si la colonne n'est pas pleine
        return self.board[0][column] == 0

    def make_move(self, column, player=None):
        """
        Joue un coup.

        Args:
            column (int): La colonne où placer la pièce (0-6)
            player (int, optional): Le joueur qui joue (1 ou 2). Si None, utilise le joueur actuel.

        Returns:
            tuple: (bool, int) - (Succès du coup, ligne où la pièce a atterri)
        """
        if self.is_game_over:
            return False, -1

        if player is None:
            player = self.current_player

        if not self.is_valid_move(column):
            return False, -1

        # Trouver la ligne la plus basse disponible dans la colonne
        row = 5
        while row >= 0 and self.board[row][column] != 0:
            row -= 1

        # Placer la pièce
        self.board[row][column] = player

        # Vérifier si le jeu est terminé
        self.check_game_over()

        # Changer de joueur
        if not self.is_game_over:
            self.current_player = 3 - player  # Alterne entre 1 et 2

        return True, row

    def check_game_over(self):
        """
        Vérifie si le jeu est terminé (victoire ou match nul).

        Returns:
            bool: True si le jeu est terminé
        """
        # Vérifier une victoire horizontale
        for row in range(6):
            for col in range(4):
                if (self.board[row][col] != 0 and
                        self.board[row][col] == self.board[row][col + 1] ==
                        self.board[row][col + 2] == self.board[row][col + 3]):
                    self.is_game_over = True
                    self.result = GameResult.PLAYER1_WIN if self.board[row][col] == 1 else GameResult.PLAYER2_WIN
                    return True

        # Vérifier une victoire verticale
        for row in range(3):
            for col in range(7):
                if (self.board[row][col] != 0 and
                        self.board[row][col] == self.board[row + 1][col] ==
                        self.board[row + 2][col] == self.board[row + 3][col]):
                    self.is_game_over = True
                    self.result = GameResult.PLAYER1_WIN if self.board[row][col] == 1 else GameResult.PLAYER2_WIN
                    return True

        # Vérifier une victoire diagonale (bas gauche vers haut droit)
        for row in range(3, 6):
            for col in range(4):
                if (self.board[row][col] != 0 and
                        self.board[row][col] == self.board[row - 1][col + 1] ==
                        self.board[row - 2][col + 2] == self.board[row - 3][col + 3]):
                    self.is_game_over = True
                    self.result = GameResult.PLAYER1_WIN if self.board[row][col] == 1 else GameResult.PLAYER2_WIN
                    return True

        # Vérifier une victoire diagonale (haut gauche vers bas droit)
        for row in range(3):
            for col in range(4):
                if (self.board[row][col] != 0 and
                        self.board[row][col] == self.board[row + 1][col + 1] ==
                        self.board[row + 2][col + 2] == self.board[row + 3][col + 3]):
                    self.is_game_over = True
                    self.result = GameResult.PLAYER1_WIN if self.board[row][col] == 1 else GameResult.PLAYER2_WIN
                    return True

        # Vérifier un match nul (plateau plein)
        if all(self.board[0][col] != 0 for col in range(7)):
            self.is_game_over = True
            self.result = GameResult.DRAW
            return True

        return False

    def get_board(self):
        """
        Renvoie le plateau actuel.

        Returns:
            list: Le plateau de jeu
        """
        return self.board

    def get_winner(self):
        """
        Renvoie le résultat du jeu.

        Returns:
            GameResult: Le résultat du jeu
        """
        return self.result