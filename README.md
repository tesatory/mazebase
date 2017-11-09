# mazebase

Basic architecture:   
the main game class is in grid_game.py
two example games in switches.py and goto.py
game states are described via the attributes of the items in the game.
a factory, main class in game_factory.py, defines a wrapper that:
  generates random games, 
  keeps a consistent vocabulary (perhaps across many games), so that game states can undertood across several games
  keeps a consistent mapping into actions
  TODO executes a curriculum
For each new game it is assumed you will write the game (subclassing grid_game) and a factory (subclassing game_factory) 
See game_factory.py for an example of how to build a factory with multiple games
