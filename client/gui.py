"""
Interface graphique améliorée pour le client Puissance 4.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
from datetime import datetime
import math


class ConnectFourGUI:
    """Interface graphique pour le jeu Puissance 4."""

    def __init__(self, play_callback=None, join_queue_callback=None, leave_queue_callback=None,
                 get_queue_info_callback=None):
        """
        Initialise l'interface graphique.

        Args:
            play_callback (callable): Fonction à appeler quand un coup est joué
            join_queue_callback (callable): Fonction à appeler pour rejoindre la file d'attente
            leave_queue_callback (callable): Fonction à appeler pour quitter la file d'attente
            get_queue_info_callback (callable): Fonction à appeler pour obtenir des informations sur la file d'attente
        """
        self.play_callback = play_callback
        self.join_queue_callback = join_queue_callback
        self.leave_queue_callback = leave_queue_callback
        self.get_queue_info_callback = get_queue_info_callback

        # État du jeu
        self.match_id = None
        self.player_number = None
        self.current_player = None
        self.board = [[0 for _ in range(7)] for _ in range(6)]
        self.is_game_over = False
        self.winner = None
        self.winning_positions = []  # Positions des pièces gagnantes

        # Informations joueurs
        self.player_name = "Joueur"
        self.opponent_name = "Adversaire"

        # État de l'interface
        self.current_screen = "menu"  # menu, queue, game
        self.connected = False
        self.in_queue = False
        self.queue_join_time = None
        self.players_in_queue = 0
        self.games_in_progress = 0

        # Animation des pièces
        self.animation_in_progress = False
        self.animation_piece = None
        self.animation_start_y = 0
        self.animation_end_y = 0
        self.animation_x = 0
        self.animation_start_time = 0
        self.animation_duration = 400  # en ms (réduit pour plus de fluidité)
        self.animation_player = None   # Joueur qui fait l'animation

        # Animation de victoire
        self.victory_animation_step = 0
        self.victory_animation_active = False

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
            'board': '#1A1B26',  # Fond du plateau plus foncé
            'board_border': '#6C7086',  # Bordure du plateau
            'empty': '#2D2F43',  # Cellules vides plus foncées
            'player1': '#FB617C',  # Rouge plus vif
            'player2': '#FADF69',  # Jaune plus vif
            'player1_shadow': '#D44D67',  # Ombre du rouge
            'player2_shadow': '#D4BB5A',  # Ombre du jaune
            'menu_bg': '#1A1B26',
            'menu_button': '#414868',
            'menu_button_hover': '#565F89',
            'queue_bg': '#24283B',
            'highlight_col': '#8AABFC'  # Couleur de surbrillance pour les colonnes
        }

        # Configurer les styles
        self.style.configure('TFrame', background=self.colors['bg'])
        self.style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['text'],
                             font=('Helvetica', 12))
        self.style.configure('TButton', background=self.colors['button'], foreground=self.colors['text'],
                             font=('Helvetica', 12))
        self.style.map('TButton', background=[('active', self.colors['button_hover'])])

        # Styles pour le menu
        self.style.configure('Menu.TFrame', background=self.colors['menu_bg'])
        self.style.configure('Menu.TLabel', background=self.colors['menu_bg'], foreground=self.colors['text'],
                             font=('Helvetica', 16))
        self.style.configure('MenuTitle.TLabel', background=self.colors['menu_bg'], foreground=self.colors['accent'],
                             font=('Helvetica', 32, 'bold'))
        self.style.configure('Menu.TButton', background=self.colors['menu_button'], foreground=self.colors['text'],
                             font=('Helvetica', 14), padding=10)
        self.style.map('Menu.TButton', background=[('active', self.colors['menu_button_hover'])])

        # Styles pour la file d'attente
        self.style.configure('Queue.TFrame', background=self.colors['queue_bg'])
        self.style.configure('Queue.TLabel', background=self.colors['queue_bg'], foreground=self.colors['text'],
                             font=('Helvetica', 14))
        self.style.configure('QueueTitle.TLabel', background=self.colors['queue_bg'], foreground=self.colors['accent'],
                             font=('Helvetica', 24, 'bold'))
        self.style.configure('Queue.TButton', background=self.colors['button'], foreground=self.colors['text'],
                             font=('Helvetica', 12))
        self.style.map('Queue.TButton', background=[('active', self.colors['button_hover'])])

        # Styles pour le statut
        self.style.configure('StatusConnected.TLabel', foreground=self.colors['green'])
        self.style.configure('StatusDisconnected.TLabel', foreground=self.colors['red'])
        self.style.configure('StatusWaiting.TLabel', foreground=self.colors['yellow'])

        # Configurer la fenêtre
        self.root.configure(bg=self.colors['bg'])

        # Créer les widgets
        self._create_widgets()

        # Initialiser les écrans
        self._create_menu_screen()
        self._create_queue_screen()
        self._create_game_screen()

        # Afficher l'écran du menu principal
        self._show_screen("menu")

        # Démarrer la mise à jour périodique
        self._start_periodic_update()

    def _create_widgets(self):
        """Crée les widgets communs de l'interface."""
        # Frame principale qui contiendra tous les écrans
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Dictionnaire pour stocker les différents écrans
        self.screens = {}

        # Variables pour le dessin du plateau
        self.cell_size = 80
        self.piece_radius = 30
        self.highlight_column = None

    def _create_menu_screen(self):
        """Crée l'écran du menu principal."""
        # Frame du menu
        menu_frame = ttk.Frame(self.main_frame, style='Menu.TFrame')
        self.screens["menu"] = menu_frame

        # Logo / Titre
        title_frame = ttk.Frame(menu_frame, style='Menu.TFrame')
        title_frame.pack(pady=(50, 30))

        # Titre du jeu avec effet d'ombre
        title_shadow = ttk.Label(title_frame, text="PUISSANCE 4", style='MenuTitle.TLabel',
                               foreground=self.colors['button'], font=('Helvetica', 32, 'bold'))
        title_shadow.pack()
        title_shadow.place(relx=0.505, rely=0.02)

        game_title = ttk.Label(title_frame, text="PUISSANCE 4", style='MenuTitle.TLabel')
        game_title.pack()

        subtitle = ttk.Label(title_frame, text="Matchmaking en ligne", style='Menu.TLabel')
        subtitle.pack(pady=10)

        # Boutons du menu
        buttons_frame = ttk.Frame(menu_frame, style='Menu.TFrame')
        buttons_frame.pack(pady=20)

        # Bouton Jouer avec effet de survol
        self.play_button = ttk.Button(buttons_frame, text="Jouer", style='Menu.TButton',
                                      command=self._on_play_button_click)
        self.play_button.pack(pady=10, ipadx=20, ipady=5, fill=tk.X)

        # Bouton Quitter
        quit_button = ttk.Button(buttons_frame, text="Quitter", style='Menu.TButton',
                                command=self.on_close)
        quit_button.pack(pady=10, ipadx=20, ipady=5, fill=tk.X)

        # Statut du serveur
        status_frame = ttk.Frame(menu_frame, style='Menu.TFrame')
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        self.server_status_label = ttk.Label(status_frame, text="Non connecté au serveur",
                                            style='StatusDisconnected.TLabel')
        self.server_status_label.pack(side=tk.LEFT)

        # Stats du serveur
        self.server_stats_label = ttk.Label(status_frame, text="", style='Menu.TLabel')
        self.server_stats_label.pack(side=tk.RIGHT)

    def _create_queue_screen(self):
        """Crée l'écran de la file d'attente."""
        # Frame de la file d'attente
        queue_frame = ttk.Frame(self.main_frame, style='Queue.TFrame')
        self.screens["queue"] = queue_frame

        # En-tête
        header_frame = ttk.Frame(queue_frame, style='Queue.TFrame')
        header_frame.pack(fill=tk.X, pady=(20, 30))

        # Bouton retour
        back_button = ttk.Button(header_frame, text="← Retour", style='Queue.TButton',
                                command=lambda: self._show_screen("menu"))
        back_button.pack(side=tk.LEFT)

        # Titre
        queue_title = ttk.Label(header_frame, text="File d'attente", style='QueueTitle.TLabel')
        queue_title.pack(side=tk.RIGHT, padx=20)

        # Frame pour les informations de la file d'attente
        info_frame = ttk.Frame(queue_frame, style='Queue.TFrame')
        info_frame.pack(fill=tk.X, pady=20)

        # Zone d'entrée du nom
        name_frame = ttk.Frame(info_frame, style='Queue.TFrame')
        name_frame.pack(fill=tk.X, pady=10)

        name_label = ttk.Label(name_frame, text="Votre nom:", style='Queue.TLabel')
        name_label.pack(side=tk.LEFT, padx=(0, 10))

        self.name_var = tk.StringVar(value=self.player_name)
        self.name_entry = ttk.Entry(name_frame, textvariable=self.name_var, font=('Helvetica', 12), width=20)
        self.name_entry.pack(side=tk.LEFT)

        # Frame pour la visualisation de la file d'attente
        self.queue_visual_frame = ttk.Frame(queue_frame, style='Queue.TFrame')
        self.queue_visual_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        # Canvas pour visualiser la file d'attente
        self.queue_canvas = tk.Canvas(self.queue_visual_frame, bg=self.colors['queue_bg'],
                                     highlightthickness=0, height=300)
        self.queue_canvas.pack(fill=tk.BOTH, expand=True)

        # Informations sur la file
        self.queue_info_frame = ttk.Frame(queue_frame, style='Queue.TFrame')
        self.queue_info_frame.pack(fill=tk.X, pady=20)

        # Temps d'attente
        self.wait_time_label = ttk.Label(self.queue_info_frame, text="Temps d'attente: --:--",
                                        style='Queue.TLabel')
        self.wait_time_label.pack(side=tk.LEFT)

        # Nombre de joueurs en attente
        self.players_waiting_label = ttk.Label(self.queue_info_frame, text="Joueurs en attente: 0",
                                              style='Queue.TLabel')
        self.players_waiting_label.pack(side=tk.RIGHT)

        # Boutons de file d'attente
        self.queue_buttons_frame = ttk.Frame(queue_frame, style='Queue.TFrame')
        self.queue_buttons_frame.pack(fill=tk.X, pady=20)

        self.join_queue_button = ttk.Button(self.queue_buttons_frame, text="Rejoindre la file d'attente",
                                           style='Queue.TButton', command=self._join_queue)
        self.join_queue_button.pack(side=tk.LEFT, padx=(0, 10))

        self.leave_queue_button = ttk.Button(self.queue_buttons_frame, text="Quitter la file d'attente",
                                            style='Queue.TButton', command=self._leave_queue)
        self.leave_queue_button.pack(side=tk.LEFT)
        self.leave_queue_button.config(state=tk.DISABLED)

    def _create_game_screen(self):
        """Crée l'écran de jeu."""
        # Frame de jeu
        game_frame = ttk.Frame(self.main_frame)
        self.screens["game"] = game_frame

        # Frame d'en-tête
        self.game_header_frame = ttk.Frame(game_frame)
        self.game_header_frame.pack(fill=tk.X, pady=(0, 20))

        # Étiquette du titre
        self.game_title_label = ttk.Label(self.game_header_frame, text="Puissance 4", font=('Helvetica', 24, 'bold'))
        self.game_title_label.pack(side=tk.LEFT, pady=10)

        # Frame de statut
        self.game_status_frame = ttk.Frame(game_frame)
        self.game_status_frame.pack(fill=tk.X, pady=(0, 20))

        # Étiquette de statut
        self.game_status_label = ttk.Label(self.game_status_frame, text="En attente...", font=('Helvetica', 14))
        self.game_status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Canvas pour le plateau de jeu
        self.board_frame = ttk.Frame(game_frame)
        self.board_frame.pack(fill=tk.BOTH, expand=True)

        self.board_canvas = tk.Canvas(self.board_frame, bg=self.colors['bg'], highlightthickness=0)
        self.board_canvas.pack(fill=tk.BOTH, expand=True)

        # Bind des événements
        self.board_canvas.bind("<Motion>", self._on_mouse_move)
        self.board_canvas.bind("<Button-1>", self._on_mouse_click)

        # Frame de bas de page
        self.game_footer_frame = ttk.Frame(game_frame)
        self.game_footer_frame.pack(fill=tk.X, pady=(20, 0))

        # Informations des joueurs
        self.player_info_frame = ttk.Frame(self.game_footer_frame)
        self.player_info_frame.pack(fill=tk.X)

        self.player1_label = ttk.Label(self.player_info_frame, text="Joueur 1: -", font=('Helvetica', 12))
        self.player1_label.pack(side=tk.LEFT, padx=(0, 20))

        self.player2_label = ttk.Label(self.player_info_frame, text="Joueur 2: -", font=('Helvetica', 12))
        self.player2_label.pack(side=tk.LEFT)

        # Bouton pour revenir au menu (visible uniquement après la fin d'une partie)
        self.back_to_menu_button = ttk.Button(self.game_footer_frame, text="Retour au menu",
                                             command=lambda: self._show_screen("menu"))
        self.back_to_menu_button.pack(side=tk.RIGHT)
        self.back_to_menu_button.pack_forget()  # Caché par défaut

    def _show_screen(self, screen_name):
        """
        Affiche l'écran spécifié et cache les autres.

        Args:
            screen_name (str): Nom de l'écran à afficher ("menu", "queue", "game")
        """
        self.current_screen = screen_name

        # Cacher tous les écrans
        for name, screen in self.screens.items():
            screen.pack_forget()

        # Si on retourne au menu principal depuis l'écran de jeu après une partie,
        # s'assurer que les boutons pour rejoindre la file d'attente sont dans le bon état
        if screen_name == "menu" and self.is_game_over:
            self.is_game_over = False
            self.match_id = None

        # Arrêter l'animation de victoire si on change d'écran
        self.victory_animation_active = False

        # Afficher l'écran demandé
        if screen_name in self.screens:
            self.screens[screen_name].pack(fill=tk.BOTH, expand=True)

            # Actions spécifiques à chaque écran
            if screen_name == "menu":
                self._update_menu_screen()
            elif screen_name == "queue":
                self._update_queue_screen()
            elif screen_name == "game":
                self._update_game_screen()

    def _update_menu_screen(self):
        """Met à jour l'écran du menu."""
        # Mettre à jour le statut du serveur
        if self.connected:
            self.server_status_label.config(text="Connecté au serveur", style='StatusConnected.TLabel')
            self.play_button.config(state=tk.NORMAL)

            # Mettre à jour les statistiques si disponibles
            stats_text = f"Joueurs en ligne: {self.players_in_queue}, Parties en cours: {self.games_in_progress}"
            self.server_stats_label.config(text=stats_text, foreground=self.colors['green'])
        else:
            self.server_status_label.config(text="Non connecté au serveur", style='StatusDisconnected.TLabel')
            self.play_button.config(state=tk.DISABLED)
            self.server_stats_label.config(text="")

    def _update_queue_screen(self):
        """Met à jour l'écran de la file d'attente."""
        # Mettre à jour l'état des boutons
        if self.in_queue:
            self.join_queue_button.config(state=tk.DISABLED)
            self.leave_queue_button.config(state=tk.NORMAL)
            self.name_entry.config(state=tk.DISABLED)

            # Mettre à jour le temps d'attente
            if self.queue_join_time:
                elapsed = time.time() - self.queue_join_time
                minutes = int(elapsed // 60)
                seconds = int(elapsed % 60)
                self.wait_time_label.config(text=f"Temps d'attente: {minutes:02d}:{seconds:02d}")
        else:
            self.join_queue_button.config(state=tk.NORMAL)
            self.leave_queue_button.config(state=tk.DISABLED)
            self.name_entry.config(state=tk.NORMAL)
            self.wait_time_label.config(text="Temps d'attente: --:--")

        # Mettre à jour le nombre de joueurs en attente
        self.players_waiting_label.config(text=f"Joueurs en attente: {self.players_in_queue}")

        # Dessiner la visualisation de la file d'attente
        self._draw_queue_visualization()

    def _update_game_screen(self):
        """Met à jour l'écran de jeu."""
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
                    self.game_status_label.config(foreground=self.colors['text'])
                elif self.winner == self.player_number:
                    self.game_status_label.config(foreground=self.colors['green'])
                else:
                    self.game_status_label.config(foreground=self.colors['red'])

                # Afficher le bouton de retour au menu
                self.back_to_menu_button.pack(side=tk.RIGHT)

                # Démarrer l'animation de victoire si le jeu vient de se terminer
                if not self.victory_animation_active and self.winning_positions:
                    self.victory_animation_active = True
                    self.victory_animation_step = 0
                    self._animate_victory()
            else:
                # En attente d'un match
                status_text = "En attente d'un match"
                self.game_status_label.config(foreground=self.colors['text'])
                self.back_to_menu_button.pack_forget()
        else:
            # Match en cours
            if self.current_player == self.player_number:
                status_text = "C'est votre tour"
                self.game_status_label.config(foreground=self.colors['green'])
            else:
                status_text = f"C'est le tour de {self.opponent_name}"
                self.game_status_label.config(foreground=self.colors['text'])

            # Cacher le bouton de retour pendant une partie
            self.back_to_menu_button.pack_forget()

        self.game_status_label.config(text=status_text)

        # Mettre à jour les informations des joueurs
        player1_text = f"Joueur 1: {self.player_name if self.player_number == 1 else self.opponent_name}"
        player2_text = f"Joueur 2: {self.player_name if self.player_number == 2 else self.opponent_name}"

        self.player1_label.config(text=player1_text, foreground=self.colors['player1'])
        self.player2_label.config(text=player2_text, foreground=self.colors['player2'])

        # Dessiner le plateau
        self._draw_board()

    def _animate_victory(self):
        """Anime les pièces gagnantes."""
        if not self.victory_animation_active or not self.winning_positions:
            return

        # Redessiner le plateau avec l'animation
        self._draw_board()

        # Incrémenter l'étape d'animation
        self.victory_animation_step += 1

        # Continuer l'animation en boucle
        if self.victory_animation_active:
            self.root.after(150, self._animate_victory)

    def _start_periodic_update(self):
        """Démarre la mise à jour périodique de l'interface."""
        def update_loop():
            while True:
                # Mettre à jour l'interface selon l'écran actuel
                self.root.after(0, self._periodic_update)
                time.sleep(1)  # Mise à jour toutes les secondes

        # Démarrer le thread de mise à jour
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()

    def _periodic_update(self):
        """Met à jour périodiquement l'interface."""
        # Mettre à jour l'écran actuel
        if self.current_screen == "menu":
            self._update_menu_screen()
        elif self.current_screen == "queue":
            self._update_queue_screen()
        elif self.current_screen == "game":
            self._update_game_screen()

        # Demander des informations sur la file d'attente au serveur
        if self.connected and self.get_queue_info_callback:
            self.get_queue_info_callback()

    def _draw_queue_visualization(self):
        """Dessine la visualisation de la file d'attente."""
        # Effacer le canvas
        self.queue_canvas.delete("all")

        # Dimensions du canvas
        width = self.queue_canvas.winfo_width()
        height = self.queue_canvas.winfo_height()

        if width <= 1:  # Le canvas n'est pas encore rendu
            self.root.after(100, self._draw_queue_visualization)
            return

        # Dessiner le fond
        self.queue_canvas.create_rectangle(0, 0, width, height, fill=self.colors['queue_bg'], outline="")

        # Si pas dans la file, afficher un message
        if not self.in_queue:
            self.queue_canvas.create_text(width // 2, height // 2,
                                         text="Rejoignez la file d'attente pour trouver un adversaire",
                                         fill=self.colors['text'], font=('Helvetica', 14))
            return

        # Animation de recherche avec pulsation
        dots = "." * (int(time.time() * 2) % 4)
        pulse_scale = 1.0 + 0.1 * math.sin(time.time() * 2)  # Effet de pulsation
        text_font = ('Helvetica', int(18 * pulse_scale), 'bold')

        self.queue_canvas.create_text(width // 2, 50,
                                     text=f"Recherche d'un adversaire{dots}",
                                     fill=self.colors['accent'], font=text_font)

        # Dessiner votre avatar au centre avec effet de gradient
        avatar_radius = 50

        # Dessiner le cercle principal avec un gradient
        for r in range(avatar_radius, int(avatar_radius * 0.7), -1):
            # Calculer une couleur plus claire vers le centre
            factor = (r - avatar_radius * 0.7) / (avatar_radius * 0.3)
            color = self._blend_colors(self.colors['accent'], "#FFFFFF", 0.7 - factor * 0.3)

            self.queue_canvas.create_oval(
                width // 2 - r, height // 2 - r,
                width // 2 + r, height // 2 + r,
                fill=color, outline=""
            )

        # Ajouter votre nom
        self.queue_canvas.create_text(width // 2, height // 2,
                                     text=self.player_name,
                                     fill=self.colors['bg'], font=('Helvetica', 14, 'bold'))

        # Dessiner les autres joueurs en attente avec animation
        if self.players_in_queue > 1:
            other_players = self.players_in_queue - 1
            max_display = min(5, other_players)  # Limiter à 5 avatars maximum

            for i in range(max_display):
                # Animation avec des sinus/cosinus pour un mouvement plus naturel
                time_offset = time.time() + i * 0.5
                angle = time_offset * 0.5
                distance = 150 + 20 * math.sin(time_offset)

                # Position calculée en cercle autour du joueur avec un mouvement ondulant
                x = width // 2 + distance * math.cos(angle + i * (2 * math.pi / max_display))
                y = height // 2 + distance * math.sin(angle + i * (2 * math.pi / max_display))

                # Taille variable pour l'effet de profondeur
                size = 35 + 10 * math.sin(time_offset * 2)

                # Effet de brillance avec un dégradé
                for r in range(int(size), int(size * 0.7), -1):
                    # Calculer une couleur plus claire vers le centre
                    factor = (r - size * 0.7) / (size * 0.3)
                    color = self._blend_colors(self.colors['button'], "#5F7ADB", 0.7 - factor * 0.5)

                    self.queue_canvas.create_oval(
                        x - r, y - r, x + r, y + r,
                        fill=color, outline=""
                    )

                # Dessiner un point d'interrogation pour représenter un joueur inconnu
                self.queue_canvas.create_text(x, y, text="?", fill=self.colors['text'],
                                             font=('Helvetica', int(size * 0.8)))

            # Si plus de 5 joueurs, afficher un texte
            if other_players > max_display:
                self.queue_canvas.create_text(width // 2, height - 50,
                                             text=f"+ {other_players - max_display} autres joueurs en attente",
                                             fill=self.colors['text'], font=('Helvetica', 12))

    def _blend_colors(self, color1, color2, blend_factor):
        """
        Mélange deux couleurs hexadécimales.

        Args:
            color1 (str): Première couleur au format hexadécimal (#RRGGBB)
            color2 (str): Deuxième couleur au format hexadécimal (#RRGGBB)
            blend_factor (float): Facteur de mélange entre 0 et 1

        Returns:
            str: Couleur résultante au format hexadécimal
        """
        # Extraire les composantes RGB
        r1 = int(color1[1:3], 16)
        g1 = int(color1[3:5], 16)
        b1 = int(color1[5:7], 16)

        r2 = int(color2[1:3], 16)
        g2 = int(color2[3:5], 16)
        b2 = int(color2[5:7], 16)

        # Mélanger les composantes
        r = int(r1 * (1 - blend_factor) + r2 * blend_factor)
        g = int(g1 * (1 - blend_factor) + g2 * blend_factor)
        b = int(b1 * (1 - blend_factor) + b2 * blend_factor)

        # Retourner la couleur au format hexadécimal
        return f"#{r:02x}{g:02x}{b:02x}"

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

        # Dessiner un effet d'ombre pour le plateau
        shadow_offset = 5
        self.board_canvas.create_rectangle(
            offset_x - 10 + shadow_offset, offset_y - 10 + shadow_offset,
            offset_x + board_width + 10 + shadow_offset, offset_y + board_height + 10 + shadow_offset,
            fill="#151521", outline="", width=0
        )

        # Dessiner le fond du plateau avec un effet de dégradé
        for i in range(10):
            factor = i / 10
            color = self._blend_colors(self.colors['board'], "#23253D", factor)
            self.board_canvas.create_rectangle(
                offset_x - 10 + i, offset_y - 10 + i,
                offset_x + board_width + 10 - i, offset_y + board_height + 10 - i,
                fill=color, outline=self.colors['board_border'], width=1
            )

        # Dessiner une bordure extérieure brillante
        self.board_canvas.create_rectangle(
            offset_x - 10, offset_y - 10,
            offset_x + board_width + 10, offset_y + board_height + 10,
            fill="", outline=self.colors['accent'], width=2
        )

        # Dessiner des décorations pour le plateau (coins arrondis)
        corner_radius = 15
        # Coins supérieurs gauche et droit
        self.board_canvas.create_arc(
            offset_x - 10, offset_y - 10,
            offset_x - 10 + 2 * corner_radius, offset_y - 10 + 2 * corner_radius,
            start=90, extent=90, outline=self.colors['accent'], style="arc", width=2
        )
        self.board_canvas.create_arc(
            offset_x + board_width + 10 - 2 * corner_radius, offset_y - 10,
            offset_x + board_width + 10, offset_y - 10 + 2 * corner_radius,
            start=0, extent=90, outline=self.colors['accent'], style="arc", width=2
        )
        # Coins inférieurs gauche et droit
        self.board_canvas.create_arc(
            offset_x - 10, offset_y + board_height + 10 - 2 * corner_radius,
            offset_x - 10 + 2 * corner_radius, offset_y + board_height + 10,
            start=180, extent=90, outline=self.colors['accent'], style="arc", width=2
        )
        self.board_canvas.create_arc(
            offset_x + board_width + 10 - 2 * corner_radius, offset_y + board_height + 10 - 2 * corner_radius,
            offset_x + board_width + 10, offset_y + board_height + 10,
            start=270, extent=90, outline=self.colors['accent'], style="arc", width=2
        )

        # Si une animation est en cours, dessiner la pièce animée
        if self.animation_in_progress:
            self._animate_piece()
            return  # Retourner et laisser l'animation gérer le reste du dessin

        # Dessiner les cellules et les pièces
        for row in range(6):
            for col in range(7):
                # Position de la cellule
                x = offset_x + col * self.cell_size + self.cell_size // 2
                y = offset_y + row * self.cell_size + self.cell_size // 2

                # Dessiner l'emplacement vide avec effet 3D
                self._draw_cell(x, y, self.colors['empty'])

                # Dessiner la pièce si présente
                if self.board[row][col] == 1:
                    self._draw_piece(x, y, self.colors['player1'], self.colors['player1_shadow'], row, col)
                elif self.board[row][col] == 2:
                    self._draw_piece(x, y, self.colors['player2'], self.colors['player2_shadow'], row, col)

        # Dessiner la colonne en surbrillance
        if self.highlight_column is not None and not self.is_game_over and self.match_id is not None and self.current_player == self.player_number:
            # Dessiner un rectangle translucide sur toute la colonne
            col_x = offset_x + self.highlight_column * self.cell_size
            self.board_canvas.create_rectangle(
                col_x, offset_y - 10,
                col_x + self.cell_size, offset_y + board_height + 10,
                fill=self.colors['highlight_col'], stipple="gray50", outline=""
            )

            # Position de la cellule pour la pièce fantôme
            x = offset_x + self.highlight_column * self.cell_size + self.cell_size // 2
            y = offset_y - self.cell_size // 2

            # Dessiner la pièce fantôme
            piece_color = self.colors['player1'] if self.player_number == 1 else self.colors['player2']
            shadow_color = self.colors['player1_shadow'] if self.player_number == 1 else self.colors['player2_shadow']

            # Créer une version "fantôme" de la pièce
            ghost_color = self._blend_colors(piece_color, "#FFFFFF", 0.7)
            ghost_shadow = self._blend_colors(shadow_color, "#FFFFFF", 0.7)

            self._draw_piece(x, y, ghost_color, ghost_shadow, -1, self.highlight_column, ghost=True)

    def _draw_cell(self, x, y, color):
        """
        Dessine une cellule vide du plateau avec un effet 3D.

        Args:
            x (int): Position X du centre de la cellule
            y (int): Position Y du centre de la cellule
            color (str): Couleur de la cellule
        """
        # Rayon externe légèrement plus grand que le rayon des pièces
        outer_radius = self.piece_radius + 2
        inner_radius = self.piece_radius

        # Dessiner un cercle externe pour l'effet d'ombre
        self.board_canvas.create_oval(
            x - outer_radius, y - outer_radius,
            x + outer_radius, y + outer_radius,
            fill="#151521", outline=""
        )

        # Dessiner le trou au milieu
        self.board_canvas.create_oval(
            x - inner_radius, y - inner_radius,
            x + inner_radius, y + inner_radius,
            fill=color, outline="#191B2A", width=1
        )

        # Ajouter un effet de lumière au bord supérieur
        self.board_canvas.create_arc(
            x - inner_radius, y - inner_radius,
            x + inner_radius, y + inner_radius,
            start=45, extent=180, fill="", outline="#2D2F43", width=1
        )

        # Ajouter un effet d'ombre au bord inférieur
        self.board_canvas.create_arc(
            x - inner_radius, y - inner_radius,
            x + inner_radius, y + inner_radius,
            start=225, extent=180, fill="", outline="#161826", width=1
        )

    def _draw_piece(self, x, y, color, shadow_color, row, col, ghost=False):
        """
        Dessine une pièce avec des effets 3D.

        Args:
            x (int): Position X du centre de la pièce
            y (int): Position Y du centre de la pièce
            color (str): Couleur principale de la pièce
            shadow_color (str): Couleur de l'ombre de la pièce
            row (int): Ligne de la pièce dans le plateau
            col (int): Colonne de la pièce dans le plateau
            ghost (bool): Si True, dessine une pièce fantôme (pour la prévisualisation)
        """
        # Vérifier si cette pièce fait partie des positions gagnantes
        is_winning = False
        highlight_pulse = 0

        if self.winning_positions and (row, col) in self.winning_positions:
            is_winning = True
            # Effet de pulsation pour l'animation de victoire
            highlight_pulse = math.sin(self.victory_animation_step * 0.5) * 5

        # Rayon de base et rayon interne pour l'effet 3D
        radius = self.piece_radius
        inner_radius = radius * 0.85

        # Pour les pièces fantômes, utiliser un rayon légèrement plus petit
        if ghost:
            radius *= 0.9
            inner_radius *= 0.9

        # Si c'est une pièce gagnante, faire varier le rayon pour l'animation
        if is_winning:
            radius += highlight_pulse
            inner_radius += highlight_pulse * 0.85

        # Dessiner l'ombre de la pièce
        self.board_canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=shadow_color, outline=""
        )

        # Créer un dégradé pour l'effet 3D
        for i in range(3):
            factor = i / 3
            r = radius - (radius - inner_radius) * factor

            # Couleur plus claire vers le centre
            if is_winning:
                # Pour les pièces gagnantes, utiliser un effet de couleur brillante qui varie
                highlight_color = "#FFFFFF" if self.victory_animation_step % 6 < 3 else color
                piece_color = self._blend_colors(color, highlight_color, factor * 0.7)
            else:
                # Pour les pièces normales, un simple dégradé
                piece_color = self._blend_colors(color, "#FFFFFF", factor * 0.4)

            self.board_canvas.create_oval(
                x - r, y - r,
                x + r, y + r,
                fill=piece_color, outline=""
            )

        # Ajouter un reflet lumineux dans le coin supérieur gauche
        highlight_size = radius * 0.5
        highlight_offset = radius * 0.3

        self.board_canvas.create_oval(
            x - radius + highlight_offset, y - radius + highlight_offset,
            x - radius + highlight_offset + highlight_size, y - radius + highlight_offset + highlight_size,
            fill="#FFFFFF", outline="", stipple="gray25"
        )

        # Pour les pièces gagnantes, ajouter un halo
        if is_winning:
            glow_color = "#FFFFFF" if self.victory_animation_step % 6 < 3 else color
            for i in range(3):
                glow_radius = radius + 2 + i * 2
                glow_alpha = "gray75" if i == 0 else ("gray50" if i == 1 else "gray25")
                self.board_canvas.create_oval(
                    x - glow_radius, y - glow_radius,
                    x + glow_radius, y + glow_radius,
                    outline=glow_color, width=2, stipple=glow_alpha
                )

    def _animate_piece(self):
        """Gère l'animation de chute d'une pièce."""
        if not self.animation_in_progress:
            return

        # Calculer la position actuelle de la pièce basée sur le temps écoulé
        current_time = time.time() * 1000  # en ms
        elapsed = current_time - self.animation_start_time
        progress = min(1.0, elapsed / self.animation_duration)

        # Appliquer une fonction d'accélération pour simuler la gravité
        # Formule: d = 0.5 * g * t^2 (mouvement uniformément accéléré)
        y_position = self.animation_start_y + (self.animation_end_y - self.animation_start_y) * (progress ** 2)

        # Ajouter un petit effet de rebond
        if progress > 0.9:
            bounce_effect = math.sin((progress - 0.9) * 10 * math.pi) * 5 * (1 - progress) * 10
            y_position += bounce_effect

        # Calculer les dimensions du plateau
        board_width = 7 * self.cell_size
        board_height = 6 * self.cell_size
        canvas_width = self.board_canvas.winfo_width()
        canvas_height = self.board_canvas.winfo_height()
        offset_x = (canvas_width - board_width) // 2
        offset_y = (canvas_height - board_height) // 2

        # Effacer le canvas et redessiner le plateau sans la pièce animée
        self.board_canvas.delete("all")
        self._draw_static_board(offset_x, offset_y, board_width, board_height)

        # Dessiner la pièce animée avec la couleur correcte du joueur
        player_color = self.colors['player1'] if self.animation_player == 1 else self.colors['player2']
        shadow_color = self.colors['player1_shadow'] if self.animation_player == 1 else self.colors['player2_shadow']

        self._draw_piece(self.animation_x, y_position, player_color, shadow_color, -1, -1)

        # Continuer l'animation si elle n'est pas terminée
        if progress < 1.0:
            self.root.after(16, self._animate_piece)  # ~60 FPS
        else:
            # Animation terminée
            self.animation_in_progress = False
            self._draw_board()

    def _draw_static_board(self, offset_x, offset_y, board_width, board_height):
        """
        Dessine le plateau sans la pièce en cours d'animation.

        Args:
            offset_x (int): Décalage X du plateau
            offset_y (int): Décalage Y du plateau
            board_width (int): Largeur du plateau
            board_height (int): Hauteur du plateau
        """
        # Dessiner un effet d'ombre pour le plateau
        shadow_offset = 5
        self.board_canvas.create_rectangle(
            offset_x - 10 + shadow_offset, offset_y - 10 + shadow_offset,
            offset_x + board_width + 10 + shadow_offset, offset_y + board_height + 10 + shadow_offset,
            fill="#151521", outline="", width=0
        )

        # Dessiner le fond du plateau avec un effet de dégradé
        for i in range(10):
            factor = i / 10
            color = self._blend_colors(self.colors['board'], "#23253D", factor)
            self.board_canvas.create_rectangle(
                offset_x - 10 + i, offset_y - 10 + i,
                offset_x + board_width + 10 - i, offset_y + board_height + 10 - i,
                fill=color, outline=self.colors['board_border'], width=1
            )

        # Dessiner une bordure extérieure brillante
        self.board_canvas.create_rectangle(
            offset_x - 10, offset_y - 10,
            offset_x + board_width + 10, offset_y + board_height + 10,
            fill="", outline=self.colors['accent'], width=2
        )

        # Dessiner des décorations pour le plateau (coins arrondis)
        corner_radius = 15
        # Coins supérieurs gauche et droit
        self.board_canvas.create_arc(
            offset_x - 10, offset_y - 10,
            offset_x - 10 + 2 * corner_radius, offset_y - 10 + 2 * corner_radius,
            start=90, extent=90, outline=self.colors['accent'], style="arc", width=2
        )
        self.board_canvas.create_arc(
            offset_x + board_width + 10 - 2 * corner_radius, offset_y - 10,
            offset_x + board_width + 10, offset_y - 10 + 2 * corner_radius,
            start=0, extent=90, outline=self.colors['accent'], style="arc", width=2
        )
        # Coins inférieurs gauche et droit
        self.board_canvas.create_arc(
            offset_x - 10, offset_y + board_height + 10 - 2 * corner_radius,
            offset_x - 10 + 2 * corner_radius, offset_y + board_height + 10,
            start=180, extent=90, outline=self.colors['accent'], style="arc", width=2
        )
        self.board_canvas.create_arc(
            offset_x + board_width + 10 - 2 * corner_radius, offset_y + board_height + 10 - 2 * corner_radius,
            offset_x + board_width + 10, offset_y + board_height + 10,
            start=270, extent=90, outline=self.colors['accent'], style="arc", width=2
        )

        # Dessiner les cellules et les pièces (sauf celle en cours d'animation)
        for row in range(6):
            for col in range(7):
                # Position de la cellule
                x = offset_x + col * self.cell_size + self.cell_size // 2
                y = offset_y + row * self.cell_size + self.cell_size // 2

                # Dessiner l'emplacement vide avec effet 3D
                self._draw_cell(x, y, self.colors['empty'])

                # Dessiner la pièce si présente et que ce n'est pas celle qu'on vient de jouer
                if self.board[row][col] == 1:
                    self._draw_piece(x, y, self.colors['player1'], self.colors['player1_shadow'], row, col)
                elif self.board[row][col] == 2:
                    self._draw_piece(x, y, self.colors['player2'], self.colors['player2_shadow'], row, col)

    def _on_play_button_click(self):
        """Gère le clic sur le bouton Jouer."""
        if self.connected:
            self._show_screen("queue")

    def _join_queue(self):
        """Rejoint la file d'attente."""
        # Mettre à jour le nom du joueur depuis l'entrée
        self.player_name = self.name_var.get() or "Joueur"

        # Appeler le callback
        if self.join_queue_callback:
            if self.join_queue_callback(self.player_name):
                self.in_queue = True
                self.queue_join_time = time.time()
                self._update_queue_screen()

    def _leave_queue(self):
        """Quitte la file d'attente."""
        if self.leave_queue_callback:
            if self.leave_queue_callback():
                self.in_queue = False
                self.queue_join_time = None
                self._update_queue_screen()

    def _on_mouse_move(self, event):
        """
        Gère le mouvement de la souris sur le plateau.

        Args:
            event: Événement de mouvement de souris
        """
        if self.match_id is None or self.is_game_over or self.current_player != self.player_number or self.animation_in_progress:
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
                if self.highlight_column != col:
                    self.highlight_column = col
                    self._draw_board()
            elif self.highlight_column is not None:
                self.highlight_column = None
                self._draw_board()
        elif self.highlight_column is not None:
            self.highlight_column = None
            self._draw_board()

    def _on_mouse_click(self, event):
        """
        Gère le clic de souris sur le plateau.

        Args:
            event: Événement de clic de souris
        """
        if self.match_id is None or self.is_game_over or self.current_player != self.player_number or self.highlight_column is None or self.animation_in_progress:
            return

        # Jouer dans la colonne surbrillée
        if self.play_callback:
            # Calculer les dimensions du plateau
            board_width = 7 * self.cell_size
            board_height = 6 * self.cell_size
            canvas_width = self.board_canvas.winfo_width()
            canvas_height = self.board_canvas.winfo_height()
            offset_x = (canvas_width - board_width) // 2
            offset_y = (canvas_height - board_height) // 2

            # Stocker la colonne jouée
            column_played = self.highlight_column

            # Démarrer l'animation de chute
            self.animation_in_progress = True
            self.animation_x = offset_x + column_played * self.cell_size + self.cell_size // 2
            self.animation_start_y = offset_y - self.cell_size // 2

            # Trouver la position finale de la pièce
            row = 5
            while row >= 0 and self.board[row][column_played] != 0:
                row -= 1

            # Stocker le joueur actuel pour l'animation
            self.animation_player = self.player_number

            self.animation_end_y = offset_y + row * self.cell_size + self.cell_size // 2
            self.animation_start_time = time.time() * 1000

            # Démarrer l'animation
            self._animate_piece()

            # Envoyer le coup au serveur
            self.play_callback(self.match_id, column_played)

    def set_connected(self, connected):
        """
        Définit l'état de connexion au serveur.

        Args:
            connected (bool): True si connecté, False sinon
        """
        self.connected = connected
        self._update_menu_screen()

    def set_in_queue(self, in_queue):
        """
        Définit l'état de file d'attente.

        Args:
            in_queue (bool): True si dans la file, False sinon
        """
        self.in_queue = in_queue

        if in_queue:
            self.queue_join_time = time.time()
        else:
            self.queue_join_time = None

        # Mettre à jour l'interface si nous sommes sur l'écran de file d'attente
        if self.current_screen == "queue":
            self._update_queue_screen()

    def update_queue_info(self, players_in_queue, games_in_progress):
        """
        Met à jour les informations sur la file d'attente.

        Args:
            players_in_queue (int): Nombre de joueurs dans la file
            games_in_progress (int): Nombre de parties en cours
        """
        self.players_in_queue = players_in_queue
        self.games_in_progress = games_in_progress

        # Mettre à jour l'interface selon l'écran actuel
        if self.current_screen == "menu":
            self._update_menu_screen()
        elif self.current_screen == "queue":
            self._update_queue_screen()

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
        self.winning_positions = []

        # Arrêter l'animation de victoire si elle est en cours
        self.victory_animation_active = False

        # Passer à l'écran de jeu
        self._show_screen("game")

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

        # Mettre à jour l'interface si nous sommes sur l'écran de jeu
        if self.current_screen == "game" and not self.animation_in_progress:
            self._update_game_screen()

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

        # Trouver les positions gagnantes pour l'animation
        self.winning_positions = []
        if winner != 0:  # Si ce n'est pas un match nul
            self._find_winning_positions(board, winner)

        # Démarrer l'animation de victoire
        if self.winning_positions:
            self.victory_animation_active = True
            self.victory_animation_step = 0
            self._animate_victory()

        # Mettre à jour l'interface si nous sommes sur l'écran de jeu
        if self.current_screen == "game":
            self._update_game_screen()

        # Afficher un message
        if winner == 0:
            messagebox.showinfo("Match nul", "La partie est terminée. Match nul !")
        elif winner == self.player_number:
            messagebox.showinfo("Victoire", "Félicitations, vous avez gagné !")
        else:
            messagebox.showinfo("Défaite", "Vous avez perdu. Meilleure chance la prochaine fois !")

    def _find_winning_positions(self, board, winner):
        """
        Trouve les positions des pièces qui forment une combinaison gagnante.

        Args:
            board (list): Plateau de jeu
            winner (int): Numéro du joueur gagnant
        """
        # Réinitialiser les positions gagnantes
        self.winning_positions = []

        # Vérifier horizontalement
        for row in range(6):
            for col in range(4):
                if (board[row][col] == winner and
                        board[row][col] == board[row][col + 1] ==
                        board[row][col + 2] == board[row][col + 3]):
                    for i in range(4):
                        self.winning_positions.append((row, col + i))
                    return

        # Vérifier verticalement
        for row in range(3):
            for col in range(7):
                if (board[row][col] == winner and
                        board[row][col] == board[row + 1][col] ==
                        board[row + 2][col] == board[row + 3][col]):
                    for i in range(4):
                        self.winning_positions.append((row + i, col))
                    return

        # Vérifier diagonalement (bas gauche vers haut droit)
        for row in range(3, 6):
            for col in range(4):
                if (board[row][col] == winner and
                        board[row][col] == board[row - 1][col + 1] ==
                        board[row - 2][col + 2] == board[row - 3][col + 3]):
                    for i in range(4):
                        self.winning_positions.append((row - i, col + i))
                    return

        # Vérifier diagonalement (haut gauche vers bas droit)
        for row in range(3):
            for col in range(4):
                if (board[row][col] == winner and
                        board[row][col] == board[row + 1][col + 1] ==
                        board[row + 2][col + 2] == board[row + 3][col + 3]):
                    for i in range(4):
                        self.winning_positions.append((row + i, col + i))
                    return

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