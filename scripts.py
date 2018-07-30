# -*- coding = utf-8 -*-

import LSBgray
import Cox
import RobustImg
import LSBwav
import RobustVideo

import argparse
import os


def parse_args():
    # 参数解析，当输入-h或输入不足时，将提示参数
    parser = argparse.ArgumentParser(description="Watermark system.")
    # 参数不带'-'为必选，带-或--为可选，type默认string
    parser.add_argument('type', type=str, help='对象类型(image,audio,video)')
    # dest显示变量名称，default默认值
    parser.add_argument('operate', type=str, help='操作(embed,extract)')
    parser.add_argument('input', type=str, help='输入文件（相对路径/绝对路径）')
    parser.add_argument('--imageMethod', dest="i", default='LSB', help='图像水印嵌入/提取方法（LSB/Cox/Robust）')
    parser.add_argument('--cox_org', dest="c", default='lena.jpg', help='Cox图像原图')
    parser.add_argument('-watermark', dest="w", default='LearningMakesMeHappy!', help='水印字符串/水印文件路径（若文件不存在则默认输入为水印）')
    parser.add_argument('output', type=str, help='输出文件（嵌入后文件/提取水印的存储位置）')

    args = parser.parse_args()
    return args


# Brian Beck提供了一个类switch()来实现其他语言中switch的功能
class switch(object):
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration

    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args:  # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False


if __name__ == '__main__':
    args = parse_args()
    # print("输入:" + args.type, args.operate, args.input, args.i, args.w, args.output)

    if args.operate == 'embed':
        if os.path.exists(args.w):
            wm = open(args.w, "r")
            org = wm.read()
            args.w = str(org)

        for case in switch(args.type):
            if case('image'):
                if args.i == 'LSB':
                    LSBgray.LSBembed(args.input, args.w, args.output)
                elif args.i == 'Cox':
                    Cox.SpreadSpectrumEmbed(args.input, args.output, 'watermark_cox.txt', 20, 1)
                    cox_org = args.input
                elif args.i == 'Robust':
                    RobustImg.ImageEmbed(args.input, args.w, args.output)
                else:
                    print('error!')
                break
            if case('audio'):
                LSBwav.LSBembed(args.input, args.w, args.output)
                break
            if case('video'):
                RobustVideo.VideoEmbed(args.input, args.w, args.output)
                break
            if case():  # 默认
                print("input error!")
                break
    elif args.operate == 'extract':
        if args.type == 'image':
            if args.i == 'LSB':
                LSBgray.LSBextract(args.input, args.output)
            elif args.i == 'Cox':
                Cox.SpreadSpectrumExtract(args.input, args.c, args.output, 20, 1)
            elif args.i == 'Robust':
                RobustImg.ImageExtract(args.input, args.output)
            else:
                print('input error!')
        elif args.type == 'audio':
            LSBwav.LSBextract(args.input, args.output)
        elif args.type == 'video':
            RobustVideo.VideoExtract(args.input, args.output)
        else:
            print("input error!")
    else:
        print("input error!")
