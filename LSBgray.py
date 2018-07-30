# -*- coding = utf8 -*-

# LSB图像水印嵌入提取
from pylab import *
from PIL import Image


# 返回十进制整数value所对应的bitsize位二进制字符串
def turn_bin(value, bitsize):
    bin_val = bin(value)[2:]
    if len(bin_val) > bitsize:
        print("Larger than the expected size")
    while len(bin_val) < bitsize:
        bin_val = "0" + bin_val
    return bin_val


# LSB图片水印嵌入
def LSBembed(image_path, watermark_str, output_path):
    im = Image.open(image_path)

    # convert('L')彩图转换为灰度图
    im = im.convert('L')

    # 调用pylab中属于numpy的array,将灰度图像转化为二维的灰度值矩阵
    im_array = array(im)

    # 调用array对象的flatten方法将二维灰度矩阵转化为一维列表
    im_array_flatten = im_array.flatten()

    print("原始水印:", watermark_str)

    # 获取水印长度和水印长度的8位二进制字符串
    watermark_length = len(watermark_str)
    watermark_len_bin = turn_bin(watermark_length, 8)

    # i-一维列表の下标
    index = 0
    # 嵌入水印长度（数组前8位为水印头）
    for data_index in watermark_len_bin:
        if int(data_index) == 0:
            im_array_flatten[index] = im_array_flatten[index] & 254
        else:
            im_array_flatten[index] = im_array_flatten[index] | 1
        index += 1

    # 嵌入水印内容,根据水印字符串的长度分组嵌入字符
    for char in watermark_str:
        for data_index in turn_bin(ord(char), 8):
            if int(data_index) == 0:
                im_array_flatten[index] = im_array_flatten[index] & 254
            else:
                im_array_flatten[index] = im_array_flatten[index] | 1
            index += 1

    # 嵌入完成，reshape()将含水印的一维列表转化为numpy的二维数组
    # im.height高（行数）,im.width宽（列数）
    image_array_embed = reshape(im_array_flatten, (im.height, im.width))

    # 调用Image模块的fromarray方法将二维数组转化为图像并保存
    im_embed = Image.fromarray(image_array_embed)
    im_embed.save(output_path)
    return None


def LSBextract(image_path, output_path):
    # 打开含水印图片，转二维矩阵为一维
    im = Image.open(image_path)
    im_array = array(im)
    im_array_flatten = im_array.flatten()

    # 取水印头，拼合出水印长度的二进制字符串bin_len
    bin_len = ""  # "0b"
    index = 0
    for index in range(0, 8):
        temp = bin(im_array_flatten[index])[-1];  # print(temp)
        bin_len = bin_len + temp  # [-1]从右向左取最后一个值

    # 将bin_len转化为整数int_len
    int_len = int(bin_len, 2);  # print('int_len:'+str(int_len))

    # 拼合水印字符串
    i = 0
    j = 0
    int_data = []
    data = []
    for i in range(int_len):
        bin_data_char = ""  # 存储一个字符的二进制字符串
        for j in range(0, 8):
            index += 1
            temp = bin(im_array_flatten[index])[-1];  # print(temp)
            bin_data_char = bin_data_char + temp;  # print(bin_data_string)

        # 将二进制字符串转为整数ASCII码，再将整数转为字符
        int_data_char = int(bin_data_char, 2)
        data_char = chr(int_data_char)  # ASCII码转换为相应字符
        int_data.append(int_data_char)
        data.append(data_char)

    # print(int_data)
    print("提取水印",data)

    water_outfile=open(output_path, 'w')
    water_outfile.write(str(data))
    water_outfile.close()

    return None


if __name__ == '__main__':
    LSBembed('original.bmp', 'Learningmakesmehappy!', 'LSBembed.bmp')
    LSBextract('LSBembed.bmp','watermark_output.txt')
