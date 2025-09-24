class ReceiverObject:
    def __init__(self, name, width, height, required_points, board):
        self.name = name
        self.width = width
        self.height = height
        self.required_points = required_points
        self.board = board

    def find_place(self):
        """Find a valid place for the receiver on the board."""
        for x in range(self.board.grid_size[0]):
            for y in range(self.board.grid_size[1]):
                for rotated in [False, True]:
                    if self.board.is_valid_position(self, x, y, rotated):
                        return x, y, rotated
        return None