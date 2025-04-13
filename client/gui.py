"""
Interface graphique pour le client Puissance 4.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading


class ConnectFourGUI:
    """Interface graphique pour le jeu Puissance 4."""

    def __init__(self, play_callback=None, join_queue_callback=None, leave_queue_callback=None):
        """
        Initialise l'interface graphique.

        Args:
            play_callback (callable): Fonction à appeler quand un coup est joué
            join_queue_callback (callable): Fonction à appeler pour rejoindre la file d'attente
            leave_queue_callback (callable): Fonction à appeler pour quitter la file d'attente
        """
        self.play_callback = play_callback
        self.join_queue_callback = join_queue_callback
        self.leave_queue_callback = leave_queue_callback

        # État du jeu
        self.match_id = None
        self.player_number = None
        self.current_player = None
        self.board = [[0 for _ in range(7)] for _ in range(6)]
        self.is_game_over = False
        self.winner = None

        # Informations joueurs
        self.player_name = "Joueur"
        self.opponent_name = "Adversaire"

        # Créer la fenêtre principale
        self.root = tk.Tk()
        self.root.title("Puissance 4 - Matchmaking")
        self.root.geometry("800x700")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Définir le style
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Couleurs
        self.colors = {
            'bg': '#1E1E2E',
            'text': '#CDD6F4',
            'accent': '#89B4FA',
            'red': '#F38BA8',
            'yellow': '#F9E2AF',
            'green': '#A6E3A1',
            'button': '#313244',
            'button_hover': '#45475A',
            'board': '#313244',
            'empty': '#45475A',
            'player1': '#F38BA8',  # Rouge
            'player2': '#F9E2AF'  # Jaune
        }

        # Configurer les styles
        self.style.configure('TFrame', background=self.colors['bg'])
        self.style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['text'],
                             font=('Helvetica', 12))
        self.style.configure('TButton', background=self.colors['button'], foreground=self.colors['text'],
                             font=('Helvetica', 12))
        self.style.map('TButton', background=[('active', self.colors['button_hover'])])

        # Configurer la fenêtre
        self.root.configure(bg=self.colors['bg'])

        # Créer les widgets
        self._create_widgets()

        # Mettre à jour l'interface
        self._update_gui()

    def _create_widgets(self):
        """Crée les widgets de l'interface."""
        # Frame principale
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame d'en-tête
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 20))

        # Étiquette du titre
        self.title_label = ttk.Label(self.header_frame, text="Puissance 4", font=('Helvetica', 24, 'bold'))
        self.title_label.pack(side=tk.LEFT, pady=10)

        # Frame de statut
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, pady=(0, 20))

        # Étiquette de statut
        self.status_label = ttk.Label(self.status_frame, text="Non connecté au serveur", font=('Helvetica', 12))
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Boutons de file d'attente
        self.queue_frame = ttk.Frame(self.main_frame)
        self.queue_frame.pack(fill=tk.X, pady=(0, 20))

        self.join_queue_button = ttk.Button(self.queue_frame, text="Rejoindre la file d'attente",
                                            command=self._join_queue)
        self.join_queue_button.pack(side=tk.LEFT, padx=(0, 10))

        self.leave_queue_button = ttk.Button(self.queue_frame, text="Quitter la file d'attente",
                                             command=self._leave_queue)
        self.leave_queue_button.pack(side=tk.LEFT)
        self.leave_queue_button.config(state=tk.DISABLED)

        # Canvas pour le plateau de jeu
        self.board_frame = ttk.Frame(self.main_frame)
        self.board_frame.pack(fill=tk.BOTH, expand=True)

        self.board_canvas = tk.Canvas(self.board_frame, bg=self.colors['board'], highlightthickness=0)
        self.board_canvas.pack(fill=tk.BOTH, expand=True)

        # Bind des événements
        self.board_canvas.bind("<Motion>", self._on_mouse_move)
        self.board_canvas.bind("<Button-1>", self._on_mouse_click)

        # Frame de bas de page
        self.footer_frame = ttk.Frame(self.main_frame)
        self.footer_frame.pack(fill=tk.X, pady=(20, 0))

        # Informations des joueurs
        self.player_info_frame = ttk.Frame(self.footer_frame)
        self.player_info_frame.pack(fill=tk.X)

        self.player1_label = ttk.Label(self.player_info_frame, text="Joueur 1: -", font=('Helvetica', 12))
        self.player1_label.pack(side=tk.LEFT, padx=(0, 20))

        self.player2_label = ttk.Label(self.player_info_frame, text="Joueur 2: -", font=('Helvetica', 12))
        self.player2_label.pack(side=tk.LEFT)

        # Variables pour le dessin du plateau
        self.cell_size = 80
        self.piece_radius = 30
        self.highlight_column = None

    def _update_gui(self):
        """Met à jour l'interface graphique."""
        # Mettre à jour l'étiquette de statut
        if self.match_id is None:
            # Pas de match en cours
            if self.is_game_over:
                # Match terminé
                if self.winner == 0:
                    status_text = "Match nul !"
                elif self.winner == self.player_number:
                    status_text = "Vous avez gagné !"
                else:
                    status_text = "Vous avez perdu !"

                # Couleur selon le résultat
                if self.winner == 0:
                    self.status_label.config(foreground=self.colors['text'])
                elif self.winner == self.player_number:
                    self.status_label.config(foreground=self.colors['green'])
                else:
                    self.status_label.config(foreground=self.colors['red'])
            else:
                # En attente d'un match
                status_text = "En attente d'un match"
                self.status_label.config(foreground=self.colors['text'])
        else:
            # Match en cours
            if self.current_player == self.player_number:
                status_text = "C'est votre tour"
                self.status_label.config(foreground=self.colors['green'])
            else:
                status_text = f"C'est le tour de {self.opponent_name}"
                self.status_label.config(foreground=self.colors['text'])

        self.status_label.config(text=status_text)

        # Mettre à jour les informations des joueurs
        player1_text = f"Joueur 1: {self.player_name if self.player_number == 1 else self.opponent_name}"
        player2_text = f"Joueur 2: {self.player_name if self.player_number == 2 else self.opponent_name}"

        self.player1_label.config(text=player1_text, foreground=self.colors['player1'])
        self.player2_label.config(text=player2_text, foreground=self.colors['player2'])

        # Désactiver le bouton de rejoindre la file si un match est en cours
        if self.match_id is not None:
            self.join_queue_button.config(state=tk.DISABLED)
            self.leave_queue_button.config(state=tk.DISABLED)

        # Dessiner le plateau
        self._draw_board()

    def _draw_board(self):
        """Dessine le plateau de jeu."""
        # Effacer le canvas
        self.board_canvas.delete("all")

        # Calculer les dimensions du plateau
        board_width = 7 * self.cell_size
        board_height = 6 * self.cell_size

        # Centrer le plateau dans le canvas
        canvas_width = self.board_canvas.winfo_width()
        canvas_height = self.board_canvas.winfo_height()

        offset_x = (canvas_width - board_width) // 2
        offset_y = (canvas_height - board_height) // 2

        # Dessiner la bordure du plateau
        self.board_canvas.create_rectangle(
            offset_x - 10, offset_y - 10,
            offset_x + board_width + 10, offset_y + board_height + 10,
            fill=self.colors['board'], outline=self.colors['accent'], width=2
        )

        # Dessiner les cellules et les pièces
        for row in range(6):
            for col in range(7):
                # Position de la cellule
                x = offset_x + col * self.cell_size + self.cell_size // 2
                y = offset_y + row * self.cell_size + self.cell_size // 2

                # Dessiner la cellule
                self.board_canvas.create_oval(
                    x - self.piece_radius, y - self.piece_radius,
                    x + self.piece_radius, y + self.piece_radius,
                    fill=self.colors['empty'], outline=""
                )

                # Dessiner la pièce si présente
                if self.board[row][col] == 1:
                    self.board_canvas.create_oval(
                        x - self.piece_radius, y - self.piece_radius,
                        x + self.piece_radius, y + self.piece_radius,
                        fill=self.colors['player1'], outline=""
                    )
                elif self.board[row][col] == 2:
                    self.board_canvas.create_oval(
                        x - self.piece_radius, y - self.piece_radius,
                        x + self.piece_radius, y + self.piece_radius,
                        fill=self.colors['player2'], outline=""
                    )

        # Dessiner la colonne en surbrillance
        if self.highlight_column is not None and not self.is_game_over and self.match_id is not None and self.current_player == self.player_number:
            # Position de la cellule
            x = offset_x + self.highlight_column * self.cell_size + self.cell_size // 2
            y = offset_y - self.cell_size // 2

            # Dessiner la pièce fantôme
            self.board_canvas.create_oval(
                x - self.piece_radius, y - self.piece_radius,
                x + self.piece_radius, y + self.piece_radius,
                fill=self.colors['player1'] if self.player_number == 1 else self.colors['player2'],
                outline="",
                stipple="gray50"
            )

    def _on_mouse_move(self, event):
        """
        Gère le mouvement de la souris sur le plateau.

        Args:
            event: Événement de mouvement de souris
        """
        if self.match_id is None or self.is_game_over or self.current_player != self.player_number:
            self.highlight_column = None
            return

        # Calculer les dimensions du plateau
        board_width = 7 * self.cell_size

        # Centrer le plateau dans le canvas
        canvas_width = self.board_canvas.winfo_width()
        offset_x = (canvas_width - board_width) // 2

        # Calculer la colonne
        if offset_x <= event.x <= offset_x + board_width:
            col = (event.x - offset_x) // self.cell_size

            # Vérifier si la colonne est valide
            if 0 <= col < 7 and self.board[0][col] == 0:
                self.highlight_column = col
            else:
                self.highlight_column = None
        else:
            self.highlight_column = None

        # Mettre à jour le plateau
        self._draw_board()

    def _on_mouse_click(self, event):
        """
        Gère le clic de souris sur le plateau.

        Args:
            event: Événement de clic de souris
        """
        if self.match_id is None or self.is_game_over or self.current_player != self.player_number or self.highlight_column is None:
            return

        # Jouer dans la colonne surbrillée
        if self.play_callback:
            self.play_callback(self.match_id, self.highlight_column)

    def _join_queue(self):
        """Rejoint la file d'attente."""
        # Demander le nom du joueur s'il n'est pas défini
        if self.player_name == "Joueur":
            name = simpledialog.askstring("Nom du joueur", "Entrez votre nom:", parent=self.root)
            if name:
                self.player_name = name

        # Appeler le callback
        if self.join_queue_callback:
            if self.join_queue_callback(self.player_name):
                self.join_queue_button.config(state=tk.DISABLED)
                self.leave_queue_button.config(state=tk.NORMAL)
                self.status_label.config(text="En attente d'un adversaire...")

    def _leave_queue(self):
        """Quitte la file d'attente."""
        if self.leave_queue_callback:
            if self.leave_queue_callback():
                self.join_queue_button.config(state=tk.NORMAL)
                self.leave_queue_button.config(state=tk.DISABLED)
                self.status_label.config(text="Non connecté au serveur")

    def set_connected(self, connected):
        """
        Définit l'état de connexion au serveur.

        Args:
            connected (bool): True si connecté, False sinon
        """
        if connected:
            self.status_label.config(text="Connecté au serveur")
            self.join_queue_button.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="Non connecté au serveur")
            self.join_queue_button.config(state=tk.DISABLED)
            self.leave_queue_button.config(state=tk.DISABLED)

    def set_in_queue(self, in_queue):
        """
        Définit l'état de file d'attente.

        Args:
            in_queue (bool): True si dans la file, False sinon
        """
        if in_queue:
            self.status_label.config(text="En attente d'un adversaire...")
            self.join_queue_button.config(state=tk.DISABLED)
            self.leave_queue_button.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="Connecté au serveur")
            self.join_queue_button.config(state=tk.NORMAL)
            self.leave_queue_button.config(state=tk.DISABLED)

    def start_game(self, match_id, player_number, your_turn, opponent_name, board):
        """
        Démarre une partie.

        Args:
            match_id (int): ID du match
            player_number (int): Numéro du joueur (1 ou 2)
            your_turn (bool): True si c'est le tour du joueur
            opponent_name (str): Nom de l'adversaire
            board (list): État initial du plateau
        """
        self.match_id = match_id
        self.player_number = player_number
        self.current_player = 1  # Le joueur 1 commence toujours dans le Puissance 4
        self.opponent_name = opponent_name
        self.board = board
        self.is_game_over = False
        self.winner = None

        # Mettre à jour l'interface
        self._update_gui()

        # Afficher un message
        messagebox.showinfo("Partie démarrée",
                            f"Vous jouez contre {opponent_name} !\nVous êtes le joueur {player_number}.")

    def update_game(self, board, your_turn):
        """
        Met à jour l'état de la partie.

        Args:
            board (list): Nouvel état du plateau
            your_turn (bool): True si c'est le tour du joueur
        """
        self.board = board
        self.current_player = self.player_number if your_turn else (3 - self.player_number)

        # Mettre à jour l'interface
        self._update_gui()

    def end_game(self, board, winner):
        """
        Termine une partie.

        Args:
            board (list): État final du plateau
            winner (int): Numéro du joueur gagnant (0 pour match nul)
        """
        self.board = board
        self.is_game_over = True
        self.winner = winner
        self.match_id = None

        # Mettre à jour l'interface
        self._update_gui()

        # Afficher un message
        if winner == 0:
            messagebox.showinfo("Match nul", "La partie est terminée. Match nul !")
        elif winner == self.player_number:
            messagebox.showinfo("Victoire", "Félicitations, vous avez gagné !")
        else:
            messagebox.showinfo("Défaite", "Vous avez perdu. Meilleure chance la prochaine fois !")

        # Réinitialiser l'interface
        self.join_queue_button.config(state=tk.NORMAL)
        self.leave_queue_button.config(state=tk.DISABLED)

    def show_error(self, message):
        """
        Affiche un message d'erreur.

        Args:
            message (str): Message d'erreur
        """
        messagebox.showerror("Erreur", message)

    def show_info(self, message):
        """
        Affiche un message d'information.

        Args:
            message (str): Message d'information
        """
        messagebox.showinfo("Information", message)

    def on_close(self):
        """Gère la fermeture de la fenêtre."""
        self.root.destroy()

    def run(self):
        """Lance la boucle principale de l'interface."""
        # Centrer la fenêtre
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # Démarrer la boucle principale
        self.root.mainloop()