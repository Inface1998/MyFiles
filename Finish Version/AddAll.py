#! /user/bin/python
# - * - coding: UTF-8 - * -
# coding: utf-8
from abaqus import *
from abaqusConstants import *
from caeModules import *
import os
import numpy as np
import math
import matplotlib.pyplot as plt
import numpy as np
# from visualization import *
from odbAccess import *
import xlwt
import math
import time

Mdb()
session.journalOptions.setValues(replayGeometry=INDEX, recoverGeometry=INDEX)
session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)
session.viewports['Viewport: 1'].assemblyDisplay.geometryOptions.setValues(datumAxes=OFF)


# 生成骨料
def create_aggregate(arr, num):
    for i in range(num):
        mySketch = myModel.ConstrainedSketch(name='sphereProfile', sheetSize=200)
        mySketch.ArcByCenterEnds(center=(arr[i][0], arr[i][1]), direction=CLOCKWISE,
                                 point1=(arr[i][0], arr[i][1] + arr[i][3]), point2=(arr[i][0], arr[i][1] - arr[i][3]))
        mySketch.Line(point1=(arr[i][0], arr[i][1] + arr[i][3]), point2=(arr[i][0], arr[i][1] - arr[i][3]))
        myConstructionLine = mySketch.ConstructionLine(point1=(arr[i][0], arr[i][1] + arr[i][3]),
                                                       point2=(arr[i][0], arr[i][1] - arr[i][3]))
        myBall = myModel.Part(name='sphere' + str(i), dimensionality=THREE_D, type=DEFORMABLE_BODY)
        myPart = myBall.BaseSolidRevolve(angle=360.0, flipRevolveDirection=OFF, sketch=mySketch)
        myModel.rootAssembly.DatumCsysByDefault(CARTESIAN)
        myModel.rootAssembly.Instance(dependent=ON, name='sphere' + str(i), part=myBall)
        myModel.rootAssembly.translate(instanceList=('sphere' + str(i),), vector=(0.0, 0.0, arr[i][2]))
        del myBall
        del myConstructionLine
        del myPart
        del mySketch


# 切割骨料
def cut_aggregate(num):
    tuple = ()
    for i in range(num):
        tuple += (a.instances['sphere' + str(i)],)
    a.InstanceFromBooleanCut(name='Part-cut',
                             instanceToBeCut=mdb.models['Model-1'].rootAssembly.instances['Part-Base-1'],
                             cuttingInstances=tuple, originalInstances=DELETE)
    del mdb.models['Model-1'].parts['Part-Base']


# 生成纤维
def create_fibers(arr, num):
    for num in range(num):
        x = arr[num][0]
        y = arr[num][1]
        z = arr[num][2]
        angle_x = arr[num][3]
        angle_z = arr[num][4]
        if angle_x > 180:
            a.Instance(name='Part-fiber-{}'.format(num), part=part, dependent=ON)
            a.translate(instanceList=('Part-fiber-{}'.format(num),), vector=(x, y, z))
            a.rotate(instanceList=('Part-fiber-{}'.format(num),), axisPoint=(x, y, z),
                              axisDirection=(0, 0, 1),
                              angle=angle_x)
            a.rotate(instanceList=('Part-fiber-{}'.format(num),), axisPoint=(x, y, z),
                              axisDirection=(-1, np.tan((90 - (angle_x - 180)) * np.pi / 180), 0),
                              angle=90 - angle_z)
        if angle_x < 180:
            a.Instance(name='Part-fiber-{}'.format(num), part=part, dependent=ON)
            a.translate(instanceList=('Part-fiber-{}'.format(num),), vector=(x, y, z))
            a.rotate(instanceList=('Part-fiber-{}'.format(num),), axisPoint=(x, y, z),
                              axisDirection=(0, 0, 1), angle=angle_x)
            a.rotate(instanceList=('Part-fiber-{}'.format(num),), axisPoint=(x, y, z),
                              axisDirection=(1, -np.tan((90 - angle_x) * np.pi / 180), 0),
                              angle=90 - angle_z)


# 骨料截面赋予
def assign_aggregate(num):
    for i in range(num):
        p = mdb.models['Model-1'].parts['sphere{}'.format(i)]
        mdb.models['Model-1'].HomogeneousSolidSection(name='Section-sphere{}'.format(i),
                                                      material='Material-Aggregate', thickness=None)
        cells = p.cells.findAt(((bg[i][0], bg[i][1], 0),))
        region = p.Set(cells=cells, name='Set-sphere{0}'.format(i))
        p.SectionAssignment(region=region, sectionName='Section-sphere{}'.format(i), offset=0.0,
                            offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)


# 定义绑定接触
def create_tie(num):
    for i in range(num):
        a = mdb.models['Model-1'].rootAssembly
        s1 = a.instances['Part-cut-1'].faces
        side1Faces1 = s1.findAt(((bg[i][0] + bg[i][3], bg[i][1], bg[i][2]),))
        a.Surface(side1Faces=side1Faces1, name='CP-{}-Part-cut-1'.format(i + 1))
        region1 = a.surfaces['CP-{}-Part-cut-1'.format(i + 1)]
        a = mdb.models['Model-1'].rootAssembly
        s1 = a.instances['sphere{}'.format(i)].faces
        side1Faces1 = s1.findAt(((bg[i][0] + bg[i][3], bg[i][1], bg[i][2]),))
        a.Surface(side1Faces=side1Faces1, name='CP-{}-sphere{}'.format(i + 1, i))
        region2 = a.surfaces['CP-{}-sphere{}'.format(i + 1, i)]
        mdb.models['Model-1'].Tie(name='CP-{}-Part-cut-1-sphere{}'.format(i + 1, i), master=region1, slave=region2,
                                  positionToleranceMethod=COMPUTED, adjust=ON, constraintEnforcement=SURFACE_TO_SURFACE)


side_length = 0.1  # mm,长方体混凝土边长
# modeling
myModel = mdb.Model(name='Model-1')
mysketch_1 = myModel.ConstrainedSketch(name='mysketch_1', sheetSize=200.0)
mysketch_1.rectangle(point1=(0.0, 0.0), point2=(side_length, side_length))
myPart = myModel.Part(name='Part-Base', dimensionality=THREE_D, type=DEFORMABLE_BODY)
myPart.BaseSolidExtrude(sketch=mysketch_1, depth=side_length)
mdb.models['Model-1'].rootAssembly.Instance(dependent=ON, name='Part-Base-1',
                                            part=mdb.models['Model-1'].parts['Part-Base'])
# 给基质骨料等赋予材料属性
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
mdb.models['Model-1'].Material(name='Material-fiber')
mdb.models['Model-1'].materials['Material-fiber'].Density(table=((7800,),))
mdb.models['Model-1'].materials['Material-fiber'].Elastic(table=((200e9, 0.3),))
mdb.models['Model-1'].materials['Material-fiber'].SpecificHeat(table=((1.0,),))
mdb.models['Model-1'].materials['Material-fiber'].Expansion(table=((9.1e-06,),))
mdb.models['Model-1'].materials['Material-fiber'].Conductivity(table=((1.25,),))
# 生成立方体试块模型
file_aggregate = '/Code/CycleInputFile/data_aggregate.txt'
# 生成骨料
a = mdb.models['Model-1'].rootAssembly
bg = np.loadtxt(file_aggregate, delimiter=',', dtype=np.float32)
countg = len(open(file_aggregate, 'rU').readlines())
create_aggregate(bg, countg)
cut_aggregate(countg)  # 切割基质，将基质中骨料部分挖除
create_aggregate(bg, countg)  # 再次生产上一部中切除了骨料
# 生成纤维
bf = np.loadtxt('E:\Abaqus\Code\CycleInputFile\data_fibers.txt', delimiter=',',dtype=np.float32)
countf = len(open(r"/Code/MyCoding\Code for abaqus\Finish Version\data_fibers.txt", 'rU').readlines())
FiberLength = bf[0][5]  # 读取纤维的长度
part = mdb.models['Model-1'].Part(name="fibers", dimensionality=THREE_D, type=DEFORMABLE_BODY)
sketch = mdb.models['Model-1'].ConstrainedSketch(name="sketch", sheetSize=200)
sketch.Line(point1=(0.0, 0.0), point2=(FiberLength, 0.0))
part.BaseWire(sketch=sketch)
create_fibers(bf, countf)
mdb.models['Model-1'].HomogeneousSolidSection(name='Section-1', material='Material-Matrix', thickness=None)
mdb.models['Model-1'].TrussSection(name='Section-2', material='Material-fiber', area=1.54e-6)
mdb.models['Model-1'].HomogeneousSolidSection(name='Section-3', material='Material-Aggregate', thickness=None)
# 基质的截面属性赋予
p = mdb.models['Model-1'].parts['Part-cut']
cells = p.cells.findAt(((side_length, 0.666 * side_length, 0.666 * side_length),))
region = regionToolset.Region(cells=cells)
p.SectionAssignment(region=region, sectionName='Section-1', offset=0.0,
                    offsetType=MIDDLE_SURFACE, offsetField='',thicknessAssignment=FROM_SECTION)
# 纤维的截面属性赋予
p = mdb.models['Model-1'].parts['fibers']
edges = p.edges.findAt(((0.5 * FiberLength, 0.0, 0.0),))
region = p.Set(edges=edges, name='Set-fiberSection')
p.SectionAssignment(region=region, sectionName='Section-2', offset=0.0,
                    offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)
# 骨料截面赋予
assign_aggregate(countg)

# 分析步设置
mdb.models['Model-1'].HeatTransferStep(name='Step-1', previous='Initial', timePeriod=60, maxNumInc=100000,
                                       initialInc=0.01, minInc=1e-5, maxInc=10, deltmx=10, amplitude=STEP)
# 场输出设置
mdb.models['Model-1'].fieldOutputRequests['F-Output-1'].setValues(variables=('NT', 'TEMP', 'HFL', 'RFL'))
# 绝对零度和stefan常数设置
mdb.models['Model-1'].setValues(absoluteZero=-273.15, stefanBoltzmann=5.67e-8)
# 定义升温幅值
mdb.models['Model-1'].TabularAmplitude(name='Amp-1', timeSpan=STEP, smooth=SOLVER_DEFAULT,
                                       data=((0.0, 20.0), (60, 25)))
# 定义表面热交换和辐射
a = mdb.models['Model-1'].rootAssembly
s1 = a.instances['Part-cut-1'].faces
side1Faces1 = s1[0:6]
region = a.Surface(side1Faces=side1Faces1, name='Surf-all')
mdb.models['Model-1'].FilmCondition(name='Int-surChange',
                                    createStepName='Step-1', surface=region, definition=EMBEDDED_COEFF,
                                    filmCoeff=1500, filmCoeffAmplitude='', sinkTemperature=1.0,
                                    sinkAmplitude='Amp-1', sinkDistributionType=UNIFORM, sinkFieldName='')
mdb.models['Model-1'].RadiationToAmbient(name='Int-surRadiation',
                                         createStepName='Step-1', surface=region, radiationType=AMBIENT,
                                         distributionType=UNIFORM, field='', emissivity=0.8, ambientTemperature=1.0,
                                         ambientTemperatureAmp='Amp-1')
# 定义纤维集合
a = mdb.models['Model-1'].rootAssembly
fiberList = []
edgesFibers = a.instances['Part-fiber-0'].edges[0:1]
for i in range(countf):
    fiberList.append(a.instances['Part-fiber-{}'.format(i)].edges[0:1])
    if i > 0:
        edgesFibers = edgesFibers + fiberList[i]
    a.Set(edges=fiberList[i], name='Set-Fiber-{}'.format(i))


# 定义骨料集合
aggregateList = []
cellsAggregate = a.instances['sphere0'].cells[0:1]
for i in range(countg):
    aggregateList.append(a.instances['sphere{}'.format(i)].cells[0:1])
    if i > 0:
        cellsAggregate = cellsAggregate + aggregateList[i]
    a.Set(cells=aggregateList[i], name='Set-Aggregate-{}'.format(i))


# 定义基质集合
cellsMatrix = a.instances['Part-cut-1'].cells[0:1]
a.Set(cells=cellsAggregate, name='Set-Aggregates')
a.Set(cells=cellsMatrix, name='Set-Matrix')
a.Set(edges=edgesFibers, name='Set-Fibers')
# 定义预定义场
region = regionToolset.Region(edges=edgesFibers, cells=cellsAggregate + cellsMatrix)
mdb.models['Model-1'].Temperature(name='Predefined Field-1', createStepName='Initial', region=region,
                                  distributionType=UNIFORM,
                                  crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, magnitudes=(20.0,))
# 定义内置区域（纤维）
p = mdb.models['Model-1'].parts['Part-cut']
a = mdb.models['Model-1'].rootAssembly
regionFibers = a.Set(edges=edgesFibers, name='Set-Fibers')
mdb.models['Model-1'].EmbeddedRegion(name='Constraint-fibers',
                                     embeddedRegion=regionFibers, hostRegion=None, weightFactorTolerance=1e-06,
                                     absoluteTolerance=0.0, fractionalTolerance=0.05, toleranceMethod=BOTH)
# define tie
create_tie(countg)
# matrix mesh
p = mdb.models['Model-1'].parts['Part-cut']
session.viewports['Viewport: 1'].setValues(displayedObject=p)
elemType1 = mesh.ElemType(elemCode=DC3D8, elemLibrary=STANDARD)
elemType2 = mesh.ElemType(elemCode=DC3D6, elemLibrary=STANDARD)
elemType3 = mesh.ElemType(elemCode=DC3D4, elemLibrary=STANDARD)
c = p.cells
pickedRegions = (c[0:1],)
p.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2, elemType3))
pickedRegions = c[0:1]
p.setMeshControls(regions=pickedRegions, elemShape=TET, technique=FREE)
p.seedPart(size=0.01, deviationFactor=0.1, minSizeFactor=0.1)
p.generateMesh()
# fiber mesh
p = mdb.models['Model-1'].parts['fibers']
session.viewports['Viewport: 1'].setValues(displayedObject=p)
elemType1 = mesh.ElemType(elemCode=DC1D2, elemLibrary=STANDARD)
pickedRegions = (p.edges[0:1],)
p.setElementType(regions=pickedRegions, elemTypes=(elemType1,))
p.seedPart(size=0.0035, deviationFactor=0.1, minSizeFactor=0.1)
p.generateMesh()
# aggregate mesh
for i in range(countg):
    p = mdb.models['Model-1'].parts['sphere{}'.format(i)]
    session.viewports['Viewport: 1'].setValues(displayedObject=p)
    elemType1 = mesh.ElemType(elemCode=DC3D8, elemLibrary=STANDARD)
    elemType2 = mesh.ElemType(elemCode=DC3D6, elemLibrary=STANDARD)
    elemType3 = mesh.ElemType(elemCode=DC3D4, elemLibrary=STANDARD)
    c = p.cells
    cells = c[0:1]
    pickedRegions = (cells,)
    p.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2, elemType3))
    p.seedPart(size=0.005, deviationFactor=0.1, minSizeFactor=0.1)
    p.setMeshControls(regions=c[0:1], elemShape=TET, technique=FREE)
    p.generateMesh()
mdb.saveAs(pathName='/Workpace/Model-temp01.cae')

