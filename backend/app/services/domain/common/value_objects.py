"""
Common domain value objects
"""


class Percentage:
    """Percentage value object"""

    def __init__(self, value: float):
        if not 0 <= value <= 100:
            raise ValueError("Percentage must be between 0 and 100")
        self.value = value

    def of(self, total: float) -> float:
        """Calculate percentage of a total"""
        return total * (self.value / 100)

    def __repr__(self) -> str:
        return f"Percentage({self.value}%)"
