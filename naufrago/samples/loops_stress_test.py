import time
oldlist = ['1', 'test', '3', 'big', '5', 'supercalifragilisticoespialidoso', 're-check', 'a', 'bBbBbBbB**"%&?=(']

# Slow
def method0():
 newlist = []
 for word in oldlist: # Most basic for loop
  newlist.append(word.upper())

# Slowest!
def method1(): # Avoiding the dots
 upper = str.upper
 newlist = []
 append = newlist.append
 for word in oldlist:
  append(upper(word))

# Less slow
def method2():
 newlist = []
 newlist = map(str.upper, oldlist) # Use map to use a C loop

# A little bit less slow
def method3():
 newlist = []
 newlist = [s.upper() for s in oldlist] # List comprehension

# Fastest!
def method4():
 newlist = []
 newlist = (s.upper() for s in oldlist) # Generator expression

t0 = time.time()
for i in xrange(100000):
 method0()
print 'method0(): ' + `time.time()-t0`

t0 = time.time()
for i in xrange(100000):
 method1()
print 'method1(): ' + `time.time()-t0`

t0 = time.time()
for i in xrange(100000):
 method2()
print 'method2(): ' + `time.time()-t0`

t0 = time.time()
for i in xrange(100000):
 method3()
print 'method3(): ' + `time.time()-t0`

t0 = time.time()
for i in xrange(100000):
 method4()
print 'method4(): ' + `time.time()-t0`
