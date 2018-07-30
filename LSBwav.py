# -*- coding = utf8 -*-

# LSB音频水印嵌入提取
import wave
import struct


# 返回十进制整数value所对应的bitsize位二进制字符串
def turn_bin(value, bitsize):
    bin_val = bin(value)[2:]
    if len(bin_val) > bitsize:
        print("Larger than the expected size")
    while len(bin_val) < bitsize:
        bin_val = "0" + bin_val
    return bin_val


def LSBembed(audio_path, watermark_str, output_path):
    print("原始水印:", watermark_str)
    # 初始化要嵌入的水印信息
    watermark = ""
    # 水印长度转化为32位二进制字符串，加入整体水印信息
    watermark_size = turn_bin(len(watermark_str), 32)
    watermark += watermark_size

    # 水印字符串转化为8位二进制字符串，加入整体水印信息
    for char in watermark_str:
        watermark += turn_bin(ord(char), 8)

    # 调用wave库读取音频文件（wav），保存原始文件的参数信息
    audio = wave.open(audio_path, 'rb')
    (nchannels, sampwidth, framerate, nframes, comptype, compname) = audio.getparams()

    # 读取所有数据，数据长度为帧数*声道数
    frames = audio.readframes(nframes * nchannels)
    samples = struct.unpack_from("%dh" % nframes * nchannels, frames)

    # 检测嵌入水印内容长度
    if len(samples) < len(watermark):
        raise OverflowError(  # 抛出异常
            "水印长度共%d比特，采样点数量为%d，采样点不足请减少水印长度。" % (
                len(watermark), len(samples)))

    encoded_samples = []  # 初始化编码文件
    watermark_flag = 0  # 标志位，水印内容嵌入完成度
    # 对原始数据循环嵌入水印
    for sample in samples:
        encoded_sample = sample  # 对单个数据嵌入水印（无水印的地方不做更改）
        if watermark_flag < len(watermark):
            encode_bit = int(watermark[watermark_flag])
            if encode_bit == 1:  # 水印为1
                encoded_sample = sample | 1
            else:  # 水印为0
                encoded_sample = sample  # 嵌入位为0
                if sample & 1 != 0:  # 嵌入位为1
                    encoded_sample = sample - 1
            watermark_flag = watermark_flag + 1
        # 将嵌入完成的单个样本，加入整体中
        encoded_samples.append(encoded_sample)

    # 保存嵌入完成的音频文件，恢复参数，打包
    output_audio = wave.open(output_path, 'wb')
    output_audio.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))
    output_frames = struct.pack("%dh" % len(encoded_samples), *encoded_samples)
    output_audio.writeframes(output_frames)

    return None


def LSBextract(wav_path, output_path):
    watermarked_audio = wave.open(wav_path, 'rb')
    (nchannels, sampwidth, framerate, nframes, comptype, compname) = watermarked_audio.getparams()
    frames = watermarked_audio.readframes(nframes * nchannels)
    samples = struct.unpack_from("%dh" % nframes * nchannels, frames)

    watermark_bytes = ""  # 提取二进制字符串形式的水印长度
    for i in range(32):  # 8
        if samples[i] & 1 == 0:  # xxxx & 1 =xxxx
            watermark_bytes += '0'
        else:
            watermark_bytes += '1'

    watermark_size = int(watermark_bytes, 2)
    # print("提取%d字节水印。" % watermark_size)

    watermark = ""  # 根据水印长度，提取水印信息
    sample_index = 32
    for n in range(watermark_size):
        bytes = ""
        for i in range(8):
            if samples[sample_index] & 1 == 0:  # xxxx & 1 =xxxx
                bytes += '0'
            else:
                bytes += '1'
            sample_index += 1
        watermark += chr(int(bytes, 2))  # 二进制字符串→ascii码→字符

    print("提取水印", watermark)
    water_outfile = open(output_path, 'w')
    water_outfile.write(watermark)
    water_outfile.close()
    return None


if __name__ == "__main__":
    watermark_str = "Learningmakesmehappy!"
    audio = "audio.wav"
    output = "LSBembed.wav"
    LSBembed(audio, watermark_str, output)
    LSBextract(output, 'watermark_output.txt')
