"""
Village domain value objects
"""


class Address:
    """Address value object"""

    def __init__(self, province: str, city: str, district: str, detail: str):
        self.province = province
        self.city = city
        self.district = district
        self.detail = detail

    def full_address(self) -> str:
        """Get full address string"""
        return f"{self.province}{self.city}{self.district}{self.detail}"

    def __repr__(self) -> str:
        return f"Address({self.full_address()})"
