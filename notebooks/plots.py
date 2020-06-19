import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d

data = pd.read_csv("../data/data.csv", index_col=None)

# fig = plt.figure()
# ax = plt.axes(projection='3d')
# ax.scatter3D(data.pos_x, data.pos_y, data.pos_z)

# plt.show()

fig = plt.figure()
ax = plt.axes(projection='3d')
ax.scatter3D(data.dir_x, data.dir_y, data.dir_z)
ax.set_title("Layout of PMTs used for generating data")
plt.savefig("../assets/pmt_layout.png")
plt.show()
