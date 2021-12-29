# -*- coding: UTF-8 -*-    
# 作者：zhangHJ
# 日期：2021/12/14  15:36
from abaqus import *
from abaqusConstants import *
from viewerModules import *
import abq_ExcelUtilities.excelUtilities
import sys
session.journalOptions.setValues(replayGeometry=INDEX, recoverGeometry=INDEX)
session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)
n = 100
for i in range(n):
    odb = session.odbs['E:/Abaqus/Workpace/Myfile12-14-15/Job-Temp0{}.odb'.format(n+1)]
    xyList = xyPlot.xyDataListFromField(odb=odb, outputPosition=NODAL, variable=((
        'NT11', NODAL), ), nodeLabels=(('PART-1-1', ('1', )), ))
    abq_ExcelUtilities.excelUtilities.XYtoExcel(
        xyDataNames='_NT11 PI: PART-1-1 N: 1', trueName='From Current XY Plot')