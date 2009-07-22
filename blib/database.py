"""Billings 3 database access."""

import os

from sqlalchemy.ext.sqlsoup import SqlSoup

from blib.convert import nsdate_to_datetime


class TimeSlipNatureConstants(object):
    my_eyes_only = 103


class DateTimeInstrumentedAttribute(object):
    # XXX: Surely a cleaner way to do this?
    # Overriding CoreData date time values with datetime objects.

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

    def setup_attributes(self):
        # XXX: See DateTimeInstrumentedAttribute comments.
        for table_name, column_name in [
            ('Client', 'modifyDate'),
            ('Client', 'createDate'),
            ('ConsolidatedTax', 'createDate'),
            ('Estimate', 'dueDate'),
            ('Estimate', 'sentDate'),
            ('Estimate', 'modifyDate'),
            ('Estimate', 'createDate'),
            ('EstimateSlip', 'dueDate'),
            ('EstimateSlip', 'endDateTime'),
            ('EstimateSlip', 'modifyDate'),
            ('EstimateSlip', 'createDate'),
            ('EstimateSlip', 'foreignAppLastTouchDate'),
            ('EstimateSlip', 'startDateTime'),
            ('Invoice', 'invoiceDate'),
            ('Invoice', 'dueDate'),
            ('Invoice', 'sentDate'),
            ('Invoice', 'modifyDate'),
            ('Invoice', 'taxPointDate'),
            ('Invoice', 'createDate'),
            ('Note', 'createDate'),
            ('Note', 'modifyDate'),
            ('Payment', 'createDate'),
            ('Payment', 'modifyDate'),
            ('PaymentInvoiceEntry', 'createDate'),
            ('PaymentInvoiceEntry', 'modifyDate'),
            ('ProFormaInvoice', 'createDate'),
            ('ProFormaInvoice', 'dueDate'),
            ('ProFormaInvoice', 'invoiceDate'),
            ('ProFormaInvoice', 'modifyDate'),
            ('Project', 'dueDate'),
            ('Project', 'completeDate'),
            ('Project', 'modifyDate'),
            ('Project', 'startDate'),
            ('Project', 'createDate'),
            ('Project', 'foreignAppLastTouchDate'),
            ('RecurringInvoice', 'lastSentDate'),
            ('RecurringInvoice', 'nextSendDate'),
            ('RecurringInvoice', 'lastPlannedSendDate'),
            ('RecurringInvoice', 'modifyDate'),
            ('Retainer', 'createDate'),
            ('Retainer', 'modifyDate'),
            ('Statement', 'sentDate'),
            ('Statement', 'fromDate'),
            ('Statement', 'toDate'),
            ('Tax', 'createDate'),
            ('TimeEntry', 'endDateTime'),
            ('TimeEntry', 'modifyDate'),
            ('TimeEntry', 'createDate'),
            ('TimeEntry', 'foreignAppLastTouchDate'),
            ('TimeEntry', 'startDateTime'),
            ('TimeSlip', 'invoicedDate'),
            ('TimeSlip', 'dueDate'),
            ('TimeSlip', 'endDateTime'),
            ('TimeSlip', 'modifyDate'),
            ('TimeSlip', 'createDate'),
            ('TimeSlip', 'foreignAppLastTouchDate'),
            ('TimeSlip', 'startDateTime'),
            ('URLReference', 'createDate'),
            ('URLReference', 'modifyDate'),
            ('User', 'createDate'),
            ('User', 'modifyDate'),
            ]:
            table = getattr(self, table_name)
            original_attribute = getattr(table, column_name)
            new_attribute = DateTimeInstrumentedAttribute(original_attribute)
            setattr(table, column_name, new_attribute)

    def setup_constants(self):
        self.TimeSlip.nature_const = TimeSlipNatureConstants

    def setup_relations(self):
        # Add one:many relations.
        self.Project.relate(
            'timeSlips',
            self.TimeSlip,
            foreign_keys=[self.TimeSlip.projectID],
            primaryjoin=self.Project.projectID == self.TimeSlip.projectID,
            backref='project',
            )
        self.TimeSlip.relate(
            'timeEntries',
            self.TimeEntry,
            foreign_keys=[self.TimeEntry.timeSlipID],
            primaryjoin=self.TimeSlip.timeSlipID == self.TimeEntry.timeSlipID,
            backref='timeSlip',
            )

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
