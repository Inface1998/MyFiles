#!/user/bin/python
# -* - coding:UTF-8 -*-
import string


# 定义各种数据类型的类
# 定义类 FrameData
class FrameData:
    def __init__(self):
        self.description = ''
        self.nodeDisplacementLabelData = []  # 节点编号列表
        # 当type为VECTOR时data存储x y z三个方向位移，当type为SCALAR时存储X Y Z 坐标和值
        self.nodeDisplacementData = []  # 由节点位移元组(X, Y, Z)组成的列表


# 定义类 Data
class Data:
    def __init__(self):
        self.data = []


# 定义类DisplacementData
class DisplacementData(Data):
    def append(self, line):
        label, TEMP = eval(line)
        self.data[-1].nodeDisplacementLabelData.append(label)
        self.data[-1].nodeDisplacementData.append((TEMP,), )
    def newFrame(self, line):
        description = line[6:]
        self.data.append(FrameData())
        self.data[-1].description = description
        print 'Frame: %2d  %s' % (len(self.data) - 1, description)


# 定义类 NodeData
class NodeData(Data):
    def append(self, line):
        label, nodeX, nodeY, nodeZ = eval(line)
        self.data.append((label, nodeX, nodeY, nodeZ))
    # 定义类ElementData


class ElementData(Data):
    def append(self, line):
        label, c1, c2, c3, c4 = eval(line)
        self.data.append((label, c1, c2, c3, c4))


def readOdbInfo(filePath):
    """
    返回元组 (nodeDate, elementData, frameData)
    nodeData    - 由元组(nodeLabel, nodeX, nodeY)组成的列表
    elementData - 由元组(elementLabel, connectivity1, 2, 3, 4)组成的列表
    frameData   - 由FrameData对象组成的列表
    """
    # 创建数据结构来保存读入的数据
    nodeData = NodeData()
    matrixElement = ElementData()
    aggregateElement = ElementData()
    matrixVapor = DisplacementData()
    aggregateVapor = DisplacementData()
    print 'Parsing file:',
    odbFromTextFile = open(filePath)
    odbFromTextLines = odbFromTextFile.readlines()
    data = None
    for line in odbFromTextLines:
        line = string.strip(line)  # 移除尾部新行
        if line == '' or line[:2] == '**':
            continue
        elif line == '*Node matrixVapor':
            data = matrixVapor
        elif line == '*Node aggregateVapor':
            data = aggregateVapor
        elif line == '*Node':
            data = nodeData
        elif line == '*MatrixElement':
            data = matrixElement
        elif line == '*AggregateElement':
            data = aggregateElement
        elif line[:6] == 'Frame:':
            # 创建新的 FrameData 对象
            data.newFrame(line)
        else:
            data.append(line)
    print 'Number of nodes:   ', len(nodeData.data)
    print 'Number of elements:', len(matrixElement.data)
    return (nodeData.data, matrixElement.data, aggregateElement.data, matrixVapor.data, aggregateVapor.data)


import os, logging, osutils

nodeData, matrixElement, aggregateElement, matrixVapor, aggregateVapor = readOdbInfo('E:/Abaqus/Code/CycleInputFile/OdbText.txt')
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
logging.basicConfig(level=logging.INFO, filename='log.txt', format=LOG_FORMAT, datefmt=DATE_FORMAT)
logging.info(matrixVapor[0].nodeDisplacementData)
logging.info(aggregateVapor[0].nodeDisplacementData)
logging.shutdown()
# 已经读入数据，现在可以创建 ODB 文件
# 移除前面调试过程中生成的 ODB 文件
if os.path.exists('TestOdb.odb'):
    osutils.remove('TestOdb.odb')

from odbAccess import *
odb = Odb('TestOdb1', analysisTitle='create Odb', path='TestOdb.odb')
part1 = odb.Part(name='part-1', embeddedSpace=THREE_D, type=DEFORMABLE_BODY)
part2 = odb.Part(name='part-2', embeddedSpace=THREE_D, type=DEFORMABLE_BODY)
part1.addNodes(nodeData=nodeData, nodeSetName='nset-1')
part2.addNodes(nodeData=nodeData, nodeSetName='nset-2')
del nodeData
# part1.addElements(elementData=matrixData, type='CAX4RH', elementSetName='eset-1')
part1.addElements(elementData=matrixElement, type='DC3D4', elementSetName='eset-1')
part2.addElements(elementData=aggregateElement, type='DC3D4', elementSetName='eset-2')
del matrixElement, aggregateElement
# 创建部件实例
instance1 = odb.rootAssembly.Instance(name='part-1-1', object=part1)
instance2 = odb.rootAssembly.Instance(name='part-2-1', object=part2)
# 根据场变量数据创建分析步和框架
step1 = odb.Step(name='step-1', description='', domain=TIME, timePeriod=10)
for i in range(len(matrixVapor)):
    frame = step1.Frame(frameId=i, frameValue=0.1 * i,
                        description=matrixVapor[i].description)
    # 向 ODB 文件中添加数据
    uField = frame.FieldOutput(name='TEMP', description='TempDisplay', type=SCALAR)  # VECTOR
    uField.addData(position=NODAL, instance=instance1, labels=matrixVapor[i].nodeDisplacementLabelData,
                   data=matrixVapor[i].nodeDisplacementData)
    uField.addData(position=NODAL, instance=instance2, labels=aggregateVapor[i].nodeDisplacementLabelData,
                   data=aggregateVapor[i].nodeDisplacementData)

del matrixVapor,aggregateVapor

# 在 Visualization 功能模块中设置默认的绘图模式是为场变量绘制变形图
# step1.setDefaultDeformedField(uField)
# 保存 ODB 文件
odb.save()
odb.close()
# 下列代码行实现自动后处理，输出 U1和U2的png图以及输出二者的动画
# from abaqusConstants import *
#
# o1 = session.openOdb(name='TestOdb.odb')
# vp = session.viewports['Viewport: 1']
# vp.setValues(displayedObject=o1)
# vp.view.setValues(session.views['Front'])
# vp.odbDisplay.display.setValues(plotState=(CONTOURS_ON_DEF,))
# vp.odbDisplay.setPrimaryVariable(
#     variableLabel='U', outputPosition=NODAL, refinement=(COMPONENT, 'U1'))
# session.printToFile(fileName='U1', format=PNG, canvasObjects=(vp,))
# session.animationController.setValues(animationType=TIME_HISTORY, viewports=('Viewport: 1',))
# session.animationController.play(duration=UNLIMITED)
# session.imageAnimationOptions.setValues(vpDecorations=ON, vpBackground=OFF, compass=OFF)
# session.writeImageAnimation(fileName='U1_animate.avi', format=AVI, canvasObjects=(vp,))
# vp.odbDisplay.setPrimaryVariable(variableLabel='U', outputPosition=NODAL, refinement=(COMPONENT, 'U2'))
# session.printToFile(fileName='U2.png', format=PNG, canvasObjects=(vp,))
# session.imageAnimationOptions.setValues(vpDecorations=OFF, vpBackground=OFF, compass=OFF, timeScale=1, frameRate=1)
# session.writeImageAnimation(fileName='U2_animate', format=AVI, canvasObjects=(vp,))
