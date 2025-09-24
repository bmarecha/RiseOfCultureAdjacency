from board import Board
from provider import ProviderObject
from receiver import ReceiverObject


def backtrack(board, receiver_index):
    """Backtracking algorithm to place receivers and providers."""
    # Base case: All receivers are placed
    if receiver_index == len(board.receivers):
        board.update_best_board()
        return True

    receiver = board.receivers[receiver_index]

    # Try placing the receiver
    for x in range(board.grid_size[0]):
        for y in range(board.grid_size[1]):
            for rotated in [False, True]:
                if board.is_valid_position(receiver, x, y, rotated):
                    # Place the receiver
                    board.place_object(receiver, x, y, rotated)

                    # Find providers to satisfy the receiver
                    required_points = receiver.required_points
                    for provider in board.providers:
                        if required_points <= 0:
                            break
                        place = provider.find_place()
                        if place:
                            px, py, protated = place
                            board.place_object(provider, px, py, protated)
                            required_points -= provider.points

                    # Recur to place the next receiver
                    if required_points <= 0 and backtrack(board, receiver_index + 1):
                        return True

                    # Backtrack: Remove the receiver and providers
                    board.remove_object(receiver, x, y, rotated)

    return False


def solve_with_backtracking(grid_size, providers, receivers):
    """Solve the problem using backtracking."""
    board = Board(grid_size, providers, receivers)
    if backtrack(board, 0):
        return board.best_board
    else:
        return None

def display_solution(board):
    """Display the solution in a grid format."""
    grid_width, grid_height = board.grid_size
    grid_display = [["." for _ in range(grid_height)] for _ in range(grid_width)]

    # Fill the grid with providers
    for provider, x, y, rotated in board.placed_providers:
        width, height = (provider.width, provider.height) if not rotated else (provider.height, provider.width)
        for dx in range(height):
            for dy in range(width):
                grid_display[x + dx][y + dy] = provider.name

    # Fill the grid with receivers
    for receiver, x, y, rotated in board.placed_receivers:
        width, height = (receiver.width, receiver.height) if not rotated else (receiver.height, receiver.width)
        for dx in range(height):
            for dy in range(width):
                grid_display[x + dx][y + dy] = receiver.name

    # Print the grid
    print("\nGrid Layout:")
    for row in grid_display:
        print(" ".join(row))

    # Print detailed placements
    print("\nDetailed Placements:")
    print("Providers placed at:")
    for provider, x, y, rotated in board.placed_providers:
        print(f"  Provider '{provider.name}' at ({x}, {y}), rotated: {'Yes' if rotated else 'No'}")
    print("Receivers placed at:")
    for receiver, x, y, rotated in board.placed_receivers:
        print(f"  Receiver '{receiver.name}' at ({x}, {y}), rotated: {'Yes' if rotated else 'No'}")

# Example usage
grid_size = (6, 6)
providers = [
    ProviderObject(name='B', width=1, height=2, points=100, effect_radius=1, board=None),
    ProviderObject(name='B', width=1, height=2, points=100, effect_radius=1, board=None),
    ProviderObject(name='D', width=2, height=2, points=200, effect_radius=2, board=None),
]
receivers = [
    ReceiverObject(name='A', width=2, height=2, required_points=400, board=None),
    ReceiverObject(name='C', width=1, height=1, required_points=100, board=None),
]

# Assign the board to providers and receivers
board = Board(grid_size, providers, receivers)
for provider in providers:
    provider.board = board
for receiver in receivers:
    receiver.board = board

solution = solve_with_backtracking(grid_size, providers, receivers)
if solution:
    print("Solution Found:")
    display_solution(solution)
else:
    print("No solution found.")