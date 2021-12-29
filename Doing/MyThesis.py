# -*- coding: UTF-8 -*-    
# 作者：zhangHJ
# 日期：2021/11/19  12:35
from abaqus import *
from abaqusConstants import *
from caeModules import *
from odbAccess import *
from visualization import *
import os
import openpyxl
import xlwt
import xlrd
import math
import time
import sys
import logging

def interp(y1, y2, x1, x2, x):
    y = (y2 - y1) / (x2 - x1) * (x - x1) + y1
    return y


def cal_initial(finiv):
    with open("E:\Abaqus\Code\CycleInputFile\Condition_mass.txt") as f:
        text = f.readlines()
        sf = float(text[0].split()[1])  # 硅灰替代率
        hydc = float(text[1].split()[1])  # 水泥水化度
        hydsf = float(text[2].split()[1])  # 硅灰的水化度
        wc = float(text[3].split()[1])  # 水灰比
        dsf = float(text[4].split()[1])  # 硅灰密度
        Em = float(text[5].split()[1])  # 基质的弹性模量
        Eag = float(text[6].split()[1])  # 骨料的弹性模量
        Sd = float(text[7].split()[1])  # 初始饱和度
        Dc0 = float(text[8].split()[1])  # 最小孔隙直径
        Dc1 = float(text[8].split()[1])  # 最大孔隙直径
        fvAFt = float(text[10].split()[1])  # 钙矾石体积分数
        fvCH = float(text[11].split()[1])  # CH体积分数
        fvCSH = float(text[12].split()[1])  # CSH体积分数
        inte = float(text[13].split()[1])  # 完成度
        ftm = float(text[14].split()[1])  # 基质抗拉强度
        fta = float(text[15].split()[1])  # 骨料抗拉强度
    # volume fractions of nomal C-S-H
    CSH = 0.68 * fvCSH * hydc * (1.0 - sf) / (wc + 0.32 * (1.0 - sf) + sf / dsf)
    # volume fractions of pozzolanic C-S-H
    pCSH = 3.77 * sf * hydsf / dsf / (wc + 0.32 * (1.0 - sf) + sf / dsf)
    # volume fraction of CH
    CH = (0.68 * fvCH * hydc * (1.0 - sf) - 1.35 * sf * hydsf / dsf) / (wc + 0.32 * (1.0 - sf) + sf / dsf)
    # volume fraction of AFt
    AFt = 0.68 * fvAFt * hydc * (1.0 - sf) / (wc + 0.32 * (1.0 - sf) + sf / dsf)
    # volume fraction of unhydrated cement
    CE = (1.0 - hydc) * 0.32 * (1.0 - sf) / (wc + 0.32 * (1.0 - sf) + sf / dsf)
    # volume fraction of unhydrated Silica fume
    SF = sf * (1.0 - hydsf) / dsf / (wc + 0.32 * (1.0 - sf) + sf / dsf)
    # volume fraction of capillary pores
    CP = 1.0 - CSH - pCSH - CH - AFt - CE - SF
    # increased volume fraction of capillary pores by fully decomposition
    CPF = 0.51633 * AFt + 0.5448 * CH + 0.19 / (0.68 * fvCSH) * CSH + 0.19 * pCSH + 0.2589 * (
            (1.0 - 0.19 / (0.68 * fvCSH)) * CSH + 0.81 * pCSH)
    # when the conversion degree of CSH is 30.7%, the increased volume fraction of capillary pores: for critical pore diameter calculation
    CP2 = 0.51633 * AFt + 0.5448 * CH + (0.19 / (0.68 * fvCSH) * CSH + 0.19 * pCSH + 0.2589 * (
            (1.0 - 0.19 / (0.68 * fvCSH)) * CSH + 0.81 * pCSH)) * 0.307
    # decompostion degree of CP2
    CP2D = CP2 / CPF
    # pore volume fraction increased by fully decomposition of AFt and CH
    CPAFt = 0.51633 * AFt
    CPCH = 0.5448 * CH
    with open(finiv, "w") as f:
        f.write("the initial volume fraction of contents of hardened cement paste\n")
        f.write("volume fraction of nomal C-S-H     {}\n".format(CSH))
        f.write("volume fraction of pozzolanic C-S-H    {}\n".format(pCSH))
        f.write("volume fraction of CH		{}\n".format(CH))
        f.write("volume fraction of AFt		{}\n".format(AFt))
        f.write("volume fraction of unhydrated cement		{}\n".format(CE))
        f.write("volume fraction of unhydrated Silica fume		{}\n".format(SF))
        f.write("volume fraction of capillary pores		{}\n".format(CP))
        f.write("volume fraction of capillary pores increased by fully decomposition		{}\n".format(CPF))
        f.write("volume fraction of capillary pores increased by fully decomposition of AFt		{}\n".format(CPAFt))
        f.write("volume fraction of capillary pores increased by fully decomposition of CH		{}\n".format(CPCH))
        f.write("volume fraction of capillary pores increased at 600oC		{}\n".format(CP2))
        f.write("decomposition degree at 600oC		{}\n".format(CP2D))
    for i in range(NE):
        # volume fraction of nomal C-S-H
        elemdh[i][1] = CSH
        # volume fraction of pozzoelanic C-S-H
        elemdh[i][2] = pCSH
        # volume fraction of CH
        elemdh[i][3] = CH
        # volume fraction of AFt
        elemdh[i][4] = AFt
        # volume fraction of unhydrated cement
        elemdh[i][5] = CE
        # volume fraction of unhydrated Silica fume
        elemdh[i][6] = SF
        # volume fraction of capillary pores
        elemdh[i][7] = CP
    return CSH, pCSH, CH, AFt, CE, SF, CP, CPF, CP2, CP2D, CPAFt, CPCH, sf, hydc, hydsf, wc, dsf, \
           Em, Eag, Sd, Dc0, Dc1, fvAFt, fvCH, fvCSH, inte, ftm, fta


def submit_job(i, thisTempCae):
    jobName = "Job-temp0{}".format(i + 1)
    myJob = mdb.Job(name=jobName, model='Model-1', numCpus=8, numDomains=8, numGPUs=0)
    myJob.submit()
    myJob.waitForCompletion()
    mdb.saveAs(pathName=thisTempCae)


def output_temp(odb_name,excel1,excel2):
    # 输出节点温度
    wb = openpyxl.load_workbook(excel1)
    sheet1 = wb.get_sheet_by_name('AllNode')
    odb = openOdb(path=odb_name)
    lastFrame = odb.steps['Step-1'].frames[-1]  # 创建变量lastFrame，得到载荷步Step-1的最后一帧
    displacement = lastFrame.fieldOutputs['NT11']  # 创建变量displacement，得到最后一帧的温度场数据
    center = odb.rootAssembly.instances['PART-1-1'].nodeSets['SET-ALL']
    centerDisplacement = displacement.getSubset(region=center)
    sheet1.cell(1,5,"Temp")
    for i in range(NN):
        data = centerDisplacement.values[i].data
        sheet1.cell(i+2,5,data)
    wb.save(excel2)
    wb.close()
    odb.close()


def calc_element(excel2):
    # 计算Element温度
    wb = openpyxl.load_workbook(excel2)
    sheet1 = wb.get_sheet_by_name('AllNode')
    sheet2 = wb.get_sheet_by_name('MElement')
    sheet3 = wb.get_sheet_by_name('AElement')
    for i in range(NME):
        node_temp = []
        node_x = []
        node_y = []
        node_z = []
        for j in range(2, 6):
            node = sheet2.cell(i + 2, j).value
            node_x.append(sheet1.cell(node + 1, 2).value)
            node_y.append(sheet1.cell(node + 1, 3).value)
            node_z.append(sheet1.cell(node + 1, 4).value)
            node_temp.append(sheet1.cell(node + 1, 5).value)
        sheet2.cell(i + 2, 6, 0.25 * (node_x[0] + node_x[1] + node_x[2] + node_x[3]))
        sheet2.cell(i + 2, 7, 0.25 * (node_y[0] + node_y[1] + node_y[2] + node_y[3]))
        sheet2.cell(i + 2, 8, 0.25 * (node_z[0] + node_z[1] + node_z[2] + node_z[3]))
        sheet2.cell(i + 2, 9, 0.25 * (node_temp[0] + node_temp[1] + node_temp[2] + node_temp[3]))
    for i in range(NAE):
        node_temp = []
        node_x = []
        node_y = []
        node_z = []
        for j in range(2, 6):
            node = sheet3.cell(i + 2, j).value
            node_x.append(sheet1.cell(node + 1, 2).value)
            node_y.append(sheet1.cell(node + 1, 3).value)
            node_z.append(sheet1.cell(node + 1, 4).value)
            node_temp.append(sheet1.cell(node + 1, 5).value)
        sheet3.cell(i + 2, 6, 0.25 * (node_x[0] + node_x[1] + node_x[2] + node_x[3]))
        sheet3.cell(i + 2, 7, 0.25 * (node_y[0] + node_y[1] + node_y[2] + node_y[3]))
        sheet3.cell(i + 2, 8, 0.25 * (node_z[0] + node_z[1] + node_z[2] + node_z[3]))
        sheet3.cell(i + 2, 9, 0.25 * (node_temp[0] + node_temp[1] + node_temp[2] + node_temp[3]))
    wb.save(excel2)
    wb.close()


def calc_decomposition(excel_name, last_excel):
    wb1 = openpyxl.load_workbook(last_excel)
    wb2 = openpyxl.load_workbook(excel_name)
    sheet1 = wb1["MElement"]
    sheet2 = wb2["MElement"]
    for i in range(NE):
        if step == 0:
            elemp[i][4] = 20
        else:
            elemp[i][4] = sheet1.cell(i + 2, 9).value
        # 计算单元平均温度以用于热分解计算
        elemp[i][5] = sheet2.cell(i + 2, 9).value
        elemp[i][3] = 0.5 * (elemp[i][4] + elemp[i][5])
        # AFt decomposition
        if (elemp[i][3] > 70.0):
            if (elemdh[i][8] < 1.0):
                elemdh[i][8] = elemdh[i][8] + 1.66e4 * math.exp(-7.0965e3 / (elemp[i][3] + 273.15)) * math.sqrt(
                    1.0 - elemdh[i][8]) * TG
            if (elemdh[i][8] > 1.0):
                elemdh[i][8] = 1.0
        # CH decomposition
        if (elemp[i][3]  > 438):
            if (elemdh[i][9] == 0.0):
                elemdh[i][9] = 0.004
            if (elemdh[i][9] < 0.5):
                elemdh[i][9] = elemdh[i][9] + 1.516e7 * math.exp(-1.527e4 / (elemp[i][3] + 273.15)) * math.sqrt(
                    elemdh[i][9]) * TG
            elif (elemdh[i][9] >= 0.5 and elemdh[i][9] < 1.0):
                elemdh[i][9] = elemdh[i][9] + 1.516e7 * math.exp(-1.527e4 / (elemp[i][3] + 273.15)) * math.sqrt(
                    1.0 - elemdh[i][9]) * TG
            if (elemdh[i][9] > 1.0):
                elemdh[i][9] = 1.0
        # CSH decomposition
        ra = 1.0 - elemdh[i][10]
        if (elemp[i][3] >= 600.0 and elemp[i][3] <= 700.0):
            if (elemdh[i][10] == 0.0):
                elemdh[i][10] = 0.005
                ra = 1.0 - elemdh[i][10]
            if (elemdh[i][10] > 0.307):
                d600 = 0.0
            else:
                t = 0.0
                for i in range(30):
                    t1 = t - (-1.0e-6 * pow(t, 3) + 0.0013 * pow(t, 2) - 0.36 * t + 97.72 - ra * 100) / (
                            -3e-6 * pow(t, 2) + 0.0026 * t - 0.36)
                    if (abs((t1 - t) / t1) <= ERRO):
                        break
                    else:
                        t = t1
                t600 = t1
                d600 = (3e-6 * pow(t600, 2) - 0.0026 * t600 + 0.36) / 100
            if (elemdh[i][10] > 0.744):
                d700 = 0.0
            else:
                t = 0.0
                for i in range(30):
                    t1 = t - (-2.0e-6 * pow(t, 3) + 0.002 * pow(t, 2) - 0.67 * t + 100.61 - ra * 100) / (
                            -6e-6 * pow(t, 2) + 0.004 * t - 0.67)
                    if (abs((t1 - t) / t1) <= ERRO):
                        break
                    else:
                        t = t1
                t700 = t1
                d700 = (6e-6 * pow(t700, 2) - 0.004 * t700 + 0.67) / 100
            if (elemdh[i][10] < 1.0):
                elemdh[i][10] = elemdh[i][10] + interp(d600, d700, 600, 700, elemp[i][3]) * TG / 60
            else:
                elemdh[i][10] = 1.0
        elif (elemp[i][3] > 700.0 and elemp[i][3] <= 800.0):
            if (elemdh[i][10] > 0.744):
                d700 = 0.0
            else:
                t = 0.0
                for j in range(30):
                    t1 = t - (-2.0e-6 * pow(t, 3) + 0.002 * pow(t, 2) - 0.67 * t + 100.61 - ra * 100) / (
                            -6e-6 * pow(t, 2) + 0.004 * t - 0.67)
                    if (abs((t1 - t) / t1) <= ERRO):
                        break;
                    else:
                        t = t1
                t700 = t1
                d700 = (6e-6 * pow(t700, 2) - 0.004 * t700 + 0.67) / 100.0
            if (elemdh[i][10] >= 0.9625):
                d800 = (1.0e-7 * pow(60.0, 4) - 3.2e-5 * pow(60.0, 3) + 0.0045 * pow(60.0,
                                                                                     2) - 0.26 * 60.0 + 5.47) / 100.0
            else:
                t = 0.0
                for i in range(30):
                    t1 = t - (-2.0e-8 * pow(t, 5) + 8.0e-6 * pow(t, 4) - 0.0015 * pow(t, 3) + 0.138 * pow(t,
                                                                                                          2) - 5.47 * t + 99.82 - ra * 100) / (
                                 -1.0e-7 * pow(t, 4) + 3.2e-5 * pow(t, 3) - 0.0045 * pow(t, 2) + 0.26 * t - 5.47)
                    if (abs((t1 - t) / t1) <= ERRO):
                        break
                    else:
                        t = t1
                t800 = t1
                d800 = (1.0e-7 * pow(t800, 4) - 3.2e-5 * pow(t800, 3) + 0.0045 * pow(t800,
                                                                                     2) - 0.26 * t800 + 5.47) / 100.0
            if (elemdh[i][10] < 1.0):
                elemdh[i][10] = elemdh[i][10] + interp(d700, d800, 700, 800, elemp[i][3]) * TG / 60
            if (elemdh[i][10] > 1.0):
                elemdh[i][10] = 1.0
        elif (elemp[i][3] > 800.0):
            if (elemdh[i][10] >= 0.9625):
                d800 = (1.0e-7 * pow(60.0, 4) - 3.2e-5 * pow(60.0, 3) + 0.0045 * pow(60.0,
                                                                                     2) - 0.26 * 60.0 + 5.47) / 100.0
            else:
                t = 0.0
                for i in range(30):
                    t1 = t - (-2.0e-8 * pow(t, 5) + 8.0e-6 * pow(t, 4) - 0.0015 * pow(t, 3) + 0.138 * pow(t,
                                                                                                          2) - 5.47 * t + 99.82 - ra * 100.0) / (
                                 -1.0e-7 * pow(t, 4) + 3.2e-5 * pow(t, 3) - 0.0045 * pow(t, 2) + 0.26 * t - 5.47)
                    if (abs((t1 - t) / t1) <= ERRO):
                        break
                    else:
                        t = t1
                t800 = t1
                d800 = (1.0e-7 * pow(t800, 4) - 3.2e-5 * pow(t800, 3) + 0.0045 * pow(t800,
                                                                                     2) - 0.26 * t800 + 5.47) / 100
            if (elemdh[i][10] < 1.0):
                elemdh[i][10] = elemdh[i][10] + d800 * TG / 60
            if (elemdh[i][10] > 1.0):
                elemdh[i][10] = 1.0
        # ======================= pore volume fraction generated by decomposition and the calculation of dehydration degree =======================
        #  volume fraction of gel pores in conventional C-S-H
        gCSH = 0.19 / (0.68 * fvCSH)
        # solid CSH volume fraction
        vs = ((0.68 * fvCSH - 0.19) * hydc * (1.0 - sf) + 3.0537 * sf * hydsf / dsf) / (wc + 0.32 * (1 - sf) + sf / dsf)
        # solid nomal CSH volume percentage
        a0 = (0.68 * fvCSH - 0.19) * hydc * (1.0 - sf) / (
                (0.68 * fvCSH - 0.19) * hydc * (1.0 - sf) + 3.0537 * sf * hydsf / dsf)
        # solid pazzolanic CSH volume percentage
        b0 = 3.0537 * sf * hydsf / dsf / ((0.68 * fvCSH - 0.19) * hydc * (1.0 - sf) + 3.0537 * sf * hydsf / dsf)
        # the volume fraction of the capillary pore increased by dehydration of CSH
        vpCSH = gCSH / (1.0 - gCSH) * vs * a0 * elemdh[i][10] + 0.2345 * vs * b0 * elemdh[i][10] + 0.2589 * elemdh[i][
            10] * vs
        vpCSH0 = gCSH / (1.0 - gCSH) * vs * a0 + 0.2345 * vs * b0 + 0.2589 * vs
        elemdh[i][11] = 0.51633 * elemdh[i][8] * elemdh[i][4] + 0.5448 * elemdh[i][9] * elemdh[i][3] + vpCSH
        elemdh[i][19] = 0.51633 * elemdh[i][4] + 0.5448 * elemdh[i][3] + vpCSH0
        elemdh[i][20] = elemdh[i][11] / elemdh[i][19]  # dehydration degree
        # =======================  the water released by dehydration (mole) =======================
        elemdh[i][12] = 0.028685 * elemdh[i][8] * elemdh[i][4] + 0.03027 * elemdh[i][9] * elemdh[i][3] + vpCSH / 18.0
        elemdh[i][13] = vs * (1.0 - elemdh[i][10]) * a0 / (1.0 - gCSH)
        elemdh[i][14] = vs * (1.0 - elemdh[i][10]) * b0 / 0.81
        elemdh[i][15] = elemdh[i][3] * (1.0 - elemdh[i][9])
        elemdh[i][16] = elemdh[i][4] * (1.0 - elemdh[i][8])
        elemdh[i][17] = elemdh[i][7] + elemdh[i][11]
        elemdh[i][18] = elemdh[i][7] * Sd + 18 * elemdh[i][12] + elemdh[i][0]
        if (elemdh[i][18] < 0.0):
            elemdh[i][18] = 0.0
        elemdh[i][22] = elemdh[i][5] + elemdh[i][6] + elemdh[i][4] * elemdh[i][8] * 0.48367 + elemdh[i][3] * elemdh[i][
            9] * 0.4552 + vs * elemdh[i][10] * 0.7411
        vh = elemdh[i][22] + elemdh[i][17] + elemdh[i][16] + elemdh[i][15] + elemdh[i][14] + elemdh[i][13]
        # ======================= E-modulus degradation prediction =======================
        Gm = Em / 2.0 / (1.0 + U)
        Km = Em / (3.0 * (1.0 - 2.0 * U))
        # E-modulus of dehydration products
        EC3A = 164.2 * pow((1.0 - 0.51633), 3.36)
        ECaO = 194.54 * pow((1.0 - 0.5448), 4)
        EnC2S = 140.2 * pow((1.0 - (gCSH + 0.2589 * (1.0 - gCSH))), 4.65)
        EpC2S = 140.2 * pow((1.0 - (0.19 + 0.2589 * (1.0 - 0.19))), 4.65)
        #  volume fraction of dehydration products
        fC3A = elemdh[i][4] * elemdh[i][8]
        fCaO = elemdh[i][3] * elemdh[i][9]
        fnC2S = elemdh[i][1] - elemdh[i][13]
        fpC2S = elemdh[i][2] - elemdh[i][14]
        # the volume fraction of dehydrated phase
        fi = fC3A + fCaO + fnC2S + fpC2S
        # ======================= the E-modulus of dehydrated phase =======================
        if (fi != 0.0):
            Ei = (EC3A * fC3A + ECaO * fCaO + EnC2S * fnC2S + EpC2S * fpC2S) / fi
            Ki = Ei / (3.0 * (1.0 - 2.0 * U))
            Ke0 = Km + (Ki - Km) * fi / (1.0 + (1.0 - fi) * (Ki - Km) / (Km + 4.0 * Gm / 3.0))
            Ee0 = Ke0 * 3.0 * (1.0 - 2.0 * U)
            RE = Ee0 / Em
            elempe[i][4] = Ee0
            elempe[i][8] = U
        else:
            Ke0 = Km
            Ee0 = Em
            RE = Ee0 / Em
            elempe[i][4] = Ee0
            elempe[i][8] = U
        # ======================= permeability prediciton =======================
        # critical pore diameter
        elemdh[i][21] = (Dc1 - Dc0) / CP2D * elemdh[i][20] + Dc0
        # level 1 permeability
        V1 = elemdh[i][14] / (elemdh[i][14] + elemdh[i][5] + elemdh[i][6] + elemdh[i][15] + elemdh[i][16])
        elempe[i][1] = 1.016e-24 * pow((V1 - 0.17), 2)
        # level 2 permeability
        V1 = elemdh[i][13] / (
                elemdh[i][13] + elemdh[i][14] + elemdh[i][5] + elemdh[i][6] + elemdh[i][15] + elemdh[i][16])
        A = 4.8823
        B = (A * (1.0 - V1) - V1) * math.sqrt(elempe[i][1]) + (A * V1 - (1.0 - V1)) * math.sqrt(7e-23)
        C = math.sqrt(7e-23) * math.sqrt(elempe[i][1])
        K21 = pow((B + math.sqrt(pow(B, 2) + 4.0 * A * C)) / (2.0 * A), 2)
        K22 = pow((B - math.sqrt(pow(B, 2) + 4.0 * A * C)) / (2.0 * A), 2)
        if (K21 >= elempe[i][1] and K21 <= 7e-23):
            elempe[i][2] = K21
        else:
            elempe[i][2] = K22
        # level 3 permeability
        V1 = elemdh[i][17]
        Dc = elemdh[i][21]
        Kh = 5.355e-3 * pow(Dc, 2)
        A = 4.5555
        B = (A * (1.0 - V1) - V1) * math.sqrt(elempe[i][2]) + (A * V1 - (1.0 - V1)) * math.sqrt(Kh)
        C = math.sqrt(Kh) * math.sqrt(elempe[i][2])
        K21 = pow((B + math.sqrt(pow(B, 2) + 4.0 * A * C)) / (2.0 * A), 2)
        K22 = pow((B - math.sqrt(pow(B, 2) + 4.0 * A * C)) / (2.0 * A), 2)
        if (K21 >= elempe[i][2] and K21 <= Kh):
            elempe[i][3] = K21
        else:
            elempe[i][3] = K22
    # =======================  output the conversion degree of Aft, CH, and CSH  =======================
    ws1 = wb2.create_sheet("conversion_degree", 0)
    ws1.cell(1, 1, "elem")
    ws1.cell(1, 2, "AFt_cd")
    ws1.cell(1, 3, "CH_cd")
    ws1.cell(1, 4, "CSH_cd")
    ws1.cell(1, 5, "Decomposition_degree")
    ws1.cell(1, 6, "LVP-1")
    ws1.cell(1, 7, "LVP-2")
    ws1.cell(1, 8, "LVP-3")
    for i in range(NE):
        ws1.cell(i + 2, 1, i + 1)
        ws1.cell(i + 2, 2, elemdh[i][8])
        ws1.cell(i + 2, 3, elemdh[i][9])
        ws1.cell(i + 2, 4, elemdh[i][10])
        ws1.cell(i + 2, 5, elemdh[i][20])
        ws1.cell(i + 2, 6, elempe[i][1])
        ws1.cell(i + 2, 7, elempe[i][1])
        ws1.cell(i + 2, 8, elempe[i][1])
    # 计算水化和分解后基质的弹模
    e0 = ftm / Em
    for i in range(NE):
        elemp[i][14] = elempe[i][4] / Em
        D1 = elemp[i][14]
        x = e0
        for j in range(50):
            x1 = x - (ftm * math.exp(-A * (x - e0)) - D1 * Em * x) / (-A * ftm * math.exp(-A * (x - e0)) - D1 * Em)
            if math.fabs((x1 - x) / x1) <= ERRO:
                break
            else:
                x = x1
        elemp[i][13] = D1 * Em * x1
    wb2.save(excel_name)
    wb1.close()
    wb2.close()


def calc_vapor(flag):
    if step*TG*TV < 100 :
        return
    else:
        wb = openpyxl.load_workbook(vapor_table)
        sheet1 = wb["saturatedWater"]
        sheet2 = wb["superheatedSteam"]
        sheet3 = wb["dynamicViscosity"]
        # 计算每行的有效值个数
        count = [0]
        for l in range(1, 25):
            for k in range(2, 37):
                if not sheet2.cell(l + 1, k).value:
                    count.append(k - 2)
                    break
        for i in range(NE):
            if flag == False:  # Flag为假时是第一次蒸气压计算
                if elemdh[i][18] != 0.0:
                    elemp[i][7] = elemdh[i][17] / elemdh[i][18] * 0.001  # (m3 / kg)
            if elemp[i][7] != 0.0:
                elemp[i][8] = -1.0
                # 温度小于100度时此时比体积为1.679
                if elemp[i][3] <= 100:
                    elemp[i][8] = 0.01
                    elemp[i][12] = 0
                    elemvp[i][1] = 1.679  # 赋予比体积
                    elemvp[i][3] = 12.02e-6  # 赋予动态粘度
                    elemvp[i][8] = 1e-3 / elemp[i][7]  # 赋予水饱和度
                # 考虑饱和蒸汽压表内的蒸汽压
                else:
                    for j in range(1, 34):
                        if (sheet1.cell(j + 1, 1).value <= elemp[i][3] <= sheet1.cell(j + 2, 1).value and
                                elemp[i][7] <= interp(sheet1.cell(j + 1, 4).value, sheet1.cell(j + 2, 4).value,
                                                      sheet1.cell(j + 1, 1).value,
                                                      sheet1.cell(j + 2, 4).value, elemp[i][3])):
                            elemp[i][8] = interp(sheet1.cell(j + 1, 2).value, sheet1.cell(j + 2, 2).value,
                                                 sheet1.cell(j + 1, 1).value,
                                                 sheet1.cell(j + 2, 4).value, elemp[i][3])
                            elemp[i][12] = 1.0
                            elemvp[i][1] = interp(sheet1.cell(j + 1, 4).value, sheet1.cell(j + 2, 4).value,
                                                  sheet1.cell(j + 1, 1).value,
                                                  sheet1.cell(j + 2, 1).value, elemp[i][3])
                            elemvp[i][3] = interp(sheet1.cell(j + 1, 5).value, sheet1.cell(j + 2, 5).value,
                                                  sheet1.cell(j + 1, 1).value,
                                                  sheet1.cell(j + 2, 1).value, elemp[i][3])
                            elemvp[i][8] = (elemp[i][7] - elemvp[i][1]) * 1e-3 / elemp[i][7] / (1e-3 - elemvp[i][1])
                            break
                # 匹配过热蒸汽表范围内的单元蒸汽压
                for j in range(1, 24):
                    # 锁定温度以确定该温度下的比体积上限值
                    volume_limit = [0]
                    dv_limit = [0]
                    if sheet2.cell(j + 1, 1).value <= elemp[i][3] <= sheet2.cell(j + 2, 1).value and count[j] >= 1:
                        for k in range(1, count[j] + 1):
                            volume_limit.append(interp(sheet2.cell(j + 1, k + 1).value, sheet2.cell(j + 2, k + 1).value,
                                                       sheet2.cell(j + 1, 1).value, sheet2.cell(j + 2, 1).value,
                                                       elemp[i][3]))
                            dv_limit.append(interp(sheet3.cell(j + 1, k + 1).value, sheet3.cell(j + 2, k + 1).value,
                                                   sheet3.cell(j + 1, 1).value, sheet3.cell(j + 2, 1).value, elemp[i][3]))
                        # 赋以过热蒸气压
                        for m in range(1, len(volume_limit)):
                            # 比体积的超限处理
                            if elemp[i][7] >= volume_limit[1]:
                                elemp[i][12] = 3
                                elemp[i][8] = sheet2.cell(1, 2).value
                                elemvp[i][3] = interp(sheet3.cell(j + 1, 2).value, sheet3.cell(j + 2, 2).value,
                                                      sheet3.cell(j + 1, 1).value, sheet3.cell(j + 2, 1).value, elemp[i][3])
                            elif len(volume_limit) > 2:
                                for n in range(2, len(volume_limit)):
                                    if elemp[i][7] >= volume_limit[n]:
                                        elemp[i][12] = 3
                                        elemp[i][8] = interp(sheet2.cell(1, n).value, sheet2.cell(1, n + 1).value,
                                                             volume_limit[n], volume_limit[n - 1], elemp[i][7])
                                        elemvp[i][3] = interp(dv_limit[n], dv_limit[n - 1], sheet3.cell(1, n).value,
                                                              sheet3.cell(1, n + 1).value, elemp[i][8])
                # 考虑数据缺失状态
                if elemp[i][8] == -1.0:
                    elemp[i][12] = 2  # 赋予状态中间数据缺失状
                    elemvp[i][1] = elemp[i][7]  # 赋予比体积
                    elemvp[i][8] = 0.0  # 液态水饱和度
                    for k in range(1, 34):
                        if sheet1.cell(k + 1, 1).value < elemp[i][3] < sheet1.cell(k + 2, 1).value:
                            elemp[i][8] = interp(sheet1.cell(k + 1, 2), sheet1.cell(k + 2, 2),
                                                 sheet1.cell(k + 1, 1),
                                                 sheet1.cell(k + 2, 4), elemp[i][3])
                            elemp[i][12] = 2.0
                            elemvp[i][3] = interp(sheet1.cell(k + 1, 5) * 1e-6, sheet1.cell(k + 2, 5),
                                                  sheet1.cell(k + 1, 1),
                                                  sheet1.cell(k + 2, 1), elemp[i][3])
                            break
        # 输出结果
        wb = openpyxl.load_workbook(excel2)
        sheet2 = wb["MatrixElement"]
        if flag == False:
            logging.info('first-elemp[j][7]' + str(elemp[1][7]))
            sheet2.cell(1, 10, "SpecificV1")
            sheet2.cell(1, 11, "DynamicV1")
            sheet2.cell(1, 12, "VaporType1")
            sheet2.cell(1, 13, "Vapor1")
            for num in range(1, NE + 1):
                sheet2.cell(num + 1, 10, elemp[j][7])
                sheet2.cell(num + 1, 11, elemvp[num - 1][3])
                sheet2.cell(num + 1, 12, elemp[j][12])
                sheet2.cell(num + 1, 13, elemp[num - 1][8])
            wb.save(excel2)
        else:
            logging.info('finall-elemp[j][7]' + str(elemp[1][7]))
            sheet2.cell(1, 16, "SpecificV2")
            sheet2.cell(1, 17, "DynamicV2")
            sheet2.cell(1, 18, "VaporType2")
            sheet2.cell(1, 19, "Vapor2")
            for num in range(1, NE + 1):
                sheet2.cell(num + 1, 16, elemp[j][7])
                sheet2.cell(num + 1, 17, elemvp[num - 1][3])
                sheet2.cell(num + 1, 18, elemp[j][12])
                sheet2.cell(num + 1, 19, elemp[num - 1][8])
            wb.save(excel2)


def submit_job(s, thisTempCae):
    jobName = "Job-temp0{}".format(s + 1)
    myJob = mdb.Job(name=jobName, model='Model-1', numCpus=8, numDomains=8, numGPUs=0)
    myJob.submit()
    myJob.waitForCompletion()
    mdb.saveAs(pathName=thisTempCae)


logging.basicConfig(level=logging.INFO, filename='./log.txt',filemode='w', format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
IT = 20  # initial temperature
U = 0.2  # poisson's ratio
ERRO = 1e-5
TG = 300  # 时间间隔
TV = 2.0 / 60  # 升温速率℃每秒
TT = 800  # 目标温度
TS = int(TT / (TG * TV))    # 分析步总数
# 读取基质节点和单元个数
mdb = openMdb(pathName='Model-temp01.cae')
logging.info("openmdb-successs")
# 读取文件中节点信息
a1 = mdb.models['Model-1'].rootAssembly.instances['Part-1-1']
NN = len(a1.nodes.getByBoundingBox(-1, -1, 0, 1, 1, 1))
NE = len(a1.elements.getByBoundingBox(-1, -1, 0, 1, 1, 1))
NME = len(a1.sets['Set-Matrix'].elements)
NAE = len(a1.sets['Set-Balls'].elements)
# 定义数组
elem = [[0 for i in range(6)] for j in range(NE)]
elemdh = [[0.0 for i in range(23)] for j in range(NE)]
elemp = [[0.0 for i in range(15)] for j in range(NE)]
elempe = [[0.0 for i in range(9)] for j in range(NE)]  # 渗透率相关
elemvp = [[0.0 for i in range(17)] for j in range(NE)]  # 动力粘度相关
# 计算硬化水泥浆体的初始体积分数并将初始信息赋予到各单元
vapor_table = "E:/Abaqus/Code/CycleInputFile/VaporTable.xlsx"
finiv = "E:/Abaqus/Code/CycleOutputFile/InitialVolume.txt"
CSH, pCSH, CH, AFt, CE, SF, CP, CPF, CP2, CP2D, CPAFt, CPCH, sf, hydc, hydsf, wc, dsf, Em, Eag, \
Sd, Dc0, Dc1, fvAFt, fvCH, fvCSH, inte, ftm, fta = cal_initial(finiv)
# 开始循环
for step in range(1):
    lastTempOdb = 'Job-temp0{}.odb'.format(step)
    lastTempCae = 'Model-temp0{}.cae'.format(step)
    thisTempOdb = "Job-temp0{}.odb".format(step + 1)
    thisTempCae = 'Model-temp0{}.cae'.format(step + 1)
    thisMassCae = 'Model-Mass0{}.cae'.format(step + 1)
    if step != 0:
        mdb = openMdb(pathName=lastTempCae)
        # 更改温度计算中的预定义场
        mdb.models['Model-1'].predefinedFields['Predefined Field-1'].setValues(
            distributionType=FROM_FILE, fileName=lastTempOdb, beginStep=1,
            beginIncrement=get_increment(lastTempOdb))
    # 更改温度幅值
    mdb.models['Model-1'].amplitudes['Amp-1'].setValues(timeSpan=STEP,smooth=SOLVER_DEFAULT,
                        data=((0.0, 20 + step * TG * TV), (TG, 20 + (step + 1) * TG * TV)))
    submit_job(step, thisTempCae)
    # 读取单步末基质节点温度
    excel1 = "E:/Abaqus/Code/CycleOutputFile/NNE.xlsx"
    excel2 = "E:/Abaqus/Code/CycleOutputFile/Step{}.xlsx".format(i+1)
    odb_name = 'Job-temp0{}.odb'.format(i+1)
    output_temp(odb_name, excel1, excel2)
    calc_element(excel2)
    # 热分解计算
    if step == 0:
        last_excel = excel2
    calc_decomposition(excel2, last_excel)
    # 蒸汽压计算
    calc_vapor(False)