# -*- coding: UTF-8 -*-    
# 作者：zhangHJ
# 日期：2021/9/6  18:17

# 在命令交互行（Abaqus / CAE最下方）输入以下指令：

# session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)

# 这种方式在rpy文件中输出的索引格式为findAt() + 坐标值。即第二种方式。



# 在命令交互行（Abaqus / CAE最下方）输入以下指令 ：

# session.journalOptions.setValues(replayGeometry=INDEX, recoverGeometry=INDEX

# 该方式会以元素的实际索引号作为对象的索引方式，即第三种方式。