# -*- coding = utf-8 -*-

import cv2
import numpy as np


# 返回十进制整数value所对应的bitsize位二进制字符串
def turn_bin(value, bitsize):
    bin_val = bin(value)[2:]
    if len(bin_val) > bitsize:
        print("Larger than the expected size")
    while len(bin_val) < bitsize:
        bin_val = "0" + bin_val
    return bin_val


# 二进制字符串扩频
def spread_spectrum(bit_string, spread_width):
    ret = ""
    for bit in bit_string:
        ret += bit * spread_width  # 字符串 +连接，*重放 a*3=aaa
    return ret


# 根据提取的扩频二进制字符串，恢复二进制水印信息
def get_original_bin(bit_string, spread_width):
    if len(bit_string) % spread_width != 0:
        print("长度错误，需是%d整数倍。" % spread_width)
        return None

    ret_string = ""
    for i in range(int(len(bit_string) / spread_width)):  # range()信息个数
        count = 0
        for j in range(spread_width):  # 取单个水印的扩频信息
            count += int(bit_string[i * spread_width + j])
        if count < spread_width / 2:  # 0多则定取出的信息为0，否则为1
            ret_string += "0"
        else:
            ret_string += "1"

    return ret_string


# 对水印信息进行扩频编码
def watermark_encode(watermark_str):
    # 初始化水印信息
    watermark = ""

    # 水印字符串长度转化为32bits的二进制字符串，并在扩频后加入水印信息中
    watermark_size = turn_bin(len(watermark_str), 8)
    watermark += spread_spectrum(watermark_size, 7)

    # 循环转化字符串中的字符为二进制字符串并加入+水印信息中
    for char in watermark_str:
        temp_string = turn_bin(ord(char), 8)
        watermark += spread_spectrum(temp_string, 7)
    return watermark


# 进行单个水印信息嵌入
def embed_bit(bit, dcted_block, alpha):
    if bit == 1:  # 嵌入信息为1，则使A > B，且A-B > 水印强度alpha
        if dcted_block[4, 3] < dcted_block[5, 2]:
            dcted_block[4, 3], dcted_block[5, 2] = dcted_block[5, 2], dcted_block[4, 3]
            if dcted_block[4, 3] - dcted_block[5, 2] < alpha:
                dcted_block[4, 3] += alpha
        elif dcted_block[4, 3] == dcted_block[5, 2]:
            dcted_block[4, 3] += alpha
    elif bit == 0:  # 嵌入信息为0，则使A < B，且A-B > 水印强度alpha
        if dcted_block[4, 3] > dcted_block[5, 2]:
            dcted_block[4, 3], dcted_block[5, 2] = dcted_block[5, 2], dcted_block[4, 3]
            if dcted_block[5, 2] - dcted_block[4, 3] < alpha:
                dcted_block[4, 3] -= alpha
        elif dcted_block[4, 3] == dcted_block[5, 2]:
            dcted_block[4, 3] -= alpha
    else:
        print("请输入正确的水印值，0或1。")


# 根据嵌入规则，提取单个水印信息，若A > B则信息为1
def extract_bit(dcted_block):
    if dcted_block[4, 3] > dcted_block[5, 2]:
        return 1
    else:
        return 0


# 进行水印嵌入
def ImageEmbed(image_path, watermark_str, output_path):
    rgb_image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    ycbcr_image = cv2.cvtColor(rgb_image, cv2.COLOR_BGR2YCR_CB)
    img = ycbcr_image[:, :, 0]

    print("原始水印:", watermark_str)
    watermark = watermark_encode(watermark_str)

    iHeight, iWidth = img.shape
    # 初始化空矩阵保存量化结果
    img2 = np.empty(shape=(iHeight, iWidth))

    index = 0
    alpha = 25
    # 分块DCT
    for startY in range(0, iHeight, 8):
        for startX in range(0, iWidth, 8):
            block = img[startY:startY + 8, startX:startX + 8].reshape((8, 8))
            # 进行DCT，并嵌入水印
            blockf = np.float32(block)
            block_dct = cv2.dct(blockf)
            if index < len(watermark):
                embed_bit(int(watermark[index]), block_dct, alpha)
                index += 1
            # store the result
            for y in range(8):
                for x in range(8):
                    img2[startY + y, startX + x] = block_dct[y, x]

    # DCT逆变换
    for startY in range(0, iHeight, 8):
        for startX in range(0, iWidth, 8):
            block = img2[startY:startY + 8, startX:startX + 8].reshape((8, 8))
            blockf = np.float32(block)
            dst = cv2.idct(blockf)
            # 保存逆变换结果
            for y in range(8):
                for x in range(8):
                    img[startY + y, startX + x] = dst[y, x]

    # 将Y分量覆盖原来的Y分量，CbCr分量保持不变
    new_ycbcr_image = ycbcr_image
    new_ycbcr_image[:, :, 0] = img

    # 将嵌入水印后的图像二维数组转化为BGR色彩空间，并写入图像
    watermarked_rgb = cv2.cvtColor(new_ycbcr_image, cv2.COLOR_YCR_CB2BGR)
    cv2.imwrite(output_path, watermarked_rgb)
    return None


# 进行水印提取
def ImageExtract(embeded_image_path, output_path):
    img = cv2.imread(embeded_image_path, cv2.IMREAD_GRAYSCALE)
    iHeight, iWidth = img.shape

    index = 0
    length_string = ""
    watermark_length = 0
    watermark_string = ""
    decoded_watermark = ""
    # 分块DCT
    for startY in range(0, iHeight, 8):
        for startX in range(0, iWidth, 8):
            block = img[startY:startY + 8, startX:startX + 8].reshape((8, 8))
            # 进行DCT，并提取水印
            blockf = np.float32(block)
            block_dct = cv2.dct(blockf)
            if index < 8 * 7:  # 提取水印长度
                bit = extract_bit(block_dct)
                if bit == 1:
                    length_string += "1"
                else:
                    length_string += "0"
                if index == 8 * 7 - 1:
                    length_string = get_original_bin(length_string, 7)
                    watermark_length = int(length_string, 2)
                index += 1
            elif index < 8 * 7 + watermark_length * 8 * 7:  # 提取水印
                bit = extract_bit(block_dct)
                if bit == 1:
                    watermark_string += "1"
                else:
                    watermark_string += "0"
                if index == 8 * 7 + watermark_length * 8 * 7 - 1:
                    watermark_string = get_original_bin(watermark_string, 7)
                    # print(watermark_string)
                    for i in range(watermark_length):
                        decoded_watermark += chr(int(watermark_string[i * 8: (i + 1) * 8], 2))
                    print("提取水印:", decoded_watermark.encode())

                index += 1

    water_outfile = open(output_path, 'w') # 提取内容部分gbk无法编码
    water_outfile.write(str(decoded_watermark.encode('utf-8')))
    # write() 只能写入字符串str类型
    # .encode('utf-8') 'ascii' 'CP437' 'gbk'
    water_outfile.close()

    return None


if __name__ == '__main__':
    ImageEmbed("lena.jpg", "Learningmakesmehappy!", "Robust_embeded.jpg")
    ImageExtract("Robust_embeded.jpg",'watermark_output.txt')
