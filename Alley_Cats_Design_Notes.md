# Alley Cats: Design Notes & Rule Clarifications

This document summarizes key design decisions, rule clarifications, and card-specific interpretations discussed for the "Alley Cats" board game.

## I. General Game Rule Clarifications

1.  **Dice Rolls for Movement:**
    *   Players roll **one die** for movement at the start of their turn, unless a game effect (e.g., a card) modifies this.
    *   *Source: Correction of a typo in `game_rules.md`.*

2.  **Visiting Special Cells (Kiosks, Basements, Owners):**
    *   Players can only gain the standard benefit (e.g., drawing a card from a Kiosk, getting food from a Basement, gaining trust/resources from an Owner's space) from any **specific, unique special cell once per turn**.
    *   A player's path can cross or land on the same special cell multiple times in a single turn, but the benefit is only awarded on the first qualifying visit to that unique cell during that turn.
    *   *Source: Clarification added to `game_rules.md`.*

3.  **Food Upkeep (Legacy Rule - Inactive):**
    *   There is **no general rule** requiring players to discard food at the start of their turn as upkeep.
    *   *Source: User confirmation.*

## II. Card-Specific Rules & Clarifications

This section details how specific cards or types of cards should be interpreted, based on our discussions and edits to `cards.json`.

1.  **Targeting Owners for Trust Gain:**
    *   When cards like "Поймал крысу," "Потереться о ноги," "Мур?," or "Принести подарок" grant trust points while on an owner's cell, the trust is gained towards the owner **of that specific cell** ("к хозяину этой клетки").

2.  **Playing Detrimental Cards:**
    *   Cards with effects that are generally detrimental to the "Кот" (Cat) they affect (e.g., "Дикий кот," "Бешеность") can be played by the drawing player on **any cat**, including themselves or an opponent, unless the card text specifies otherwise (e.g., "ты" or "другой кот"). This allows for strategic play or roleplaying.

3.  **"Title" Cards (e.g., "Лучший котик," "Искатель приключений," "Гроза дворов"):**
    *   **Uniqueness:** Each title is unique; only one player can hold a specific title at any given time.
    *   **Transfer:** If Player A holds a title and Player B subsequently plays the same title card, Player A immediately discards their title card, and Player B becomes the new holder of that title.
    *   **Card Wording:** Updated to: "Этот титул уникален. Если другой кот становится [Титулом] (обычно, сыграв такую же карту), немедленно сбрось эту карту."
    *   **Discard Condition:** Updated to: "Когда другой кот также становится [Титулом]".
    *   **"Искатель приключений":**
        *   Effect simplified to only: "Прибавь 2 к броскам на перемещение." The previous basement-related bonus was removed.
        *   Typo "код" corrected to "кот".
    *   **Removed Title Card:** "Попрошайка" has been removed from the game.

4.  **Card: "Мур?" (Purr?)**
    *   The condition "Если у тебя их больше трёх - возьми 2 еды" has been clarified to: "Если у тебя теперь больше трёх очков доверия **к этому хозяину** - возьми 2 еды." (referring to the owner on whose cell the card was played).

5.  **Cards: "Сбегать в ларёк" (Run to the Kiosk) & "Защитник" (Defender)**
    *   These cards are played on an owner's cell, and their delayed effect grants trust "к хозяину, **на чьей клетке была сыграна эта карта**" (to the owner on whose cell this card was originally played). Players need to remember this association.
    *   **"Защитник":**
        *   The fight condition triggers "После того, как ты **поучаствовал в драке** с кем-нибудь (независимо от исхода)..." (win, lose, or draw).
        *   The card's description explicitly includes "сбрось эту карту" as part of its effect resolution.

6.  **Card: "Принести подарок" (Bring a Gift)**
    *   The amount of food to discard is "Сбрось **1 или более** единиц еды по твоему выбору."

7.  **Card: "Все было не так!" (It Wasn't Like That!)**
    *   Targeting clarified to: "Сбрось любую сыгранную карту, положенную перед **любым** игроком (включая тебя)." This affects persistent cards in front of players.

8.  **Card: "Справедливость" (Justice)**
    *   To function as a comeback mechanic, it targets *other* players: "**Один из других** игроков с наибольшим количеством еды даёт тебе 2 еды. **Один из других** игроков с наибольшим количеством карт даёт тебе 1 карту. (Если в каком-либо случае таких игроков несколько, выбираешь ты)." The player playing "Справедливость" cannot be the one giving resources to themselves.

9.  **Card: "Похожесть" (Resemblance/Likeness)**
    *   **Activation:** Played as an interrupt from the hand, not on your turn ("Играй эту карту не в свой ход"). Costs 2 food. Discarded immediately after use ("Сразу").
    *   **Trigger:** "когда другой игрок должен получить очки доверия (из любого источника)" – applies to any source of trust gain for an opponent.
    *   **Effect:** "Те очки доверия вместо него получаешь ты (а тот игрок не получает ничего)." The player of "Похожесть" steals all the points; the original recipient gets none from that event.

10. **Card: "Подобрать" (Pick Up/Scavenge)**
    *   **Activation:** Played as an interrupt from the hand, not on your turn ("Играй эту карту не в свой ход"). Costs 2 food. "Подобрать" itself is discarded immediately after use ("Сразу").
    *   **Trigger:** "в тот момент, когда любая **другая** карта должна отправиться в сброс (из любого источника)."
    *   **Effect:** "Та другая карта, **вместо того чтобы пойти в сброс**, попадает тебе в руку." The targeted card is redirected to the hand of the player who played "Подобрать" and never enters the discard pile.

11. **Removed Cards:**
    *   "Попрошайка"
    *   "Блошки"

## III. Map Design Principles & Observations (`map.txt`)

This reflects the map state *before* the rejected edit on (2024-05-16).

1.  **Player Interaction:**
    *   Player clashes are intended to be inevitable and a core part of the gameplay experience. The map size (approx. 10x13, with internal walls) for 3-5 players should encourage this.

2.  **Restricted Access Locations (Cul-de-sacs):**
    *   The Basement (`B`) at map coordinates (Row 1, Column 8) is a notable "cul-de-sac," accessible only from the cell at (Row 2, Column 8). Such restricted access points can be intentional design features, creating specific tactical considerations.
    *   *(This was the state before the rejected edit that attempted to open another path to this Basement.)*

3.  **Owner Locations & Balance:**
    *   Student (`S`) is at (R2,C1) – far left, somewhat isolated. (Grants 1 Trust).
    *   Cook (`C`) is at (R8,C8) – bottom right. (Grants 2 Food).
    *   Librarian (`L`) is at (R5,C9) – right side, mid-map. (Grants 1 Card).
    *   The strategic value and accessibility of these owners, given their different rewards, should be monitored during playtesting.

4.  **Resource Hotspots & Scarcity:**
    *   **Kiosk Cluster:** Two Kiosks (`K K`) are adjacent near the Cook (`C`) at (R8,C4) and (R8,C5), making this area potentially strong for card acquisition.
    *   **Basement Distribution:** Basements (food source) appear less frequent on the eastern (right) side of the map.

5.  **Potential Strategic Zones:**
    *   The Cook + Kiosk cluster.
    *   The Student area (with two Basements in reasonable proximity).
    *   The Librarian area (with one Kiosk nearby).

Consider playtesting to see how these map features influence game flow, resource competition, and owner strategies. 
This document should serve as a guide for future design iterations and ensure consistency in rule application and card interpretation. 