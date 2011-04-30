import time
loop_count = 1000000

def manual_add():
 a = 0
 for num in xrange(loop_count):
  a += 1

def object_add():
 b = 0
 for num in xrange(loop_count):
  b.__add__(1)

t0 = time.time()
manual_add()
print 'manual_add(): ' + `time.time()-t0`

t0 = time.time()
object_add()
print 'object_add(): ' + `time.time()-t0`
