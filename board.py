from copy import deepcopy
from provider import ProviderObject
from receiver import ReceiverObject


class Board:
	def __init__(self, grid_size, providers, receivers):
		self.grid_size = grid_size
		self.current_grid_borders = (0, 0, 0, 0)  # (min_x, max_x, min_y, max_y)
		self.grid = {}  # Dictionary to track positions and objects
		self.providers = providers
		self.receivers = receivers
		self.placed_providers = []
		self.placed_receivers = []
		self.best_board = None  # To track the best board state

	def clone(self):
		"""Create a deep copy of the board."""
		return deepcopy(self)

	def compare(self, other_board):
		"""Compare two boards based on the number of placed receivers."""
		return len(self.placed_receivers) - len(other_board.placed_receivers)

	def is_valid_position(self, obj, x, y, rotated):
		"""Check if an object can be placed at (x, y) on the grid."""
		width, height = (obj.width, obj.height) if not rotated else (obj.height, obj.width)
		grid_max_width, grid_max_height = self.grid_size
		grid_borders = self.current_grid_borders
		# Check if placing the object expands the grid borders
		if x < self.current_grid_borders[0]:
			grid_borders = (x, self.current_grid_borders[1], self.current_grid_borders[2], self.current_grid_borders[3])
		if x + width > self.current_grid_borders[1]:
			grid_borders = (self.current_grid_borders[0], x + width, self.current_grid_borders[2], self.current_grid_borders[3])
		if y < self.current_grid_borders[2]:
			grid_borders = (self.current_grid_borders[0], self.current_grid_borders[1], y, self.current_grid_borders[3])
		if y + height > self.current_grid_borders[3]:
			grid_borders = (self.current_grid_borders[0], self.current_grid_borders[1], self.current_grid_borders[2], y + height)
		# Check if the new borders exceed grid size
		if (grid_borders[1] - grid_borders[0] > grid_max_width) or (grid_borders[3] - grid_borders[2] > grid_max_height):
			return False

		# Check for overlaps
		for dx in range(height):
			for dy in range(width):
				if (x + dx, y + dy) in self.grid:  # Cell is already occupied
					return False
		# If all checks passed, the position is valid
		print(f"Valid position for {obj.name} at ({x}, {y}), rotated: {rotated}")
		for y in range(self.grid_size[1]):
			for x in range(self.grid_size[0]):
				if (x, y) in self.grid:
					print(self.grid[(x, y).name[0]], end=' ')
				else:
					print('.', end=' ')
			print()

		return True

	def place_object(self, obj, x, y, rotated):
		"""Place an object on the grid."""
		width, height = (obj.width, obj.height) if not rotated else (obj.height, obj.width)
		for dx in range(height):
			for dy in range(width):
				self.grid[(x + dx, y + dy)] = obj

		if isinstance(obj, ProviderObject):
			self.placed_providers.append((obj, x, y, rotated))
		elif isinstance(obj, ReceiverObject):
			self.placed_receivers.append((obj, x, y, rotated))

	def remove_object(self, obj, x, y, rotated):
		"""Remove an object from the grid."""
		width, height = (obj.width, obj.height) if not rotated else (obj.height, obj.width)
		for dx in range(height):
			for dy in range(width):
				del self.grid[(x + dx, y + dy)]

		if isinstance(obj, ProviderObject):
			self.placed_providers = [
				p for p in self.placed_providers if p[0] != obj or p[1] != x or p[2] != y or p[3] != rotated
			]
		elif isinstance(obj, ReceiverObject):
			self.placed_receivers = [
				r for r in self.placed_receivers if r[0] != obj or r[1] != x or r[2] != y or r[3] != rotated
			]

	def update_best_board(self):
		"""Update the best board if the current board is better."""
		if self.best_board is None or self.compare(self.best_board) > 0:
			self.best_board = self.clone()