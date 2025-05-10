# This file will define the Player class and related functionalities. 

OWNER_STUDENT = "Student"
OWNER_COOK = "Cook"
OWNER_LIBRARIAN = "Librarian"
ALL_OWNERS = [OWNER_STUDENT, OWNER_COOK, OWNER_LIBRARIAN]

class Player:
    """Represents a player (a cat) in the Alley Cats game."""

    INITIAL_FOOD = 5
    INITIAL_CARDS_IN_HAND = 0 # Cards are drawn during game setup

    def __init__(self, player_id: str, initial_row: int, initial_col: int, is_human: bool = True):
        self.id: str = player_id
        self.row: int = initial_row
        self.col: int = initial_col
        self.is_human: bool = is_human

        self.food: int = Player.INITIAL_FOOD
        self.cards_in_hand: list = [] # Should be list[Card] later
        self.trust_levels: dict[str, int] = {owner: 0 for owner in ALL_OWNERS}
        
        self.active_titles: list = [] # Should be list[Card] later, for Title cards
        self.persistent_effects: list = [] # Should be list[Card] for cards like Дикий Кот

        # For game rule: "Бонусы от посещения клеток ... можно получить только один раз за ход для каждой такой уникальной клетки"
        self.visited_special_cells_this_turn: set[tuple[int, int]] = set()

    def __repr__(self) -> str:
        return (
            f"Player(id='{self.id}', pos=({self.row},{self.col}), food={self.food}, "
            f"cards_count={len(self.cards_in_hand)}, trust={self.trust_levels}, "
            f"titles_count={len(self.active_titles)}, effects_count={len(self.persistent_effects)})")

    def update_position(self, new_row: int, new_col: int):
        """Updates the player's position on the board."""
        self.row = new_row
        self.col = new_col

    def gain_food(self, amount: int):
        """Increases the player's food tokens."""
        if amount < 0:
            print(f"Warning: Tried to gain negative food ({amount}). Ignoring.")
            return
        self.food += amount
        print(f"{self.id} gained {amount} food. Total: {self.food}")

    def lose_food(self, amount: int) -> bool:
        """Decreases the player's food tokens. Returns True if successful, False otherwise."""
        if amount < 0:
            print(f"Warning: Tried to lose negative food ({amount}). Ignoring.")
            return True # Or False, depending on strictness
        if self.food >= amount:
            self.food -= amount
            print(f"{self.id} lost {amount} food. Remaining: {self.food}")
            return True
        else:
            print(f"{self.id} does not have enough food to lose {amount}. Has: {self.food}")
            return False

    def add_card_to_hand(self, card): # card type will be Card later
        """Adds a card to the player's hand."""
        self.cards_in_hand.append(card)
        # print(f"{self.id} received card: {card.title}") # Assuming card has a title

    def remove_card_from_hand(self, card): # card type will be Card later
        """Removes a specific card from the player's hand. Returns True if successful."""
        try:
            self.cards_in_hand.remove(card)
            # print(f"{self.id} removed card: {card.title}")
            return True
        except ValueError:
            # print(f"Card {card.title} not found in {self.id}'s hand.")
            return False

    def gain_trust(self, owner_name: str, amount: int):
        """Increases trust with a specific owner."""
        if owner_name not in self.trust_levels:
            print(f"Error: Unknown owner '{owner_name}'. Cannot gain trust.")
            return
        if amount < 0:
            print(f"Warning: Tried to gain negative trust ({amount}) for {owner_name}. Ignoring.")
            return
        
        # Rule: "Дикий кот не может получать новые очки доверия"
        # Rule: "Бешеность не может получать новые очки доверия"
        # This check should ideally be in a helper method like self.can_gain_trust()
        # For now, simple check, will be refined when cards are implemented
        if any(effect.title == "Дикий кот" for effect in self.persistent_effects) or \
           any(effect.title == "Бешеность" for effect in self.persistent_effects):
            print(f"{self.id} has an effect preventing trust gain.")
            return

        self.trust_levels[owner_name] += amount
        print(f"{self.id} gained {amount} trust with {owner_name}. Total: {self.trust_levels[owner_name]}")
        # Check for win condition here or in the game loop

    def lose_trust(self, owner_name: str, amount: int):
        """Decreases trust with a specific owner."""
        if owner_name not in self.trust_levels:
            print(f"Error: Unknown owner '{owner_name}'. Cannot lose trust.")
            return
        if amount < 0:
            print(f"Warning: Tried to lose negative trust ({amount}) for {owner_name}. Ignoring.")
            return
        self.trust_levels[owner_name] = max(0, self.trust_levels[owner_name] - amount)
        print(f"{self.id} lost {amount} trust with {owner_name}. Remaining: {self.trust_levels[owner_name]}")

    def add_title(self, title_card):
        """Adds a title card to the player's active titles."""
        # Remove if already present to avoid duplicates, though titles are unique in game state
        if title_card not in self.active_titles:
            self.active_titles.append(title_card)
            # print(f"{self.id} gained title: {title_card.title}")

    def remove_title(self, title_card):
        """Removes a title card from the player's active titles."""
        try:
            self.active_titles.remove(title_card)
            # print(f"{self.id} lost title: {title_card.title}")
        except ValueError:
            pass # Already removed or wasn't there
            
    def add_persistent_effect(self, effect_card):
        """Adds a persistent effect card (like Дикий Кот)."""
        if effect_card not in self.persistent_effects:
            self.persistent_effects.append(effect_card)
            # print(f"{self.id} now has effect: {effect_card.title}")

    def remove_persistent_effect(self, effect_card_title: str) -> bool:
        """Removes a persistent effect card by its title. Returns True if removed."""
        initial_len = len(self.persistent_effects)
        self.persistent_effects = [card for card in self.persistent_effects if card.title != effect_card_title]
        if len(self.persistent_effects) < initial_len:
            # print(f"{self.id} lost effect: {effect_card_title}")
            return True
        return False

    def start_new_turn(self):
        """Resets turn-specific player state."""
        self.visited_special_cells_this_turn.clear()
        print(f"Starting new turn for {self.id}.")

    def has_visited_cell_this_turn(self, row: int, col: int) -> bool:
        """Checks if the player has already gained a benefit from a specific cell this turn."""
        return (row, col) in self.visited_special_cells_this_turn

    def record_cell_visit_this_turn(self, row: int, col: int):
        """Records that the player has gained a benefit from a cell this turn."""
        self.visited_special_cells_this_turn.add((row, col))

    # Placeholder for methods that will check active card effects
    def can_pass_through_walls(self) -> bool:
        # e.g., check for "Дикий кот", "Лучший котик"
        # return any(title.type == "WallPass" for title in self.active_titles)
        return False # Placeholder

    def get_movement_bonus(self) -> int:
        # e.g., check for "Искатель приключений" (+2)
        bonus = 0
        # if any(title.name == "Искатель приключений" for title in self.active_titles):
        #     bonus += 2
        return bonus # Placeholder

    def get_fight_bonus(self) -> int:
        # e.g., check for "Бешеность" (+1), "Гроза дворов" (+1)
        bonus = 0
        # if any(effect.name == "Бешеность" for effect in self.persistent_effects):
        #     bonus +=1
        # if any(title.name == "Гроза дворов" for title in self.active_titles):
        #     bonus += 1
        return bonus # Placeholder

    # More methods will be added as needed, e.g., for playing cards, fighting, etc.

# Example Usage (for testing, can be removed later)
if __name__ == '__main__':
    player1 = Player("Catrick Swayze", 0, 0)
    print(player1)
    player1.gain_food(3)
    player1.lose_food(10) # Test losing more than available
    player1.lose_food(2)
    print(player1)

    player1.gain_trust(OWNER_STUDENT, 2)
    player1.gain_trust(OWNER_COOK, 1)
    player1.lose_trust(OWNER_STUDENT, 1)
    player1.lose_trust("NonExistentOwner", 1)
    print(player1)

    player1.start_new_turn()
    print(f"Visited (1,1)? {player1.has_visited_cell_this_turn(1,1)}")
    player1.record_cell_visit_this_turn(1,1)
    print(f"Visited (1,1) again? {player1.has_visited_cell_this_turn(1,1)}") 