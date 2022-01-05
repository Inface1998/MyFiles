#!/user/bin/python
# -* - coding:UTF-8 -*-
from Code.MyCoding.MyTool.display.parseodbinfo import readOdbInfo
import logging

nodeData, elementData, frameData = readOdbInfo('/Code/CycleInputFile/OdbText.txt')
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
logging.basicConfig(level=logging.INFO, filename='../../../source/chapter 5/log.txt', format=LOG_FORMAT, datefmt=DATE_FORMAT)
logging.info(frameData[0].nodeDisplacementData)
logging.shutdown()
# 已经读入数据，现在可以创建 ODB 文件
from odbAccess import *
# 移除前面调试过程中生成的 ODB 文件
import os, osutils
if os.path.exists('../../../source/chapter 5/TestOdb.odb'):
    osutils.remove('TestOdb.odb')


odb = Odb('TestOdb1', analysisTitle='create Odb', path='../../../source/chapter 5/TestOdb.odb')
part1 = odb.Part(name='part-1', embeddedSpace=THREE_D, type=DEFORMABLE_BODY)
part1.addNodes(nodeData=nodeData, nodeSetName='nset-1')
del nodeData
# part1.addElements(elementData=elementData, type='CAX4RH', elementSetName='eset-1')
part1.addElements(elementData=elementData, type='DC3D4', elementSetName='eset-1')
del elementData
# 创建部件实例
instance1 = odb.rootAssembly.Instance(name='part-1-1', object=part1)
# 根据场变量数据创建分析步和框架
step1 = odb.Step(name='step-1', description='',domain=TIME, timePeriod=3.323)

for i in range(len(frameData)):
    frame = step1.Frame(frameId=i, frameValue=0.1 * i,
                        description=frameData[i].description)
    # 向 ODB 文件中添加数据
    uField = frame.FieldOutput(name='TEMP', description='TempDisplay', type=VECTOR)#VECTOR
    uField.addData(position=NODAL, instance=instance1,labels=frameData[i].nodeDisplacementLabelData,
        data=frameData[i].nodeDisplacementData)

del frameData
# 在 Visualization 功能模块中设置默认的绘图模式是为场变量绘制变形图
step1.setDefaultDeformedField(uField)
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
