"""
Module de communication réseau pour le client Puissance 4.
"""
import socket
import threading
import queue
import time
from common.protocol import MessageType, create_message, parse_message

class NetworkClient:
    """Client réseau pour la communication avec le serveur."""

    def __init__(self, host='localhost', port=5555, message_callback=None):
        """
        Initialise le client réseau.

        Args:
            host (str): Adresse du serveur
            port (int): Port du serveur
            message_callback (callable): Fonction à appeler quand un message est reçu
        """
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.message_callback = message_callback
        self.receive_thread = None
        self.send_queue = queue.Queue()
        self.send_thread = None

    def connect(self):
        """
        Établit la connexion avec le serveur.

        Returns:
            bool: True si la connexion a réussi
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.socket.setblocking(True)
            self.socket.settimeout(0.5)  # Timeout de 500ms
            self.connected = True

            # Démarrer le thread de réception
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()

            # Démarrer le thread d'envoi
            self.send_thread = threading.Thread(target=self._send_loop)
            self.send_thread.daemon = True
            self.send_thread.start()

            return True

        except Exception as e:
            print(f"Erreur de connexion: {e}")
            return False

    def disconnect(self):
        """Ferme la connexion avec le serveur."""
        if self.connected:
            try:
                # Envoyer un message de déconnexion
                self.send_message(MessageType.DISCONNECT)

                # Fermer le socket
                self.socket.close()
            except Exception as e:
                print(f"Erreur lors de la déconnexion: {e}")
            finally:
                self.connected = False

    def _receive_loop(self):
        """Boucle de réception des messages."""
        buffer = b""

        try:
            while self.connected:
                try:
                    # Recevoir des données
                    data = self.socket.recv(4096)
                    if not data:
                        # Connexion fermée par le serveur
                        break

                    buffer += data

                    # Traiter tous les messages complets dans le buffer
                    while b"\n" in buffer:
                        message_bytes, buffer = buffer.split(b"\n", 1)

                        # Traiter le message
                        msg_type, data = parse_message(message_bytes)

                        # Appeler le callback si défini
                        if self.message_callback:
                            self.message_callback(msg_type, data)

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
            if self.connected:  # Ignorer les erreurs après déconnexion
                print(f"Erreur lors de la réception: {e}")

        finally:
            # Marquer comme déconnecté
            self.connected = False

            # Appeler le callback avec une erreur si défini
            if self.message_callback:
                self.message_callback(MessageType.ERROR, {"error": "Déconnecté du serveur"})

    def _send_loop(self):
        """Boucle d'envoi des messages."""
        try:
            while self.connected:
                try:
                    # Récupérer un message de la file d'attente (avec timeout)
                    message = self.send_queue.get(timeout=0.1)

                    # Envoyer le message
                    self.socket.sendall(message)

                    # Marquer comme traité
                    self.send_queue.task_done()

                except queue.Empty:
                    # Ignorer les timeouts, c'est normal
                    continue
                except socket.error as e:
                    if hasattr(e, 'errno') and e.errno == 10035:  # WSAEWOULDBLOCK
                        # Réessayer plus tard
                        self.send_queue.put(message)
                        time.sleep(0.1)
                        continue
                    else:
                        # Autre erreur socket
                        raise

        except Exception as e:
            if self.connected:  # Ignorer les erreurs après déconnexion
                print(f"Erreur lors de l'envoi: {e}")

    def send_message(self, msg_type, data=None):
        """
        Envoie un message au serveur.

        Args:
            msg_type (MessageType): Type de message
            data (dict, optional): Données du message
        """
        if not self.connected:
            return False

        try:
            # Créer le message
            message = create_message(msg_type, data)

            # Ajouter à la file d'attente
            self.send_queue.put(message)

            return True

        except Exception as e:
            print(f"Erreur lors de la création du message: {e}")
            return False

    def join_queue(self, player_name):
        """
        Rejoint la file d'attente.

        Args:
            player_name (str): Nom du joueur
        """
        return self.send_message(MessageType.JOIN_QUEUE, {"name": player_name})

    def leave_queue(self):
        """Quitte la file d'attente."""
        return self.send_message(MessageType.LEAVE_QUEUE)

    def play_move(self, match_id, column):
        """
        Joue un coup.

        Args:
            match_id (int): ID du match
            column (int): Colonne jouée (0-6)
        """
        return self.send_message(MessageType.PLAY_MOVE, {
            "match_id": match_id,
            "column": column
        })

    def request_queue_info(self):
        """
        Demande des informations sur la file d'attente.

        Returns:
            bool: True si la demande a été envoyée
        """
        return self.send_message(MessageType.QUEUE_INFO_REQUEST)