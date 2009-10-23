"""Billings 3 database access."""

import os

from sqlalchemy.ext.sqlsoup import SqlSoup
from sqlalchemy.orm import column_property
from sqlalchemy.orm.properties import ColumnProperty

from blib.convert import datetime_to_nsdate, nsdate_to_datetime


class TimeSlipNatureConstants(object):
    my_eyes_only = 103


class DateTimeInstrumentedAttribute(object):
    """Override NSDate values with datetime objects."""

    def __init__(self, original):
        self.original = original

    def __set__(self, instance, value):
        self.original.__set__(instance, value)

    def __delete__(self, instance):
        self.original.__delete__(instance)

    def __get__(self, instance, owner):
        if instance is None:
            return self.original
        else:
            value = self.original.__get__(instance, owner)
            if value is None:
                return None
            else:
                return nsdate_to_datetime(value)


class NsdateComparator(ColumnProperty.Comparator):
    """Properly compare datetime objects with NSDate-valued columns."""

    def __lt__(self, other):
        return self.__clause_element__() < datetime_to_nsdate(other)

    def __le__(self, other):
        return self.__clause_element__() <= datetime_to_nsdate(other)

    def __eq__(self, other):
        return self.__clause_element__() == datetime_to_nsdate(other)

    def __gt__(self, other):
        return self.__clause_element__() > datetime_to_nsdate(other)

    def __ge__(self, other):
        return self.__clause_element__() >= datetime_to_nsdate(other)


class BillingsDb(SqlSoup):
    """A SqlAlchemy/SqlSoup-based ORM to a Billings 3 database."""

    def __init__(self, billings_path):
        db_path = os.path.abspath(
            os.path.join(
                billings_path,
                'Database', 'billings.bid',
                ))
        uri = 'sqlite:///' + db_path
        SqlSoup.__init__(self, uri)
        self.setup_attributes()
        self.setup_constants()
        self.setup_relations()
        self.setup_column_introspection()

    def setup_attributes(self):
        # Get all of the date-related column names.
        date_columns = {
            # table_name: [col_name, ...],
            }
        for table_name in self.engine.table_names():
            table = getattr(self, table_name)
            for column_name in table.c.keys():
                if (column_name.endswith('Date')
                    or column_name.endswith('DateTime')
                    ):
                    cols = date_columns.setdefault(table_name, [])
                    cols.append(column_name)
        # Override date-related columns.
        for table_name, column_names in date_columns.iteritems():
            # Map comparators.
            properties = {}
            table = self.entity(table_name)
            for column_name in column_names:
                column = table.c[column_name]
                properties[column_name] = column_property(
                    column,
                    comparator_factory=NsdateComparator,
                    )
            # Keep new table.
            table = self.map(self.entity(table_name), properties=properties)
            setattr(self, table_name, table)
            # Assign instrumented attributes.
            for column_name in column_names:
                original_attribute = getattr(table, column_name)
                new_attribute = DateTimeInstrumentedAttribute(
                    original_attribute)
                setattr(table, column_name, new_attribute)

    def setup_constants(self):
        self.TimeSlip.nature_const = TimeSlipNatureConstants

    def setup_relations(self):
        # Add generic one:many relations.
        for one, many, many_plural in [
            ('Category', 'EstimateSlip', None),
            ('Category', 'SlipTemplate', None),
            ('Category', 'TimeSlip', None),
            ('Client', 'Invoice', None),
            ('Client', 'Payment', None),
            ('Client', 'ProFormaInvoice', None),
            ('Client', 'Project', None),
            ('Client', 'RecurringInvoice', None),
            ('Client', 'Retainer', None),
            ('Client', 'Statement', None),
            ('ClientCategory', 'Client', None),
            ('ConsolidatedTax', 'Estimate', None),
            ('ConsolidatedTax', 'EstimateSlip', None),
            ('ConsolidatedTax', 'Invoice', None),
            ('ConsolidatedTax', 'SlipTemplate', None),
            ('ConsolidatedTax', 'Tax', 'taxes'),
            ('ConsolidatedTax', 'TaxConsolidatedTaxEntry',
             'taxConsolidatedTaxEntries'),
            ('ConsolidatedTax', 'TimeSlip', None),
            ('Estimate', 'EstimateSlip', None),
            ('Invoice', 'PaymentInvoiceEntry', 'paymentInvoiceEntries'),
            ('Invoice', 'TimeSlip', None),
            ('Payment', 'PaymentInvoiceEntry', 'paymentInvoiceEntries'),
            ('Project', 'Estimate', None),
            ('Project', 'EstimateSlip', None),
            ('Project', 'Invoice', None),
            ('Project', 'Note', None),
            ('Project', 'Payment', None),
            ('Project', 'Retainer', None),
            ('Project', 'TimeSlip', None),
            ('Project', 'URLReference', None),
            ('RecurringInvoice', 'SlipTemplate', None),
            ('Tax', 'TaxConsolidatedTaxEntry', 'taxConsolidatedTaxEntries'),
            ('TimeSlip', 'TimeEntry', 'timeEntries'),
            ('User', 'EstimateSlip', None),
            ('User', 'SlipTemplate', None),
            ('User', 'TimeSlip', None),
            ]:
            one_table = getattr(self, one)
            one_field = one[0].lower() + one[1:]
            one_id = one_field + 'ID'
            many_table = getattr(self, many)
            many_field = many_plural or many[0].lower() + many[1:] + 's'
            many_id = many_field + 'ID'
            one_table.relate(
                many_field,
                many_table,
                foreign_keys=[getattr(many_table, one_id)],
                primaryjoin=(getattr(one_table, one_id)
                             == getattr(many_table, one_id)),
                backref=one_field,
                )
        # TODO: Add additional relationships that aren't generic 1:many...
        # or that have shortened ID fields.

    def setup_column_introspection(self):
        for table_name in self.engine.table_names():
            table = getattr(self, table_name)
            def _getAttributeNames(c=table.c):
                return c.keys()
            table.c._getAttributeNames = _getAttributeNames

    def _getAttributeNames(self):
        """Allows autocompletion of table names in IPython shell."""
        return self.engine.table_names()

    def client_timeslips(self, company_name):
        return self.TimeSlip.filter(
            (self.Client.company == company_name)
            & (self.Project.clientID == self.Client.clientID)
            & (self.TimeSlip.projectID == self.Project.projectID)
            & (self.TimeSlip.activeForTiming == False)
            & (self.TimeSlip.nature != self.TimeSlip.nature_const.my_eyes_only)
            ).all()


def default_billings_db():
    billings_path = os.path.join(
        os.path.expanduser('~'),
        'Library', 'Application Support', 'Billings',
        )
    return BillingsDb(billings_path)
