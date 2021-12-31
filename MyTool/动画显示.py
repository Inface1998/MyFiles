# -*- coding: UTF-8 -*-    
# 作者：zhangHJ
# 日期：2021/12/31  10:09
import matplotlib.pyplot as plt
import imageio, os


def generate_gif(state, dis):
    images = []
    target_dir = "E:/Abaqus/Code/CycleOutputFile/12-30"
    for n in range(32):
        file_name = target_dir + '/step{}/{}-{}mm.png'.format(n + 1, state, dis)
        images.append(imageio.imread(file_name))
    imageio.mimsave(target_dir + '/{}{}gif.gif'.format(state, dis), images, duration=1)


name_list = ["begin", "final"]
dis_list = [1, 3, 5, 10]
for i in range[len(name_list)]:
    for j in range[len(dis_list)]:
        generate_gif(name_list[i], dis_list[j])
