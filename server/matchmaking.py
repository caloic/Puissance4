"""
Module de matchmaking pour le serveur.
Gère la file d'attente et la création de matchs.
"""
import threading
import time
from server.database import Database
from common.protocol import GameResult


class MatchmakingManager:
    """Gestionnaire de matchmaking pour le serveur."""

    def __init__(self, database, match_callback=None):
        """
        Initialise le gestionnaire de matchmaking.

        Args:
            database (Database): Instance de la base de données
            match_callback (callable, optional): Fonction appelée quand un match est créé
        """
        self.db = database
        self.match_callback = match_callback
        self.running = False
        self.thread = None
        self.active_matches = {}  # {match_id: game_instance}

    def start(self):
        """Démarre le thread de vérification de la file d'attente."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._check_queue_loop)
            self.thread.daemon = True
            self.thread.start()

    def stop(self):
        """Arrête le thread de vérification de la file d'attente."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _check_queue_loop(self):
        """Boucle de vérification de la file d'attente."""
        while self.running:
            try:
                self._match_players()
            except Exception as e:
                print(f"Erreur lors du matchmaking: {e}")

            # Attendre un peu avant de vérifier à nouveau
            time.sleep(1)

    def _match_players(self):
        """
        Vérifie la file d'attente et crée des matchs si possible.
        """
        # Récupérer les joueurs en attente
        queue = self.db.get_queue(limit=10)

        # S'il y a au moins 2 joueurs, créer un match
        if len(queue) >= 2:
            player1 = queue[0]
            player2 = queue[1]

            # Créer le match dans la base de données
            match_id = self.db.create_match(
                player1['player_ip'], player1['player_port'], player1['player_name'],
                player2['player_ip'], player2['player_port'], player2['player_name']
            )

            print(f"Match créé: {match_id} entre {player1['player_name']} et {player2['player_name']}")

            # Appeler le callback si défini
            if self.match_callback:
                self.match_callback(match_id, player1, player2)

    def record_move(self, match_id, player_number, column):
        """
        Enregistre un coup joué.

        Args:
            match_id (int): ID du match
            player_number (int): Numéro du joueur (1 ou 2)
            column (int): Colonne jouée (0-6)

        Returns:
            tuple: (bool, dict) - (Succès, Informations sur le coup)
        """
        # Récupérer le match
        match_data = self.db.get_match(match_id)
        if not match_data or match_data['is_finished']:
            return False, {"error": "Match non trouvé ou terminé"}

        # Vérifier que c'est bien le tour du joueur
        from server.game_logic import ConnectFourGame
        game = ConnectFourGame()
        game.load_board(match_data['board'])

        if game.current_player != player_number:
            return False, {"error": "Ce n'est pas votre tour"}

        # Jouer le coup
        success, row = game.make_move(column)
        if not success:
            return False, {"error": "Coup invalide"}

        # Mettre à jour le plateau dans la base de données
        self.db.update_board(match_id, game.get_board())

        # Enregistrer le tour
        turn_id = self.db.add_turn(match_id, player_number, column)

        # Vérifier si le jeu est terminé
        if game.is_game_over:
            self.db.finish_match(match_id, game.get_winner())

        # Retourner les informations du coup
        return True, {
            "match_id": match_id,
            "player": player_number,
            "column": column,
            "row": row,
            "board": game.get_board(),
            "is_game_over": game.is_game_over,
            "result": game.get_winner().name if game.is_game_over else None,
            "next_player": game.current_player
        }

    def get_match_status(self, match_id):
        """
        Récupère le statut actuel d'un match.

        Args:
            match_id (int): ID du match

        Returns:
            dict: Statut du match
        """
        match_data = self.db.get_match(match_id)
        if not match_data:
            return {"error": "Match non trouvé"}

        # Charger le jeu pour déterminer le joueur actuel et l'état de la partie
        from server.game_logic import ConnectFourGame
        game = ConnectFourGame()
        game.load_board(match_data['board'])

        return {
            "match_id": match_id,
            "board": game.get_board(),
            "current_player": game.current_player,
            "is_game_over": match_data['is_finished'] == 1,
            "result": match_data['result'] if match_data['is_finished'] == 1 else None,
            "player1": {
                "ip": match_data['player1_ip'],
                "port": match_data['player1_port'],
                "name": match_data['player1_name']
            },
            "player2": {
                "ip": match_data['player2_ip'],
                "port": match_data['player2_port'],
                "name": match_data['player2_name']
            }
        }