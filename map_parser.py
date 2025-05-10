# This file will contain functions to parse map.txt and represent the game board. 
from board_elements import Cell, Wall, Kiosk, Basement, StudentCell, CookCell, LibrarianCell

def load_map(filepath: str) -> list[list[Cell]]:
    """
    Loads the game map from a text file and represents it as a grid of Cell objects.

    Args:
        filepath: The path to the map file.

    Returns:
        A list of lists of Cell objects.
        Returns an empty list if the file is not found or is empty.
    """
    game_board: list[list[Cell]] = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for r, line in enumerate(f):
                stripped_line = line.strip('\n') # Keep trailing tabs if any, just strip newline
                if not stripped_line and r == 0 and not game_board: # Handle completely empty file scenario better
                    continue 
                
                row_cells_str = stripped_line.split('\t')
                row_objects: list[Cell] = []
                for c, symbol in enumerate(row_cells_str):
                    if symbol == '.':
                        row_objects.append(Wall(r, c))
                    elif symbol == 'K':
                        row_objects.append(Kiosk(r, c))
                    elif symbol == 'B':
                        row_objects.append(Basement(r, c))
                    elif symbol == 'S':
                        row_objects.append(StudentCell(r, c))
                    elif symbol == 'C':
                        row_objects.append(CookCell(r, c))
                    elif symbol == 'L':
                        row_objects.append(LibrarianCell(r, c))
                    elif symbol == '' or symbol.isspace(): # Empty string from split or just whitespace
                        # This is a traversable empty path
                        row_objects.append(Cell(r, c, ' ')) # Represent empty path with a space symbol
                    else:
                        # Default to a generic Cell for any other unexpected symbols, treating them as traversable
                        # Or we could raise an error for unknown symbols if strict parsing is needed.
                        # print(f"Warning: Unknown symbol '{symbol}' at ({r},{c}). Treating as traversable Cell.")
                        row_objects.append(Cell(r, c, symbol))
                game_board.append(row_objects)
            
            # Ensure all rows have the same number of columns for a consistent grid
            if game_board:
                max_cols = 0
                # First pass to find the maximum number of columns based on actual content
                for r_idx, row in enumerate(game_board):
                    # Count actual cell objects, not just string length, to be accurate with Cell instantiation
                    current_cols = len(row)
                    if current_cols > 0:
                         max_cols = max(max_cols, current_cols)
                    # If a row was completely empty in the file leading to an empty list of objects, 
                    # it might need padding if other rows have content. However, split('\t') on an empty line
                    # gives [''], so len(row_cells_str) would be 1, and one Cell(r,c,' ') is added.
                    # This handles lines with only tabs correctly too.

                # Second pass to pad rows
                for r_idx, row in enumerate(game_board):
                    while len(row) < max_cols:
                        # Add empty traversable cells for padding
                        row.append(Cell(r_idx, len(row), ' '))

            return game_board
            
    except FileNotFoundError:
        print(f"Error: Map file not found at {filepath}")
        return []
    except Exception as e:
        print(f"An error occurred while loading the map: {e}")
        return []

# Example usage (can be removed or kept for testing)
if __name__ == '__main__':
    parsed_map = load_map('map.txt')
    if parsed_map:
        for row_obj in parsed_map:
            print([cell.symbol for cell in row_obj]) # Print symbols for a more readable test output
        print("\nFull cell objects:")
        for row_obj in parsed_map:
            print(row_obj) 