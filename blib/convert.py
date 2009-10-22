"""Data conversion functions."""

from datetime import datetime
from time import mktime

import CoreData


def nsdate_to_datetime(decimal):
    """Convert a NSDate decimal value to a Python datetime object."""
    nsdate = CoreData.NSDate.alloc().initWithTimeIntervalSinceReferenceDate_(
        decimal)
    unixtime = nsdate.timeIntervalSince1970()
    dt = datetime.fromtimestamp(unixtime)
    del nsdate
    return dt


def datetime_to_nsdate(dt):
    """Convert a Python datetime object to a NSDate decimal value."""
    unixtime = mktime(dt.timetuple()) + 1e-6*dt.microsecond
    nsdate = CoreData.NSDate.alloc().initWithTimeIntervalSince1970_(unixtime)
    decimal = nsdate.timeIntervalSinceReferenceDate()
    del nsdate
    return decimal
