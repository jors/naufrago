import time
import datetime

#now = datetime.datetime.now()
#split = str(now).split(' ')
split = str(datetime.datetime.now()).split(' ')

ds = split[0].split('-')
#ds = now_date.split('-')
ts = split[1].split(':')
#ts = now_time.split(':')

# feedparser-alike stringdate!
fs = (int(ds[0]), int(ds[1]), int(ds[2]), int(ts[0]), int(ts[1]), int(float(ts[2])))

# Datetime a epoch/seconds
t = datetime.datetime(fs[0], fs[1], fs[2], fs[3], fs[4], fs[5])
secs = time.mktime(t.timetuple())
print "Epoch Seconds: ", secs

# Epoch/seconds a datetime
now = datetime.datetime.fromtimestamp(secs)
print "Datetime: ", now

# Datetime to human-readable
print now.ctime()
