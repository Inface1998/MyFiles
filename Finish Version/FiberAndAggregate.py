# -*- coding: UTF-8 -*-    
# 作者：zhangHJ
# 日期：2021/8/23  9:39
# from abaqus import *
# from abaqusConstants import *
# from caeModules import *
# import os
# import matplotlib.pyplot as plt
# from visualization import *
# from odbAccess import *
# import xlwt
import math
import os

import numpy as np

# 判断骨料是否相交
def interact_judgement(data_aggregate, point1):
    x1 = point1[0]
    y1 = point1[1]
    z1 = point1[2]
    r1 = point1[3]
    sign = True
    for ii in data_aggregate:
        x2 = ii[0]
        y2 = ii[1]
        z2 = ii[2]
        r2 = ii[3]
        if x2 - x1 < r1 + r2 and y2 - y1 < r1 + r2 and z2 - z1 < r1 + r2:
            # distance calculate
            distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)
            if distance < (r1 + r2):
                sign = False
                break
    return sign


#  判断纤维是否相交
def fiber_judgement(line1, fibers):
    for i in range(len(fibers)):
        xa = line1[0][0]
        ya = line1[0][1]
        za = line1[0][2]
        xb = xa + line1[1][0] * np.sin(line1[1][2] * np.pi / 180) * np.cos(line1[1][1] * np.pi / 180)
        yb = ya + line1[1][0] * np.sin(line1[1][2] * np.pi / 180) * np.sin(line1[1][1] * np.pi / 180)
        zb = za + line1[1][0] * np.cos(line1[1][2] * np.pi / 180)
        xc = fibers[i][0][0]
        yc = fibers[i][0][1]
        zc = fibers[i][0][2]
        xd = xc + line1[1][0] * np.sin(fibers[i][1][2] * np.pi / 180) * np.cos(fibers[i][1][1] * np.pi / 180)
        yd = yc + line1[1][0] * np.sin(fibers[i][1][2] * np.pi / 180) * np.sin(fibers[i][1][1] * np.pi / 180)
        zd = zc + line1[1][0] * np.cos(fibers[i][1][2] * np.pi / 180)
        # f(p,q)=Ap^2+Bq^2+Cpq+Dp+Eq+F
        A = (xb - xa) * (xb - xa) + (yb - ya) * (yb - ya) + (zb - za) * (zb - za)
        B = (xd - xc) * (xd - xc) + (yd - yc) * (yd - yc) + (zd - zc) * (zd - zc)
        C = -2 * ((xb - xa) * (xd - xc) + (yb - ya) * (yd - yc) + (zb - za) * (zd - zc))
        D = 2 * ((xa - xc) * (xb - xa) + (ya - yc) * (yb - ya) + (za - zc) * (zb - za))
        E = -2 * ((xa - xc) * (xd - xc) + (ya - yc) * (yd - yc) + (za - zc) * (zd - zc))
        # F = (xa - xc) * (xa - xc) + (ya - yc) * (ya - yc) + (za - zc) * (za - zc)
        # f关于p的偏导数 fp = 2 * A * p  +     C * q  + D, q是常量
        # f关于q的偏导数fq =      C * p  + 2 * B * q  + E, p是常量
        p1 = (2 * B * D - C * E) / (C ** 2 - 4 * A * B)
        print (p1)
        q1 = (2 * A * E - C * D) / (C ** 2 - 4 * A * B)
        print (q1)
        x1 = xa + (xb - xa) * p1
        y1 = ya + (yb - ya) * p1
        z1 = za + (zb - za) * p1
        x2 = xc + (xd - xc) * q1
        y2 = yc + (yd - yc) * q1
        z2 = zc + (zd - zc) * q1
        distance = min(math.sqrt(((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)),
                       math.sqrt(((xa - xc) ** 2 + (ya - yc) ** 2 + (za - zc) ** 2)),
                       math.sqrt(((xa - xd) ** 2 + (ya - yd) ** 2 + (za - zd) ** 2)),
                       math.sqrt(((xb - xc) ** 2 + (yb - yc) ** 2 + (zb - zc) ** 2)),
                       math.sqrt(((xb - xd) ** 2 + (yb - yd) ** 2 + (zb - zd) ** 2)))
        if distance > fiber_r * 2:
            return True
        else:
            return False


#  判断纤维和骨料是否相交
def mix_judgement(data_aggregate, line1, fiber_length):
    # 将骨料的原点带入纤维端点的两个法平面方程左式判断算出的数是否落入两法平面右数区间
    # 根据fibers信息求出线段的方向向量
    # 1.两端点信息
    x1 = line1[0][0]
    y1 = line1[0][1]
    z1 = line1[0][2]
    x2 = x1 + fiber_length * np.sin(line1[1][2] * np.pi / 180) * np.cos(line1[1][1] * np.pi / 180)
    y2 = y1 + fiber_length * np.sin(line1[1][2] * np.pi / 180) * np.sin(line1[1][1] * np.pi / 180)
    z2 = z1 + fiber_length * np.cos(line1[1][2] * np.pi / 180)
    # 2.根据坐标点确定两个法平面方程
    # 纤维的方向向量为(a,b,c)
    # 纤维的端点法平面为ax + by + cz = m（n）
    a = np.sin(line1[1][2] * np.pi / 180) * np.cos(line1[1][1] * np.pi / 180)
    b = np.sin(line1[1][2] * np.pi / 180) * np.sin(line1[1][1] * np.pi / 180)
    c = np.cos(line1[1][2] * np.pi / 180)
    # 端点1法平面方程右数
    m = a * line1[0][0] + b * line1[0][1] + c * line1[0][2]
    # 端点2法平面方程右数
    n = a * line1[0][0] + b * line1[0][1] + c * line1[0][2] + fiber_length * (
            a ** 2 + b ** 2 + c ** 2)
    for j in range(len(data_aggregate)):
        aggregate_a = data_aggregate[j][0] * a + data_aggregate[j][1] * b + data_aggregate[j][2] * c
        if aggregate_a >= m and aggregate_a <= n:
            # 此时落入了两平面之间,海伦公式求面积得最小距离
            side1 = fiber_length
            side2 = math.sqrt((data_aggregate[j][0] - x1) ** 2 + (data_aggregate[j][1] - y1) ** 2 + (
                    data_aggregate[j][2] - z1) ** 2)
            side3 = math.sqrt((data_aggregate[j][0] - x2) ** 2 + (data_aggregate[j][1] - y2) ** 2 + (
                    data_aggregate[j][2] - z2) ** 2)
            p = (side1 + side2 + side3) / 2
            min_dis = math.sqrt(p * (p - side1) * (p - side2) * (p - side3)) / (side1 * 0.5)
        else:
            min_dis = min(math.sqrt((data_aggregate[j][0] - x1) ** 2 + (data_aggregate[j][1] - y1) ** 2 + (
                    data_aggregate[j][2] - z1) ** 2),
                          math.sqrt((data_aggregate[j][0] - x2) ** 2 + (data_aggregate[j][1] - y2) ** 2 + (
                                  data_aggregate[j][2] - z2) ** 2))
        if min_dis <= data_aggregate[j][3] + fiber_r:
            return False
    return True


# 创建纤维数据
def fibers_date(num, fiber_length):
    while True:
        # 防止钢纤维在外围区域堆积
        amend = 0.002 # 向内修正2mm
        x = np.random.uniform(amend, side_length-amend)
        y = np.random.uniform(amend, side_length-amend)
        z = np.random.uniform(amend, side_length-amend)
        angle_x = np.random.uniform(0, 360)
        angle_z = np.random.uniform(0, 180)
        line1 = ((x, y, z), (fiber_length, angle_x, angle_z))
        xb = x + line1[1][0] * np.sin(line1[1][2] * np.pi / 180) * np.cos(line1[1][1] * np.pi / 180)
        yb = y + line1[1][0] * np.sin(line1[1][2] * np.pi / 180) * np.sin(line1[1][1] * np.pi / 180)
        zb = z + line1[1][0] * np.cos(line1[1][2] * np.pi / 180)
        # 判断纤维是否超出边界
        if xb >= side_length or yb >= side_length or zb >= side_length or xb <= 0 or yb <= 0 or zb <= 0:
            continue
        # 判断第一根纤维是否与骨料相交
        if len(fibers) == 0 and mix_judgement(data_aggregate, line1, fiber_length):
            fibers.append(line1)
        # 判断其他纤维是否与骨料相交
        elif len(fibers) != 0:
            if fiber_judgement(line1, fibers) and mix_judgement(data_aggregate, line1, fiber_length):
                fibers.append(line1)
        if len(fibers) >= num:
            break


# 创建骨料数据
def aggregate_date(r_limit1, r_limit2, volume_ratio):
    # Generate spheres randomly
    points1 = []
    volume1 = 0
    count = 1
    while True:
        # 球形骨料的半径
        x1 = np.random.uniform(r_limit2, side_length - r_limit2)  # 球心的x坐标
        y1 = np.random.uniform(r_limit2, side_length - r_limit2)  # 球心的y坐标
        z1 = np.random.uniform(r_limit2, side_length - r_limit2)  # 球心的Z坐标
        r1 = np.random.uniform(r_limit1, r_limit2)
        point1 = (x1, y1, z1, r1)
        if len(points1) == 0:
            points1.append(point1)
            data_aggregate.append(point1)
            volume1 += ((point1[3]) ** 3) * np.pi * 4 / 3
        elif interact_judgement(data_aggregate, point1):
            points1.append(point1)
            data_aggregate.append(point1)
            volume1 += ((point1[3]) ** 3) * np.pi * 4 / 3
            count += 1
            print(count)
        if volume1 >= volume_ratio * (side_length ** 3):
            break


# 定义立方体试块边长
side_length = 0.1
# 创建骨料
data_aggregate = []  # 骨料信息
# 1.建立10~15mm的骨料
aggregate_date(0.01, 0.015, 0.12)
# # 2.建立5~10mm的骨料
# aggregate_date(0.005/2, 0.01/2, 0.08)

# 创建纤维
fibers = []
fiber_r = 0.00035        # 纤维半径
fiber_length = 0.035    # 纤维长度
fiber_amount = 750   # 纤维根数 >=2
fibers_date(fiber_amount, fiber_length)
# 提取数据到指定文件
with open("E:\Abaqus\Code\CycleInputFile\data_aggregate.txt", 'w') as da:
    for i in range(len(data_aggregate)):
        da.write('%.8f' % data_aggregate[i][0] + "," +
                 '%.8f' % data_aggregate[i][1] + "," +
                 '%.8f' % data_aggregate[i][2] + "," +
                 '%.8f' % data_aggregate[i][3])
        if i != len(data_aggregate) - 1:
            da.write("\n")

with open("E:\Abaqus\Code\CycleInputFile\data_fibers.txt", 'w') as da:
    for i in range(len(fibers)):
        da.write('%.8f' % fibers[i][0][0] + "," +
                 '%.8f' % fibers[i][0][1] + "," +
                 '%.8f' % fibers[i][0][2] + "," +
                 '%.8f' % fibers[i][1][1] + "," +
                 '%.8f' % fibers[i][1][2] + "," +
                 '%.8f' % fibers[i][1][0])
        if i != len(fibers) - 1:
            da.write("\n")
