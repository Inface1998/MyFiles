# -*- coding: UTF-8 -*-    
# 作者：zhangHJ
# 日期：2022/2/8  20:03
import os
import time

work_path = os.getcwd()
excel_path = work_path + "\OutputExcel"
localtime = time.localtime(time.time())
T = str(localtime.tm_mon) + "-" + str(localtime.tm_mday) + "-" + str(localtime.tm_hour)
excel_path = os.path.join(excel_path, T)
print excel_path