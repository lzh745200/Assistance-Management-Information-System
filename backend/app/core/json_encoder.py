"""Custom JSON encoder.

Provides a json.JSONEncoder subclass that handles types commonly
encountered in the application (datetime, Decimal, UUID, etc.) so they
serialise cleanly in API responses.
"""

import datetime
import decimal
import json
import uuid
from enum import Enum


class AppJSONEncoder(json.JSONEncoder):
    """A JSON encoder that knows about application domain types.

    Additional types handled:
    - datetime, date, time -> ISO 8601 string
    - Decimal -> float or string (configurable)
    - UUID -> string
    - set -> list
    - Anything with __json__() method -> its return value
    - Enum members -> their .value
    """

    def __init__(self, *args, decimal_as_string: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self._decimal_as_string = decimal_as_string

    def default(self, o):
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        if isinstance(o, datetime.date):
            return o.isoformat()
        if isinstance(o, datetime.time):
            return o.isoformat()
        if isinstance(o, decimal.Decimal):
            if self._decimal_as_string:
                return str(o)
            return float(o)
        if isinstance(o, uuid.UUID):
            return str(o)
        if isinstance(o, set):
            return list(o)
        if hasattr(o, "__json__"):
            return o.__json__()
        return super().default(o)


def dumps(obj, *, indent: int = None, ensure_ascii: bool = False, **kwargs) -> str:
    """Serialise obj to a JSON string using AppJSONEncoder."""
    return json.dumps(obj, cls=AppJSONEncoder, indent=indent, ensure_ascii=ensure_ascii, **kwargs)


def loads(s: str, **kwargs):
    """Parse a JSON string. Thin wrapper around json.loads."""
    return json.loads(s, **kwargs)

CustomJSONEncoder = AppJSONEncoder
