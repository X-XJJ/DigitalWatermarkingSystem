FFMPEG_BIN = "E:\\ffmpeg-win64\\bin\\ffmpeg.exe"

import subprocess as sp
import numpy
import Robustness as robust


def VideoEmbed(input_video, watermark_string, output_video):
    command_read = [FFMPEG_BIN,
                    '-i', input_video,  # -i 设定输入流
                    '-f', 'image2pipe',  # -f 设定输出格式为流，image2pipe管道
                    '-pix_fmt', 'yuv420p',  # yuv420p  rgb24
                    # -pix_fmt 设置像素格式，'列表'作为参数显示所有像素格式支持
                    '-vcodec', 'rawvideo', '-']
    # vcodec 指定流的文件格式
    # rawvideo 原始视频流（未经混合 - 只含一视频流）
    pipe_read = sp.Popen(command_read, stdout=sp.PIPE, bufsize=10 ** 8)
    command_write = [FFMPEG_BIN,
                     '-y',  # -y 若文件存在，则覆盖
                     '-f', 'rawvideo',
                     '-vcodec', 'rawvideo',
                     '-s', '360x480',  # -s 设定画面的宽与高
                     '-pix_fmt', 'yuv420p',
                     '-i', '-',  # The imput comes from a pipe
                     '-q:v', '2',  # -q:v 存储jpeg的图像质量，一般2为高
                     output_video]
    width = 360  # 360 320
    height = 480  # 480 240
    pipe_write = sp.Popen(command_write, stdin=sp.PIPE)
    raw_image = pipe_read.stdout.read(width * height * 3)
    num = 0
    while raw_image != None and len(raw_image) != 0:
        # transform the byte read into a numpy array
        image = numpy.fromstring(raw_image, dtype='uint8')
        num += 1
        # print(image.shape, num)
        if image.shape == (width * height * 3,):
            # 当嵌到结尾时，最后一帧的大小可能不足
            # reshape()要求数组变换形态前后的数据内容不变，帧大小不足即数据不够
            image = image.reshape((height, width, 3))
            # throw away the data in the pipe's buffer.
            pipe_read.stdout.flush()
            img_tmp = image[:height, :width, 0]
            robust.embed_watermark(img_tmp, watermark_string)
        pipe_write.stdin.write(image.tostring())  # 管道里写一帧
        raw_image = pipe_read.stdout.read(width * height * 3)  # 管道里读一帧
    return None


def VideoExtract(input_video, output_path):
    command_read = [FFMPEG_BIN,
                    '-i', input_video,
                    '-f', 'image2pipe',
                    '-pix_fmt', 'yuv420p',
                    '-vcodec', 'rawvideo', '-']
    pipe_read = sp.Popen(command_read, stdout=sp.PIPE, bufsize=10 ** 8)
    width = 360  # 360 320
    height = 480  # 480 240
    raw_image = pipe_read.stdout.read(width * height * 3)
    num = 0
    while raw_image != None and len(raw_image) != 0:
        # transform the byte read into a numpy array
        image = numpy.fromstring(raw_image, dtype='uint8')
        num += 1
        # print(image.shape, num)
        if image.shape == (width * height * 3,):
            image = image.reshape((height, width, 3))
            # throw away the data in the pipe's buffer.
            pipe_read.stdout.flush()
            img_tmp = image[:height, :width, 0]
            robust.extract_watermark(img_tmp, output_path)
        raw_image = pipe_read.stdout.read(width * height * 3)

    return None


if __name__ == "__main__":
    VideoEmbed("video1.mp4", "anjing", "embed_video.mp4")
    VideoExtract("embed_video.mp4", 'watermark_output.txt')
