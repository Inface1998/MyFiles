from abaqus import *
from abaqusConstants import *
from caeModules import *
import os
import numpy as np
from visualization import *
from odbAccess import *
import xlwt
import math

Mdb()
session.journalOptions.setValues(replayGeometry=INDEX, recoverGeometry=INDEX)
# session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)
session.viewports['Viewport: 1'].assemblyDisplay.geometryOptions.setValues(datumAxes=OFF)

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
        # if C ** 2 - 4 * A * B > -0.1 and C ** 2 - 4 * A * B < 0.001:  # 避免分子过小引起较大误差
        #     return False
        p1 = (2 * B * D - C * E) / (C ** 2 - 4 * A * B)
        q1 = (2 * A * E - C * D) / (C ** 2 - 4 * A * B)
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



def fibers_data(num, fiber_length):
    while True:
        # 防止钢纤维在外围区域堆积
        amend = 0
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
        if len(fibers) == 0 :
            fibers.append(line1)
        # 判断其他纤维是否与骨料相交
        elif len(fibers) != 0:
            if fiber_judgement(line1, fibers) :
                fibers.append(line1)
        if len(fibers) >= num:
            break



def create_fibers():
    for num in range(fiber_amount):
        x = b[num][0]
        y = b[num][1]
        z = b[num][2]
        angle_x = b[num][3]
        angle_z = b[num][4]
        if angle_x > 180:
            myAssembly.Instance(name='Part-fiber-solid-{}'.format(num), part=part, dependent=ON)
            myAssembly.translate(instanceList=('Part-fiber-solid-{}'.format(num),), vector=(x, y, z))
            myAssembly.rotate(instanceList=('Part-fiber-solid-{}'.format(num),), axisPoint=(x, y, z),
                              axisDirection=(0, 0, 1),angle=angle_x)
            myAssembly.rotate(instanceList=('Part-fiber-solid-{}'.format(num),), axisPoint=(x, y, z),
                              axisDirection=(-1, np.tan((90 - (angle_x - 180)) * np.pi / 180), 0),
                              angle=90 - angle_z)
        if angle_x < 180:
            myAssembly.Instance(name='Part-fiber-solid-{}'.format(num), part=part, dependent=ON)
            myAssembly.translate(instanceList=('Part-fiber-solid-{}'.format(num),), vector=(x, y, z))
            myAssembly.rotate(instanceList=('Part-fiber-solid-{}'.format(num),), axisPoint=(x, y, z),
                              axisDirection=(0, 0, 1), angle=angle_x)
            myAssembly.rotate(instanceList=('Part-fiber-solid-{}'.format(num),), axisPoint=(x, y, z),
                              axisDirection=(1, -np.tan((90 - angle_x) * np.pi / 180), 0),
                              angle=90 - angle_z)

# 定义立方体试块边长
side_length = 0.05      # 单位m
# 创建纤维
fibers = []
fiber_r = 0.0002        # 纤维半径
fiber_length = 0.015    # 纤维长度
fiber_amount = 325     # 纤维根数
fibers_data(fiber_amount, fiber_length)
file_fibers = "E:\Abaqus\Code\Code for abaqus\Code for abaqus\Finish Version\data_fibers.txt"
with open(file_fibers, 'w') as da:
    for i in range(len(fibers)):
        da.write('%.5f' % fibers[i][0][0] + "," +
                 '%.5f' % fibers[i][0][1] + "," +
                 '%.5f' % fibers[i][0][2] + "," +
                 '%.5f' % fibers[i][1][1] + "," +
                 '%.5f' % fibers[i][1][2] + "," +
                 '%.5f' % fibers[i][1][0])
        if i != len(fibers) - 1:
            da.write("\n")


# modeling
myModel = mdb.Model(name='Model-1')
mysketch_1 = myModel.ConstrainedSketch(name='mysketch_1', sheetSize=1.0)
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

mdb.models['Model-1'].Material(name='Material-fiber')
mdb.models['Model-1'].materials['Material-fiber'].Density(table=((7800,),))
mdb.models['Model-1'].materials['Material-fiber'].Elastic(table=((200e9, 0.3),))
mdb.models['Model-1'].materials['Material-fiber'].SpecificHeat(table=((1.0,),))
mdb.models['Model-1'].materials['Material-fiber'].Expansion(table=((9.1e-06,),))
mdb.models['Model-1'].materials['Material-fiber'].Conductivity(table=((1.25,),))

# 生成立方体试块模型
myAssembly = mdb.models['Model-1'].rootAssembly
# 生成纤维
b = np.loadtxt(file_fibers, delimiter=',',dtype=np.float32)
part = mdb.models['Model-1'].Part(name="fibers", dimensionality=THREE_D, type=DEFORMABLE_BODY)
sketch = mdb.models['Model-1'].ConstrainedSketch(name="sketch", sheetSize=1)
sketch.Line(point1=(0.0, 0.0), point2=(fiber_length, 0.0))
part.BaseWire(sketch=sketch)
create_fibers()
# 赋予纤维截面
p = mdb.models['Model-1'].parts['fibers']
mdb.models['Model-1'].TrussSection(name='Section-Fiber',
    material='Material-fiber', area=3.14e-08)
edges = p.edges.findAt(((0.25*fiber_length, 0.0, 0.0), ))
region = p.Set(edges=edges, name='Set-1')
p.SectionAssignment(region=region, sectionName='Section-Fiber', offset=0.0,
    offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)
# 赋予基质截面
p = mdb.models['Model-1'].parts['Part-Base']
mdb.models['Model-1'].HomogeneousSolidSection(name='Section-Matrix',
    material='Material-Matrix', thickness=None)
cells = p.cells.findAt(((side_length, 0.66*side_length, 0.66*side_length), ))
region = p.Set(cells=cells, name='Set-1')
p.SectionAssignment(region=region, sectionName='Section-Matrix', offset=0.0,
    offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)
# 分析步设置
mdb.models['Model-1'].HeatTransferStep(name='Step-1', previous='Initial', timePeriod=5.0, maxNumInc=30000,
                                       initialInc=0.01, minInc=0.005, maxInc=0.1, deltmx=0.5, amplitude=STEP)
# 场输出设置
mdb.models['Model-1'].fieldOutputRequests['F-Output-1'].setValues(variables=('NT', 'TEMP'))
# 绝对零度和stefan常数设置
mdb.models['Model-1'].setValues(absoluteZero=-273.15, stefanBoltzmann=5.67e-8)
# 定义温度幅值
mdb.models['Model-1'].TabularAmplitude(name='Amp-temp', timeSpan=STEP,
    smooth=SOLVER_DEFAULT, data=((0.0, 20.0), (5.0, 200.0)))
# 定义表面热交换
a = mdb.models['Model-1'].rootAssembly
s1 = a.instances['Part-Base-1'].faces
side1Faces1 = s1[1:3]+s1[4:5]
# side1Faces1 = s1[0:6]
region = a.Surface(side1Faces=side1Faces1, name='Surf-total3')
mdb.models['Model-1'].FilmCondition(name='Int-film', createStepName='Step-1',
    surface=region, definition=EMBEDDED_COEFF, filmCoeff=1500,
    filmCoeffAmplitude='', sinkTemperature=1.0, sinkAmplitude='Amp-temp',
    sinkDistributionType=UNIFORM, sinkFieldName='')
# 定义表面热辐射
mdb.models['Model-1'].RadiationToAmbient(name='Int-radi',
    createStepName='Step-1', surface=region, radiationType=AMBIENT,
    distributionType=UNIFORM, field='', emissivity=0.8, ambientTemperature=1.0,
    ambientTemperatureAmp='Amp-temp')
# 将纤维定义为一个集合
a = mdb.models['Model-1'].rootAssembly
fiberList = []
edgesFibers = a.instances['Part-fiber-solid-0'].edges[0:1]
for i in range(fiber_amount):
    fiberList.append(a.instances['Part-fiber-solid-{}'.format(i)].edges[0:1])
    if i >0:
        edgesFibers = edgesFibers + fiberList[i]


# 内置区域设置
regionFibers = a.Set(edges = edgesFibers,name = 'SetAllFibers')
mdb.models['Model-1'].EmbeddedRegion(name='Constraint-1',
    embeddedRegion=regionFibers, hostRegion=None, weightFactorTolerance=1e-06,
    absoluteTolerance=0.0, fractionalTolerance=0.05, toleranceMethod=BOTH)
# 将整体定义为一个集合
c1 = a.instances['Part-Base-1'].cells
cells1 = c1[0:1]
regionAll = a.Set(edges = edgesFibers,cells = cells1, name = 'SetAll')
mdb.models['Model-1'].Temperature(name='Predefined Field-1',
    createStepName='Initial', region=regionAll, distributionType=UNIFORM,
    crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, magnitudes=(20.0, ))
# 定义边界条件
# 负面法线为x轴的面限制x轴方向位移
f1 = a.instances['Part-Base-1'].faces[0:1]
region = a.Set(faces=f1, name='Set-x')
mdb.models['Model-1'].DisplacementBC(name='BC-1', createStepName='Initial',
    region=region, u1=SET, u2=UNSET, u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET,
    amplitude=UNSET, distributionType=UNIFORM, fieldName='', localCsys=None)
# 负面法线为y轴的面限制y轴方向位移
f2 = a.instances['Part-Base-1'].faces[3:4]
region = a.Set(faces=f2, name='Set-y')
mdb.models['Model-1'].DisplacementBC(name='BC-2', createStepName='Initial',
    region=region, u1=UNSET, u2=SET, u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET,
    amplitude=UNSET, distributionType=UNIFORM, fieldName='', localCsys=None)
# 负面法线为z轴的面限制z轴方向位移
f3 = a.instances['Part-Base-1'].faces[5:6]
region = a.Set(faces=f3, name='Set-z')
mdb.models['Model-1'].DisplacementBC(name='BC-3', createStepName='Initial',
    region=region, u1=UNSET, u2=UNSET, u3=SET, ur1=UNSET, ur2=UNSET, ur3=UNSET,
    amplitude=UNSET, distributionType=UNIFORM, fieldName='', localCsys=None)
# Matrix网格划分
p = mdb.models['Model-1'].parts['Part-Base']
session.viewports['Viewport: 1'].setValues(displayedObject=p)
elemType1 = mesh.ElemType(elemCode=DC3D8, elemLibrary=STANDARD)
elemType2 = mesh.ElemType(elemCode=DC3D6, elemLibrary=STANDARD)
elemType3 = mesh.ElemType(elemCode=DC3D4, elemLibrary=STANDARD)
cells = p.cells[0:1]
pickedRegions =(cells, )
p.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2, elemType3))
p.seedPart(size=0.005, deviationFactor=0.1, minSizeFactor=0.1)
p.generateMesh()
# fiber网格划分
p = mdb.models['Model-1'].parts['fibers']
session.viewports['Viewport: 1'].setValues(displayedObject=p)
elemType1 = mesh.ElemType(elemCode=DC1D2, elemLibrary=STANDARD)
edges = p.edges[0:1]
pickedRegions =(edges, )
p.setElementType(regions=pickedRegions, elemTypes=(elemType1, ))
p.seedPart(size=0.0015, deviationFactor=0.1, minSizeFactor=0.1)
p.generateMesh()
# 完成
mdb.Job(name='Job-1', model='Model-1', numCpus=8,numDomains=8, numGPUs=0)
mdb.jobs['Job-1'].submit()
# 计算开始
myJob.waitForCompletion()

