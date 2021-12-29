# -*- coding: UTF-8 -*-    
# 作者：zhangHJ
# 日期：2021/11/9  9:20
import numpy as np
from pylab import*
# 提取数据
# 创建空数组提取指定时间的温度值
# 确定需要提取的点
data_temp600 = []
data_temp700 = []
data_temp800 = []
data_time = []
for t in range (360):
    data_temp600.append(-1e-6*pow(t,3)+0.0013*pow(t,2)-0.36*t+97.72)
    data_temp700.append(-2e-6*pow(t,3)+0.002*pow(t,2)-0.67*t+100.61)
    data_temp800.append(-2e-8*pow(t,5)+8e-6*pow(t,4)-0.0015*pow(t,3)+0.13*pow(t,2)-5.47*t+99.82)
    data_time.append(t)
Y1 = data_temp600
Y2 = data_temp700
Y3 = data_temp800
C = data_time
# 绘制余弦曲线，使用蓝色的、连续的、宽度为 1 （像素）的线条
plot(C, Y1, color="blue", linewidth=1.0, linestyle="-")
# 绘制正弦曲线，使用绿色的、连续的、宽度为 1 （像素）的线条
plot(C, Y2, color="green", linewidth=1.0, linestyle="-")

plot(C, Y3, color="orange", linewidth=1.0, linestyle="-")

# 设置横轴的上下限,设置横轴记号
xlim(0,400)
xticks(np.linspace(0,400,9,endpoint=True))
# 设置纵轴的上下限,设置纵轴记号
ylim(0,100)
yticks(np.linspace(0,100,9,endpoint=True))

#设置图片边界
xmin ,xmax = C[0], C[359]
ymin, ymax = Y1[0], Y1[359]

# dx = (xmax - xmin) * 0.2
# dy = (ymax - ymin) * 0.2
#
# xlim(xmin - dx, xmax + dx)
# ylim(ymin - dy, ymax + dy)
plt.show()