# This file will contain the main game logic, turn management, and rule enforcement. 

import random
from typing import List, Tuple, Dict, Optional

from map_parser import load_map
from board_elements import Cell, OwnerCell, Kiosk, Basement # More specific imports
from player import Player, ALL_OWNERS # Assuming player.py has ALL_OWNERS
from card import Card, Deck
from agenda import AgendaCard, AgendaDeck # Added Agenda imports
# Import specific objective conditions and effects needed for isinstance checks or direct use
from objective_conditions import EndedTurnWithPlayerStatCondition 
from effects import (
    EFFECT_REGISTRY, Effect, ConditionalEffect, ApplyTitleEffect, ApplyPersistentEffectCard, 
    AddPersistentCellVisitBonusEffect, AddPersistentFoodSourceBonusEffect,
    ArmDelayedEffect, GrantTemporaryBonusEffect # Import new effect types
)
from objective_conditions import (
    OBJECTIVE_REGISTRY, ObjectiveCondition, PlayerIsOnAnyOwnerCellCondition, IsOnSameCellAsTargetCondition, # and other specific ones if used directly
    UsedSpecificCardWithContextCondition, PerformedVoluntaryActionOnLocationCondition,
    SuccessfullyPlayedCardWithEffectTypeCondition
)
# Effects will be used by Card.activate(), so Game needs to provide state to them.
# from effects import Effect 

class Game:
    """Orchestrates the game of Alley Cats."""

    WIN_TRUST_LEVEL = 10
    INITIAL_CARDS_TO_DEAL = 3

    def __init__(self, player_ids: List[str], map_filepath: str = "map.txt", card_filepath: str = "cards.json", agenda_filepath: str = "secret_agendas.json"):
        print("Initializing Alley Cats game...")
        self.board: List[List[Cell]] = load_map(map_filepath)
        if not self.board:
            raise ValueError("Failed to load the map. Cannot start game.")
        
        self.deck: Deck = Deck(card_filepath)
        if self.deck.get_draw_pile_size() == 0 and self.deck.get_discard_pile_size() == 0 :
             # This check might be too strict if cards.json could be initially empty for some reason
             # but generally, a game needs cards.
            print("Warning: Deck is empty after loading. cards.json might be missing or empty.")
            # raise ValueError("Deck is empty. Cannot start game without cards.")

        self.agenda_deck: AgendaDeck = AgendaDeck(agenda_filepath) # Initialize AgendaDeck
        if not self.agenda_deck.agenda_cards and not self.agenda_deck.played_agendas:
            print("Warning: Agenda deck is completely empty (no cards to draw and none played). secret_agendas.json might be missing or empty.")

        self.players: List[Player] = []
        self._initialize_players(player_ids)
        
        self._deal_initial_cards()
        self._deal_initial_agendas() # Deal agendas after players are created

        self.current_player_index: int = 0
        self.game_over: bool = False
        self.winner: Optional[Player] = None

        self.owner_locations: Dict[str, Tuple[int, int]] = self._find_owner_locations()
        print(f"Owner locations found: {self.owner_locations}")

        print("Game initialized.")

    def _find_owner_locations(self) -> Dict[str, Tuple[int, int]]:
        locations = {}
        for r_idx, row in enumerate(self.board):
            for c_idx, cell in enumerate(row):
                if isinstance(cell, OwnerCell): # Checks for StudentCell, CookCell, LibrarianCell
                    # Ensure owner_name is one of the defined ALL_OWNERS for consistency
                    if cell.owner_name in ALL_OWNERS:
                         locations[cell.owner_name] = (r_idx, c_idx)
                    else:
                        print(f"Warning: Found an OwnerCell with unrecognized owner_name '{cell.owner_name}' at ({r_idx},{c_idx}).")
        
        # Validate that all expected owners are found
        for owner_key in ALL_OWNERS:
            if owner_key not in locations:
                print(f"Critical Warning: Owner '{owner_key}' not found on the map! Check map.txt and board_elements.py.")
                # Depending on game rules, this could be a fatal error.
        return locations

    def _get_valid_start_position(self) -> Tuple[int, int]:
        """Finds a random valid (non-wall, traversable) starting position."""
        valid_positions = []
        for r, row_cells in enumerate(self.board):
            for c, cell in enumerate(row_cells):
                # A simple check: not a Wall and not an OwnerCell (usually players don't start on owner cells)
                if cell.symbol != '.': # Crude check for non-wall, assumes '.' is wall
                    is_occupied = False
                    for p in self.players:
                        if p.row == r and p.col == c:
                            is_occupied = True
                            break
                    if not is_occupied:
                        valid_positions.append((r, c))
        
        if not valid_positions:
            # This should ideally not happen with a reasonably sized map
            print("Warning: No valid starting positions found! Defaulting to (0,0) or first available.")
            # Fallback, try to find any non-wall, even if it's a special cell
            for r, row_cells in enumerate(self.board):
                for c, cell in enumerate(row_cells):
                    if cell.symbol != '.': return (r,c)
            return (0,0) # Absolute fallback
        return random.choice(valid_positions)

    def _initialize_players(self, player_ids: List[str]):
        if not player_ids:
            raise ValueError("Player IDs list cannot be empty.")

        for p_id in player_ids:
            start_row, start_col = self._get_valid_start_position()
            # For now, all players are human. Add a way to specify AI players later.
            player = Player(player_id=p_id, initial_row=start_row, initial_col=start_col, is_human=True)
            self.players.append(player)
            print(f"Player {p_id} initialized at ({start_row}, {start_col}).")
    
    def _deal_initial_cards(self):
        print(f"Dealing {Game.INITIAL_CARDS_TO_DEAL} cards to each player...")
        for player in self.players:
            for _ in range(Game.INITIAL_CARDS_TO_DEAL):
                card = self.deck.draw()
                if card:
                    player.add_card_to_hand(card)
                    # print(f"Dealt {card.title} to {player.id}") # Can be verbose
                else:
                    print(f"Warning: Could not draw a card for {player.id} during initial deal. Deck might be too small.")
                    break # Stop dealing to this player if deck runs out
            print(f"{player.id} starts with {len(player.cards_in_hand)} cards.")

    def _deal_initial_agendas(self):
        print("Dealing secret agendas...")
        for player in self.players:
            agenda = self.agenda_deck.deal()
            if agenda:
                player.set_secret_agenda(agenda)
            else:
                print(f"Warning: Could not deal an agenda to {player.id}. Agenda deck might be empty.")

    def get_current_player(self) -> Player:
        return self.players[self.current_player_index]

    def next_turn(self):
        # Check for end-of-turn agenda conditions for the player whose turn is ending
        current_player_ending_turn = self.get_current_player()
        if current_player_ending_turn.secret_agenda:
            for condition in current_player_ending_turn.secret_agenda.objective_conditions:
                if isinstance(condition, EndedTurnWithPlayerStatCondition):
                    # This check updates internal state for the condition if it relies on knowing it was met at end of turn
                    # The actual reveal is still player-driven in _handle_agenda_phase
                    condition.is_met(current_player_ending_turn, self, event_data={"event_type": "EndOfTurn"})
                    # We don't need the return value here, just to trigger the check if the condition type expects it.

        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        new_current_player = self.get_current_player()
        new_current_player.start_new_turn() # Reset turn-specific flags for the player
        print(f"\n--- {new_current_player.id}'s Turn ---")

    def get_cell(self, row: int, col: int) -> Optional[Cell]:
        if 0 <= row < len(self.board) and 0 <= col < len(self.board[row]):
            return self.board[row][col]
        return None
        
    def player_draws_cards(self, player: Player, num_cards: int):
        """Called by effects like DrawCardsEffect."""
        print(f"Game: {player.id} attempts to draw {num_cards} card(s).")
        for i in range(num_cards):
            card = self.deck.draw()
            if card:
                player.add_card_to_hand(card)
                print(f"Game: {player.id} drew {card.title} ({i+1}/{num_cards}).")
            else:
                print(f"Game: {player.id} could not draw card {i+1}/{num_cards} (deck empty?).")
                break # Stop if deck runs out

    def display_board_state(self):
        """Basic text representation of the board with player positions."""
        print("\n--- Current Board State ---")
        # Create a character grid for display
        display_grid = [[cell.symbol for cell in row] for row in self.board]
        
        # Mark player positions
        for idx, player in enumerate(self.players):
            p_char = str(idx + 1) # Represent players as 1, 2, 3...
            if 0 <= player.row < len(display_grid) and 0 <= player.col < len(display_grid[player.row]):
                # If multiple players on a cell, previous ones might be overwritten. Simple display for now.
                display_grid[player.row][player.col] = p_char
            else:
                print(f"Warning: Player {player.id} is out of bounds at ({player.row},{player.col})")

        for row in display_grid:
            print("  ".join(row)) # Add some spacing for readability
        print("-------------------------")

    def display_player_status(self, player: Player, show_secret_agenda_for_current_player: bool = False):
        print(f"Status for {player.id}:")
        print(f"  Position: ({player.row}, {player.col})")
        print(f"  Food: {player.food}")
        print(f"  Cards in hand: {len(player.cards_in_hand)}")
        if player.is_human and show_secret_agenda_for_current_player and player.secret_agenda:
            print(f"  Secret Agenda: {player.secret_agenda.title} - \"{player.secret_agenda.objective_text}\"")
        elif player.secret_agenda: # For debug or if AI needs to know its own agenda
            pass # Or print for all players if not in strict hot-seat mode
        if player.revealed_persistent_agendas:
            print(f"  Revealed Agendas: {[pa.title for pa in player.revealed_persistent_agendas]}")
        print(f"  Trust: {player.trust_levels}")
        if player.active_titles:
            print(f"  Active Titles: {[t.title for t in player.active_titles]}")
        if player.persistent_effects:
             print(f"  Persistent Effects: {[e.title for e in player.persistent_effects]}")
        print("-------------------------")
        
    def check_win_condition(self, player: Player) -> bool:
        for owner, trust in player.trust_levels.items():
            if trust >= Game.WIN_TRUST_LEVEL:
                self.game_over = True
                self.winner = player
                print(f"🎉🎉🎉 Game Over! Player {player.id} has won by reaching {trust} trust with {owner}! 🎉🎉🎉")
                return True
        return False

    def _trigger_armed_effects(self, player: Player, event_type: str, event_context: Dict[str, Any] | None = None):
        if event_context is None: event_context = {}
        triggered_cards_to_remove = [] # Store Card objects, not (Card, ctx) tuples

        # Iterate over a copy if modifying the list during iteration, or build a list of cards to remove.
        for armed_card_obj, play_context in list(player.armed_delayed_effects): # Iterate a copy or manage removals carefully
            if not armed_card_obj.effects or not isinstance(armed_card_obj.effects[0], ArmDelayedEffect):
                continue

            arm_effect_definition_params = armed_card_obj.effects[0].params # These are from cards.json for ArmDelayedEffect
            trigger_cond_data = arm_effect_definition_params.get("trigger_condition", {})
            
            condition_met = False
            if trigger_cond_data.get("type") == event_type:
                if event_type == "VisitedCellType" and trigger_cond_data.get("cell_type_symbol") == event_context.get("cell_symbol"):
                    condition_met = True
                elif event_type == "ParticipatedInFight": 
                    condition_met = True 
                elif event_type == "VisitedDifferentOwnerCell":
                    original_owner = play_context.get("played_on_owner_name") # Get from stored context
                    newly_visited_owner = event_context.get("owner_name")
                    if newly_visited_owner and original_owner and newly_visited_owner != original_owner : 
                         condition_met = True
                         # Pass context for applying effects. Merge with existing event_context carefully.
                         event_context["original_owner_for_postman"] = original_owner
                         event_context["newly_visited_owner_for_postman"] = newly_visited_owner
            
            if condition_met:
                print(f"Triggering armed effect of card '{armed_card_obj.title}' for {player.id} due to event: {event_type}")
                triggered_effects_data = arm_effect_definition_params.get("triggered_effects", [])
                
                for eff_data in triggered_effects_data:
                    eff_class = EFFECT_REGISTRY.get(eff_data.get("type"))
                    eff_params_from_json = eff_data.get("params", {})
                    if eff_class:
                        current_eff_params = eff_params_from_json.copy() # Start with base params from JSON

                        # Context-dependent parameter overrides for specific effects
                        if eff_class is GainTrustEffect:
                            if current_eff_params.get("owner_name_from_context") == "original" and event_context.get("original_owner_for_postman"):
                                current_eff_params["owner_name"] = event_context["original_owner_for_postman"]
                            elif current_eff_params.get("owner_name_from_context") == "new_visited" and event_context.get("newly_visited_owner_for_postman"):
                                current_eff_params["owner_name"] = event_context["newly_visited_owner_for_postman"]
                            elif current_eff_params.get("owner_name_from_context") == True: # General case, e.g. "Сбегать в ларёк"
                                if play_context.get("played_on_owner_name"):
                                    current_eff_params["owner_name"] = play_context.get("played_on_owner_name")
                                else:
                                    print(f"Warning: Could not determine context owner for {armed_card_obj.title}'s triggered GainTrustEffect.")
                                    continue # Skip this specific effect if context missing
                        
                        try:
                            eff_instance = eff_class(current_eff_params)
                            eff_instance.execute(source_card=armed_card_obj, executing_player=player, game_state=self, targets=None) # Assuming no new targets for triggered effects for now
                        except Exception as e:
                            print(f"Error executing triggered effect {eff_class.__name__} for {armed_card_obj.title}: {e}")
                
                if arm_effect_definition_params.get("self_discard_on_trigger", False):
                    triggered_cards_to_remove.append(armed_card_obj)
                    # self.deck.discard(armed_card_obj) # Discard happens after loop
        
        for card_to_remove in triggered_cards_to_remove:
            player.remove_armed_delayed_effect(card_to_remove) # remove by card object
            self.deck.discard(card_to_remove)
            print(f"Card '{card_to_remove.title}' was triggered, used, and discarded.")

    def _handle_player_landing_on_cell(self, player: Player, cell: Cell):
        """Handles logic when a player lands on or enters a cell, including benefits and stat tracking."""
        if not cell:
            return

        original_food = player.food # For checking food gain for certain bonuses
        original_card_count = len(player.cards_in_hand)

        if isinstance(cell, OwnerCell):
            player.record_owner_visit(cell)
        # elif isinstance(cell, Kiosk): player.record_generic_cell_visit("Kiosk") # Add if Kiosk/Basement visits needed for agendas
        # elif isinstance(cell, Basement): player.record_generic_cell_visit("Basement")

        if not player.has_visited_cell_this_turn(cell.row, cell.col) or isinstance(cell, OwnerCell):
            print(f"Processing cell entry for {cell.__class__.__name__} at ({cell.row}, {cell.col})")
            benefit_granted_this_interaction = False
            landed_on_owner_name = None
            gained_food_from_cell = 0
            # drew_cards_from_cell = 0 # If needed for bonuses on card draw from cell

            if isinstance(cell, OwnerCell):
                landed_on_owner_name = cell.owner_name
                if cell.owner_name == "Student": 
                    player.gain_trust("Student", 1)
                elif cell.owner_name == "Cook": 
                    player.gain_food(2)
                    gained_food_from_cell = 2
                elif cell.owner_name == "Librarian": 
                    self.player_draws_cards(player, 1)
                    # drew_cards_from_cell = 1
                benefit_granted_this_interaction = True
            elif isinstance(cell, Kiosk):
                self.player_draws_cards(player, 1)
                # drew_cards_from_cell = 1
                benefit_granted_this_interaction = True
            elif isinstance(cell, Basement):
                player.gain_food(2)
                gained_food_from_cell = 2
                benefit_granted_this_interaction = True
            
            if benefit_granted_this_interaction:
                player.record_cell_visit_this_turn(cell.row, cell.col)

            # Now check for persistent agenda bonuses related to this cell visit/benefit
            for active_agenda in player.revealed_persistent_agendas:
                for reward_effect in active_agenda.reward_effects: # Assuming reward_effects are instantiated Effect objects
                    if isinstance(reward_effect, AddPersistentCellVisitBonusEffect): 
                        if reward_effect.params.get("owner_name_trigger") == landed_on_owner_name:
                            bonus_eff_data = reward_effect.params.get("bonus_effect", {})
                            bonus_type = bonus_eff_data.get("type")
                            bonus_params = bonus_eff_data.get("params", {})
                            if bonus_type == "GainFood":
                                amount = bonus_params.get("amount", 0)
                                if amount > 0:
                                    print(f"Applying persistent agenda bonus from '{active_agenda.title}': gain {amount} food.")
                                    player.gain_food(amount)
                    elif isinstance(reward_effect, AddPersistentFoodSourceBonusEffect):
                        source_trigger = reward_effect.params.get("source_trigger", {})
                        if source_trigger.get("type") == "GainedFoodFromOwnerCell" and \
                           source_trigger.get("owner_name") == landed_on_owner_name and \
                           gained_food_from_cell > 0: # Check if food was actually gained from this owner cell in this interaction
                            bonus_amount = reward_effect.params.get("bonus_food_amount", 0)
                            if bonus_amount > 0:
                                print(f"Applying persistent agenda bonus from '{active_agenda.title}': gain {bonus_amount} additional food.")
                                player.gain_food(bonus_amount)
            self._trigger_armed_effects(player, "VisitedDifferentOwnerCell", {"owner_name": landed_on_owner_name}) # For Postman
        else:
            print(f"Already received standard benefit from cell ({cell.row},{cell.col}) this turn.")

    def _handle_agenda_phase(self, current_player: Player):
        print("\n3. Agenda Phase")
        if not current_player.secret_agenda:
            print(f"{current_player.id} has no secret agenda or has already revealed it.")
            return

        # For human players, ask if they want to try revealing.
        # For AI, it would make this decision based on its policy.
        attempt_reveal = False
        if current_player.is_human:
            reveal_choice = input(f"{current_player.id}, your agenda is '{current_player.secret_agenda.title}'. Attempt to reveal? (yes/no): ").lower()
            if reveal_choice == 'yes':
                attempt_reveal = True
        # else: # AI Player Logic
        #    attempt_reveal = current_player.decide_to_reveal_agenda(self) 

        if attempt_reveal:
            revealed_agenda_card = current_player.secret_agenda # Get the card, don't remove from player yet
            print(f"{current_player.id} attempts to reveal agenda: {revealed_agenda_card.title}")
            print(f"  Objective: {revealed_agenda_card.objective_text}")

            if revealed_agenda_card.check_objective(current_player, self): # Use structured check
                print(f"Objective for '{revealed_agenda_card.title}' MET! Applying reward.")
                revealed_agenda_card.apply_reward(current_player, self)
                
                current_player.secret_agenda = None # Mark as processed from secret slot

                if revealed_agenda_card.is_persistent and not revealed_agenda_card.discard_after_use:
                    current_player.add_persistent_agenda_bonus(revealed_agenda_card)
                elif revealed_agenda_card.discard_to_box_on_reveal:
                    self.agenda_deck.discard_to_box(revealed_agenda_card)
                    print(f"Agenda '{revealed_agenda_card.title}' discarded to box.")
                else: # Not persistent, or discard_after_use is true (for one-time persistent rewards)
                    # If it has discard_after_use, it implies a one-time persistent effect.
                    # For now, non-persistent non-boxed agendas are just considered revealed and used up.
                    # The actual removal for discard_after_use would happen when the ability is consumed.
                    print(f"Agenda '{revealed_agenda_card.title}' revealed and reward applied.")
                
                if self.check_win_condition(current_player): return
            else:
                print(f"Objective for '{revealed_agenda_card.title}' NOT met. Agenda remains secret.")
        else:
            if current_player.is_human: # Only print this if a human actively said no
                 print(f"{current_player.id} chooses not to attempt agenda reveal this turn.")

    def _handle_fight_phase(self, current_player: Player):
        print("\n--- Fight Phase (Placeholder) ---")
        # Check if on same cell with other players
        opponents_on_cell = [p for p in self.players if p != current_player and p.row == current_player.row and p.col == current_player.col]
        if not opponents_on_cell:
            print("No opponents on the same cell.")
            return

        if current_player.is_human:
            target_idx_str = input(f"Fight with whom? {[f'{i}:{opp.id}' for i, opp in enumerate(opponents_on_cell)]} (index or 'skip'): ")
            if target_idx_str.lower() == 'skip': return
            try:
                target_opponent = opponents_on_cell[int(target_idx_str)]
                # Simple dice roll fight
                p1_roll = random.randint(1,6) + current_player.get_fight_bonus()
                p2_roll = random.randint(1,6) + target_opponent.get_fight_bonus()
                print(f"{current_player.id} (bonus {current_player.get_fight_bonus()}) rolls {p1_roll}")
                print(f"{target_opponent.id} (bonus {target_opponent.get_fight_bonus()}) rolls {p2_roll}")

                winner, loser = None, None
                if p1_roll > p2_roll: winner, loser = current_player, target_opponent
                elif p2_roll > p1_roll: winner, loser = target_opponent, current_player
                
                if winner:
                    print(f"{winner.id} wins the fight against {loser.id}!")
                    choice = 'food' # Default
                    if winner.is_human:
                        choice = input(f"{winner.id}, take 2 food ('food') or 1 random card ('card') from {loser.id}?: ").lower()
                    if choice == 'card' and loser.cards_in_hand:
                        stolen_card = random.choice(loser.cards_in_hand)
                        loser.remove_card_from_hand(stolen_card)
                        winner.add_card_to_hand(stolen_card)
                        print(f"{winner.id} took card {stolen_card.title} from {loser.id}.")
                    else: # Default to food or if no cards
                        amount_taken = min(2, loser.food)
                        loser.lose_food(amount_taken)
                        winner.gain_food(amount_taken)
                        print(f"{winner.id} took {amount_taken} food from {loser.id}.")
                    # Check for "Гроза дворов" type effects for additional consequences
                    for title_card in winner.active_titles:
                        if title_card.title == "Гроза дворов" and title_card.attributes_granted.get("OnSuccessfulFightInflictTrustLoss"): 
                            print(f"'{title_card.title}' effect: {loser.id} loses 1 trust.")
                            # Loser chooses which owner, simplified for now
                            loser.lose_trust(ALL_OWNERS[0], 1) 
                else: print("Fight is a draw!")
                self._trigger_armed_effects(current_player, "ParticipatedInFight", {"opponent": target_opponent.id, "outcome": "win" if winner == current_player else ("loss" if loser == current_player else "draw")})
                self._trigger_armed_effects(target_opponent, "ParticipatedInFight", {"opponent": current_player.id, "outcome": "win" if winner == target_opponent else ("loss" if loser == target_opponent else "draw")})
            except (ValueError, IndexError): print("Invalid target for fight.")

    def run_game(self):
        """Main game loop."""
        print("\nStarting Alley Cats!")
        turn_counter = 0
        max_turns = 100 # Safety break for development

        while not self.game_over and turn_counter < max_turns:
            turn_counter += 1
            current_player = self.get_current_player()
            print(f"\nTurn {turn_counter} - Player: {current_player.id}")
            
            self.display_board_state()
            self.display_player_status(current_player, show_secret_agenda_for_current_player=current_player.is_human)

            # --- 0. Check for Interrupts (Beginning of turn) --- 
            # self._handle_interrupt_phase(current_player, "StartOfTurn")

            # --- 1. Movement Phase --- 
            print("\n1. Movement Phase")
            
            # Dice Roll with Re-roll option
            roll_again = True
            final_roll = 0
            attempts = 0
            while roll_again and attempts < 2: # Max 1 re-roll
                attempts += 1
                current_dice_roll = random.randint(1, 6)
                print(f"{current_player.id} rolled a {current_dice_roll}.")
                final_roll = current_dice_roll
                roll_again = False # Assume this is the final roll unless re-roll is used

                if attempts == 1 and current_player.has_one_time_reroll_ability:
                    if current_player.is_human:
                        use_reroll = input("You have a re-roll ability. Use it? (yes/no): ").lower()
                        if use_reroll == 'yes':
                            if current_player.consume_one_time_reroll():
                                print("Re-rolling dice...")
                                roll_again = True 
                            else: # Should not happen if has_one_time_reroll_ability was true
                                print("Could not use re-roll ability.")
                    # else: AI decides to use reroll
            
            # movement_bonus = current_player.get_movement_bonus() # TODO: Implement
            total_movement = final_roll # + movement_bonus
            print(f"{current_player.id} will move {total_movement} spaces.")
            
            if current_player.is_human:
                try:
                    print(f"Current position: ({current_player.row}, {current_player.col})")
                    move_str = input(f"{current_player.id}, enter new position 'row,col' (or 'skip'): ")
                    if move_str.lower() == 'skip':
                        print(f"{current_player.id} skips movement.")
                    else:
                        new_r, new_c = map(int, move_str.split(','))
                        # TODO: Add proper distance validation based on total_movement and path checking
                        target_cell = self.get_cell(new_r, new_c)
                        if target_cell and target_cell.symbol != '.':
                            # Simplified: direct jump. Proper impl would be step-by-step.
                            current_player.update_position(new_r, new_c)
                            print(f"{current_player.id} moved to ({new_r}, {new_c}).")
                            self._handle_player_landing_on_cell(current_player, target_cell)
                        else:
                            print("Invalid move (out of bounds or wall). Position unchanged.")
                except Exception as e:
                    print(f"Error during movement input: {e}. Position unchanged.")
            # else: AI Player movement logic

            if self.check_win_condition(current_player): break

            # --- Check for Interrupts (After Movement, Before Main Action) ---
            # self._handle_interrupt_phase(current_player, "AfterMovement")

            # --- 2. Action Phase ---
            print("\n2. Action Phase")
            if current_player.is_human:
                action_choice = input(f"{current_player.id}, take action: play card ('play'), fight ('fight'), skip ('skip'): ").lower()
                if action_choice == 'play':
                    if not current_player.cards_in_hand:
                        print(f"{current_player.id} has no cards to play.")
                    else:
                        print("Your cards:")
                        for i, card_in_hand in enumerate(current_player.cards_in_hand):
                            print(f"  {i}: {card_in_hand.title} (Cost: {card_in_hand.cost})") # Show cost
                        try:
                            card_idx_str = input("Enter index of card to play (or 'cancel'): ")
                            if card_idx_str.lower() != 'cancel':
                                card_idx = int(card_idx_str)
                                if 0 <= card_idx < len(current_player.cards_in_hand):
                                    card_to_play = current_player.cards_in_hand[card_idx]
                                    targets = None # Placeholder for target selection logic
                                    if card_to_play.target_needed: # Basic target selection
                                        target_p_idx_str = input(f"Card '{card_to_play.title}' needs a target. Enter player index (0-{len(self.players)-1}), not you ({self.current_player_index}): ")
                                        target_p_idx = int(target_p_idx_str)
                                        if 0 <= target_p_idx < len(self.players) and target_p_idx != self.current_player_index:
                                            targets = [self.players[target_p_idx]]
                                        else:
                                            print("Invalid target selected. Cannot play card.")
                                            continue # Skip this card play attempt

                                    if card_to_play.can_play(current_player, self):
                                        paid_cost = True
                                        for resource, amount_cost in card_to_play.cost.items(): # Renamed amount to amount_cost
                                            if resource == "food":
                                                if not current_player.lose_food(amount_cost):
                                                    paid_cost = False; break
                                        
                                        if paid_cost:
                                            original_hand_card = current_player.cards_in_hand.pop(card_idx) # Remove by index
                                            current_player.record_card_usage(original_hand_card.title) # Record usage for agendas
                                            original_hand_card.activate(current_player, self, targets)
                                            
                                            if original_hand_card.discard_condition == "Сразу":
                                                self.deck.discard(original_hand_card)
                                            # TODO: More robust handling of other discard conditions, titles, persistent effects
                                            # This part heavily relies on specific ApplyTitleEffect, ApplyPersistentEffect etc.
                                            # to move the card to player.active_titles or player.persistent_effects instead of discard.
                                            elif "Title" in original_hand_card.card_type_flags or "Persistent" in original_hand_card.card_type_flags:
                                                 print(f"Card '{original_hand_card.title}' (type: {original_hand_card.card_type_flags}) played. Its effects manage its state.")
                                            else: # Default non-immediate to discard for now if not title/persistent
                                                print(f"Card '{original_hand_card.title}' discard '{original_hand_card.discard_condition}' - discarding.")
                                                self.deck.discard(original_hand_card)
                                        else: print(f"Failed to pay cost for {card_to_play.title}.")
                                    else: print(f"Cannot play {card_to_play.title} (affordability/conditions).")
                                else: print("Invalid card index.")
                        except Exception as e:
                            print(f"Error playing card: {e}")
                            import traceback; traceback.print_exc() # Detailed error for debugging
                elif action_choice == 'fight':
                    self._handle_fight_phase(current_player)
                # else: skip
            # else: AI Player action logic

            if self.check_win_condition(current_player): break
            
            # Check for agendas that trigger at end of turn
            if current_player.secret_agenda:
                for condition in current_player.secret_agenda.objective_conditions:
                    if isinstance(condition, EndedTurnWithPlayerStatCondition): # Requires EndedTurnWithPlayerStatCondition to be imported
                        if condition.is_met(current_player, self, event_data={"event_type": "EndOfTurn"}):
                            print(f"Agenda condition '{condition}' for '{current_player.secret_agenda.title}' met at end of turn.")
                            # This doesn't auto-reveal, player still needs to choose to reveal in agenda phase.
                            # But it confirms a condition that *must* be checked at end of turn.
                        # else: 
                            # print(f"Agenda condition '{condition}' for '{current_player.secret_agenda.title}' NOT met at end of turn.")
                            pass # Condition not met, or not of this type

            self._handle_agenda_phase(current_player)
            if self.game_over: break

            self.next_turn()

        if not self.game_over:
            print(f"\nGame ended after {max_turns} turns (safety break).")
        elif self.winner:
            print(f"Congratulations to {self.winner.id}!")

        print("\nFinal Player Statuses:")
        for p in self.players:
            self.display_player_status(p, show_secret_agenda_for_current_player=True)

if __name__ == "__main__":
    print("Welcome to Alley Cats - CLI Edition!")
    num_players = 0
    player_names_list = []
    # Simplified setup for testing
    # while True:
    #     try:
    #         num_str = input("Enter number of players (2-4, or type 'test' for 2 default players): ")
    #         if num_str.lower() == 'test':
    #             player_names_list = ["Player1", "Player2"]
    #             break
    #         num_players = int(num_str)
    #         if 2 <= num_players <= 4:
    #             break
    #         else:
    #             print("Please enter a number between 2 and 4.")
    #     except ValueError:
    #         print("Invalid input.")

    # for i in range(num_players):
    #     name = input(f"Enter name for Player {i+1}: ")
    #     player_names_list.append(name if name.strip() else f"Player{i+1}")
    player_names_list = ["Catrick", "Pawdrey"] # Hardcode for faster testing for now
    print(f"Starting game with players: {', '.join(player_names_list)}")
    
    try:
        game_instance = Game(player_ids=player_names_list)
        game_instance.run_game()
    except Exception as e:
        print(f"\nFATAL ERROR DURING GAME: {e}")
        import traceback
        traceback.print_exc() 