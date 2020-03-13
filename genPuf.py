import random
import numpy as np

size = (32,32)
puf = np.random.randint(0,2,size=size, dtype=np.bool)
np.savetxt("puf.txt", puf, fmt='%d')



