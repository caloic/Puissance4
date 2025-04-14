# Puissance 4 en ligne - Serveur de Matchmaking

![Puissance 4](https://img.shields.io/badge/Jeu-Puissance%204-red)
![Python](https://img.shields.io/badge/Language-Python-blue)

Un jeu de Puissance 4 en ligne avec système de matchmaking, permettant à des joueurs de s'affronter en temps réel via Internet. Le projet comprend un serveur, un client avec interface graphique animée et une base de données.

## 🎮 Fonctionnalités

- **Système de matchmaking en temps réel** : file d'attente et association automatique des joueurs
- **Interface graphique animée** avec effets visuels et transitions fluides
- **Communication réseau robuste** basée sur les sockets TCP
- **Persistance des données** avec SQLite
- **Logique de jeu Puissance 4 complète** avec détection des victoires et matchs nuls

## 🛠️ Technologies utilisées

- **Python** : Langage principal du projet, utilisé à la fois pour le client et le serveur
- **Tkinter** : Bibliothèque graphique pour l'interface utilisateur
- **SQLite** : Système de gestion de base de données légère
- **JSON** : Format d'échange de données entre le client et le serveur
- **Threading** : Gestion des processus parallèles pour la communication asynchrone
- **Socket** : Communication réseau bas niveau entre client et serveur

## 📋 Prérequis

- Python 3.8 ou supérieur
- Aucune bibliothèque externe n'est nécessaire (uniquement les bibliothèques standard de Python)

## 🚀 Installation et lancement

1. Clonez le dépôt :
   ```bash
   git clone https://github.com/caloic/Puissance4.git
   cd puissance4
   ```

2. Création et activation de l'environnement virtuel :
   ```bash
   # Création de l'environnement virtuel
   python -m venv .venv
   
   # Activation de l'environnement virtuel
   # Sur Windows :
   .venv\Scripts\activate
   # Sur Unix/MacOS :
   source .venv/bin/activate
   ```

3. Lancement du serveur :
   ```bash
   python main_server.py
   ```
   Par défaut, le serveur utilise le port 5555 si aucun port n'est spécifié.

4. Lancement du client :
   ```bash
   python main_client.py
   ```
   Par défaut, le client se connecte à `localhost:5555` si aucun paramètre n'est spécifié.

## 📂 Structure du projet

```
puissance4/
├── client/                  # Code du client
│   ├── __init__.py
│   ├── client.py            # Client principal
│   ├── gui.py               # Interface graphique
│   └── network.py           # Communication réseau
├── server/                  # Code du serveur
│   ├── __init__.py
│   ├── database.py          # Gestion de la base de données
│   ├── game_logic.py        # Logique du jeu Puissance 4
│   ├── matchmaking.py       # Gestion du matchmaking
│   └── server.py            # Serveur principal
├── common/                  # Code partagé
│   ├── __init__.py
│   └── protocol.py          # Protocole de communication
├── main_client.py           # Point d'entrée du client
└── main_server.py           # Point d'entrée du serveur
```

## 🕹️ Utilisation

1. Lancez le serveur
2. Lancez le client (plusieurs instances pour tester)
3. Entrez votre nom et rejoignez la file d'attente
4. Attendez qu'un adversaire rejoigne la file d'attente
5. Jouez en cliquant sur les colonnes du plateau

## 👥 Développeurs

Ce projet a été réalisé par :

- **Dylan ARLIN**
  - Architecture générale du projet
  - Développement du serveur et matchmaking
  - Gestion de la base de données
  - Logique du jeu Puissance 4
  - Protocole de communication

- **Loïc CANO**
  - Développement de l'interface graphique
  - Animation et effets visuels
  - Intégration client-serveur
  - Tests et débogage
  - Documentation

## 🔄 Améliorations futures

- Système de comptes utilisateurs
- Historique des parties et classement des joueurs
- Options de jeu supplémentaires (taille du plateau, variantes de règles)
- Parties privées entre amis
- Interface web responsive en complément du client desktop
- Chat entre joueurs

---

Projet développé à Montpellier Ynov Campus.
