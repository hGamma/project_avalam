# Notations

## class Board

### Attributs
- `m` : La matrice du plateau. Chaque case contient (nb de pions de la tour)*(signe du joueur qui la tiens)
- `rows` et `columns` : Le nombre de lignes et colonnes.
- `max_height` : Hauteur max d'une tour

### Méthodes
- `clone()`
- `get_percepts()` : Getter de la matrice
- `get_towers()` : Yield un générateur des tours présentes sur le plateau. Une tour est sous la forme : `(i,j,k)` où :
  - `(i, j)` : coordonnées de la tour
  - `k` : Valeur signée de la tour
- `get_tower_actions(i,j)` : Renvoie les actions légales de la tour `(i,j)`. Les actions sont représentées sous la forme `(i1, j1, i2, j2)` où :
  - `(i1, j1)` sont les coordonnées de la tour à bouger
  - `(i2, j2)` sont les coordonnées de la case cible due la tour
- `is_tower_movable(i,j)`
- `get_actions()` : Yield un générateur de toutes les actions possibles sur le plateau.
- `play_actions(i1, j1, i2, j2)` : Joue en place l'action précisée. Renvoie une exception si le coup est illégal.
- `is_finished()` : Booléen qui indique si la partie est terminée.
- `get_score()` : Renvoie le score du joueur +1 (jaune)

### Fonctions annexes
- `dict_to_board(dict)` : Constructeur de Board à partir d'un dictionaire dont les keys `m`, `rows` et `max_height`ont été remplies.
- `load_percepts(file_csv_name)`

## class Agent

Une classe abstraite pour tous les agents

### Méthodes abstraites
- `initialize(percepts, players, time_left)` : Joué au début de la partie.
  - `percepts` : La matrice du plateau actuel
  - `players` : Le joueur qui va jouer avec cet agent. +1 pour le joueur max et -1 pour le joueur min. Attention à bien inverser le Board avec le paramètre invert dans le constructeur si c'est le joueur min.
  - `time_left` : Le temps restant en secondes

- `play(percepts, players, step, time_left)` : Renvoie le coup à jouer