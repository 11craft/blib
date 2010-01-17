"""Billings 3 database access."""

import blib.patch_sqlite

import os

from sqlalchemy.ext.sqlsoup import PKNotFoundError, SqlSoup


class TimeSlipNatureConstants(object):
    my_eyes_only = 103


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
        self.setup_constants()
        self.setup_relations()
        self.setup_column_introspection()

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
            one_id = '_rowid'
            many_table = getattr(self, many)
            many_field = many_plural or many[0].lower() + many[1:] + 's'
            many_id = one_field + 'ID'
            one_table.relate(
                many_field,
                many_table,
                foreign_keys=[getattr(many_table, many_id)],
                primaryjoin=(getattr(one_table, one_id)
                             == getattr(many_table, many_id)),
                backref=one_field,
                )
        # TODO: Add additional relationships that aren't generic 1:many...
        # or that have shortened ID fields.

    def setup_column_introspection(self):
        for table_name in self.engine.table_names():
            try:
                table = getattr(self, table_name)
            except PKNotFoundError:
                pass
            else:
                def _getAttributeNames(c=table.c):
                    return c.keys()
                table.c._getAttributeNames = _getAttributeNames

    def _getAttributeNames(self):
        """Allows autocompletion of table names in IPython shell."""
        return self.engine.table_names()

    def client_timeslips(self, company_name):
        return self.TimeSlip.filter(
            (self.Client.company == company_name)
            & (self.Project.clientID == self.Client._rowid)
            & (self.TimeSlip.projectID == self.Project._rowid)
            & (self.TimeSlip.activeForTiming == False)
            & (self.TimeSlip.nature != self.TimeSlip.nature_const.my_eyes_only)
            ).all()


def default_billings_db():
    billings_path = os.path.join(
        os.path.expanduser('~'),
        'Library', 'Application Support', 'Billings',
        )
    return BillingsDb(billings_path)
