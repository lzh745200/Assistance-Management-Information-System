"""
Project domain value objects
"""

from datetime import date


class DateRange:
    """Date range value object"""

    def __init__(self, start_date: date, end_date: date):
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")
        self.start_date = start_date
        self.end_date = end_date

    def contains(self, check_date: date) -> bool:
        """Check if date is within range"""
        return self.start_date <= check_date <= self.end_date

    def overlaps(self, other: "DateRange") -> bool:
        """Check if two date ranges overlap"""
        return self.start_date <= other.end_date and other.start_date <= self.end_date

    def __repr__(self) -> str:
        return f"DateRange({self.start_date}, {self.end_date})"
