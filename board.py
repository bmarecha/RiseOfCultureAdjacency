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
	
	def points_map_total(self):
		"""Calculate the total number of points on unoccupied places on the points_map"""
		total = sum((points / 100) ** 2 for (pos, points) in self.points_map.items() if pos not in self.grid)
		return total

	def is_valid_position(self, obj, x, y, rotated):
		"""Check if an object can be placed at (x, y) on the grid."""
		width, height = (obj.width, obj.height) if not rotated else (obj.height, obj.width)
		# Check if placing the object expands the grid borders
		if self.calculate_and_check_border_extension(x, y, width, height, False) is None:
			return False

		# Check for overlaps
		for dx in range(height):
			for dy in range(width):
				if (x + dx, y + dy) in self.grid:  # Cell is already occupied
					return False

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

	def calculate_and_check_border_extension(self, x, y, width = 1, height = 1, rotated=False):
		"""
		Calculate the border extension by placing an object with the given width and height
		at position (x, y). Check if the extension is within the maximum allowed grid size.

		Args:
			x (int): The x-coordinate of the top-left corner of the object.
			y (int): The y-coordinate of the top-left corner of the object.
			width (int): The width of the object.
			height (int): The height of the object.
			rotated (bool): Whether the object is rotated (swap width and height).

		Returns:
			int: The total border extension if within the maximum grid size.
			None: If the border extension exceeds the maximum grid size.
		"""
		# Swap width and height if the object is rotated
		width, height = (width, height) if not rotated else (height, width)
		# Current grid borders
		min_x, max_x, min_y, max_y = self.current_grid_borders
		# Calculate new borders after placing the object
		new_min_x = min(min_x, x)
		new_max_x = max(max_x, x + width - 1)
		new_min_y = min(min_y, y)
		new_max_y = max(max_y, y + height - 1)

		# Calculate the border extension
		extension_x = (new_max_x - new_min_x + 1) - (max_x - min_x + 1)
		extension_y = (new_max_y - new_min_y + 1) - (max_y - min_y + 1)

		# Calculate the new grid size
		new_grid_width = new_max_x - new_min_x + 1
		new_grid_height = new_max_y - new_min_y + 1

		# Check if the new grid size exceeds the maximum allowed grid size
		max_grid_width, max_grid_height = self.grid_size
		if new_grid_width > max_grid_width or new_grid_height > max_grid_height:
			return None  # Not within max borders

		return (extension_x, extension_y)

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
	
	def backtrack(self):
		"""Backtracking algorithm to place receivers and providers."""
		# Base case: Check if all receivers are placed
		if not self.receivers:
			self.update_best_board()
			return True

		# Step 1: Place Receiver
		receiver = self.receivers.pop(0)  # Get the next receiver to place
		indentation = "  " * (len(self.placed_receivers))  # Create indentation based on the number of placed receivers
		print(f"{indentation}Trying to place receiver: {receiver.name}")  # Log the receiver being placed
		possible_positions = self.find_possible_positions_for_receiver(receiver)

		for position in possible_positions:
			x, y, rotated = position
			print(f"{indentation}Attempting to place receiver at position: ({x}, {y}), rotated: {rotated}")  # Log position attempt

			# Place the receiver
			self.place_object(receiver, x, y, rotated)

			# Step 2: Place Providers
			if self.place_providers_for_receiver(receiver, (x, y, rotated)):
				print(f"{indentation}Successfully placed providers for receiver: {receiver.name}")  # Log success
				# Continue to the next receiver
				if self.backtrack():
					return True

			# Backtrack: Remove the receiver and its providers
			print(f"{indentation}Backtracking: Removing receiver from position: ({x}, {y}), rotated: {rotated}")  # Log backtrack
			self.remove_object(receiver, x, y, rotated)

		# If no valid position for the receiver, backtrack
		self.receivers.insert(0, receiver)  # Put the receiver back in the list
		print(f"{indentation}No valid position found for receiver: {receiver.name}, backtracking...")  # Log no valid position
		return False

	def find_possible_positions_for_receiver(self, receiver):
		"""Find all possible positions for the receiver, ordered by interest."""
		possible_positions = []

		# Restrict to positions in the points map or (0, 0) if points map is empty
		if self.points_map:
			for (x, y), points in self.points_map.items():
				for rotated in [False, True]:
					if self.is_valid_position(receiver, x, y, rotated):
						possible_positions.append((x, y, rotated))
		else:
			# Default to (0, 0) if points map is empty
			for rotated in [False, True]:
				if self.is_valid_position(receiver, 0, 0, rotated):
					possible_positions.append((0, 0, rotated))

		# Order positions by how interesting they are (e.g., points available)
		possible_positions.sort(key=lambda pos: self.calculate_position_interest(receiver, pos), reverse=True)
		return possible_positions

	def calculate_position_interest(self, receiver, position):
		"""Calculate how interesting a position is for placing a receiver."""
		x, y, rotated = position
		width, height = (receiver.width, receiver.height) if not rotated else (receiver.height, receiver.width)

		# Calculate total points available at the receiver's position
		total_points = 0
		for dx in range(width):
			for dy in range(height):
				total_points += self.points_map.get((x + dx, y + dy), 0)

		# Add other heuristics if needed (e.g., proximity to other receivers)
		return total_points

	def place_providers_for_receiver(self, receiver, receiver_position):
		"""Place providers to satisfy the receiver's requirements."""
		required_points = receiver.required_points
		placed_providers = []

		for provider in self.providers:
			if required_points <= 0:
				break

			# Find the best place for the provider
			place = provider.find_place(receiver_position, receiver.width, receiver.height)
			if place:
				px, py, protated = place
				self.place_object(provider, px, py, protated)
				placed_providers.append((provider, px, py, protated))
				required_points -= provider.points

		# Check if the receiver's requirements are satisfied
		if required_points > 0:
			# Remove placed providers if requirements are not met
			for provider, px, py, protated in placed_providers:
				self.remove_object(provider, px, py, protated)
			return False

		return True