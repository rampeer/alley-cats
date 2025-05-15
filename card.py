# This file will define the Card class and functions for managing the card deck. 

import json
import random
from typing import List, Dict, Any, TYPE_CHECKING, Optional

# Import Effect and its related components for Deck operation
from effects import EFFECT_REGISTRY, Effect, ConditionalEffect

# Conditional import for type hinting to avoid circular dependency
if TYPE_CHECKING:
    # from effects import Effect # No longer needed here as it's imported globally for Deck
    from player import Player
    from game import Game

class Card:
    """Represents a single playing card in the Alley Cats game."""
    def __init__(self, 
                 title: str, 
                 description: str, 
                 discard_condition: str, 
                 effects: List[Effect],  # This hint now works because Effect is known
                 cost: Dict[str, Any], 
                 timing: str, 
                 target_needed: bool, 
                 card_type_flags: Optional[List[str]] = None, 
                 attributes_granted: Optional[Dict[str, Any]] = None,
                 card_id: Optional[str] = None):
        self.title: str = title
        self.description: str = description
        self.discard_condition: str = discard_condition
        self.id: str = card_id if card_id else f"{title.replace(' ', '_')}_{random.randint(10000,99999)}"
        
        self.effects: List[Effect] = effects 
        self.cost: Dict[str, Any] = cost if cost is not None else {}
        self.timing: str = timing if timing is not None else "InTurn"
        self.target_needed: bool = target_needed if target_needed is not None else False
        self.card_type_flags: List[str] = card_type_flags if card_type_flags is not None else []
        self.attributes_granted: Dict[str, Any] = attributes_granted if attributes_granted is not None else {}

    def __repr__(self) -> str:
        return f"Card(title='{self.title}', id='{self.id}', effects_count={len(self.effects)})"

    def __eq__(self, other) -> bool:
        """Two cards are considered equal if their unique IDs are the same.
           If you need to check for card *type* equality (e.g. two "Поймал мышку" cards are of the same type),
           compare their titles: card1.title == card2.title.
        """
        if isinstance(other, Card):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        """Allows Card objects to be added to sets or used as dict keys based on their unique ID."""
        return hash(self.id)

    def can_play(self, player: 'Player', game_state: 'Game') -> bool:
        """Checks if the player can currently afford to play this card based on its cost."""
        for resource, amount in self.cost.items():
            if resource == "food":
                if player.food < amount:
                    print(f"{player.id} cannot afford {amount} food for {self.title} (has {player.food}).")
                    return False
            # Add other resource checks (e.g., cards_to_discard) if needed
        return True

    def activate(self, executing_player: 'Player', game_state: 'Game', targets: List['Player'] | None = None) -> bool:
        """
        Activates all effects of this card.
        Assumes cost has already been paid and timing/targeting is validated by the Game class.
        """
        print(f"{executing_player.id} is activating card: {self.title}")
        all_effects_succeeded = True # Or track if any effect made a change
        for effect in self.effects:
            success = effect.execute(self, executing_player, game_state, targets)
            if not success:
                # Decide on behavior: should one failed effect stop others?
                # For now, let's say some effects might be optional or fail gracefully.
                print(f"An effect of {self.title} did not fully succeed or apply.")
                # all_effects_succeeded = False # Uncomment if one failure means overall failure
        
        # The Game class will handle discarding based on self.discard_condition
        return all_effects_succeeded

class Deck:
    """Manages the deck of cards, including draw and discard piles."""
    def __init__(self, card_data_filepath: str = "cards.json"):
        self.draw_pile: list[Card] = []
        self.discard_pile: list[Card] = []
        # self._effect_factory = EffectFactory(EFFECT_REGISTRY) # Removed earlier, which was correct
        self._load_cards(card_data_filepath)
        self.shuffle()

    def _create_effect_instance(self, effect_data: Dict[str, Any]) -> Optional[Effect]: # Type hint should now work
        effect_type_str = effect_data.get("type")
        effect_params = effect_data.get("params", {})
        
        effect_class = EFFECT_REGISTRY.get(effect_type_str)
        if not effect_class:
            print(f"Warning: Unknown effect type '{effect_type_str}' in card data. Skipping this effect.")
            return None
        
        try:
            effect_instance = effect_class(effect_params)
            if isinstance(effect_instance, ConditionalEffect):
                # Recursively instantiate sub-effects for ConditionalEffect
                then_effects_data = effect_instance.params.get("then_effects", [])
                else_effects_data = effect_instance.params.get("else_effects", [])
                
                effect_instance.then_effects_instances = [
                    sub_effect for sub_effect_data in then_effects_data 
                    if (sub_effect := self._create_effect_instance(sub_effect_data)) is not None
                ]
                effect_instance.else_effects_instances = [
                    sub_effect for sub_effect_data in else_effects_data
                    if (sub_effect := self._create_effect_instance(sub_effect_data)) is not None
                ]
            return effect_instance
        except Exception as e:
            print(f"Error instantiating effect '{effect_type_str}' (params: {effect_params}): {e}")
            import traceback; traceback.print_exc() # More debug info
            return None

    def _load_cards(self, filepath: str):
        """Loads card definitions from a JSON file and populates the draw pile."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                all_card_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: Card data file not found at {filepath}. No cards loaded.")
            return
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {filepath}. No cards loaded.")
            return

        for card_info in all_card_data:
            title = card_info.get("title", "Unnamed Card")
            description = card_info.get("description", "")
            discard_condition = card_info.get("discard_condition", "Сразу")
            count = card_info.get("count", 0)

            # New fields based on the Strategy/Component pattern
            cost = card_info.get("cost", {})
            timing = card_info.get("timing", "InTurn")
            target_needed = card_info.get("target_needed", False)
            card_type_flags = card_info.get("card_type_flags", [])
            attributes_granted = card_info.get("attributes_granted", {})
            effects_data_list = card_info.get("effects", []) # List of effect dictionaries

            instantiated_effects: List[Effect] = []
            for effect_data in effects_data_list:
                effect_instance = self._create_effect_instance(effect_data)
                if effect_instance:
                    instantiated_effects.append(effect_instance)
            
            if not instantiated_effects and effects_data_list: # Some effects were defined but failed to load
                print(f"Warning: Card '{title}' had effect definitions but none were successfully instantiated.")
            elif not effects_data_list:
                print(f"Note: Card '{title}' has no defined effects in JSON.")

            for _ in range(count):
                self.draw_pile.append(Card(
                    title=title, 
                    description=description, 
                    discard_condition=discard_condition,
                    effects=instantiated_effects, # Pass the list of Effect objects
                    cost=cost,
                    timing=timing,
                    target_needed=target_needed,
                    card_type_flags=card_type_flags,
                    attributes_granted=attributes_granted
                ))
        
        print(f"Deck loaded with {len(self.draw_pile)} cards from {len(all_card_data)} types (Strategy/Component)." )

    def shuffle(self):
        """Shuffles the draw pile."""
        random.shuffle(self.draw_pile)
        print("Deck shuffled.")

    def draw(self) -> Card | None:
        """Draws a card from the top of the draw pile.
           If the draw pile is empty, it attempts to reshuffle the discard pile.
        """
        if not self.draw_pile:
            print("Draw pile empty. Attempting to reshuffle discard pile.")
            if not self.discard_pile:
                print("Discard pile is also empty. No cards to draw.")
                return None
            self.reshuffle_discard_pile()
            if not self.draw_pile: # Still empty after trying to reshuffle (e.g. discard was also empty)
                print("No cards available to draw even after reshuffle attempt.")
                return None
        
        return self.draw_pile.pop(0) # Draw from the "top" (index 0)

    def discard(self, card: Card):
        """Adds a card to the discard pile."""
        if card:
            self.discard_pile.append(card)
            # print(f"Card '{card.title}' discarded.") # Can be verbose
        else:
            print("Warning: Tried to discard a None card.")

    def needs_reshuffle(self) -> bool:
        """Checks if the draw pile is empty and there are cards in the discard pile."""
        return not self.draw_pile and bool(self.discard_pile)

    def reshuffle_discard_pile(self):
        """Moves all cards from the discard pile to the draw pile and shuffles it."""
        if not self.discard_pile:
            print("No cards in discard pile to reshuffle.")
            return

        print(f"Reshuffling {len(self.discard_pile)} cards from discard into draw pile.")
        self.draw_pile.extend(self.discard_pile)
        self.discard_pile.clear()
        self.shuffle()

    def get_draw_pile_size(self) -> int:
        return len(self.draw_pile)

    def get_discard_pile_size(self) -> int:
        return len(self.discard_pile)

# Example Usage:
if __name__ == '__main__':
    # Create a dummy cards.json for testing if it doesn't exist
    # You should have your actual cards.json for this to work properly
    try:
        with open('cards.json', 'r') as f:
            pass
    except FileNotFoundError:
        print("Creating dummy cards.json for testing Deck class.")
        dummy_cards_data = [
            {"count": 2, "title": "Test Card A", "description": "Does A", "discard_condition": "Сразу"},
            {"count": 1, "title": "Test Card B", "description": "Does B", "discard_condition": "Постоянно"}
        ]
        with open('cards.json', 'w', encoding='utf-8') as f:
            json.dump(dummy_cards_data, f)

    deck = Deck()
    print(f"Draw pile size: {deck.get_draw_pile_size()}, Discard pile size: {deck.get_discard_pile_size()}")
    
    drawn_cards = []
    for _ in range(deck.get_draw_pile_size() + 1): # Try to draw all cards and one more
        card = deck.draw()
        if card:
            print(f"Drawn: {card}")
            drawn_cards.append(card)
        else:
            print("Could not draw a card.")
            break
    
    print(f"Draw pile size: {deck.get_draw_pile_size()}, Discard pile size: {deck.get_discard_pile_size()}")

    for card in drawn_cards:
        deck.discard(card)
    
    print(f"Draw pile size: {deck.get_draw_pile_size()}, Discard pile size: {deck.get_discard_pile_size()}")

    if deck.needs_reshuffle():
        print("Deck needs reshuffle.")
        # deck.reshuffle_discard_pile() # draw() handles this automatically

    card = deck.draw()
    if card:
        print(f"Drawn after potential reshuffle: {card}")
    print(f"Draw pile size: {deck.get_draw_pile_size()}, Discard pile size: {deck.get_discard_pile_size()}")
