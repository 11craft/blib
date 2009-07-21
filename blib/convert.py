"""Data conversion functions."""

import datetime

import CoreData


def nsdate_to_datetime(decimal):
    """Convert a NSDate decimal value to a Python datetime object."""
    nsdate = CoreData.NSDate.dateWithTimeIntervalSinceReferenceDate_(decimal)
    unixtime = nsdate.timeIntervalSince1970()
    dt = datetime.datetime.fromtimestamp(unixtime)
    return dt
