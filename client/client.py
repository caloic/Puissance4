"""
Client principal pour le jeu Puissance 4.
"""
import threading
import tkinter as tk
from client.network import NetworkClient
from client.gui import ConnectFourGUI
from common.protocol import MessageType


class GameClient:
    """Client de jeu pour Puissance 4."""

    def __init__(self, host='localhost', port=5555):
        """
        Initialise le client de jeu.

        Args:
            host (str): Adresse du serveur
            port (int): Port du serveur
        """
        self.host = host
        self.port = port
        self.network = NetworkClient(host, port, self._on_message_received)
        self.gui = None
        self.in_queue = False
        self.match_id = None
        self.player_number = None
        self.players_in_queue = 0
        self.games_in_progress = 0
        self.players_online = 0
        self.last_queue_request = 0

    def start(self):
        """Démarre le client."""
        # Créer l'interface graphique
        self.gui = ConnectFourGUI(
            play_callback=self._on_play,
            join_queue_callback=self._on_join_queue,
            leave_queue_callback=self._on_leave_queue,
            get_queue_info_callback=self._on_get_queue_info
        )

        # Connecter au serveur
        connection_thread = threading.Thread(target=self._connect_to_server)
        connection_thread.daemon = True
        connection_thread.start()

        # Lancer l'interface graphique
        self.gui.run()

        # Déconnexion
        if self.network.connected:
            self.network.disconnect()

    def _connect_to_server(self):
        """Connecte au serveur."""
        connected = self.network.connect()

        # Mettre à jour l'interface
        if self.gui:
            self.gui.set_connected(connected)

            if not connected:
                self.gui.show_error(f"Impossible de se connecter au serveur {self.host}:{self.port}")
            else:
                # Demander les informations de la file d'attente
                self._request_queue_info()

    def _on_message_received(self, msg_type, data):
        """
        Gère les messages reçus du serveur.

        Args:
            msg_type (MessageType): Type de message
            data (dict): Données du message
        """
        if msg_type == MessageType.JOIN_QUEUE:
            self._handle_join_queue_response(data)

        elif msg_type == MessageType.LEAVE_QUEUE:
            self._handle_leave_queue_response(data)

        elif msg_type == MessageType.MATCH_FOUND:
            self._handle_match_found(data)

        elif msg_type == MessageType.GAME_START:
            self._handle_game_start(data)

        elif msg_type == MessageType.MOVE_PLAYED:
            self._handle_move_played(data)

        elif msg_type == MessageType.GAME_END:
            self._handle_game_end(data)

        elif msg_type == MessageType.QUEUE_INFO_RESPONSE:
            self._handle_queue_info_response(data)

        elif msg_type == MessageType.ERROR:
            self._handle_error(data)

    def _handle_join_queue_response(self, data):
        """
        Gère la réponse à un message JOIN_QUEUE.

        Args:
            data (dict): Données du message
        """
        if data.get("status") == "success":
            self.in_queue = True

            # Mettre à jour l'interface
            if self.gui:
                self.gui.set_in_queue(True)

            # Demander les informations mises à jour de la file d'attente
            self._request_queue_info()

    def _handle_leave_queue_response(self, data):
        """
        Gère la réponse à un message LEAVE_QUEUE.

        Args:
            data (dict): Données du message
        """
        if data.get("status") == "success":
            self.in_queue = False

            # Mettre à jour l'interface
            if self.gui:
                self.gui.set_in_queue(False)

            # Demander les informations mises à jour de la file d'attente
            self._request_queue_info()

    def _handle_match_found(self, data):
        """
        Gère un message MATCH_FOUND.

        Args:
            data (dict): Données du message
        """
        match_id = data.get("match_id")
        player1_name = data.get("player1_name")
        player2_name = data.get("player2_name")

        if match_id is not None:
            self.match_id = match_id
            self.in_queue = False

            # Afficher un message
            if self.gui:
                self.gui.show_info(f"Match trouvé !\nJoueur 1: {player1_name}\nJoueur 2: {player2_name}")

            # Demander les informations mises à jour de la file d'attente
            self._request_queue_info()

    def _handle_game_start(self, data):
        """
        Gère un message GAME_START.

        Args:
            data (dict): Données du message
        """
        match_id = data.get("match_id")
        your_player = data.get("your_player")
        your_turn = data.get("your_turn")
        opponent_name = data.get("opponent_name")
        board = data.get("board")

        if match_id is not None and your_player is not None and board is not None:
            self.match_id = match_id
            self.player_number = your_player

            # Démarrer la partie dans l'interface
            if self.gui:
                self.gui.start_game(match_id, your_player, your_turn, opponent_name, board)

    def _handle_move_played(self, data):
        """
        Gère un message MOVE_PLAYED.

        Args:
            data (dict): Données du message
        """
        match_id = data.get("match_id")
        board = data.get("board")
        your_turn = data.get("your_turn")

        if match_id == self.match_id and board is not None:
            # Mettre à jour la partie dans l'interface
            if self.gui:
                self.gui.update_game(board, your_turn)

    def _handle_game_end(self, data):
        """
        Gère un message GAME_END.

        Args:
            data (dict): Données du message
        """
        match_id = data.get("match_id")
        board = data.get("board")
        winner = data.get("winner")

        if match_id == self.match_id and board is not None:
            # Terminer la partie dans l'interface
            if self.gui:
                self.gui.end_game(board, winner)

            # Réinitialiser l'état
            self.match_id = None
            self.player_number = None

            # Demander les informations mises à jour de la file d'attente
            self._request_queue_info()

    def _handle_queue_info_response(self, data):
        """
        Gère la réponse à un message QUEUE_INFO_REQUEST.

        Args:
            data (dict): Données du message
        """
        players_in_queue = data.get("players_in_queue", 0)
        games_in_progress = data.get("games_in_progress", 0)
        players_online = data.get("players_online", 0)  # Récupérer le nombre total de joueurs

        # Mettre à jour l'état local
        self.players_in_queue = players_in_queue
        self.games_in_progress = games_in_progress
        self.players_online = players_online  # Stocker le nombre total

        # Mettre à jour l'interface
        if self.gui:
            self.gui.update_queue_info(players_online, games_in_progress)

    def _handle_error(self, data):
        """
        Gère un message ERROR.

        Args:
            data (dict): Données du message
        """
        error_message = data.get("error", "Erreur inconnue")

        # Afficher l'erreur dans l'interface
        if self.gui:
            self.gui.show_error(error_message)

    def _on_play(self, match_id, column):
        """
        Callback appelé quand le joueur joue un coup.

        Args:
            match_id (int): ID du match
            column (int): Colonne jouée (0-6)

        Returns:
            bool: True si le coup a été envoyé
        """
        return self.network.play_move(match_id, column)

    def _on_join_queue(self, player_name):
        """
        Callback appelé quand le joueur rejoint la file d'attente.

        Args:
            player_name (str): Nom du joueur

        Returns:
            bool: True si la demande a été envoyée
        """
        return self.network.join_queue(player_name)

    def _on_leave_queue(self):
        """
        Callback appelé quand le joueur quitte la file d'attente.

        Returns:
            bool: True si la demande a été envoyée
        """
        return self.network.leave_queue()

    def _on_get_queue_info(self):
        """
        Callback appelé quand l'interface demande des informations sur la file d'attente.
        """
        # Limiter la fréquence des requêtes (max 1 fois toutes les 2 secondes)
        import time
        current_time = time.time()
        if current_time - self.last_queue_request >= 2:
            self.last_queue_request = current_time
            self._request_queue_info()

    def _request_queue_info(self):
        """
        Demande des informations sur la file d'attente au serveur.
        """
        if self.network.connected:
            self.network.request_queue_info()