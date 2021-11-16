%matplotlib ipympl
#ipympl

import matplotlib
import matplotlib.pyplot as plt
from IPython import display
x = [1,2,3]
y = [4,5,6]
fig, axis = plt.subplots(1, 1, squeeze=False)
axis[0,0].plot(x, y)
