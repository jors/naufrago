import time
import datetime

# feedparser stringdate!
fs = (2010, 4, 11, 14, 10, 55)

# Datetime a epoch/seconds
t = datetime.datetime(fs[0], fs[1], fs[2], fs[3], fs[4], fs[5])
secs = time.mktime(t.timetuple())
print "Epoch Seconds: ", secs

# Epoch/seconds a datetime
now = datetime.datetime.fromtimestamp(secs)
print "Datetime: ", now

# Datetime to human-readable
print now.ctime()
