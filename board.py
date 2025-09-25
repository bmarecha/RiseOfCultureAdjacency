from copy import deepcopy
from provider import ProviderObject
from receiver import ReceiverObject


class Board:
	def __init__(self, grid_size, providers, receivers):
		self.grid_size = grid_size
		self.current_grid_borders = (0, 0, 0, 0)  # (min_x, max_x, min_y, max_y)
		self.grid = {}  # Dictionary to track positions and objects
		self.points_map = {}  # Dictionary to track points contributed by providers
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
		self.print_grid()

		return True

	def place_object(self, obj, x, y, rotated):
		"""Place an object on the grid."""
		width, height = (obj.width, obj.height) if not rotated else (obj.height, obj.width)
		for dx in range(height):
			for dy in range(width):
				self.grid[(x + dx, y + dy)] = obj

		if isinstance(obj, ProviderObject):
			self.placed_providers.append((obj, x, y, rotated))
			# Update points_map for all cells within the provider's effect radius
			for dx in range(-obj.effect_radius, width + obj.effect_radius + 1):
				for dy in range(-obj.effect_radius, height + obj.effect_radius + 1):
					px, py = x + dx, y + dy
					if (px, py) not in self.grid:  # Only update unoccupied cells
						self.points_map[(px, py)] = self.points_map.get((px, py), 0) + obj.points

		elif isinstance(obj, ReceiverObject):
			self.placed_receivers.append((obj, x, y, rotated))

	def remove_object(self, obj, x, y, rotated):
		"""Remove an object from the grid."""
		width, height = (obj.width, obj.height) if not rotated else (obj.height, obj.width)

		if isinstance(obj, ProviderObject):
			self.placed_providers = [
				p for p in self.placed_providers if p[0] != obj or p[1] != x or p[2] != y or p[3] != rotated
			]
			# Update points_map for all cells within the provider's effect radius
			for dx in range(-obj.effect_radius, width + obj.effect_radius + 1):
				for dy in range(-obj.effect_radius, height + obj.effect_radius + 1):
					px, py = x + dx, y + dy
					if (px, py) not in self.grid:  # Only update unoccupied cells
						self.points_map[(px, py)] = self.points_map.get((px, py), 0) - obj.points
		elif isinstance(obj, ReceiverObject):
			self.placed_receivers = [
				r for r in self.placed_receivers if r[0] != obj or r[1] != x or r[2] != y or r[3] != rotated
			]
		# Remove the object from the grid after updating points_map
		for dx in range(height):
			for dy in range(width):
				del self.grid[(x + dx, y + dy)]

	def calculate_border_extension(self, obj, x, y, rotated):
		"""Calculate how much the grid borders would extend by placing an object at (x, y)."""
		min_x, max_x, min_y, max_y = self.current_grid_borders
		width, height = (obj.width, obj.height) if not rotated else (obj.height, obj.width)

		new_min_x = min(min_x, x)
		new_max_x = max(max_x, x + width - 1)
		new_min_y = min(min_y, y)
		new_max_y = max(max_y, y + height - 1)

		# Calculate the total border extension
		extension = (new_max_x - new_min_x + 1) - (max_x - min_x + 1) + \
					(new_max_y - new_min_y + 1) - (max_y - min_y + 1)
		return extension

	def find_place_for_object(self, obj):
		"""Find the best place for an object by minimizing border extension."""
		min_x, max_x, min_y, max_y = self.current_grid_borders
		grid_width, grid_height = self.grid_size
		best_position = None
		min_extension = float('inf')

		# Adjust search boundaries to fit within the grid size
		if (max_y - min_y + min(obj.height, obj.width)) <= grid_height:
			max_y = max_y + max(obj.height, obj.width)
			min_y = min_y - max(obj.height, obj.width)
		if (max_x - min_x + min(obj.height, obj.width)) <= grid_width:
			max_x = max_x + max(obj.height, obj.width)
			min_x = min_x - max(obj.height, obj.width)
		# Scan every position within the maximum grid border
		for x in range(min_x, max_x + 1):
			for y in range(min_y, max_y + 1):
				for rotated in [False, True]:
					if self.is_valid_position(obj, x, y, rotated):
						extension = self.calculate_border_extension(obj, x, y, rotated)
						# If the extension is 0, take this position immediately
						if extension == 0:
							return x, y, rotated
						# Otherwise, keep track of the position with the least extension
						if extension < min_extension:
							min_extension = extension
							best_position = (x, y, rotated)

		return best_position

	def update_best_board(self):
		"""Update the best board if the current board is better."""
		if self.best_board is None or self.compare(self.best_board) > 0:
			self.best_board = self.clone()

	def print_grid(self):
		"""Print the grid based on current grid borders."""
		min_x, max_x, min_y, max_y = self.current_grid_borders
		print("\nGrid:")
		for y in range(min_y, max_y + 1):
			for x in range(min_x, max_x + 1):
				if (x, y) in self.grid:
					# Print the first character of the object's name
					print(self.grid[(x, y)].name[0], end=" ")
				else:
					print(".", end=" ")  # Empty cell
			print()  # Newline after each row

	def print_points_map(self):
		"""Print the points map."""
		min_x, max_x, min_y, max_y = self.current_grid_borders
		print("\nPoints Map:")
		for y in range(min_y, max_y + 1):
			for x in range(min_x, max_x + 1):
				if (x, y) in self.points_map:
					print(f"{self.points_map[(x, y)]:3}", end=" ")
				else:
					print(" . ", end=" ")

	def print_board_details(self):
		"""Print the board with details."""
		min_x, max_x, min_y, max_y = self.current_grid_borders
		grid_width, grid_height = self.grid_size

		print("\n=== Board Details ===")
		print(f"Current Grid Borders: x=({min_x}, {max_x}), y=({min_y}, {max_y})")
		print(f"Current Grid Size: {max_x - min_x + 1} x {max_y - min_y + 1}")
		print(f"Max Grid Size: {grid_width} x {grid_height}")
		print(f"Number of Placed Providers: {len(self.placed_providers)}")
		print(f"Number of Unplaced Providers: {len(self.providers) - len(self.placed_providers)}")
		print(f"Number of Placed Receivers: {len(self.placed_receivers)}")
		print(f"Number of Unplaced Receivers: {len(self.receivers) - len(self.placed_receivers)}")

		# Print the grid
		self.print_grid()