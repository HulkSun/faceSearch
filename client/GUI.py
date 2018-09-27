import os
import re
import threading
import time
import tkinter as tk
from tkinter import Label, LabelFrame, StringVar, Tk, Toplevel, messagebox, ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

from client.middleware import Middleware
from client.tools import (get_all_file_path, open_dir, open_file, open_pdf,
                          resize)
from config import Config
from logger import logger

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600


def center_window(root, width, height):
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws / 2) - (width / 2)
    y = (hs / 2) - (height / 2)
    root.geometry('%dx%d+%d+%d' % (width, height, x, y))


class ProgressBar(object):
    """显示添加进度条"""
    win_width = 500
    win_height = 120
    control = False
    destroy_flag = False
    end_button_flag = False

    def __init__(self):
        """绘制进度条及相关文字信息"""
        self.control = False
        self.root = Toplevel()
        self.root.title("添加进度")
        center_window(self.root, self.win_width, self.win_height)
        self.root.resizable(width=False, height=False)
        self.root.attributes('-disabled', True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.frame = tk.Frame(self.root)
        self.canvas = tk.Canvas(
            self.frame, width=self.win_width - 140, height=30, bg="white")
        self.percent = StringVar()
        Label(self.frame, textvariable=self.percent).grid(row=0, column=2)
        self.frame.grid(row=0, column=1, padx=2, pady=2)
        self.canvas.grid(row=0, column=1, padx=2, pady=2)

        self.info = tk.Label(self.root, text="正在添加数据，请耐心等待！\n请勿进行其他操作！")
        self.info.grid(row=1, column=1, padx=2, pady=2)

        self.end_button = tk.Button(
            self.root, text="中断", command=self.change_control)

        self.out_rec = self.canvas.create_rectangle(
            5, 5, self.win_width - 150, 25, outline="green", width=1)

    def callback_show_add_batch_progress(self, now_schedule, all_schedule):
        """根据处理进度更新进度条"""
        self.root.attributes('-disabled', False)
        if not self.end_button_flag:
            self.end_button_flag = True
            self.end_button.grid(row=2, column=1, padx=2, pady=2)
        fill_rec = self.canvas.create_rectangle(
            5, 5, 5, 25, outline="", width=0, fill="green")
        self.canvas.coords(
            fill_rec,
            (5, 5, (now_schedule / all_schedule) * (self.win_width - 140), 25))
        self.root.update()
        self.percent.set(
            str(now_schedule) + '/' + str(all_schedule) + ' (' +
            str(round(now_schedule / all_schedule * 100, 2)) + '%)')
        if round(now_schedule / all_schedule * 100, 2) == 100.00:
            self.destroy_win()

    def if_end_add_batch_thread(self):
        return self.control

    def change_control(self):
        if messagebox.askyesno("提示", "中断后未添加的可继续添加！\n 是否中断？"):
            self.control = True
            self.destroy_win()

    def destroy_win(self):
        if not self.destroy_flag:
            self.destroy_flag = True
            self.root.destroy()

    def on_closing(self):
        self.change_control()

    def __del__(self):
        self.destroy_win()


class ProgressCircle(object):
    win_width = 200
    win_height = 50

    def __init__(self):
        self.root = Toplevel()
        self.root.title("检索进行中...")
        center_window(self.root, self.win_width, self.win_height)
        self.root.attributes('-disabled', True)
        self.info_label = tk.Label(self.root, text="检索大约需要一分钟，请等待！")

    def show(self):
        self.info_label.pack()

    def fade(self):
        self.root.destroy()


class main_window(object):
    """程序主界面"""

    global WINDOW_WIDTH
    global WINDOW_HEIGHT

    search_by_face_source_image_path = ""
    middleware = Middleware()

    def __init__(self):
        self.config = Config()
        self.tmp_dir = self.config.tmp_dir
        self.check_auto_add_dir()
        self.init_gui()

    def ui_process(self):
        self.menu_tab()  # 显示tab菜单
        self.search_frame_page(self.search_tab)  # 添加搜索界面
        self.manage_frame_page(self.manage_tab)  # 添加管理界面
        self.about_frame_page(self.about_tab)  # 添加关于界面

    def menu_tab(self):
        tab_control = ttk.Notebook(self.root)

        self.search_tab = ttk.Frame(tab_control)
        tab_control.add(self.search_tab, text='照片检索')

        self.manage_tab = ttk.Frame(tab_control)
        tab_control.add(self.manage_tab, text='照片管理')

        self.about_tab = tk.Frame(tab_control)
        tab_control.add(self.about_tab, text='帮助与关于')

        tab_control.pack(expand=1, fill="both")

    def search_frame_page(self, root):
        """检索界面"""
        search_frame = tk.Frame(root)
        button_frame = tk.Frame(search_frame)

        open_file_button = tk.Button(
            button_frame, text="打开照片", command=self.get_source_image)
        start_button = tk.Button(
            button_frame, text="开始搜索", command=self.start_search_by_face)
        threshold_label = tk.Label(button_frame, text="    检索阈值：")
        self.threshold_entry = tk.Spinbox(
            button_frame,
            values=(0.8, 0.85, 0.9, 0.95, 1.0),
            width=5,
            state='readonly')
        image_frame = LabelFrame(search_frame, text="检索结果")

        source_image_label = tk.LabelFrame(
            image_frame,
            text="待查照片",
            width=WINDOW_WIDTH * 0.4,
            height=WINDOW_HEIGHT * 0.8)

        self.image_label = tk.Label(
            source_image_label,
            width=int(WINDOW_WIDTH * 0.4 - 10),
            height=int(WINDOW_HEIGHT * 0.8 - 10))

        result_image_label = tk.LabelFrame(
            image_frame,
            text="匹配结果",
            width=int(WINDOW_WIDTH * 0.4),
            height=int(WINDOW_HEIGHT * 0.8))

        # 检索结果显示表格
        self.search_by_face_result_table = ttk.Treeview(result_image_label)

        vsb = ttk.Scrollbar(
            self.search_by_face_result_table,
            orient="vertical",
            command=self.search_by_face_result_table.yview)
        vsb.pack(side=tk.RIGHT)
        self.search_by_face_result_table.configure(yscrollcommand=vsb.set)

        self.search_by_face_result_table["columns"] = ("id", "name", "sim")

        self.search_by_face_result_table.column(
            "#0", width=50, anchor="center")
        self.search_by_face_result_table.column(
            "id", width=10, anchor="center")
        self.search_by_face_result_table.column(
            "name", width=10, anchor="center")
        self.search_by_face_result_table.column(
            "sim", width=5, anchor="center")

        self.search_by_face_result_table.heading("#0", text="照片")
        self.search_by_face_result_table.heading("#1", text="工号")
        self.search_by_face_result_table.heading("#2", text="姓名")
        self.search_by_face_result_table.heading("#3", text="相似度")

        style = ttk.Style(self.root)
        style.configure("Treeview", rowheight=70)

        open_file_button.pack(padx=5, pady=5, side=tk.LEFT)
        threshold_label.pack(padx=5, pady=5, side=tk.LEFT)
        self.threshold_entry.pack(padx=5, pady=5, side=tk.LEFT)
        start_button.pack(padx=5, pady=5, side=tk.LEFT)

        button_frame.pack()

        source_image_label.pack(padx=5, pady=5, side=tk.LEFT)
        result_image_label.pack(padx=5, pady=5, side=tk.LEFT)
        source_image_label.pack_propagate(False)
        result_image_label.pack_propagate(False)
        image_frame.pack(padx=5, pady=5, fill=tk.X)
        search_frame.pack()

    def manage_frame_page(self, root):
        """管理界面"""
        manage_frame = tk.Frame(root)
        add_frame = tk.LabelFrame(
            manage_frame,
            text="添加员工信息",
            width=WINDOW_WIDTH * 0.4,
            height=WINDOW_HEIGHT * 0.8)

        fetch_frame = tk.LabelFrame(
            manage_frame,
            text="查找员工",
            width=WINDOW_WIDTH * 0.4,
            height=WINDOW_HEIGHT * 0.8)

        add_single_frame = tk.LabelFrame(
            add_frame,
            text="单个添加",
            width=int(WINDOW_WIDTH * 0.4 - 5),
            height=int(WINDOW_HEIGHT * 0.5))

        add_single_id_frame = tk.Frame(add_single_frame)
        add_single_id_text = tk.Label(add_single_id_frame, text="员工工号: ")
        self.add_single_id_entry = tk.Entry(add_single_id_frame)
        add_single_id_text.pack(padx=2, pady=2, side=tk.LEFT)
        self.add_single_id_entry.pack(padx=2, pady=2, side=tk.LEFT)
        add_single_id_frame.pack(padx=2, pady=2)

        add_single_name_frame = tk.Frame(add_single_frame)
        add_single_name_text = tk.Label(add_single_name_frame, text="员工姓名: ")
        self.add_single_name_entry = tk.Entry(add_single_name_frame)
        add_single_name_text.pack(padx=2, pady=2, side=tk.LEFT)
        self.add_single_name_entry.pack(padx=2, pady=2, side=tk.LEFT)
        add_single_name_frame.pack(padx=2, pady=2)

        add_single_photo_frame = tk.Frame(add_single_frame)
        add_single_photo_text = tk.Label(add_single_photo_frame, text="员工照片: ")
        self.add_single_photo_path = StringVar()
        add_single_photo_entry = tk.Entry(
            add_single_photo_frame,
            width=15,
            textvariable=self.add_single_photo_path)
        add_single_photo_button = tk.Button(
            add_single_photo_frame,
            text="打开",
            command=self.update_add_single_photo)
        self.add_single_photo_label = tk.Label(
            add_single_frame, width=90, height=120)
        add_single_photo_text.pack(padx=2, pady=2, side=tk.LEFT)
        add_single_photo_entry.pack(padx=2, pady=2, side=tk.LEFT)
        add_single_photo_button.pack(padx=2, pady=2, side=tk.LEFT)

        add_single_photo_frame.pack(padx=2, pady=2)
        self.add_single_photo_label.pack(padx=2, pady=2)
        self.add_single_photo_label.pack_propagate(False)
        add_single_button_frame = tk.Frame(add_single_frame)
        add_single_confirm_button = tk.Button(
            add_single_button_frame,
            text="确认",
            command=self.start_add_single_image)
        add_single_reset_button = tk.Button(
            add_single_button_frame,
            text="重置",
            command=self.reset_add_single_entry)
        add_single_confirm_button.pack(padx=2, pady=2, side=tk.LEFT)
        add_single_reset_button.pack(padx=2, pady=2, side=tk.LEFT)
        add_single_button_frame.pack(padx=2, pady=5)

        add_batch_frame = tk.LabelFrame(
            add_frame,
            text="批量添加",
            width=int(WINDOW_WIDTH * 0.4 - 10),
            height=int(WINDOW_HEIGHT * 0.2))
        add_batch_text = tk.Label(
            add_batch_frame, text="提示信息： \n 文件夹中的照片命名格式为'工号姓名'，例：10000张三")
        add_batch_text.pack(padx=2, pady=2, fill=tk.X)
        add_batch_file_frame = tk.Frame(add_batch_frame)
        add_batch_file_frame.pack()
        self.add_batch_file_entry_text = StringVar()
        add_bacth_file_entry = tk.Entry(
            add_batch_file_frame, textvariable=self.add_batch_file_entry_text)
        add_bacth_file_button_frame = tk.Frame(add_batch_file_frame)
        add_bacth_file_button = tk.Button(
            add_bacth_file_button_frame,
            text="打开文件夹",
            command=self.open_batch_dir)
        self.add_batch_confirm_button = tk.Button(
            add_bacth_file_button_frame,
            text="开始添加",
            command=self.start_add_batch_images)
        add_bacth_file_entry.pack()
        add_bacth_file_button_frame.pack()
        add_bacth_file_button.pack(padx=2, pady=2, side=tk.LEFT)

        search_by_id_frame = LabelFrame(
            fetch_frame,
            width=int(WINDOW_WIDTH * 0.4),
            height=int(WINDOW_HEIGHT * 0.8))
        self.search_by_id_input = tk.Entry(search_by_id_frame)
        self.search_by_id_input.insert(10, "请输入工号进行搜索")
        search_by_id_button = tk.Button(
            search_by_id_frame, text="搜索", command=self.start_search_by_id)

        search_by_id_result_label = LabelFrame(
            fetch_frame,
            text="搜索结果",
            width=int(WINDOW_WIDTH * 0.4 - 10),
            height=int(WINDOW_HEIGHT * 0.8 - 20))
        self.search_by_id_result_table = ttk.Treeview(
            search_by_id_result_label)

        vsb = ttk.Scrollbar(
            self.search_by_id_result_table,
            orient="vertical",
            command=self.search_by_id_result_table.yview)
        vsb.pack(side=tk.RIGHT)
        self.search_by_id_result_table.configure(yscrollcommand=vsb.set)

        self.search_by_id_result_table["columns"] = ("id", "name", "operate")

        self.search_by_id_result_table.column("#0", width=50, anchor="center")
        self.search_by_id_result_table.column("id", width=10, anchor="center")
        self.search_by_id_result_table.column(
            "name", width=10, anchor="center")
        self.search_by_id_result_table.column(
            "operate", width=5, anchor="center")

        self.search_by_id_result_table.heading("#0", text="照片")
        self.search_by_id_result_table.heading("#1", text="工号")
        self.search_by_id_result_table.heading("#2", text="姓名")
        self.search_by_id_result_table.heading("#3", text="操作")

        style = ttk.Style(self.root)
        style.configure("Treeview", rowheight=70)

        add_batch_frame.pack(padx=5, pady=10)
        add_batch_frame.pack_propagate(False)
        add_single_frame.pack(padx=5, pady=10)
        add_single_frame.pack_propagate(False)
        add_frame.pack(padx=5, pady=10, side=tk.LEFT)
        add_frame.pack_propagate(False)

        self.search_by_id_input.pack(padx=5, pady=10, side=tk.LEFT)
        search_by_id_button.pack(padx=5, pady=10, side=tk.LEFT)
        search_by_id_frame.pack(padx=5, pady=10)
        search_by_id_result_label.pack(
            padx=5, pady=10, fill=tk.BOTH, expand=True)
        search_by_id_result_label.pack_propagate(True)

        fetch_frame.pack(padx=5, pady=10, side=tk.LEFT)
        fetch_frame.pack_propagate(False)

        manage_frame.pack()

    def about_frame_page(self, root):
        """关于界面"""
        about_frame = tk.LabelFrame(root, text="关于", width=400)
        logo_label = tk.Label(about_frame)
        logo_image = ImageTk.PhotoImage(
            Image.open(self.config.get_logo_path()).resize((300, 100),
                                                           Image.ANTIALIAS))
        logo_label.config(image=logo_image)
        logo_label.image = logo_image
        name_label = tk.Label(
            about_frame, text=Config().SYSTEM_NAME, font=('微软雅黑', 20))
        version_label = tk.Label(
            about_frame,
            text="Version: " + self.config.VERSION,
            font=('微软雅黑', 10))
        developer_label = tk.Label(
            about_frame,
            text="Author: " + self.config.AUTHOR,
            font=('微软雅黑', 10))
        about_frame.pack(padx=5, pady=5)
        name_label.pack(padx=5, pady=5)
        version_label.pack(padx=5, pady=5)
        developer_label.pack(padx=5, pady=5)
        logo_label.pack(padx=5, pady=5)

        help_frame = LabelFrame(root, text='帮助', width=400)
        help_button = tk.Button(
            root, text="打开帮助文档", command=lambda: open_pdf(Config().help_doc))
        help_frame.pack(padx=5, pady=5)
        help_button.pack(padx=5, pady=5)

    def show_welcome_page(self):
        welcome_root = Toplevel(self.root, bg='gray', borderwidth=1)
        welcome_root.overrideredirect(True)
        welcome_root.wm_attributes('-topmost', 1)
        center_window(welcome_root, 600, 500)
        text_frame = tk.Frame(welcome_root, width=600, height=400)
        logo_label = tk.Label(text_frame)
        logo_image = ImageTk.PhotoImage(
            Image.open(self.config.get_logo_path()).resize((300, 100),
                                                           Image.ANTIALIAS))
        logo_label.config(image=logo_image)
        logo_label.image = logo_image

        welcome_image_label = tk.Label(text_frame)
        welcome_image = ImageTk.PhotoImage(
            Image.open(self.config.welcome_image_path).resize((300, 200),
                                                              Image.ANTIALIAS))
        welcome_image_label.config(image=welcome_image)
        welcome_image_label.image = welcome_image

        title_label = tk.Label(
            text_frame,
            text="欢迎使用" + Config().SYSTEM_NAME + "!",
            font=('微软雅黑', 20))
        version_label = tk.Label(
            text_frame,
            text="Version: " + self.config.VERSION,
            font=('微软雅黑', 10))
        close_button = tk.Button(
            welcome_root,
            text="关闭",
            command=lambda: self.welcome_page_on_closing(welcome_root))
        text_frame.pack_propagate(True)
        text_frame.pack(padx=2, pady=2, fill=tk.BOTH, expand=True)
        logo_label.pack(padx=3, pady=3)
        title_label.pack(padx=3, pady=3)
        version_label.pack(padx=3, pady=3)
        welcome_image_label.pack(padx=5, pady=5)
        close_button.pack(padx=2, pady=2, side=tk.BOTTOM, fill=tk.X)
        welcome_root.after(5000,
                           lambda: self.welcome_page_on_closing(welcome_root))

    def welcome_page_on_closing(self, welcome_root):
        welcome_root.destroy()
        self.root.wm_attributes('-topmost', 1)
        self.root.wm_attributes('-topmost', 0)

    def open_batch_dir(self):
        image_dir = open_dir()
        if image_dir is not None and image_dir is not "":
            self.add_batch_file_entry_text.set(image_dir)
            self.add_batch_confirm_button.pack(padx=2, pady=2)

    def get_source_image(self):
        source_image_path = open_file()
        if source_image_path is not None and source_image_path is not "":
            self.update_source_image_label(source_image_path)

    def update_source_image_label(self, source_image_path):
        """显示待查图片"""
        photo = ImageTk.PhotoImage(
            resize(WINDOW_WIDTH * 0.4 - 20, WINDOW_HEIGHT * 0.8 - 20,
                   (source_image_path)))
        self.image_label.config(image=photo)
        self.image_label.image = photo
        self.image_label.pack()
        self.search_by_face_source_image_path = source_image_path

    def update_add_single_photo(self):
        """显示待添加的照片"""
        image_path = open_file()
        if image_path is not None and image_path is not "":
            self.add_single_photo_path.set(image_path)
            photo = ImageTk.PhotoImage(resize(120, 150, (image_path)))
            self.add_single_photo_label.config(image=photo)
            self.add_single_photo_label.image = photo
            self.add_single_photo_label.pack()

    def reset_add_single_entry(self):
        """重置输入框"""
        self.add_single_id_entry.delete(0, tk.END)
        self.add_single_name_entry.delete(0, tk.END)
        self.add_single_photo_path.set("")
        self.add_single_photo_label.image = None

    def start_add_single_image(self):
        """单张照片开始入库"""
        work_id = self.add_single_id_entry.get()
        name = self.add_single_name_entry.get()
        image_path = self.add_single_photo_path.get()

        if work_id is None or work_id is "":
            messagebox.showerror("错误", "请输入工号！")
            return
        else:
            if not work_id.isdigit():
                messagebox.showerror("错误", "工号输入有误！")
                return

        if name is None or name is "":
            messagebox.showerror("错误", "请输入姓名！")
            return

        if image_path is None or image_path is "":
            messagebox.showerror("错误", "请选择照片！")
            return
        else:
            if not os.path.exists(image_path):
                messagebox.showerror("错误", "文件不存在，请重新打开！")
                return

        # 开始入库
        if self.middleware.add_face(work_id, name, image_path) is 0:
            messagebox.showinfo("提示", "添加失败！/n 照片中无法检测到人脸！")
        else:
            messagebox.showinfo("提示", "添加成功")
        self.reset_add_single_entry()

    def start_add_batch_images(self, source_images_dir=None, if_delete=False):
        """多张照片开始入库"""
        if source_images_dir is None:
            images_dir = self.add_batch_file_entry_text.get()
        else:
            images_dir = source_images_dir
        if not os.path.exists(images_dir):
            messagebox.showerror("错误", "文件夹不存在！")
            return
        logger.info("start prepare info!")
        image_path_list = get_all_file_path(images_dir)
        id_list = []
        name_list = []
        for file_path in image_path_list:
            filename = os.path.basename(file_path)
            if re.match(r"(^\d{5,6})(\D?)+\.(jpg|JPG)$", filename):
                work_id = ''.join([x for x in filename if x.isdigit()])
                id_list.append(work_id)
                if len(work_id) == (len(filename) - 4):
                    name_list.append("无")
                else:
                    name_list.append(filename[len(work_id):len(filename) - 4])
        logger.info("prepare info end!")
        # 子线程开始入库
        th = threading.Thread(
            target=self.thread_add_batch_images,
            args=(id_list, name_list, image_path_list, if_delete))
        th.setDaemon(True)
        th.start()

    def thread_add_batch_images(self,
                                id_list,
                                name_list,
                                image_path_list,
                                if_delete_source_images=False):
        self.disable_window()
        pb = ProgressBar()
        start = time.clock()
        logger.info("Add batch images begin!")
        ret = self.middleware.add_face_batch(
            [id_list, name_list, image_path_list],
            pb.callback_show_add_batch_progress, pb.if_end_add_batch_thread)
        logger.info("Add batch images end!")
        end = time.clock()
        pb.destroy_win()
        self.enable_window()

        if if_delete_source_images:
            for image_path in image_path_list:
                os.remove(image_path)
        if ret:
            message = "新添加了" + str(ret) + "条记录！\n" + "耗时" + str(
                round(end - start, 2)) + "s"
            messagebox.showinfo("提示", message)
        else:
            messagebox.showinfo("提示", "所选照片已经在库中，无需操作！")

    def start_search_by_id(self):
        """通过工号检索"""
        work_id = self.search_by_id_input.get()
        if work_id is None or work_id is "":
            messagebox.showerror("错误", "请输入工号")
        else:
            if not work_id.isdigit():
                messagebox.showerror("错误", "输入工号有误！")
            else:
                results = self.middleware.search_by_id(work_id)
                if len(results) is 0:
                    messagebox.showinfo("提示", "未找到记录！")
                else:
                    self.search_by_id_result_table.pack(
                        fill=tk.BOTH, expand=True)
                    for child in self.search_by_id_result_table.get_children():
                        self.search_by_id_result_table.delete(child)
                    self.search_by_id_result_table.bind(
                        "<Double-Button-1>", self.delete_of_search_by_id_table)
                    self.photo_to_show = []
                    for result in results:
                        name = result[2]
                        image_path = result[3]
                        self.photo_to_show.append(
                            ImageTk.PhotoImage(resize(50, 65, (image_path))))

                        self.search_by_id_result_table.insert(
                            "",
                            'end',
                            value=(work_id, name, "双击删除"),
                            image=self.photo_to_show[-1])

    def start_search_by_face(self):

        th = threading.Thread(target=self.threading_search_by_face)
        th.setDaemon(True)
        th.start()

    def threading_search_by_face(self):
        """通过人脸照片检索"""
        if self.search_by_face_source_image_path is None or self.search_by_face_source_image_path is "":
            messagebox.showerror("错误", "请先打开图片")
            return
        self.disable_window()
        pc = ProgressCircle()
        pc.show()
        self.search_by_face_result_table.pack(fill=tk.BOTH, expand=True)
        self.search_by_face_result_table.bind("<Double-Button-1>",
                                              self.show_large_image_window)
        for child in self.search_by_face_result_table.get_children():
            self.search_by_face_result_table.delete(child)

        threshold = float(self.threshold_entry.get())
        results, max_face_position, all_face_positions = self.middleware.search_by_face(
            self.search_by_face_source_image_path, threshold)
        pc.fade()
        if len(max_face_position) is 0:
            messagebox.showinfo("提示", "所选照片中无法检测到人脸！")
        else:
            self.update_source_image_with_boxes(max_face_position,
                                                all_face_positions)
            if len(results) is 0 or results is None:
                messagebox.showinfo("提示", "未找到相似度较高的人员！")
            else:
                self.photo_to_show = []
                count = 10  # 显示top10
                for result in results:
                    if count is 0:
                        break
                    count = count - 1
                    work_id = result[1]
                    name = result[2]
                    image_path = result[3]
                    score = round(result[5], 2)
                    self.photo_to_show.append(
                        ImageTk.PhotoImage(resize(50, 65, (image_path))))

                    self.search_by_face_result_table.insert(
                        "",
                        'end',
                        value=(work_id, name, score),
                        image=self.photo_to_show[-1])
        self.enable_window()

    def update_source_image_with_boxes(self, max_face_position,
                                       all_face_positions):
        source_image = cv2.imdecode(
            np.fromfile(self.search_by_face_source_image_path, dtype=np.uint8),
            cv2.IMREAD_COLOR)
        for position in all_face_positions:
            position = position.astype(int)
            cv2.rectangle(source_image, (position[0], position[1]),
                          (position[2], position[3]), (0, 255, 0), 2)
        max_face_position = max_face_position.astype(int)
        cv2.rectangle(
            source_image, (max_face_position[0], max_face_position[1]),
            (max_face_position[2], max_face_position[3]), (0, 0, 255), 3)
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)
        tmp_image_path = self.tmp_dir + os.path.basename(
            self.search_by_face_source_image_path)
        cv2.imencode('.jpg', source_image)[1].tofile(tmp_image_path)
        photo = ImageTk.PhotoImage(
            resize(WINDOW_WIDTH * 0.4 - 20, WINDOW_HEIGHT * 0.8 - 20,
                   (tmp_image_path)))
        self.image_label.config(image=photo)
        self.image_label.image = photo
        # self.image_label.pack()

    def delete_of_search_by_id_table(self, event):
        """通过工号删除"""
        info = []
        for item in self.search_by_id_result_table.selection():
            values = self.search_by_id_result_table.item(item, "value")
            info.append(values)
        if len(info) is not 0:
            if messagebox.askyesno(
                    "提示", "删除员工 " + str(info[0][0]) + str(info[0][1]) + "?"):
                self.middleware.delete_by_id(info[0][0])
                for child in self.search_by_id_result_table.get_children():
                    self.search_by_id_result_table.delete(child)

    def thread_check_auto_add_dir(self):
        logger.debug("start check auto add!")
        auto_add_dir = self.config.auto_add_dir
        if os.path.exists(auto_add_dir) and os.listdir(auto_add_dir):
            if messagebox.askyesno('提示', '检测到新图片，是否立刻添加？'):
                self.start_add_batch_images(auto_add_dir, True)

    def check_auto_add_dir(self):
        th = threading.Thread(target=self.thread_check_auto_add_dir)
        th.setDaemon(True)
        th.start()

    def show_large_image_window(self, event):
        """显示检索结果照片的大图"""
        info = []
        for item in self.search_by_face_result_table.selection():
            values = self.search_by_face_result_table.item(item, "value")
            info.append(values)
        if len(info) is not 0:
            results = self.middleware.search_by_id(info[0][0])
            if len(results) is not 0:
                image_path = results[0][3]
                Image.open(image_path).show()
            else:
                messagebox.showerror("错误", "无法显示原始照片！")

    def enable_window(self):
        self.root.attributes('-disabled', False)

    def disable_window(self):
        self.root.attributes('-disabled', True)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            # 清空临时文件夹中的文件
            for root, dirs, files in os.walk(self.tmp_dir):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            self.root.destroy()

    def init_gui(self):
        self.root = Tk()
        self.show_welcome_page()
        self.root.title(Config().SYSTEM_NAME)
        center_window(self.root, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.root.resizable(width=False, height=False)
        self.ui_process()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
