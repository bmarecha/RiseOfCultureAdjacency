class ProviderObject:
	def __init__(self, name, width, height, points, effect_radius, board):
		self.name = name
		self.width = width
		self.height = height
		self.points = points
		self.effect_radius = effect_radius
		self.board = board

	def find_place(self, receiver_position, receiver_width, receiver_height):
		"""
		Find the best place for the provider to satisfy a specific receiver.
		The provider will be placed within range of the receiver, maximizing
		the points it contributes to unoccupied cells.
		"""
		receiver_x, receiver_y, receiver_rotated = receiver_position
		receiver_width, receiver_height = (
			(receiver_width, receiver_height)
			if not receiver_rotated
			else (receiver_height, receiver_width)
		)

		best_position = None
		max_unoccupied_points = -1

		# Define the range of positions to check (within the provider's effect radius)
		for x in range(receiver_x - self.effect_radius, receiver_x + receiver_width + self.effect_radius):
			for y in range(receiver_y - self.effect_radius, receiver_y + receiver_height + self.effect_radius):
				for rotated in [False, True]:
					# Check if the provider can be placed at this position
					if not self.board.is_valid_position(self, x, y, rotated):
						continue

					# Calculate the points contributed to unoccupied cells in the provider's range
					unoccupied_points = self.calculate_unoccupied_points(
						x, y, rotated, receiver_x, receiver_y, receiver_width, receiver_height
					)

					# Update the best position if this one contributes more points
					if unoccupied_points > max_unoccupied_points:
						max_unoccupied_points = unoccupied_points
						best_position = (x, y, rotated)

		return best_position

	def calculate_unoccupied_points(self, x, y, rotated, receiver_x, receiver_y, receiver_width, receiver_height):
		"""
		Calculate the total points contributed by the provider to unoccupied cells
		within its effect radius when placed at (x, y), considering the receiver's area.
		"""
		width, height = (self.width, self.height) if not rotated else (self.height, self.width)
		total_points = 0

		# Iterate over all cells within the provider's effect radius
		for dx in range(-self.effect_radius, self.effect_radius + 1):
			for dy in range(-self.effect_radius, self.effect_radius + 1):
				px, py = x + dx, y + dy

				# Skip out-of-bounds cells
				if not self.board.calculate_and_check_border_extension(px, py):
					continue

				# Check if the cell overlaps with the receiver's area
				if receiver_x <= px < receiver_x + receiver_width and receiver_y <= py < receiver_y + receiver_height:
					total_points += self.points

				# Skip cells that are already occupied
				if (px, py) in self.board.grid:
					continue

				# Add the provider's points to the total
				total_points += self.points

		return total_points