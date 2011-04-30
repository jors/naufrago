import time
loop_count = 1000000

def method0():
 var = "This is a short sentence"
 for num in xrange(loop_count):
  if "is" in var:
   pass

def method1():
 var = "This is a short sentence"
 for num in xrange(loop_count):
  if var.find("is"):
   pass

t0 = time.time()
method0()
print 'method0(): ' + `time.time()-t0`

t0 = time.time()
method1()
print 'method1(): ' + `time.time()-t0`
