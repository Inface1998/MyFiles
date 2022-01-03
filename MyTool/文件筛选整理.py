# -*- coding: UTF-8 -*-    
# 作者：zhangHJ
# 日期：2021/3/14  20:22
import os
import shutil
import time


def move_file(targetDir):
    # 删除.文件
    # 移动odb，cae文件到新文件夹test中
    localtime = time.localtime(time.time())
    T = str(localtime.tm_mon) + "-" + str(localtime.tm_mday) + "-" + str(localtime.tm_hour)
    newDir = os.path.join(targetDir, T)
    try:
        os.mkdir(newDir)
    except:
        print('diretory "test" already exist')
    infor = os.listdir(targetDir)
    for item in infor:
        print(item)
        if item == "NNE.xlsx":
            continue
        tempdir = os.path.join(targetDir, item)
        print(tempdir)
        extStr = os.path.splitext(item)[1]
        print(extStr)
        if os.path.isfile(tempdir):
            if extStr == '.py' or extStr == '.bat':
                continue
            elif extStr == '.cae' or extStr == '.odb' or extStr == '.inp' or extStr == '.jnl' or extStr == '.xlsx':
                shutil.move(tempdir, newDir)
            else:
                os.remove(tempdir)


targetDir1 = 'E:/Abaqus/Workpace'
move_file(targetDir1)
targetDir2 = "E:/Abaqus/Code/CycleOutputFile"
move_file(targetDir2)
