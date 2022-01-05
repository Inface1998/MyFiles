#!/user/bin/python
# -* - coding:UTF-8 -*-
import sys, os, string

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
        label, NodeX, NodeY, NodeZ, TEMP = eval(line)
        self.data[-1].nodeDisplacementLabelData.append(label)
        self.data[-1].nodeDisplacementData.append((TEMP, 0, 0), )

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
    elementData = ElementData()
    displacementData = DisplacementData()

    print 'Parsing file:',
    odbFromTextFile = open(filePath)
    odbFromTextLines = odbFromTextFile.readlines()

    data = None

    for line in odbFromTextLines:
        line = string.strip(line)  # 移除尾部新行
        if line == '' or line[:2] == '**':
            continue
        elif line == '*Node displacement':
            data = displacementData
            print 'Now Reading: Node displacement'
        elif line == '*Node':
            data = nodeData
            print 'Now Reading: Node'
        elif line == '*Element':
            data = elementData
            print 'Now Reading: Element'
        elif line[:6] == 'Frame:':
            # 创建新的 FrameData 对象
            data.newFrame(line)
        else:
            data.append(line)

    print 'Number of nodes:   ', len(nodeData.data)
    print 'Number of elements:', len(elementData.data)

    return (nodeData.data, elementData.data, displacementData.data)
