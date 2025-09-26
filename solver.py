from board import Board
from test_cases import test_cases

def solve_with_backtracking(grid_size, providers, receivers):
	"""Solve the problem using backtracking."""
	board = Board(grid_size, providers, receivers)
	if board.backtrack():
		return board.best_board
	else:
		return None

def display_solution(board):
	"""Display the solution in a grid format."""
	board.print_grid()
	# Print detailed placements
	print("\nDetailed Placements:")
	print("Providers placed at:")
	for provider, x, y, rotated in board.placed_providers:
		print(f"  Provider '{provider.name}' at ({x}, {y}), rotated: {'Yes' if rotated else 'No'}")
	print("Receivers placed at:")
	for receiver, x, y, rotated in board.placed_receivers:
		print(f"  Receiver '{receiver.name}' at ({x}, {y}), rotated: {'Yes' if rotated else 'No'}")

def main(selected_case="case_1"):

	if selected_case not in test_cases:
		print("Available test cases:")
		for case_name in test_cases.keys():
			print(f"  - {case_name}")
		print(f"Test case '{selected_case}' not found.")
		return

	# Load the selected test case
	case = test_cases[selected_case]
	grid_size = case["grid_size"]
	providers = case["providers"]
	receivers = case["receivers"]

	# Assign the board to providers and receivers
	board = Board(grid_size, providers, receivers)
	for provider in providers:
		provider.board = board
	for receiver in receivers:
		receiver.board = board

	# Solve the problem
	solution = solve_with_backtracking(grid_size, providers, receivers)
	if solution:
		print("Solution Found:")
		display_solution(solution)
	else:
		print("No solution found.")


if __name__ == "__main__":
	main()