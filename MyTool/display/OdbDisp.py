# -*- coding: UTF-8 -*-    
# 作者：zhangHJ
# 日期：2022/1/5  10:33
# 已经读入数据，现在可以创建 ODB 文件
from odbAccess import *
# 移除前面调试过程中生成的 ODB 文件
import os, osutils
if os.path.exists('TestOdb.odb'):
    osutils.remove('TestOdb.odb')

odb = Odb('TestOdb', analysisTitle='create Odb', path='TestOdb.odb')
part1 = odb.Part(name='part-1', embeddedSpace=THREE_D, type=DEFORMABLE_BODY)
part1.addNodes(nodeData=nodeData, nodeSetName='nset-1')
del nodeData

part1.addElements(elementData=elementData, type='CAX4RH', elementSetName='eset-1')
del elementData
# 创建部件实例
instance1 = odb.rootAssembly.Instance(name='part-1-1', object=part1)
# 根据场变量数据创建分析步和框架
step1 = odb.Step(name='step-1', description='',domain=TIME, timePeriod=3.323)

for i in range(len(frameData)):
    frame = step1.Frame(frameId=i, frameValue=0.1 * i,
                        description=frameData[i].description)
    # 向 ODB 文件中添加节点位移数据
    uField = frame.FieldOutput(name='U', description='Displacements', type=VECTOR)
    uField.addData(position=NODAL, instance=instance1, labels=frameData[i].nodeDisplacementLabelData,
                   data=frameData[i].nodeDisplacementData)


del frameData
# 在 Visualization 功能模块中设置默认的绘图模式是为场变量绘制变形图
step1.setDefaultDeformedField(uField)
# 保存 ODB 文件
odb.save()
odb.close()