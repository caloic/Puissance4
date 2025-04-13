"""
Point d'entrée pour le client Puissance 4.
"""
import sys
from client.client import GameClient

if __name__ == "__main__":
    # Paramètres par défaut
    host = 'localhost'
    port = 5555

    # Récupérer les paramètres depuis les arguments si fournis
    if len(sys.argv) > 1:
        host = sys.argv[1]

    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"Port invalide: {sys.argv[2]}. Utilisation du port par défaut: {port}")

    # Créer et démarrer le client
    print(f"Démarrage du client, connexion à {host}:{port}...")
    client = GameClient(host, port)
    client.start()