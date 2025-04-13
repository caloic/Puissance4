"""
Protocole de communication entre le client et le serveur pour le jeu Puissance 4.
"""
import json
from enum import Enum, auto


class MessageType(Enum):
    """Types de messages échangés entre client et serveur."""
    JOIN_QUEUE = auto()  # Client rejoint la file d'attente
    MATCH_FOUND = auto()  # Le serveur informe qu'un match a été trouvé
    GAME_START = auto()  # Le serveur démarre la partie
    PLAY_MOVE = auto()  # Client joue un coup
    MOVE_PLAYED = auto()  # Serveur informe d'un coup joué
    GAME_END = auto()  # Serveur informe de la fin de partie
    ERROR = auto()  # Message d'erreur
    LEAVE_QUEUE = auto()  # Client quitte la file d'attente
    DISCONNECT = auto()  # Client se déconnecte


class GameResult(Enum):
    """Résultats possibles d'une partie."""
    PLAYER1_WIN = auto()
    PLAYER2_WIN = auto()
    DRAW = auto()
    IN_PROGRESS = auto()


def create_message(msg_type, data=None):
    """
    Crée un message formaté pour la communication.

    Args:
        msg_type (MessageType): Type du message
        data (dict, optional): Données du message

    Returns:
        bytes: Message encodé prêt à être envoyé
    """
    if data is None:
        data = {}

    message = {
        "type": msg_type.name,
        "data": data
    }

    # Encode en JSON puis en bytes avec un caractère de fin de message
    return (json.dumps(message) + "\n").encode('utf-8')


def parse_message(message_bytes):
    """
    Parse un message reçu.

    Args:
        message_bytes (bytes): Message reçu

    Returns:
        tuple: (MessageType, dict) Le type de message et les données
    """
    try:
        # Décode le message
        message_str = message_bytes.decode('utf-8').strip()
        message = json.loads(message_str)

        # Extrait le type et les données
        msg_type = MessageType[message["type"]]
        data = message["data"]

        return msg_type, data
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        # En cas d'erreur, retourne un message d'erreur
        return MessageType.ERROR, {"error": str(e)}