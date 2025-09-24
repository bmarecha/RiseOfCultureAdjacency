class ProviderObject:
    def __init__(self, name, width, height, points, effect_radius, board):
        self.name = name
        self.width = width
        self.height = height
        self.points = points
        self.effect_radius = effect_radius
        self.board = board

    def find_place(self):
        """Find a valid place for the provider on the board."""
        for x in range(self.board.grid_size[0]):
            for y in range(self.board.grid_size[1]):
                for rotated in [False, True]:
                    if self.board.is_valid_position(self, x, y, rotated):
                        return x, y, rotated
        return None