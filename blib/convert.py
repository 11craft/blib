"""Data conversion functions."""

from decimal import Decimal
from datetime import datetime
from time import mktime


SECS_1970_2001 = Decimal('978307200.0')


def nsdate_to_datetime(decimal):
    """Convert a NSDate decimal value to a Python datetime object."""
    return datetime.fromtimestamp(decimal + SECS_1970_2001)


def datetime_to_nsdate(dt):
    """Convert a Python datetime object to a NSDate decimal value."""
    unixtime = str(mktime(dt.timetuple()) + 1e-6*dt.microsecond)
    return Decimal(unixtime) - SECS_1970_2001
