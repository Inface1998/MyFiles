# -*- coding: UTF-8 -*-    
# 作者：zhangHJ
# 日期：2021/9/1  19:53
from abaqus import *
from abaqusConstants import *
from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from optimization import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *
from caeModules import *
from driverUtils import executeOnCaeStartup
from odbAccess import *
import numpy as np
import xlrd
import xlwt
import os
import math

Mdb()
session.journalOptions.setValues(replayGeometry=INDEX, recoverGeometry=INDEX)
session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)
session.viewports['Viewport: 1'].assemblyDisplay.geometryOptions.setValues(datumAxes=OFF)

def create_aggregate():
    for i in range(count):
            mySketch = myModel.ConstrainedSketch(name='sphereProfile', sheetSize=200)
            mySketch.ArcByCenterEnds(center=(b[i][0], b[i][1]), direction=CLOCKWISE,
                                     point1=(b[i][0], b[i][1] + b[i][3]), point2=(b[i][0], b[i][1] - b[i][3]))
            mySketch.Line(point1=(b[i][0], b[i][1] + b[i][3]), point2=(b[i][0], b[i][1] - b[i][3]))
            myConstructionLine = mySketch.ConstructionLine(point1=(b[i][0], b[i][1] + b[i][3]),
                                                           point2=(b[i][0], b[i][1] - b[i][3]))
            myBall = myModel.Part(name='sphere' + str(i), dimensionality=THREE_D, type=DEFORMABLE_BODY)
            myPart = myBall.BaseSolidRevolve(angle=360.0, flipRevolveDirection=OFF, sketch=mySketch)
            myModel.rootAssembly.DatumCsysByDefault(CARTESIAN)
            myModel.rootAssembly.Instance(dependent=OFF, name='sphere' + str(i), part=myBall)
            myModel.rootAssembly.translate(instanceList=('sphere' + str(i),), vector=(0.0, 0.0, b[i][2]))
            del myBall
            del myConstructionLine
            del myPart
            del mySketch

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


# 创建骨料数据
def aggregate_data(r_limit1, r_limit2, volume_ratio):
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


def cut_aggregate():
    tuple = ()
    for i in range(count):
        tuple += (a.instances['sphere' + str(i)],)
    a.InstanceFromBooleanCut(name='Part-cut',
                             instanceToBeCut=mdb.models['Model-1'].rootAssembly.instances['Part-Base-1'],
                             cuttingInstances=tuple, originalInstances=DELETE)
    del mdb.models['Model-1'].parts['Part-Base']



# 定义立方体试块边长（mm）
side_length = 100
# 创建骨料
data_aggregate = []  # 骨料信息
# 1.建立10~15mm的骨料
aggregate_data(10 / 2.0, 15 / 2.0, 0.1)
# 提取数据到指定文件
cwd = os.getcwd()
data_file =cwd+"\data_aggregate.txt"
with open(data_file, 'w') as da:
    for i in range(len(data_aggregate)):
        da.write('%.5f' % data_aggregate[i][0] + "," +
                 '%.5f' % data_aggregate[i][1] + "," +
                 '%.5f' % data_aggregate[i][2] + "," +
                 '%.5f' % data_aggregate[i][3])
        if i != len(data_aggregate) - 1:
            da.write("\n")


# modeling
myModel = mdb.Model(name='Model-1')
mysketch_1 = myModel.ConstrainedSketch(name='mysketch_1', sheetSize=200.0)
mysketch_1.rectangle(point1=(0.0, 0.0), point2=(side_length, side_length))
myPart = myModel.Part(name='Part-Base', dimensionality=THREE_D, type=DEFORMABLE_BODY)
myPart.BaseSolidExtrude(sketch=mysketch_1, depth=side_length)
mdb.models['Model-1'].rootAssembly.Instance(dependent=ON, name='Part-Base-1',
                                            part=mdb.models['Model-1'].parts['Part-Base'])

mdb.models['Model-1'].Material(name='Material-Matrix')
mdb.models['Model-1'].materials['Material-Matrix'].Density(table=((2300.0,),))
mdb.models['Model-1'].materials['Material-Matrix'].Elastic(table=((30e9, 0.3),))
mdb.models['Model-1'].materials['Material-Matrix'].SpecificHeat(table=((1.0,),))
mdb.models['Model-1'].materials['Material-Matrix'].Expansion(table=((9.1e-06,),))
mdb.models['Model-1'].materials['Material-Matrix'].Conductivity(table=((1.25,),))

mdb.models['Model-1'].Material(name='Material-Aggregate')
mdb.models['Model-1'].materials['Material-Aggregate'].Density(table=((2900.0,),))
mdb.models['Model-1'].materials['Material-Aggregate'].Elastic(table=((40e9, 0.3),))
mdb.models['Model-1'].materials['Material-Aggregate'].SpecificHeat(table=((1.2,),))
mdb.models['Model-1'].materials['Material-Aggregate'].Expansion(table=((8.1e-06,),))
mdb.models['Model-1'].materials['Material-Aggregate'].Conductivity(table=((1.55,),))
# 生成立方体试块模型
myAssembly = mdb.models['Model-1'].rootAssembly
# 生成骨料
b = np.loadtxt(data_file, delimiter=',',dtype=np.float32)
print(b)
count = len(open(data_file, 'rU').readlines())
print(count)
create_aggregate()
a = mdb.models['Model-1'].rootAssembly
