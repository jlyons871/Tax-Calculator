import time
from numba import jit, njit

x = 0
def doit1(i):
    global x
    x = x + i

list = range(150000)
t = time.time()
for i in list:
    doit1(i)

print "funct calls: %.3f" % (time.time()-t)


x = 0
def doit2(list):
    global x
    for i in list:
        x = x + i

list = range(150000)
t = time.time()
doit2(list)
print "loop: %.3f" % (time.time()-t)

t = time.time()
jit(doit2(list))
print "jit loop: %.3f" % (time.time()-t)

"""
RESULTS:
funct calls: 0.036
loop: 0.012
jit loop: 0.011
"""



