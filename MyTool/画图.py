# -*- coding: UTF-8 -*-    
# 作者：zhangHJ
# 日期：2021/11/9  9:20
import numpy as np
from pylab import*
import openpyxl
# 提取数据
# 创建空数组提取指定时间的温度值
# 确定需要提取的点
data_temp = []
data_vapor = []
data_time = []
for i in range (1,81):
    wb = openpyxl.load_workbook('E:/Abaqus/Code/OutPutFiles/CycleOutputFile/11-9/NodeElement-{}.xlsx'.format(i))
    sheet1 = wb["MatrixElement"]
    data_temp.append(sheet1.cell(6729, 6).value)
    data_vapor.append(sheet1.cell(6729,12).value)
    data_time.append(400/80.0*i)
X = data_time
C = data_temp
# 绘制余弦曲线，使用蓝色的、连续的、宽度为 1 （像素）的线条
plot(X, C, color="blue", linewidth=1.0, linestyle="-")
# 绘制正弦曲线，使用绿色的、连续的、宽度为 1 （像素）的线条
# plot(X, S, color="green", linewidth=1.0, linestyle="-")

# 设置横轴的上下限,设置横轴记号
xlim(0,400)
xticks(np.linspace(0,400,9,endpoint=True))
# 设置纵轴的上下限,设置纵轴记号
ylim(0,800)
yticks(np.linspace(0,800,9,endpoint=True))

#设置图片边界
xmin ,xmax = X[0], X[79]
ymin, ymax = C[0], C[79]

dx = (xmax - xmin) * 0.2
dy = (ymax - ymin) * 0.2

xlim(xmin - dx, xmax + dx)
ylim(ymin - dy, ymax + dy)
plt.show()