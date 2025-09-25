# test_cases.py

from provider import ProviderObject
from receiver import ReceiverObject

test_cases = {
    "case_1": {
        "grid_size": (6, 6),
        "providers": [
            ProviderObject(name='B', width=1, height=2, points=100, effect_radius=1, board=None),
            ProviderObject(name='B', width=1, height=2, points=100, effect_radius=1, board=None),
            ProviderObject(name='D', width=2, height=2, points=200, effect_radius=2, board=None),
        ],
        "receivers": [
            ReceiverObject(name='A', width=2, height=2, required_points=400, board=None),
            ReceiverObject(name='C', width=1, height=1, required_points=100, board=None),
        ],
    },
    "case_2": {
        "grid_size": (8, 8),
        "providers": [
            ProviderObject(name='P1', width=1, height=1, points=50, effect_radius=1, board=None),
            ProviderObject(name='P2', width=2, height=2, points=150, effect_radius=2, board=None),
        ],
        "receivers": [
            ReceiverObject(name='R1', width=3, height=3, required_points=200, board=None),
            ReceiverObject(name='R2', width=2, height=2, required_points=100, board=None),
        ],
    },
    # Add more test cases as needed
}