class Cell:
    """Base class for all cell types on the game board."""
    def __init__(self, row: int, col: int, symbol: str):
        self.row = row
        self.col = col
        self.symbol = symbol

    def __repr__(self):
        return f"{self.__class__.__name__}({self.row}, {self.col}, '{self.symbol}')"

    def on_enter(self, player, game_state):
        """
        Action to perform when a player enters this cell.
        To be implemented by subclasses.
        """
        pass # Base cells might do nothing or this could be an abstract method

class Wall(Cell):
    """Represents an impassable wall cell."""
    def __init__(self, row: int, col: int):
        super().__init__(row, col, '.')

    def on_enter(self, player, game_state):
        # Players should not be able to enter a wall.
        # This logic might be better handled by movement validation.
        print("Cannot enter a wall.")
        pass 

class Kiosk(Cell):
    """Represents a Kiosk cell where players can draw a card."""
    def __init__(self, row: int, col: int):
        super().__init__(row, col, 'K')

    def on_enter(self, player, game_state):
        # Logic to draw a card will be handled by the Game class
        # This method can signify the type of interaction.
        print(f"Player {player.id} entered Kiosk at ({self.row},{self.col}). Should draw a card.")
        # game_state.player_draws_card(player)
        pass

class Basement(Cell):
    """Represents a Basement cell where players can get food."""
    def __init__(self, row: int, col: int):
        super().__init__(row, col, 'B')

    def on_enter(self, player, game_state):
        # Logic to gain food will be handled by the Game class
        print(f"Player {player.id} entered Basement at ({self.row},{self.col}). Should gain 2 food.")
        # player.gain_food(2)
        pass

class OwnerCell(Cell):
    """Base class for cells occupied by an owner."""
    def __init__(self, row: int, col: int, symbol: str, owner_name: str):
        super().__init__(row, col, symbol)
        self.owner_name = owner_name

    def on_enter(self, player, game_state):
        # Common logic for entering any owner cell, if any, or specific in subclass
        print(f"Player {player.id} entered {self.owner_name}'s cell at ({self.row},{self.col}).")
        pass

class StudentCell(OwnerCell):
    """Represents the Student's cell."""
    def __init__(self, row: int, col: int):
        super().__init__(row, col, 'S', 'Student')

    def on_enter(self, player, game_state):
        super().on_enter(player, game_state) # Call base if it has common logic
        # Logic to gain trust with Student
        print(f"Should gain 1 trust with Student.")
        # player.gain_trust(self.owner_name, 1)
        pass

class CookCell(OwnerCell):
    """Represents the Cook's cell."""
    def __init__(self, row: int, col: int):
        super().__init__(row, col, 'C', 'Cook')

    def on_enter(self, player, game_state):
        super().on_enter(player, game_state)
        # Logic to gain 2 food (as per game_rules.md for visiting Cook directly)
        print(f"Should gain 2 food.")
        # player.gain_food(2)
        pass

class LibrarianCell(OwnerCell):
    """Represents the Librarian's cell."""
    def __init__(self, row: int, col: int):
        super().__init__(row, col, 'L', 'Librarian')

    def on_enter(self, player, game_state):
        super().on_enter(player, game_state)
        # Logic to draw a card (as per game_rules.md for visiting Librarian directly)
        print(f"Should draw 1 card.")
        # game_state.player_draws_card(player)
        pass 