# -*- coding: UTF-8 -*-    
# 作者：zhangHJ
# 日期：2021/11/1  19:42
import shutil
import os
thisPath = os.getcwd()
infor = os.listdir(thisPath)
for item in infor:
    tempdir = os.path.join(thisPath, item)
    extStr = os.path.splitext(item)[1]
    if os.path.isfile(tempdir):
        if extStr == '.py' or extStr == '.bat' or extStr == '.txt':
            print "yes"
            print tempdir
