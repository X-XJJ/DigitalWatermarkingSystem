# -*- coding = utf-8 -*-

import cv2
import numpy as np

# 返回一个符合高斯分布的，值取1,0两个值的伪随机序列
def GenerateGaussianSequence(n=1000):
    # 生成1行n列的符合高斯分布的伪随机矩阵
    random_sequence = np.random.randn(1, n)

    # 展开成一维数组
    random_sequence = random_sequence.flatten()

    # 将一维数组的进行极化，即当数组中的数为x, 则有-1-if x<0, 0-if x==0, 1-if x>0
    watermark_sequence = np.sign(random_sequence)

    # 逐一将所有-1置为0得到一个二进制序列
    for i in range(n):
        if watermark_sequence[i] == -1:
            watermark_sequence[i] = 0

    return watermark_sequence


def SpreadSpectrumEmbed(image_path, output_path, wmfile, n, alpha):
    # IMREAD_COLOR:读取彩色图像，OpenCV读取图像的色彩空间默认为BGR
    rgb_image = cv2.imread(image_path, cv2.IMREAD_COLOR)

    # 将色彩空间转化为YCbCr
    ycbcr_image = cv2.cvtColor(rgb_image, cv2.COLOR_BGR2YCR_CB)

    # 读出的数据类型是numpy三维数组，行列分别对应图像的高和宽，最后一个维度是[Y,Cb,Cr]
    # 对数组进行切片操作，前两个切片过程":"操作分别取了行和列的所有数据
    # 最后一个取出了[Y,Cb,Cr]中的Y分量，结果为一个numpy二维数组，行列不变，每个点保存的是Y的数值
    y = ycbcr_image[:, :, 0]

    # cv2.dct需要输入一个浮点类型，因此先转化为浮点再进行DCT变换
    yf = np.float32(y)
    dct_image = cv2.dct(yf)

    # 将DCT变换的结果展开为1维数组
    dct_vector = dct_image.flatten()

    # 切片取出下标为0的元素，即直流分量，得到交流分量列表
    ac_vector = dct_vector[1:]

    # argsort可以得到排序后的各个元素的索引，其中参数-ac_vector加上负号表明是降序
    index = np.argsort(-ac_vector)

    # 生成水印序列
    watermark_seq = GenerateGaussianSequence(n)

    # 对降序排列的ac系数进行水印嵌入，嵌入公式为xi = x + wi * a，其中a为强度
    for i in range(0, n):
        ac_vector[index[i]] = ac_vector[index[i]] + (watermark_seq[i] * alpha)

    # 当ac_vector改变时，dct_vector会同步改变，所以水印嵌入完成
    # 将一维数组恢复为图像宽高相对应的二维数组
    watermarked_dct_image = np.reshape(dct_vector, (512, 512))

    # 对该二维数组进行逆DCT变换得到嵌入水印后的图像Y分量
    watermarked_dct_imagef = np.float32(watermarked_dct_image)
    inverse_dct_image = cv2.idct(watermarked_dct_imagef)

    # 将Y分量覆盖原来的Y分量，CbCr分量保持不变
    new_ycbcr_image = ycbcr_image
    new_ycbcr_image[:, :, 0] = inverse_dct_image

    # 将嵌入水印后的图像二维数组转化为BGR色彩空间，并写入图像
    # 这一过程存在量化等处理，因此可能影响部分水印值
    watermarked_rgb = cv2.cvtColor(new_ycbcr_image, cv2.COLOR_YCR_CB2BGR)
    cv2.imwrite(output_path, watermarked_rgb)

    # 保存随机生成的水印序列
    wm = open(wmfile, "w")
    org = []
    for i in watermark_seq:
        wm.write(str(int(i)))
    wm.close()
    wm = open(wmfile, "r")
    org = []
    for i in wm.readline():
        org.append(int(i))
    print("原始水印", org)
    return None


def SpreadSpectrumExtract(suspfile, origfile, output_path, n, alpha):
    # OpenCV读嵌入后图像，色彩空间默认BGR；RGB转化为YCbCr
    rgb_image_w = cv2.imread(suspfile)
    ycbcr_image_w = cv2.cvtColor(rgb_image_w, cv2.COLOR_BGR2YCR_CB)
    # 对数组进行切片操作，前两个切片过程":"操作分别取了行和列的所有数据
    # 最后一个取出了[Y,Cb,Cr]中的Y分量，即numpy二维数组，每个点保存的是Y的数值
    y_w = ycbcr_image_w[:, :, 0]

    # cv2.dct需要输入浮点类型，so先转化浮点再进行DCT变换
    y_wf = np.float32(y_w)
    dct_image_w = cv2.dct(y_wf)

    # 展开结果为1维数组，[1:]切片取下标为0的元素，即直流分量，得到交流分量列表
    dct_vector_w = dct_image_w.flatten()[1:]
    # argsort得到排序后各元素的索引，参数加负号表降序
    index_w = np.argsort(-dct_vector_w)

    # OpenCV读取原图
    rgb_image = cv2.imread(origfile)
    ycbcr_image = cv2.cvtColor(rgb_image, cv2.COLOR_BGR2YCR_CB)
    y = ycbcr_image[:, :, 0]
    yf = np.float32(y)
    dct_image = cv2.dct(yf)
    dct_vector = dct_image.flatten()[1:]
    index = np.argsort(-dct_vector)

    w = [0] * n  # 初始化存放提取水印的空间
    for i in range(0, n):  # 按公式，提取单个水印，拼合
        w[i] = (dct_vector_w[index_w[i]] - dct_vector[index[i]]) / alpha
        w[i] = np.sign(w[i])  # 标志化提取的水印信息
        if w[i] == -1:
            w[i] = 0
        else:
            w[i] = 1
    print("提取水印", w)

    # 保存提取出的水印序列
    wm = open(output_path, "w")
    org = []
    for i in w:
        wm.write(str(int(i)))
    wm.close()
    return None

if __name__ == '__main__':
    SpreadSpectrumEmbed('lena.jpg', 'COXlena.jpg', 'watermark_cox.txt', 20, 1)
    SpreadSpectrumExtract('COXlena.jpg', 'lena.jpg', 'watermark_output.txt', 20, 1)
