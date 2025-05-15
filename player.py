# This file will define the Player class and related functionalities. 
from typing import List, Dict, Any, Optional, TYPE_CHECKING, Tuple

# Conditional imports to avoid circular dependencies during type hinting
if TYPE_CHECKING:
    from card import Card
    from agenda import AgendaCard
    from board_elements import OwnerCell # For tracking visits

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
        self.cards_in_hand: List['Card'] = [] # Should be list[Card] later
        self.trust_levels: Dict[str, int] = {owner: 0 for owner in ALL_OWNERS}
        
        self.active_titles: List['Card'] = [] # Should be list[Card] later, for Title cards
        self.persistent_effects: List['Card'] = [] # Should be list[Card] for cards like Дикий Кот

        # Agenda related attributes
        self.secret_agenda: Optional['AgendaCard'] = None
        self.revealed_persistent_agendas: List['AgendaCard'] = [] # For agendas that give ongoing bonuses

        # For game rule: "Бонусы от посещения клеток ... можно получить только один раз за ход для каждой такой уникальной клетки"
        self.visited_special_cells_this_turn: set[tuple[int, int]] = set()

        # Stats for Agenda Objective Tracking
        self.visit_counts_this_game: Dict[str, int] = {owner: 0 for owner in ALL_OWNERS} # Tracks visits to Owner cells
        # self.visit_counts_this_game["Kiosk"] = 0 # Example for other cell types if needed
        # self.visit_counts_this_game["Basement"] = 0
        self.used_card_types_log: List[str] = [] # Log titles of cards successfully used/played
        self.action_log_this_turn: List[Dict[str, Any]] = [] # For complex turn-specific actions, e.g. {"type": "GaveFood", "amount": 2}
        
        # Agenda/Card granted abilities
        self.has_one_time_reroll_ability: bool = False
        # Add other specific ability flags as needed by rewards/effects

        self.armed_delayed_effects: List[Tuple[Card, Dict[str, Any]]] = [] # Store card and its play context
        self.temporary_bonuses_this_turn: List[Dict[str, Any]] = [] # For cards like "Быстрые лапки"

    def __repr__(self) -> str:
        agenda_title = self.secret_agenda.title if self.secret_agenda else "None"
        armed_effects_repr = [(card.title, ctx) for card, ctx in self.armed_delayed_effects]
        return (
            f"Player(id='{self.id}', pos=({self.row},{self.col}), food={self.food}, "
            f"cards_count={len(self.cards_in_hand)}, trust={self.trust_levels}, "
            f"titles_count={len(self.active_titles)}, effects_count={len(self.persistent_effects)}, "
            f"armed_effects={armed_effects_repr}, temp_bonuses={self.temporary_bonuses_this_turn}, "
            f"secret_agenda='{agenda_title}', revealed_agendas={len(self.revealed_persistent_agendas)}, "
            f"reroll_ability={self.has_one_time_reroll_ability})"
        )

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
        print(f"> {self.id} gained {amount} food. Total: {self.food}")

    def lose_food(self, amount: int) -> bool:
        """Decreases the player's food tokens. Returns True if successful, False otherwise."""
        if amount < 0:
            print(f"Warning: Tried to lose negative food ({amount}). Ignoring.")
            return True # Or False, depending on strictness
        if self.food >= amount:
            self.food -= amount
            print(f"> {self.id} lost {amount} food. Remaining: {self.food}")
            return True
        else:
            print(f"> {self.id} does not have enough food to lose {amount}. Has: {self.food}")
            return False

    def add_card_to_hand(self, card): # card type will be Card later
        """Adds a card to the player's hand."""
        if card:
            self.cards_in_hand.append(card)
            print(f"> {self.id} received card: {card.title}")

    def remove_card_from_hand(self, card): # card type will be Card later
        """Removes a specific card from the player's hand. Returns True if successful."""
        try:
            self.cards_in_hand.remove(card)
            print(f"> {self.id} removed card: {card.title} from hand.")
            return True
        except ValueError:
            print(f"Warning: Card {card.title} not found in {self.id}'s hand to remove.")
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
            print(f"> {self.id} has an effect preventing trust gain.")
            return

        self.trust_levels[owner_name] += amount
        print(f"> {self.id} gained {amount} trust with {owner_name}. Total: {self.trust_levels[owner_name]}")
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
        print(f"> {self.id} lost {amount} trust with {owner_name}. Remaining: {self.trust_levels[owner_name]}")

    def add_title(self, title_card):
        """Adds a title card to the player's active titles."""
        # Remove if already present to avoid duplicates, though titles are unique in game state
        if title_card not in self.active_titles:
            self.active_titles.append(title_card)
            print(f"> {self.id} gained title: {title_card.title}")

    def remove_title(self, title_card):
        """Removes a title card from the player's active titles."""
        try:
            self.active_titles.remove(title_card)
            print(f"> {self.id} lost title: {title_card.title}")
        except ValueError:
            pass # Already removed or wasn't there
            
    def add_persistent_effect(self, effect_card):
        """Adds a persistent effect card (like Дикий Кот)."""
        if effect_card not in self.persistent_effects:
            self.persistent_effects.append(effect_card)
            print(f"> {self.id} now has persistent effect: {effect_card.title}")

    def remove_persistent_effect(self, effect_card_title: str) -> bool:
        """Removes a persistent effect card by its title. Returns True if removed."""
        initial_len = len(self.persistent_effects)
        self.persistent_effects = [card for card in self.persistent_effects if card.title != effect_card_title]
        removed = len(self.persistent_effects) < initial_len
        if removed: print(f"> {self.id} lost effect: {effect_card_title}")
        return removed

    def start_new_turn(self):
        """Resets turn-specific player state."""
        self.visited_special_cells_this_turn.clear()
        self.action_log_this_turn.clear() # Clear turn-specific action log
        self.temporary_bonuses_this_turn.clear() # Clear temporary bonuses at start of new turn
        print(f"> Starting new turn for {self.id}. (Turn-specific stats cleared)")

    def has_visited_cell_this_turn(self, row: int, col: int) -> bool:
        """Checks if the player has already gained a benefit from a specific cell this turn."""
        return (row, col) in self.visited_special_cells_this_turn

    def record_cell_visit_this_turn(self, row: int, col: int):
        """Records that the player has gained a benefit from a cell this turn."""
        self.visited_special_cells_this_turn.add((row, col))

    def get_movement_bonus(self) -> int:
        bonus = 0
        # Check active titles (from Cards)
        for title_card in self.active_titles:
            if title_card.attributes_granted.get("MovementBonus"): # e.g. {"MovementBonus": 2}
                bonus += int(title_card.attributes_granted["MovementBonus"])
        
        # Check persistent effects from cards
        # for effect_card in self.persistent_effects:
        #     if effect_card.attributes_granted.get("MovementBonus"): 
        #         bonus += int(effect_card.attributes_granted["MovementBonus"])

        # Check persistent agenda bonuses
        # Agendas might grant bonuses differently, e.g. through their own effect descriptions
        # For now, assume if an agenda grants a movement bonus, it would be reflected here
        # or the game logic would handle it via the specific agenda's effect type.
        # Example: if an agenda effect added a temporary {"MovementBonus": X} to player.temp_stats
        # Add check for temporary bonuses
        for temp_bonus_info in self.temporary_bonuses_this_turn:
            if temp_bonus_info.get("MovementBonus"):
                bonus += int(temp_bonus_info["MovementBonus"])
        return bonus

    def can_pass_through_walls(self) -> bool:
        # Check active titles
        for title_card in self.active_titles:
            if title_card.attributes_granted.get("WallPass") == True:
                return True
        
        # Check persistent effects from cards (e.g. "Дикий кот")
        for effect_card in self.persistent_effects:
            if effect_card.attributes_granted.get("WallPass") == True:
                return True
        
        # Check persistent agenda bonuses
        # for agenda in self.revealed_persistent_agendas:
            # if agenda_grants_wall_pass_logic ...
        # Add check for temporary bonuses
        for temp_bonus_info in self.temporary_bonuses_this_turn:
            if temp_bonus_info.get("WallPass") == True:
                return True
        return False

    def get_fight_bonus(self) -> int:
        bonus = 0
        # Check active titles
        for title_card in self.active_titles:
            if title_card.attributes_granted.get("FightBonus"): # e.g. {"FightBonus": 1}
                bonus += int(title_card.attributes_granted["FightBonus"])
        
        # Check persistent effects from cards (e.g. "Бешеность")
        for effect_card in self.persistent_effects:
            if effect_card.attributes_granted.get("FightBonus"): 
                bonus += int(effect_card.attributes_granted["FightBonus"])

        # Check persistent agenda bonuses
        # for agenda in self.revealed_persistent_agendas:
            # if agenda_grants_fight_bonus_logic ...
        return bonus

    def has_active_effect_preventing_trust_gain(self) -> bool:
        for effect_card in self.persistent_effects:
            # Based on cards like "Дикий кот", "Бешеность"
            if effect_card.title in ["Дикий кот", "Бешеность"]:
                 # More robust: check effect_card.attributes_granted.get("PreventsTrustGain") == True
                return True
        return False

    def set_secret_agenda(self, agenda_card: 'AgendaCard'):
        if self.secret_agenda is None:
            self.secret_agenda = agenda_card
            print(f"> {self.id} received secret agenda: {agenda_card.title}")
        else:
            print(f"Warning: {self.id} already has a secret agenda. Cannot set new one: {agenda_card.title}")

    def reveal_agenda(self) -> Optional['AgendaCard']:
        """Called when a player believes they have completed their secret agenda."""
        # In a full implementation, this would trigger objective checking.
        # For now, it just reveals the card for manual processing.
        if self.secret_agenda:
            print(f"> {self.id} reveals agenda: {self.secret_agenda.title}")
            # print(f"  Objective: {self.secret_agenda.objective_text}")
            # print(f"  Reward: {self.secret_agenda.reward_text}")
            revealed = self.secret_agenda
            # self.secret_agenda = None # Agenda is revealed, no longer secret in the same way
                                      # Game logic will decide if it's discarded or moved to persistent.
            return revealed
        else:
            print(f"> {self.id} has no secret agenda to reveal.")
            return None
    
    def add_persistent_agenda_bonus(self, agenda_card: 'AgendaCard'):
        """Adds an agenda card that provides an ongoing bonus."""
        if agenda_card not in self.revealed_persistent_agendas:
            self.revealed_persistent_agendas.append(agenda_card)
            print(f"> {self.id} now has persistent agenda bonus from: {agenda_card.title}")

    def remove_persistent_agenda_bonus(self, agenda_card_title: str) -> bool:
        initial_len = len(self.revealed_persistent_agendas)
        self.revealed_persistent_agendas = [
            card for card in self.revealed_persistent_agendas if card.title != agenda_card_title
        ]
        if len(self.revealed_persistent_agendas) < initial_len:
            return True
        return False

    # --- Methods for tracking stats for Agendas ---
    def record_owner_visit(self, owner_cell: 'OwnerCell'):
        if owner_cell.owner_name in self.visit_counts_this_game:
            self.visit_counts_this_game[owner_cell.owner_name] += 1
        else:
            self.visit_counts_this_game[owner_cell.owner_name] = 1
        print(f"> {self.id} visit count for {owner_cell.owner_name}: {self.visit_counts_this_game[owner_cell.owner_name]}")

    def record_card_usage(self, card_title: str, context: Optional[Dict[str, Any]] = None):
        self.used_card_types_log.append(card_title)
        # For more complex context for UsedSpecificCardWithContextCondition, log to action_log_this_turn
        if context: 
            action_log_entry = {"type": "UsedCardWithContext", "card_title": card_title, **context}
            self.record_action_in_turn(action_log_entry)

    def record_action_in_turn(self, action_details: Dict[str, Any]):
        """Records a significant action taken this turn, for complex agenda checks."""
        self.action_log_this_turn.append(action_details)
        print(f"> {self.id} logged action: {action_details}")

    def grant_one_time_reroll(self):
        self.has_one_time_reroll_ability = True
        print(f"> {self.id} gained a one-time re-roll ability!")

    def consume_one_time_reroll(self) -> bool:
        if self.has_one_time_reroll_ability:
            self.has_one_time_reroll_ability = False
            print(f"> {self.id} used their one-time re-roll ability.")
            return True
        return False

    def add_armed_delayed_effect(self, card: 'Card', context: Optional[Dict[str, Any]] = None):
        """Adds a card whose effect is armed, along with its play context."""
        if context is None:
            context = {}
        # Avoid adding the exact same card instance multiple times if logic error somewhere else
        # Simple check by card id for now.
        if not any(armed_card.id == card.id for armed_card, _ in self.armed_delayed_effects):
            self.armed_delayed_effects.append((card, context))
            print(f"> {self.id} armed card: {card.title} w/ context {context}")
        else:
            print(f"Warning: Card {card.title} (id: {card.id}) already armed.")

    def remove_armed_delayed_effect(self, card_to_remove: 'Card'):
        original_len = len(self.armed_delayed_effects)
        self.armed_delayed_effects = [(card, ctx) for card, ctx in self.armed_delayed_effects if card.id != card_to_remove.id]
        if len(self.armed_delayed_effects) < original_len:
            print(f"> {self.id} removed armed card: {card_to_remove.title}")
        else:
            print(f"Warning: armed card {card_to_remove.title} not found to remove.")

    def add_temporary_bonus(self, bonus_details: Dict[str, Any]):
        """Adds a temporary bonus for the current turn (e.g., from Быстрые лапки)."""
        self.temporary_bonuses_this_turn.append(bonus_details)
        print(f"> {self.id} gained temporary bonus: {bonus_details}")

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