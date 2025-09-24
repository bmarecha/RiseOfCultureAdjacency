from ortools.linear_solver import pywraplp
import numpy as np


class ProviderObject:
	def __init__(self, name, width, height, points, effect_radius):
		self.name = name
		self.width = width
		self.height = height
		self.points = points  # Points provided by this object
		self.effect_radius = effect_radius  # Radius of effect for providing points


class ReceiverObject:
	def __init__(self, name, width, height, required_points):
		self.name = name
		self.width = width
		self.height = height
		self.required_points = required_points  # Points needed for this object


def create_decision_variables(solver, grid_size, providers, receivers):
	"""Create decision variables for providers, receivers, and rotations."""
	grid_width, grid_height = grid_size

	provider_vars = {
		(i, x, y): solver.BoolVar(f'provider_{i}_{x}_{y}')
		for i, _ in enumerate(providers)
		for x in range(grid_width)
		for y in range(grid_height)
	}

	receiver_vars = {
		(i, x, y): solver.BoolVar(f'receiver_{i}_{x}_{y}')
		for i, _ in enumerate(receivers)
		for x in range(grid_width)
		for y in range(grid_height)
	}
	# Decision variables for receiver satisfaction
	satisfaction_vars = {
		i: solver.BoolVar(f'satisfaction_{i}')
		for i in range(len(receivers))
	}

	rotation_vars = {
		i: solver.BoolVar(f'rotation_{i}')
		for i in range(len(providers) + len(receivers))
	}

	return provider_vars, receiver_vars, rotation_vars, satisfaction_vars


def add_constraints(solver, grid_size, providers, receivers, provider_vars, receiver_vars, rotation_vars, satisfaction_vars):
	"""Add constraints to the solver."""
	grid_width, grid_height = grid_size

	# Constraint: Each receiver type can only be placed up to its count
	for i, receiver in enumerate(receivers):
		solver.Add(
			sum(receiver_vars[(i, x, y)] for x in range(grid_width) for y in range(grid_height)) <= 1
		)

	# Constraint: Each provider type can only be placed up to its count
	for i, provider in enumerate(providers):
		solver.Add(
			sum(provider_vars[(i, x, y)] for x in range(grid_width) for y in range(grid_height)) <= 1
		)

	# Unified constraint: No two objects (providers or receivers) can overlap
	for x in range(grid_width):
		for y in range(grid_height):
			solver.Add(
				sum(
					provider_vars[(i, px, py)]
					for i, provider in enumerate(providers)
					for px in range(max(0, x - provider.height + 1), min(grid_width, x + 1))
					for py in range(max(0, y - provider.width + 1), min(grid_height, y + 1))
				) +
				sum(
					receiver_vars[(i, rx, ry)]
					for i, receiver in enumerate(receivers)
					for rx in range(max(0, x - receiver.height + 1), min(grid_width, x + 1))
					for ry in range(max(0, y - receiver.width + 1), min(grid_height, y + 1))
				) <= 1
			)

	# Constraint: Ensure objects respect their dimensions in the chosen orientation
	for i, obj in enumerate(providers + receivers):
		for x in range(grid_width):
			for y in range(grid_height):
				# If not rotated
				if x + obj.height <= grid_width and y + obj.width <= grid_height:
					solver.Add(
						sum(
							provider_vars[(i, x + dx, y + dy)]
							for dx in range(obj.height)
							for dy in range(obj.width)
							if (i, x + dx, y + dy) in provider_vars  # Check key existence
						) <= rotation_vars[i]
					)
				# If rotated
				if x + obj.width <= grid_width and y + obj.height <= grid_height:
					solver.Add(
						sum(
							provider_vars[(i, x + dx, y + dy)]
							for dx in range(obj.width)
							for dy in range(obj.height)
							if (i, x + dx, y + dy) in provider_vars  # Check key existence
						) <= (1 - rotation_vars[i])
					)

	# Constraint: Receivers must meet their required points
	# Constraint: Receivers must meet their required points to be satisfied
	M = 1000000  # A large constant for the Big-M method
	for i, receiver in enumerate(receivers):
		for x in range(grid_width):
			for y in range(grid_height):
				if x + receiver.height <= grid_width and y + receiver.width <= grid_height:
					total_points = 0
					for px in range(max(0, x - receiver.height), min(grid_width, x + receiver.height)):
						for py in range(max(0, y - receiver.width), min(grid_height, y + receiver.width)):
							for j, provider in enumerate(providers):
								if (
									px + provider.height <= grid_width
									and py + provider.width <= grid_height
									and abs(px - x) <= provider.effect_radius
									and abs(py - y) <= provider.effect_radius
								):
									total_points += provider.points * provider_vars[(j, px, py)]
					# Debug: Print total points for each receiver
					print(f"Receiver {receiver.name} at ({x}, {y}): Total Points = {total_points}, Required = {receiver.required_points}")
					solver.Add(total_points + M * (1 - satisfaction_vars[i]) >= receiver.required_points)
					solver.Add(total_points <= receiver.required_points - 1 + M * satisfaction_vars[i])


def extract_solution(solver, grid_size, providers, receivers, provider_vars, receiver_vars, rotation_vars):
	"""Extract the solution from the solver."""
	grid_width, grid_height = grid_size
	solution = {'providers': [], 'receivers': []}

	for i, provider in enumerate(providers):
		for x in range(grid_width):
			for y in range(grid_height):
				if provider_vars[(i, x, y)].solution_value() > 0.5:
					rotated = rotation_vars[i].solution_value() > 0.5
					solution['providers'].append((provider.name, x, y, rotated))

	for i, receiver in enumerate(receivers):
		for x in range(grid_width):
			for y in range(grid_height):
				if receiver_vars[(i, x, y)].solution_value() > 0.5:
					rotated = rotation_vars[len(providers) + i].solution_value() > 0.5
					solution['receivers'].append((receiver.name, x, y, rotated))

	return solution


def display_solution(grid_size, solution, providers, receivers):
	"""Display the solution in a grid format."""
	grid_display = np.full(grid_size, '.', dtype=str)
	grid_width, grid_height = grid_size

	# Place receivers on the grid
	for receiver in solution['receivers']:
		name, x, y, rotated = receiver
		receiver_obj = next(r for r in receivers if r.name == name)
		width, height = (receiver_obj.width, receiver_obj.height) if not rotated else (receiver_obj.height, receiver_obj.width)

		# Ensure the object fits within the grid
		if x + height > grid_width or y + width > grid_height:
			print(f"Error: Receiver '{name}' at ({x}, {y}) with dimensions ({width}x{height}) does not fit within the grid.")
			continue

		# Mark the grid with the receiver's name
		for dx in range(height):
			for dy in range(width):
				if 0 <= x + dx < grid_width and 0 <= y + dy < grid_height:
					grid_display[x + dx][y + dy] = name

	# Place providers on the grid
	for provider in solution['providers']:
		name, x, y, rotated = provider
		provider_obj = next(p for p in providers if p.name == name)
		width, height = (provider_obj.width, provider_obj.height) if not rotated else (provider_obj.height, provider_obj.width)

		# Ensure the object fits within the grid
		if x + height > grid_width or y + width > grid_height:
			print(f"Error: Provider '{name}' at ({x}, {y}) with dimensions ({width}x{height}) does not fit within the grid.")
			continue

		# Mark the grid with the provider's name
		for dx in range(height):
			for dy in range(width):
				if 0 <= x + dx < grid_width and 0 <= y + dy < grid_height:
					grid_display[x + dx][y + dy] = name

	# Display the grid
	print("\nGrid Layout:")
	for row in grid_display:
		print(" ".join(row))


def solve_with_ilp(grid_size, providers, receivers):
	"""Solve the problem using Integer Linear Programming."""
	solver = pywraplp.Solver.CreateSolver('SCIP')
	if not solver:
		print("SCIP solver is not available.")
		return None

	provider_vars, receiver_vars, rotation_vars, satisfaction_vars = create_decision_variables(solver, grid_size, providers, receivers)
	add_constraints(solver, grid_size, providers, receivers, provider_vars, receiver_vars, rotation_vars, satisfaction_vars)

	# Objective: Maximize the number of satisfied receivers
	objective = solver.Objective()
	for i in range(len(receivers)):
		objective.SetCoefficient(satisfaction_vars[i], 1)
	for i in range(len(providers)):
		for x in range(grid_size[0]):
			for y in range(grid_size[1]):
				objective.SetCoefficient(provider_vars[(i, x, y)], 0.1)  # Small weight for provider placement
	objective.SetMaximization()

	# Solve the problem
	status = solver.Solve()
	if status == pywraplp.Solver.OPTIMAL:
		print('Optimal solution found!')
		grid_width, grid_height = grid_size  # Define grid_width and grid_height
		# Debug: Print objective function coefficients
		print("Objective Function Coefficients:")
		for i, receiver in enumerate(receivers):
			print(f"Satisfaction Variable for Receiver {receiver.name}: Coefficient = {solver.Objective().GetCoefficient(satisfaction_vars[i])}")
		for i, provider in enumerate(providers):
			for x in range(grid_width):
				for y in range(grid_height):
					print(f"Provider Variable ({i}, {x}, {y}): Coefficient = {solver.Objective().GetCoefficient(provider_vars[(i, x, y)])}")
		# Debug: Print solution values
		print("Solution Values:")
		for i, provider in enumerate(providers):
			for x in range(grid_width):
				for y in range(grid_height):
					if provider_vars[(i, x, y)].solution_value() > 0.5:
						print(f"Provider {provider.name} placed at ({x}, {y})")
		for i, receiver in enumerate(receivers):
			for x in range(grid_width):
				for y in range(grid_height):
					if receiver_vars[(i, x, y)].solution_value() > 0.5:
						print(f"Receiver {receiver.name} placed at ({x}, {y})")
		for i, receiver in enumerate(receivers):
			print(f"Satisfaction Variable for Receiver {receiver.name}: {satisfaction_vars[i].solution_value()}")
		return extract_solution(solver, grid_size, providers, receivers, provider_vars, receiver_vars, rotation_vars)
	else:
		print('No optimal solution found.')
		return None


# Define the grid and objects
grid_size = (8, 8)

providers = [
	ProviderObject(name='B', width=1, height=2, points=100, effect_radius=1),
	ProviderObject(name='B', width=1, height=2, points=100, effect_radius=1),
	ProviderObject(name='D', width=2, height=2, points=200, effect_radius=2),
]

receivers = [
	ReceiverObject(name='A', width=2, height=2, required_points=400),
	ReceiverObject(name='C', width=1, height=1, required_points=100),
]

# Solve the problem
solution = solve_with_ilp(grid_size, providers, receivers)
if solution:
	print("\n=== Solution Found ===")
	
	print("\nProviders placed at:")
	for provider in solution['providers']:
		print(f"  Provider '{provider[0]}' placed at position (x={provider[1]}, y={provider[2]}), rotated: {provider[3]}")

	print("\nReceivers placed at:")
	for receiver in solution['receivers']:
		print(f"  Receiver '{receiver[0]}' placed at position (x={receiver[1]}, y={receiver[2]}), rotated: {receiver[3]}")

	display_solution(grid_size, solution, providers, receivers)
else:
	print("No optimal solution found.")