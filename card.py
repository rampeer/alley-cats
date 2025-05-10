# This file will define the Card class and functions for managing the card deck. 

import json
import random

class Card:
    """Represents a single playing card in the Alley Cats game."""
    def __init__(self, title: str, description: str, discard_condition: str, card_id: str = None):
        self.title: str = title
        self.description: str = description
        self.discard_condition: str = discard_condition
        # card_id could be useful if we need to track individual instances of identical cards
        # For now, title might be sufficient for most effect lookups.
        # Create a simple unique enough ID for now, helps if we need to distinguish identical cards in hand.
        self.id = card_id if card_id else f"{title.replace(' ', '_')}_{random.randint(10000,99999)}" 

    def __repr__(self) -> str:
        return f"Card(title='{self.title}', id='{self.id}')"

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

class Deck:
    """Manages the deck of cards, including draw and discard piles."""
    def __init__(self, card_data_filepath: str = "cards.json"):
        self.draw_pile: list[Card] = []
        self.discard_pile: list[Card] = []
        self._load_cards(card_data_filepath)
        self.shuffle()

    def _load_cards(self, filepath: str):
        """Loads card definitions from a JSON file and populates the draw pile."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                all_card_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: Card data file not found at {filepath}")
            # Potentially raise an exception or handle as a critical error
            return
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {filepath}")
            return

        for card_info in all_card_data:
            count = card_info.get("count", 0)
            title = card_info.get("title", "Unnamed Card")
            description = card_info.get("description", "")
            discard_condition = card_info.get("discard_condition", "Сразу") # Default if missing
            
            for _ in range(count):
                self.draw_pile.append(Card(title, description, discard_condition))
        
        print(f"Deck loaded with {len(self.draw_pile)} cards from {len(all_card_data)} types.")

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
