"""Billings 3 database access."""

import os

from sqlalchemy.ext.sqlsoup import SqlSoup


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
