"""
Point d'entrée pour le serveur de matchmaking Puissance 4.
"""
import sys
import signal
from server.server import GameServer


def signal_handler(sig, frame):
    """
    Gère les signaux d'interruption (Ctrl+C).

    Args:
        sig: Signal reçu
        frame: Frame courante
    """
    print("\nArrêt du serveur...")
    if 'server' in globals():
        server.stop()
    sys.exit(0)


if __name__ == "__main__":
    # Configuration du gestionnaire de signal pour Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Port par défaut
    port = 5555

    # Récupérer le port depuis les arguments si fourni
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Port invalide: {sys.argv[1]}. Utilisation du port par défaut: {port}")

    # Créer et démarrer le serveur
    print(f"Démarrage du serveur sur le port {port}...")
    server = GameServer(port=port)
    server.start()