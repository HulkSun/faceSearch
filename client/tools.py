import hashlib
import operator as op
import os
import webbrowser
from tkinter import filedialog

from PIL import Image

from config import Config

### use misc to resize image
# def resize(w_box, h_box, source_image_path):
#     source_image = misc.imread(source_image_path, mode='RGB')
#     w, h = source_image.shape[:2]
#     f1 = 1.0 * w_box / w
#     f2 = 1.0 * h_box / h
#     factor = min([f1, f2])
#     width = int(w * factor)
#     height = int(h * factor)
#     resize_image = misc.imresize(source_image, (width, height))
#     return Image.fromarray(resize_image.astype('uint8'), 'RGB')


### use PIL to resize image
def resize(w_box, h_box, source_image_path):
    source_image = Image.open(source_image_path).convert("RGB")
    w, h = source_image.size
    f1 = 1.0 * w_box / w
    f2 = 1.0 * h_box / h
    factor = min([f1, f2])
    width = int(w * factor)
    height = int(h * factor)
    return source_image.resize((width, height), Image.ANTIALIAS)


def get_all_file_path(path):
    result = []
    for root, _, files in os.walk(path):
        for file_name in files:
            result.append(os.path.join(root, file_name))
    return result


def resize_and_store(source_image_path):
    w_box = 1000/2
    h_box = 1500/2
    save_path = Config().save_image_dir
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    save_image_path = save_path + os.path.basename(source_image_path)
    save_image = resize(w_box, h_box, source_image_path)
    save_image.save(save_image_path)
    return save_image_path


def judge_jpeg(source_image_path):
    try:
        image = Image.open(source_image_path)
        return image.format == 'JPEG'
    except IOError:
        return False
    except OSError:
        return False


class ProcessedImageList(object):
    def __init__(self):
        self.processeed_list = []
        if os.path.isfile(Config().processed_image_list_path):
            self.fp = open(Config().processed_image_list_path, 'r')
            self.processeed_list = self.fp.readlines()
            self.fp.close()
        self.fp = open(Config().processed_image_list_path, 'a')

    def getFileMD5(self, filepath):
        f = open(filepath, 'rb')
        md5obj = hashlib.md5()
        md5obj.update(f.read())
        hash_code = md5obj.hexdigest()
        f.close()
        return str(hash_code).upper()

    def filter(self, source_image_path):
        source_md5 = self.getFileMD5(source_image_path)
        for md5 in self.processeed_list:
            if op.eq(source_md5, md5.strip('\n')):
                return True
        return False

    def update(self, source_image_path):
        source_md5 = self.getFileMD5(source_image_path)
        self.fp.write(str(source_md5 + '\n'))
        self.fp.flush()

    def __del__(self):
        if not self.fp.closed:
            self.fp.close()


def open_pdf(filename):
    webbrowser.open(filename)


def open_file():
    """打开选择文件对话框"""
    filename = filedialog.askopenfilename(
        initialdir="/",
        title="选择照片",
        filetypes=(("Image File", "*.jpg"), ("Image File", "*.JPG")))
    return filename


def open_dir():
    """打开选择文件夹对话框"""
    file_dir = filedialog.askdirectory()
    return file_dir
