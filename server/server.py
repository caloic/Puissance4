"""
Serveur principal pour le jeu Puissance 4.
Gère les connexions clients et les messages.
"""
import socket
import threading
import time
import select
from server.database import Database
from server.matchmaking import MatchmakingManager
from common.protocol import MessageType, create_message, parse_message

class GameServer:
    """Serveur de jeu pour Puissance 4."""

    def __init__(self, host='0.0.0.0', port=5555):
        """
        Initialise le serveur.

        Args:
            host (str): Adresse d'écoute du serveur
            port (int): Port d'écoute du serveur
        """
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}  # {(ip, port): {"socket": socket, "name": name}}
        self.running = False
        self.db = Database()
        self.matchmaking = MatchmakingManager(self.db, self._on_match_created)

    def start(self):
        """Démarre le serveur."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.server_socket.setblocking(False)

            print(f"Serveur démarré sur {self.host}:{self.port}")

            self.running = True
            self.matchmaking.start()

            # Thread principal pour accepter les connexions
            accept_thread = threading.Thread(target=self._accept_connections)
            accept_thread.daemon = True
            accept_thread.start()

            # Attendre que le thread se termine
            while self.running:
                time.sleep(0.1)

        except Exception as e:
            print(f"Erreur au démarrage du serveur: {e}")
        finally:
            self.stop()

    def stop(self):
        """Arrête le serveur."""
        self.running = False
        self.matchmaking.stop()

        # Fermer toutes les connexions client
        for client_info in self.clients.values():
            try:
                client_info["socket"].close()
            except:
                pass

        # Fermer le socket serveur
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        # Fermer la base de données
        self.db.close()

        print("Serveur arrêté")

    def _accept_connections(self):
        """Thread pour accepter les connexions entrantes."""
        while self.running:
            try:
                # Utiliser select pour accepter des connexions sans bloquer
                readable, _, _ = select.select([self.server_socket], [], [], 0.5)

                if self.server_socket in readable:
                    client_socket, client_address = self.server_socket.accept()
                    client_socket.setblocking(True)  # Mettre le socket client en mode bloquant

                    # Créer un thread pour gérer ce client
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                    print(f"Nouvelle connexion de {client_address[0]}:{client_address[1]}")

            except Exception as e:
                if self.running:  # Ignorer les erreurs pendant l'arrêt
                    print(f"Erreur lors de l'acceptation des connexions: {e}")
                    time.sleep(1)  # Attendre un peu avant de réessayer

    def _handle_client(self, client_socket, client_address):
        """
        Gère la communication avec un client.

        Args:
            client_socket (socket): Socket du client
            client_address (tuple): Adresse du client (ip, port)
        """
        # Enregistrer le client
        self.clients[client_address] = {
            "socket": client_socket,
            "name": f"Guest_{client_address[0]}_{client_address[1]}"
        }

        # Configurer le socket en mode bloquant avec timeout
        client_socket.setblocking(True)
        client_socket.settimeout(0.5)  # Timeout de 500ms

        buffer = b""

        try:
            while self.running:
                try:
                    # Recevoir des données
                    data = client_socket.recv(4096)
                    if not data:
                        # Connexion fermée par le client
                        break

                    buffer += data

                    # Traiter tous les messages complets dans le buffer
                    while b"\n" in buffer:
                        message_bytes, buffer = buffer.split(b"\n", 1)

                        # Traiter le message
                        self._process_message(message_bytes, client_address)

                except socket.timeout:
                    # Ignorer les timeouts, c'est normal
                    continue
                except socket.error as e:
                    if hasattr(e, 'errno') and e.errno == 10035:  # WSAEWOULDBLOCK
                        # Opération non bloquante qui n'a pas pu être complétée immédiatement
                        # C'est normal, continuer
                        continue
                    else:
                        # Autre erreur socket
                        raise

        except Exception as e:
            print(f"Erreur lors de la communication avec {client_address}: {e}")

        finally:
            # Déconnecter le client
            print(f"Client déconnecté: {client_address[0]}:{client_address[1]}")

            # Retirer le client de la file d'attente s'il y est
            self.db.remove_from_queue(client_address[0], client_address[1])

            # Fermer le socket
            try:
                client_socket.close()
            except:
                pass

            # Supprimer le client de la liste
            if client_address in self.clients:
                del self.clients[client_address]

    def _process_message(self, message_bytes, client_address):
        """
        Traite un message reçu d'un client.

        Args:
            message_bytes (bytes): Message reçu
            client_address (tuple): Adresse du client (ip, port)
        """
        msg_type, data = parse_message(message_bytes)

        if msg_type == MessageType.ERROR:
            print(f"Erreur de parsing du message: {data['error']}")
            return

        # Traiter selon le type de message
        if msg_type == MessageType.JOIN_QUEUE:
            self._handle_join_queue(client_address, data)

        elif msg_type == MessageType.LEAVE_QUEUE:
            self._handle_leave_queue(client_address)

        elif msg_type == MessageType.PLAY_MOVE:
            self._handle_play_move(client_address, data)

        elif msg_type == MessageType.QUEUE_INFO_REQUEST:
            self._handle_queue_info_request(client_address)

        elif msg_type == MessageType.DISCONNECT:
            # Le client va se déconnecter, rien à faire ici
            pass

        else:
            # Type de message non reconnu ou non autorisé pour un client
            print(f"Type de message non géré: {msg_type.name}")
            self._send_error(client_address, "Type de message non géré")

    def _handle_queue_info_request(self, client_address):
        """
        Gère un message de type QUEUE_INFO_REQUEST.

        Args:
            client_address (tuple): Adresse du client (ip, port)
        """
        # Récupérer les informations sur la file d'attente
        players_in_queue = len(self.db.get_queue())

        # Compter le nombre total de joueurs connectés (incluant ceux qui ne sont pas en file d'attente)
        total_players_online = len(self.clients)

        # Compter le nombre de matchs en cours
        self.db.cursor.execute("SELECT COUNT(*) FROM matches WHERE is_finished = 0")
        games_in_progress = self.db.cursor.fetchone()[0]

        # Envoyer les informations au client
        self._send_message(client_address, MessageType.QUEUE_INFO_RESPONSE, {
            "players_in_queue": players_in_queue,
            "games_in_progress": games_in_progress,
            "players_online": total_players_online
        })

    def _handle_join_queue(self, client_address, data):
        """
        Gère un message de type JOIN_QUEUE.

        Args:
            client_address (tuple): Adresse du client (ip, port)
            data (dict): Données du message
        """
        player_name = data.get("name", f"Guest_{client_address[0]}_{client_address[1]}")

        # Mettre à jour le nom du client
        if client_address in self.clients:
            self.clients[client_address]["name"] = player_name

        # Ajouter le joueur à la file d'attente
        self.db.add_to_queue(client_address[0], client_address[1], player_name)

        print(f"Joueur {player_name} ({client_address[0]}:{client_address[1]}) ajouté à la file d'attente")

        # Confirmer au client qu'il est dans la file d'attente
        self._send_message(client_address, MessageType.JOIN_QUEUE, {
            "status": "success",
            "message": "Vous êtes dans la file d'attente"
        })

    def _handle_leave_queue(self, client_address):
        """
        Gère un message de type LEAVE_QUEUE.

        Args:
            client_address (tuple): Adresse du client (ip, port)
        """
        # Retirer le joueur de la file d'attente
        removed = self.db.remove_from_queue(client_address[0], client_address[1])

        # Vérifier également si le joueur est dans un match actif
        match = self.db.get_active_match_by_player(client_address[0], client_address[1])

        if removed:
            print(f"Joueur ({client_address[0]}:{client_address[1]}) retiré de la file d'attente")

            # Confirmer au client qu'il a quitté la file d'attente
            self._send_message(client_address, MessageType.LEAVE_QUEUE, {
                "status": "success",
                "message": "Vous avez quitté la file d'attente"
            })
        elif match:
            # Le joueur n'était pas dans la file d'attente mais dans un match
            self._send_message(client_address, MessageType.LEAVE_QUEUE, {
                "status": "success",
                "message": "Vous n'étiez pas dans la file d'attente (match en cours/terminé)"
            })
        else:
            # Message plus informatif au lieu d'une erreur
            self._send_message(client_address, MessageType.LEAVE_QUEUE, {
                "status": "success",
                "message": "Vous n'étiez pas dans la file d'attente"
            })

    def _handle_play_move(self, client_address, data):
        """
        Gère un message de type PLAY_MOVE.

        Args:
            client_address (tuple): Adresse du client (ip, port)
            data (dict): Données du message
        """
        match_id = data.get("match_id")
        column = data.get("column")

        if match_id is None or column is None:
            self._send_error(client_address, "Paramètres manquants")
            return

        # Récupérer le match
        match_data = self.db.get_match(match_id)
        if not match_data:
            self._send_error(client_address, "Match non trouvé")
            return

        # Déterminer quel joueur joue
        player_number = None
        if match_data["player1_ip"] == client_address[0] and match_data["player1_port"] == client_address[1]:
            player_number = 1
        elif match_data["player2_ip"] == client_address[0] and match_data["player2_port"] == client_address[1]:
            player_number = 2

        if player_number is None:
            self._send_error(client_address, "Vous ne participez pas à ce match")
            return

        # Enregistrer le coup
        success, move_info = self.matchmaking.record_move(match_id, player_number, column)

        if not success:
            self._send_error(client_address, move_info.get("error", "Erreur inconnue"))
            return

        # Informer les deux joueurs du coup joué
        self._notify_move_played(match_data, move_info)

        # Si le jeu est terminé, informer les joueurs
        if move_info.get("is_game_over", False):
            self._notify_game_end(match_data, move_info)

    def _notify_move_played(self, match_data, move_info):
        """
        Informe les joueurs d'un coup joué.

        Args:
            match_data (dict): Données du match
            move_info (dict): Informations sur le coup joué
        """
        # Adresses des joueurs
        player1_addr = (match_data["player1_ip"], match_data["player1_port"])
        player2_addr = (match_data["player2_ip"], match_data["player2_port"])

        # Informer le joueur 1
        self._send_message(player1_addr, MessageType.MOVE_PLAYED, {
            "match_id": move_info["match_id"],
            "player": move_info["player"],
            "column": move_info["column"],
            "row": move_info["row"],
            "board": move_info["board"],
            "your_turn": move_info["next_player"] == 1
        })

        # Informer le joueur 2
        self._send_message(player2_addr, MessageType.MOVE_PLAYED, {
            "match_id": move_info["match_id"],
            "player": move_info["player"],
            "column": move_info["column"],
            "row": move_info["row"],
            "board": move_info["board"],
            "your_turn": move_info["next_player"] == 2
        })

    def _notify_game_end(self, match_data, move_info):
        """
        Informe les joueurs de la fin du jeu.

        Args:
            match_data (dict): Données du match
            move_info (dict): Informations sur le coup final
        """
        # Adresses des joueurs
        player1_addr = (match_data["player1_ip"], match_data["player1_port"])
        player2_addr = (match_data["player2_ip"], match_data["player2_port"])

        # Déterminer le résultat pour chaque joueur
        result = move_info["result"]

        # Informer le joueur 1
        self._send_message(player1_addr, MessageType.GAME_END, {
            "match_id": move_info["match_id"],
            "board": move_info["board"],
            "result": result,
            "winner": 1 if result == "PLAYER1_WIN" else (2 if result == "PLAYER2_WIN" else None)
        })

        # Informer le joueur 2
        self._send_message(player2_addr, MessageType.GAME_END, {
            "match_id": move_info["match_id"],
            "board": move_info["board"],
            "result": result,
            "winner": 1 if result == "PLAYER1_WIN" else (2 if result == "PLAYER2_WIN" else None)
        })

    def _on_match_created(self, match_id, player1, player2):
        """
        Callback appelé quand un match est créé.

        Args:
            match_id (int): ID du match créé
            player1 (dict): Informations sur le joueur 1
            player2 (dict): Informations sur le joueur 2
        """
        # Adresses des joueurs
        player1_addr = (player1["player_ip"], player1["player_port"])
        player2_addr = (player2["player_ip"], player2["player_port"])

        # Informer les joueurs qu'un match a été trouvé
        for player_addr in [player1_addr, player2_addr]:
            self._send_message(player_addr, MessageType.MATCH_FOUND, {
                "match_id": match_id,
                "player1_name": player1["player_name"],
                "player2_name": player2["player_name"]
            })

        # Démarrer la partie
        time.sleep(1)  # Petit délai pour laisser le temps aux clients de traiter le message précédent

        match_data = self.db.get_match(match_id)

        # Informer le joueur 1 que c'est son tour
        self._send_message(player1_addr, MessageType.GAME_START, {
            "match_id": match_id,
            "your_player": 1,
            "your_turn": True,
            "opponent_name": player2["player_name"],
            "board": match_data["board"]
        })

        # Informer le joueur 2 que c'est le tour du joueur 1
        self._send_message(player2_addr, MessageType.GAME_START, {
            "match_id": match_id,
            "your_player": 2,
            "your_turn": False,
            "opponent_name": player1["player_name"],
            "board": match_data["board"]
        })

    def _send_message(self, client_address, msg_type, data):
        """
        Envoie un message à un client.

        Args:
            client_address (tuple): Adresse du client (ip, port)
            msg_type (MessageType): Type de message
            data (dict): Données du message
        """
        if client_address in self.clients:
            try:
                message = create_message(msg_type, data)
                self.clients[client_address]["socket"].sendall(message)
            except Exception as e:
                print(f"Erreur lors de l'envoi d'un message à {client_address}: {e}")

    def _send_error(self, client_address, error_message):
        """
        Envoie un message d'erreur à un client.

        Args:
            client_address (tuple): Adresse du client (ip, port)
            error_message (str): Message d'erreur
        """
        self._send_message(client_address, MessageType.ERROR, {
            "error": error_message
        })