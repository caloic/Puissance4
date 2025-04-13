"""
Gestion de la base de données pour le serveur de matchmaking.
Stocke les informations sur la file d'attente, les matchs et les tours de jeu.
"""
import sqlite3
import json
import os
from datetime import datetime
from common.protocol import GameResult


class Database:
    """Classe gérant la base de données du serveur."""

    def __init__(self, db_path="server_data.db"):
        """
        Initialise la connexion à la base de données.

        Args:
            db_path (str): Chemin vers le fichier de base de données
        """
        # Vérifie si le fichier de base de données existe déjà
        db_exists = os.path.exists(db_path)

        # Connexion à la base de données
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
        self.cursor = self.conn.cursor()

        # Si la base de données n'existe pas, créer les tables
        if not db_exists:
            self._create_tables()

    def _create_tables(self):
        """Crée les tables nécessaires dans la base de données."""
        # Table pour la file d'attente
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_ip TEXT NOT NULL,
            player_port INTEGER NOT NULL,
            player_name TEXT NOT NULL,
            join_time TIMESTAMP NOT NULL
        )
        ''')

        # Table pour les matchs
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player1_ip TEXT NOT NULL,
            player1_port INTEGER NOT NULL,
            player1_name TEXT NOT NULL,
            player2_ip TEXT NOT NULL,
            player2_port INTEGER NOT NULL,
            player2_name TEXT NOT NULL,
            board TEXT NOT NULL,
            is_finished BOOLEAN NOT NULL DEFAULT 0,
            result TEXT,
            created_at TIMESTAMP NOT NULL,
            finished_at TIMESTAMP
        )
        ''')

        # Table pour les tours de jeu
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            player_number INTEGER NOT NULL,  -- 1 pour joueur 1, 2 pour joueur 2
            column_played INTEGER NOT NULL,
            played_at TIMESTAMP NOT NULL,
            FOREIGN KEY (match_id) REFERENCES matches (id)
        )
        ''')

        self.conn.commit()

    def add_to_queue(self, player_ip, player_port, player_name):
        """
        Ajoute un joueur à la file d'attente.

        Args:
            player_ip (str): Adresse IP du joueur
            player_port (int): Port du joueur
            player_name (str): Pseudo du joueur

        Returns:
            int: ID du joueur dans la file
        """
        # Vérifie si le joueur est déjà dans la file
        self.cursor.execute(
            "SELECT id FROM queue WHERE player_ip = ? AND player_port = ?",
            (player_ip, player_port)
        )
        existing = self.cursor.fetchone()

        if existing:
            # Si le joueur est déjà dans la file, mettre à jour son pseudo et l'heure
            self.cursor.execute(
                "UPDATE queue SET player_name = ?, join_time = ? WHERE id = ?",
                (player_name, datetime.now(), existing['id'])
            )
            self.conn.commit()
            return existing['id']
        else:
            # Sinon, ajouter le joueur à la file
            self.cursor.execute(
                "INSERT INTO queue (player_ip, player_port, player_name, join_time) VALUES (?, ?, ?, ?)",
                (player_ip, player_port, player_name, datetime.now())
            )
            self.conn.commit()
            return self.cursor.lastrowid

    def remove_from_queue(self, player_ip, player_port):
        """
        Retire un joueur de la file d'attente.

        Args:
            player_ip (str): Adresse IP du joueur
            player_port (int): Port du joueur

        Returns:
            bool: True si le joueur a été retiré, False sinon
        """
        self.cursor.execute(
            "DELETE FROM queue WHERE player_ip = ? AND player_port = ?",
            (player_ip, player_port)
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_queue(self, limit=10):
        """
        Récupère les joueurs dans la file d'attente, triés par ordre d'arrivée.

        Args:
            limit (int): Nombre maximum de joueurs à récupérer

        Returns:
            list: Liste des joueurs dans la file d'attente
        """
        self.cursor.execute(
            "SELECT * FROM queue ORDER BY join_time LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in self.cursor.fetchall()]

    def create_match(self, player1_ip, player1_port, player1_name,
                     player2_ip, player2_port, player2_name):
        """
        Crée un nouveau match entre deux joueurs.

        Args:
            player1_ip (str): IP du joueur 1
            player1_port (int): Port du joueur 1
            player1_name (str): Pseudo du joueur 1
            player2_ip (str): IP du joueur 2
            player2_port (int): Port du joueur 2
            player2_name (str): Pseudo du joueur 2

        Returns:
            int: ID du match créé
        """
        # Plateau vide pour Puissance 4 (7 colonnes x 6 lignes)
        empty_board = [[0 for _ in range(7)] for _ in range(6)]

        self.cursor.execute(
            """
            INSERT INTO matches (
                player1_ip, player1_port, player1_name,
                player2_ip, player2_port, player2_name,
                board, is_finished, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                player1_ip, player1_port, player1_name,
                player2_ip, player2_port, player2_name,
                json.dumps(empty_board), datetime.now()
            )
        )
        self.conn.commit()

        # Supprimer ces joueurs de la file d'attente
        self.remove_from_queue(player1_ip, player1_port)
        self.remove_from_queue(player2_ip, player2_port)

        return self.cursor.lastrowid

    def get_match(self, match_id):
        """
        Récupère les informations d'un match.

        Args:
            match_id (int): ID du match

        Returns:
            dict: Informations du match
        """
        self.cursor.execute("SELECT * FROM matches WHERE id = ?", (match_id,))
        match = self.cursor.fetchone()

        if match:
            match_dict = dict(match)
            # Convertir le plateau de JSON à liste Python
            match_dict['board'] = json.loads(match_dict['board'])
            return match_dict
        return None

    def get_active_match_by_player(self, player_ip, player_port):
        """
        Trouve le match actif d'un joueur.

        Args:
            player_ip (str): Adresse IP du joueur
            player_port (int): Port du joueur

        Returns:
            dict: Informations du match ou None
        """
        self.cursor.execute(
            """
            SELECT * FROM matches 
            WHERE is_finished = 0 AND (
                (player1_ip = ? AND player1_port = ?) OR 
                (player2_ip = ? AND player2_port = ?)
            )
            """,
            (player_ip, player_port, player_ip, player_port)
        )
        match = self.cursor.fetchone()

        if match:
            match_dict = dict(match)
            # Convertir le plateau de JSON à liste Python
            match_dict['board'] = json.loads(match_dict['board'])
            return match_dict
        return None

    def update_board(self, match_id, new_board):
        """
        Met à jour l'état du plateau de jeu.

        Args:
            match_id (int): ID du match
            new_board (list): Nouveau plateau de jeu

        Returns:
            bool: True si la mise à jour a réussi
        """
        self.cursor.execute(
            "UPDATE matches SET board = ? WHERE id = ?",
            (json.dumps(new_board), match_id)
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def add_turn(self, match_id, player_number, column_played):
        """
        Ajoute un tour de jeu.

        Args:
            match_id (int): ID du match
            player_number (int): Numéro du joueur (1 ou 2)
            column_played (int): Colonne jouée (0-6)

        Returns:
            int: ID du tour créé
        """
        self.cursor.execute(
            "INSERT INTO turns (match_id, player_number, column_played, played_at) VALUES (?, ?, ?, ?)",
            (match_id, player_number, column_played, datetime.now())
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_turns(self, match_id):
        """
        Récupère tous les tours d'un match.

        Args:
            match_id (int): ID du match

        Returns:
            list: Liste des tours joués
        """
        self.cursor.execute(
            "SELECT * FROM turns WHERE match_id = ? ORDER BY played_at",
            (match_id,)
        )
        return [dict(row) for row in self.cursor.fetchall()]

    def finish_match(self, match_id, result):
        """
        Termine un match avec un résultat.

        Args:
            match_id (int): ID du match
            result (GameResult): Résultat du match

        Returns:
            bool: True si la mise à jour a réussi
        """
        self.cursor.execute(
            "UPDATE matches SET is_finished = 1, result = ?, finished_at = ? WHERE id = ?",
            (result.name, datetime.now(), match_id)
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def close(self):
        """Ferme la connexion à la base de données."""
        if self.conn:
            self.conn.close()