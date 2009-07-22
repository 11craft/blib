"""A bridge between Billings and Adium."""

import time

import appscript

import argparse

from blib.database import default_billings_db


parser = argparse.ArgumentParser()
parser.add_argument(
    '-c', '--client', metavar='client-name',
    help='The name of the client to broadcast about.',
    )
parser.add_argument(
    '-d', '--destination', metavar='chat-name',
    help='The name of the chat to broadcast to.',
    )
parser.add_argument(
    '-i', '--interval', metavar='seconds', type=int, default=90,
    help='Interval between database scans; should be more than a minute.',
    )


def main():
    args = parser.parse_args()
    db = default_billings_db()
    def all_timeslips():
        db.expunge_all()
        return db.TimeSlip.filter(
            (db.Client.company == args.client)
            & (db.Project.clientID == db.Client.clientID)
            & (db.TimeSlip.projectID == db.Project.projectID)
            & (db.TimeSlip.activeForTiming == True)
            & (db.TimeSlip.nature != db.TimeSlip.nature_const.my_eyes_only)
            ).all()
    def active_timeslips():
        last_datetimes = {}
        # First get the last datetimes all the time slips.
        slips = all_timeslips()
        for slip in slips:
            key = slip.timeSlipID
            entries = slip.timeEntries
            if len(entries) > 0:
                last_datetimes[key] = entries[-1].endDateTime
        # Sleep and see what changed.
        time.sleep(args.interval)
        active = set()
        slips = all_timeslips()
        for slip in slips:
            key = slip.timeSlipID
            if key in last_datetimes:
                entries = slip.timeEntries
                if len(entries) > 0:
                    if last_datetimes[key] != entries[-1].endDateTime:
                        active.add(key)
        return active
    def send_message(message):
        print message
        appscript.app('Adium').chats[args.destination].send(message=message)
    print 'Press Ctrl-C to stop.'
    last_active = set()
    while True:
        currently_active = set(active_timeslips())
        # No longer active slips.
        for key in last_active - currently_active:
            timeslip = db.TimeSlip.get(key)
            send_message('/me is no longer working on %s: %s' % (
                    timeslip.project.nickname or timeslip.project.name,
                    timeslip.name,
                    ))
        # Newly-active slips.
        for key in currently_active - last_active:
            timeslip = db.TimeSlip.get(key)
            send_message('/me is now working on %s: %s' % (
                    timeslip.project.nickname or timeslip.project.name,
                    timeslip.name,
                    ))
        # Reset last active status.
        last_active = currently_active
