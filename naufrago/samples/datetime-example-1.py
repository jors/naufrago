# File: datetime-example-1.py

import datetime

now = datetime.datetime(2003, 8, 4, 12, 30, 45)

print now
print repr(now)
print type(now)
print now.year, now.month, now.day
print now.hour, now.minute, now.second
print now.microsecond

print datetime.datetime.now()
