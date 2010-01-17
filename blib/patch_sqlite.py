from datetime import datetime
from decimal import Decimal

from sqlalchemy.databases import sqlite
import sqlalchemy.types as sqltypes


class CustomSLDateTime(sqlite.SLDateTime):

    def result_processor(self, dialect):
        # Billings 3.5+ stores UNIX epoch floats, not NSDate floats or
        # ISO dates.
        def process(value):
            if value is not None:
                return datetime.fromtimestamp(value)
            else:
                return None
        return process


sqlite.colspecs[sqltypes.DateTime] = CustomSLDateTime

sqlite.ischema_names['DATETIME'] = CustomSLDateTime
sqlite.ischema_names['TIMESTAMP'] = CustomSLDateTime
