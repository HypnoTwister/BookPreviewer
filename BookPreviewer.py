import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import  *
from PyQt5.QtCore import *
import math
import os
import re
import csv
import datetime

def resource_path(relativePath):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relativePath)

# READING = "第2章-第1节.txt"
# READING = "测试文章.txt"

PUNCTUATION_STR = r'；：\-，。“”‘’？——！《》￥@#%……&*（）|、~·【】'
LETTERS = 'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'
NUMS = '1234567890'
WEEK = ['周一','周二','周三','周四','周五','周六','周日']
BACKGROUND_PNG = resource_path("resources/background.png")
CUSTOM_FONTS = resource_path("resources/MiSans-Normal.ttf")
# ICON_PATH = resource_path("resources/book.ico")
ICON_PATH = resource_path("resources/smartphone.png")
CSV_COUNTER = resource_path('resources/writingcounter.csv')

# BOOK_SHELF = os.path.dirname(os.path.abspath(__file__))
BOOK_SHELF = r'D:\Documents\Books\Writing'
# RARE_CHS = r'[\u3400-\u4DBF\uF900-\uFAFF\U00020000-\U0002EBEF]'
COMMON_CHS = r'[\u4E00-\u9FFF\u3400-\u4DBF]'
NOT_COMMON = rf'[^{PUNCTUATION_STR}{LETTERS}{NUMS}\u4E00-\u9FFF \n]'
NUMBER = r'([0-9]+)'

def load_custom_font():
    """加载自定义字体"""
    font_id = QFontDatabase.addApplicationFont(CUSTOM_FONTS)
    if font_id == -1:
        print(f"Failed to load font from {CUSTOM_FONTS}")
    else:
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        return font_family
    return '微软雅黑'

class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None, logger = None):
        super().__init__(parent)
        self.setReadOnly(True)
        # 禁用文本框的焦点获取，确保点击不影响光标位置
        self.setFocusPolicy(Qt.NoFocus)
        # 禁用选择文本功能
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setCursor(Qt.ArrowCursor)
        self.currentBlock = 0
        self.logger = logger
        # self.setAutoFillBackground(False)
        # # 添加事件过滤器
    #     self.installEventFilter(self)

    # def eventFilter(self, obj, event):
    #     if event.type() in [QEvent.MouseButtonPress, QEvent.MouseButtonRelease]:
    #         # 禁用所有鼠标点击事件，使其不响应任何点击
    #         return True
    #     return super().eventFilter(obj, event)

    def wheelEvent(self, event):
        # 处理滚轮事件以确保可以滚动
        self.refreshingBlockNum(event)
        super().wheelEvent(event)

    # def mousePressEvent(self, event):
    #     # 获取当前点击的block号
    #     cursor = self.cursorForPosition(event.pos())
    #     block_number = cursor.blockNumber()
    #     print(f"Clicked on block number: {block_number}")
    #     super().mousePressEvent(event)

    # def mouseDoubleClickEvent(self, event):
    #     # 禁用鼠标 DoubleClick
    #     pass

    # def mouseReleaseEvent(self, event):
    #     # 禁用鼠标释放事件
    #     pass

    # def enterEvent(self, event):
    #     # 禁用鼠标 enter
    #     self.setCursor(Qt.ArrowCursor)  # 将光标设置为箭头形状
    #     super().enterEvent(event)
    #     # pass

    def mouseMoveEvent(self, event):
         # 获取当前点击的block号
        self.refreshingBlockNum(event)
        super().mouseMoveEvent(event)

    def refreshingBlockNum(self, event):
        if isinstance(self.logger, QLabel):
            cursor = self.cursorForPosition(event.pos())
            self.currentBlock = cursor.blockNumber()+1
            self.logger.setText(f'当前:{self.currentBlock}')

class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        # 设置窗口大小和标题
        self.setWindowTitle("Phone Simulator")
        # self.setGeometry(100, 100, 360, 801)
        self.main_height = 750
        self.main_width = int(9.5/20 * self.main_height)
        self.content_width = self.main_width - self.main_width//6
        self.content_height = int(27/32*self.main_height)
        self.edge_spacing = self.main_height//40
        self.head_btn_size = self.main_height//32
        self.setFixedSize(self.main_width, self.main_height)
        # 禁用窗口装饰，模拟手机屏幕外观
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)  # 使窗口背景透明

        # 初始化变量用于跟踪鼠标移动
        self.old_pos = None

        # 设置背景图
        self.set_background_image(BACKGROUND_PNG)

        # # 加载自定义字体
        # self.load_custom_font(CUSTOM_FONTS)

        # 强行控制每行显示的可见行数
        self.fixed_visible_lines = 25  # 例如，固定显示10行

        self.add_floating_buttons()

        self.novel_content = ''
        self.header = ["date","count"]

        # Create a QVBoxLayout
        layout = QVBoxLayout(self)
        # 📅📊📈📆🗃️📇📱

        headerline = QVBoxLayout()
        header = QHBoxLayout()
        self.comb_file = QComboBox(self)
        self.collect_files = []
        self.refresh_mark = False
        self.refresh_items()
        self.comb_file.setMaximumWidth(self.content_width)

        header.addSpacing(self.edge_spacing)
        header.addWidget(self.comb_file)
        self.btn_open = QPushButton('...')
        self.btn_open.setObjectName('square')
        self.btn_open.setFixedWidth(self.head_btn_size)
        self.btn_open.setFixedHeight(self.head_btn_size)
        self.btn_open.clicked.connect(self.open_folder)
        self.btn_tabs = QPushButton('A')
        # self.btn_tabs.setCheckable(True)
        # self.btn_tabs.setChecked(True)
        self.btn_tabs.setObjectName('ico')
        self.btn_tabs.setFixedWidth(self.head_btn_size)
        self.btn_tabs.setFixedHeight(self.head_btn_size)
        self.btn_tabs.clicked.connect(self.tab_switching)

        self.btn_close = QPushButton('✕')
        self.btn_close.setObjectName('Warning')
        self.btn_close.clicked.connect(QApplication.instance().quit)
        self.btn_close.setFixedWidth(self.head_btn_size)
        self.btn_close.setFixedHeight(self.head_btn_size)

        header.addWidget(self.btn_open)
        header.addWidget(self.btn_tabs)
        header.addWidget(self.btn_close)
        header.addSpacing(self.edge_spacing)
        headerline.addWidget(QLabel(''))
        headerline.addLayout(header)
        headerline.addSpacing(2)
        layout.addLayout(headerline)

        # --------------------小说内容----------------------
        content = QHBoxLayout()
        # 创建一个 QTextEdit 用于显示小说内容
        self.text_edit = CustomTextEdit(self)
        self.text_edit.setFixedHeight(self.content_height)
        self.text_edit.setFixedWidth(self.content_width)
        # self.text_edit.setEnabled(False)
        self.text_edit.setStyleSheet("background: transparent; color: black; border: none;")
        # Add QTextEdit to the layout

        content.addStretch()
        content.addWidget(self.text_edit)
        content.addStretch()

        footer = QHBoxLayout()
        self.counter = QLabel(self.get_counter_label())
        self.counter.setContentsMargins(self.edge_spacing,0,0,0)
        self.block_pos=QLabel(f'当前: {self.text_edit.currentBlock}')
        self.block_pos.setContentsMargins(0,0,self.edge_spacing,0)
        self.text_edit.logger = self.block_pos
        footer.addWidget(self.counter)
        footer.addWidget(self.block_pos)
        footer.setAlignment(Qt.AlignBottom)  # Set alignment to right

        # 禁用滚动条
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 让 QTextEdit 不接受鼠标事件
        # self.text_edit.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.lines = self.novel_content.split('\n')

        # 加载文档
        self.comb_file.currentTextChanged.connect(self.reload_novel_from_combo)
        self.comb_file.setCurrentIndex(1)

        # 设置鼠标滚动时一次滚动多行
        scrollbar = self.text_edit.verticalScrollBar()
        scrollbar.setSingleStep(5 * self.text_edit.fontMetrics().height())

        # self.text_edit.setText(self.novel_content)
        self.adjust_scrollbar()
        self.adjust_line_height()

        # self.highlight_rare_ch()
        self.highlight_text()
        layout.addLayout(content)
        layout.addLayout(footer)

        # ------------------------------------------

        # --------------------图表----------------------
        content = QHBoxLayout()
        self.diagram_page = QScrollArea()
        self.diagram_page.setObjectName('srcArea')
        # self.diagram_page.setWidgetResizable(True)
        self.diagram_page.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.diagram_page.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.diagram_page.setViewportMargins(-10,0,0,0)
        self.diagram_page.setContentsMargins(0,0,0,0)
        self.diagram_page.setFixedWidth(self.content_width)
        self.diagram_page.setFixedHeight(self.content_height)

        self.diagram_page_widget = QWidget()
        self.diagram_page_widget.setObjectName('srcArea')
        self.diagram_page_widget.setContentsMargins(0,0,0,0)
        # self.diagram_page_widget.setFixedWidth(self.content_width)
        # self.diagram_page_widget.setFixedHeight(self.content_height)

        self.diagram_page_layout = QVBoxLayout(self.diagram_page_widget)
        self.diagrams_page_gui()
        self.diagram_page.setWidget(self.diagram_page_widget)
        content.addSpacing(self.edge_spacing)
        content.addWidget(self.diagram_page)
        content.addStretch()
        layout.addLayout(content)
        # ----------------------End----------------------

        self.switch_to_book_content(True)
        layout.addStretch()
        self.setLayout(layout)

    def tab_switching(self):
        if self.btn_tabs.text() != 'A':
            self.btn_tabs.setText("A")
            self.switch_to_book_content(True)
        else:
            self.btn_tabs.setText("↗")
            self.switch_to_book_content(False)

    def set_layout_vis(self, layout, visible):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if isinstance(item, QWidgetItem):
                widget = item.widget()
                if widget is not None:
                    widget.setVisible(visible)
            elif isinstance(item, QLayoutItem):
                sub_layout = item.layout()
                if sub_layout is not None:
                    self.set_layout_vis(sub_layout, visible)

    def switch_to_book_content(self, visible):
        self.update_diagrams()
        self.text_edit.setVisible(visible)
        self.counter.setVisible(visible)
        self.block_pos.setVisible(visible)
        self.diagram_page.setVisible(not(visible))
        self.diagram_page_widget.setVisible(not(visible))
        self.set_layout_vis(self.diagram_page_layout, not(visible))

    def diagrams_page_gui(self):
        week_widget = QWidget()
        diagram_week = QVBoxLayout()
        week_widget.setLayout(diagram_week)
        week_widget.setObjectName('borderblock')
        week_widget.setFixedWidth(self.content_width-6)
        today = datetime.date.today()
        weekfrom = today-datetime.timedelta(days=6)
        lbl_week = QLabel(f'周视图: {weekfrom.month}/{weekfrom.day}-{today.month}/{today.day}')
        lbl_week.setObjectName('HeaderGraph')
        self.lyt_weekBars = QVBoxLayout()

        for i in range(7):
            linebar = QHBoxLayout()
            lbl_weekname = QLabel('')
            lbl_weekname.setObjectName('SubGraph')
            # lbl_weekname.setFixedWidth(self.content_width*10//100)
            linebar.addWidget(lbl_weekname)
            # lbl_bar = QLabel('')
            # # lbl_bar.setObjectName('bar')
            # linebar.addWidget(lbl_bar)
            lbl_bar = QProgressBar()
            # lbl_bar.setObjectName('bar')
            linebar.addWidget(lbl_bar)
            linebar.addStretch()
            self.lyt_weekBars.addLayout(linebar)
        diagram_week.addWidget(lbl_week)
        diagram_week.addLayout(self.lyt_weekBars)
        # self.diagram_page.addWidget(week_widget)
        self.diagram_page_layout.addWidget(week_widget)


        # ----------------------------------------------------------
        month_widget = QWidget()
        diagram_month = QVBoxLayout()
        month_widget.setLayout(diagram_month)
        month_widget.setObjectName('borderblock')
        month_widget.setFixedWidth(self.content_width-6)

        lbl_month = QLabel(f'月视图: {today.month}月')
        lbl_month.setObjectName('HeaderGraph')
        self.month_graph = QHBoxLayout()
        self.month_list = QVBoxLayout()
        month_range = self.get_current_monthdays(datetime.date.today())

        offset = 6
        lastm = 0
        for m in range(month_range):
            currentlbl = (m//3)+1
            if currentlbl == lastm and m!=0: continue
            lastm = currentlbl
            # offset_date = datetime.date.today() - datetime.timedelta(m)
            lbl_str = str(m+1)
            lbl_dayname = QLabel(lbl_str)
            lbl_dayname.setObjectName('month_day')
            lbl_dayname.setAlignment(Qt.AlignTop)
            lbl_dayname.setFixedHeight(28)
            self.month_list.addWidget(lbl_dayname)
        # self.month_list.addStretch()
        self.month_list.addSpacing(offset)
        # self.month_list.setFixedWidth(self.content_width*10//100)
        lyt_vbox = QVBoxLayout()
        self.lyt_monthBars = QVBoxLayout()
        lyt_vbox.addSpacing(offset)
        for i in range(month_range):
            lbl_bar = QLabel('')
            lbl_bar.setFixedWidth(0)
            lbl_bar.setFixedHeight(6)
            self.lyt_monthBars.addWidget(lbl_bar)
        self.lyt_monthBars.addStretch()
        lyt_vbox.addLayout(self.lyt_monthBars)
        self.month_graph.addLayout(self.month_list)
        self.month_graph.addLayout(lyt_vbox)
        self.month_graph.addStretch()

        diagram_month.addWidget(lbl_month)
        diagram_month.addLayout(self.month_graph)
        self.diagram_page_layout.addWidget(month_widget)

        self.diagram_page_layout.addStretch()

    def update_diagrams(self):
        self.records = self.get_records()
        self.update_week_diagram()
        self.update_month_diagram()

    def update_week_diagram(self):
        self.records_in_week = self.filted_date()
        # print(self.records_in_week)
        max_count = max(self.records_in_week.values(), default=1)
        max_barwidth = self.content_width*88//100 - self.edge_spacing - 8
        today = datetime.date.today()
        for i in range(7):
            date = today-datetime.timedelta(days=6) + datetime.timedelta(days=i)
            count = self.records_in_week.get(date, 0)
            barname = self.lyt_weekBars.itemAt(i).layout().itemAt(0).widget()
            bar = self.lyt_weekBars.itemAt(i).layout().itemAt(1).widget()
            if isinstance(barname, QLabel):
                if i==6 :barname.setText('今')
                else: barname.setText(str(date.day))
                barname.setFixedWidth(16)
            if isinstance(bar, QProgressBar):
                bar_width = count*100//max_count
                bar.setMaximum(100)
                if bar_width<0:
                    bar_width = abs(bar_width)
                    bar.setObjectName('bar-minus')
                elif bar_width == 0:
                    bar.setObjectName('bar-zero')
                elif i==today.day-1:
                    bar.setObjectName('bar-h')
                else:
                    bar.setObjectName('bar')
                bar_width = max(2,bar_width)
                bar.setValue(bar_width)
                bar.setFixedWidth(max_barwidth)
                bar.setTextVisible(True)
                bar_value = f" {count}"
                bar.setFormat(bar_value)
                # font_metrics = QFontMetrics(bar.font())
                # text_width = font_metrics.horizontalAdvance(bar_value)
                # progress_bar_length = bar_width * max_barwidth // 100
                # if text_width > progress_bar_length:
                #     shift = " "*(progress_bar_length//5)
                #     bar.setFormat(f"{shift}{bar_value}")
                # bar = QProgressBar()
                bar.setAlignment(Qt.AlignmentFlag.AlignVCenter)

    def update_month_diagram(self):
        self.records_in_month = self.filted_date('month')
        print(self.records_in_month)
        today = datetime.date.today()
        # day_range = (today - today.replace(day=1) + datetime.timedelta(days = 1)).days
        month_range = self.get_current_monthdays(datetime.date.today())
        max_count = max(self.records_in_month.values(), default=1)
        max_barwidth = self.content_width*90//100 - self.edge_spacing
        print(month_range)
        for i in range(month_range):
            date = today.replace(day=1) + datetime.timedelta(days=i)
            count = self.records_in_month.get(date, 0)
            bar = self.lyt_monthBars.itemAt(i).widget()
            if isinstance(bar, QLabel):
                bar_width = count*max_barwidth//max_count
                print(bar_width)
                if bar_width<0:
                    bar_width = abs(bar_width)
                    bar.setObjectName('bar-minus')
                elif count == 0:
                    bar.setObjectName('bar-zero')
                elif i==today.day-1:
                    bar.setObjectName('bar-h')
                else:
                    bar.setObjectName('bar')
                bar_width = max(5,bar_width)
                bar.setFixedWidth(bar_width)
            # print(f"Date[{date}] >>>> {count}")

    def filted_date(self, mode = 'week'):
        today = datetime.date.today()
        if mode == 'week':
            last_monday = today - datetime.timedelta(days=6)
            records_in_range = {}
            for k in self.records:
                if k >= last_monday:
                    records_in_range[k] = self.records[k]
            # print(records_in_range)
            return records_in_range
        elif mode == 'month':
            first_of_month = today.replace(day=1)
            records_in_range = {}
            for k in self.records:
                if k >= first_of_month:
                    records_in_range[k] = self.records[k]
            # print(records_in_range)
            return records_in_range
        return {}

    def add_floating_buttons(self):
        # 创建悬浮按钮
        self.floating_button1 = QPushButton('', self)
        self.floating_button2 = QPushButton('', self)
        self.floating_button3 = QPushButton('', self)

        self.floating_button1.setObjectName('sidebar')
        self.floating_button2.setObjectName('sidebar')
        self.floating_button3.setObjectName('sidebar')

        # 设置按钮大小
        w = int(0.045*self.main_width)
        h = int(0.06*self.main_height)
        h3 = int(0.0725*self.main_height)
        self.floating_button1.setFixedSize(w, h)
        self.floating_button2.setFixedSize(w, h)
        self.floating_button3.setFixedSize(w, h3)

        # 设置按钮位置
        v = int(0.175*self.main_height)
        self.floating_button1.move(self.main_width-w, v)  # 绝对位置
        self.floating_button2.move(self.main_width-w, v+h)  # 绝对位置
        self.floating_button3.move(self.main_width-w, int(0.3675*self.main_height))  # 绝对位置

        self.floating_button1.clicked.connect(self.on_floating_button1_clicked)
        self.floating_button2.clicked.connect(self.on_floating_button2_clicked)
        self.floating_button3.clicked.connect(self.on_floating_button3_clicked)
        self.matchNext = 0

    def get_records(self):
        date_counts = {}
        with open(CSV_COUNTER, mode='r', newline='') as file:
            reader = csv.reader(file)
            readerlist = list(reader)
            for i in range(len(readerlist)):
            # for row in reader:
                row = readerlist[i]
                date_str= row[0]
                count = row[1]
                date = self.get_datetime(date_str)
                added = int(count)
                if i >0 : added = added - int(readerlist[i-1][1])
                date_counts[date] = added
        return date_counts
    def get_current_monthdays(self, now):
        # 获取当前日期
        # now = datetime.date.today()
        # 计算下个月的第一天
        next_month = datetime.date.today()
        if now.month == 12:
            next_month = datetime.date(now.year + 1, 1, 1)
        else:
            next_month = datetime.date(now.year, now.month + 1, 1)
        # 当前月份的最后一天
        last_day_of_current_month = next_month - datetime.timedelta(days=1)
        days_in_month = last_day_of_current_month.day

        print(f"当前月份的天数: {days_in_month}")
        return days_in_month

    def update_writing_count(self):
        self.records = self.get_records()
        current_count = self.get_writing_count()
        last_date = list(self.records.keys())[-1]
        # last_date = self.get_datetime(self.records[-1]['date'])
        today = datetime.date.today()
        # yesterday = self.get_yesterday(today)
        # if yesterday > last_date:
        # additional = current_count - int(self.last_record['count'])
        # print(f"{today}|{last_date}---{additional}")
        new_row = [str(today),str(current_count)]

        with open(CSV_COUNTER, mode='r', newline='') as file:
            reader = csv.reader(file)
            rows = list(reader)

        # 修改最后一行或追加新行
        if today != last_date:
            rows.append(new_row)
        else:
            rows[-1] = new_row

        # 将修改后的内容写回 CSV 文件
        with open(CSV_COUNTER, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)

    def get_datetime(self, str_day):
        return datetime.datetime.strptime(str_day, '%Y-%m-%d').date()

    def get_yesterday(self, daytime):
        return daytime - datetime.timedelta(days=1)

    def get_writing_count(self):
        total = 0
        for f_name in self.txt_files:
            f_path  = os.path.join(BOOK_SHELF, f_name)
            f_path = f_path.replace('\\','/')
            if f_path.endswith('/'): f_path = f_path[0:-1]
            if not os.path.exists(f_path): continue
            try:
                with open(f_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    clean_content = content.replace('\n','').replace(' ','')
                    total += len(clean_content)
            except:
                continue
        return total

    def on_floating_button1_clicked(self):
        if self.fixed_visible_lines > 2:
            self.fixed_visible_lines -= 1
            self.adjust_scrollbar()
            self.adjust_line_height()
        print('Font Size Add!')

    def on_floating_button2_clicked(self):
        if self.fixed_visible_lines< 100:
            self.fixed_visible_lines += 1
            self.adjust_scrollbar()
            self.adjust_line_height()
        print('Font Size Minus!')

    def on_floating_button3_clicked(self):
        if len(self.matched_positions) == 0 : return
        if self.matchNext >= len(self.matched_positions):
            self.matchNext = 0
        if self.matchNext < 0:
            self.matchNext = len(self.matched_positions)-1
        pos = self.matched_positions[self.matchNext]
        self.scroll_to_character(pos)
        self.matchNext += 1

    def scroll_to_character(self, position):
        """滚动到特定字符位置所在的块"""
        document = self.text_edit.document()
        block = document.findBlock(position)
        # 获取滚动条
        scrollbar = self.text_edit.verticalScrollBar()
        # 获取块的垂直位置
        block_rect = self.text_edit.document().documentLayout().blockBoundingRect(block)
        block_top = int(block_rect.top())
        # 设置滚动条位置
        scrollbar.setValue(block_top)

    def open_folder(self):
        global BOOK_SHELF

        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            BOOK_SHELF = folder_path
            self.refresh_items()
            self.reload_novel_from_combo(True)

    def highlight_text(self):
        currentFile = self.comb_file.currentText()
        if currentFile.startswith('Doc_'): return
        # pass
        text = self.text_edit.toPlainText()
        pattern = re.compile(NOT_COMMON)

        # 使用 \g<0> 来引用整个匹配结果
        highlighted_text = pattern.sub(r'<span style="color:red;">\g<0></span>', text)

        # 获取匹配到的位置
        matches = pattern.finditer(text)
        self.matched_positions = [match.start() for match in matches]
        # 根据匹配到的位置找到所在的block
        self.matched_blocks = []
        for pos in self.matched_positions:
            for i in range(self.text_edit.document().blockCount()):
                if i+1 in self.matched_blocks: continue
                block = self.text_edit.document().findBlockByNumber(i)
                if block.position()<= pos < block.position() + block.length():
                    self.matched_blocks.append(i+1)
                    break
        # print(f"Match found in block Num: {self.matched_blocks}")
        # 使用 CSS 样式来保留空格和换行
        html_text = f'<div style="white-space: pre-wrap;">{highlighted_text}</div>'

        # 设置 HTML 格式的文本到 QTextEdit
        self.text_edit.setHtml(html_text)

    def get_counter_label(self):
        clean_content = self.novel_content.replace('\n','').replace(' ','')
        total = len(clean_content)

        chinese_characters = re.findall(COMMON_CHS, clean_content)
        chinese_count = len(chinese_characters)

        # 匹配生僻汉字
        rare_chinese_characters = re.findall(NOT_COMMON, clean_content)
        rare_chinese_count = len(rare_chinese_characters)

        count_text = f'总字符: {total} 汉字: {chinese_count} 警告: {rare_chinese_count}  '
        return count_text

    def reload_novel_from_combo(self, keep_scroll = False):
        scroll_position = self.text_edit.verticalScrollBar().value()
        self.novel_content = self.load_novel(self.comb_file.currentText())
        self.text_edit.setText(self.novel_content)

        self.counter.setText(self.get_counter_label())
        self.highlight_text()

        if keep_scroll:
            # 恢复滚动条位置
           self.text_edit.verticalScrollBar().setValue(scroll_position)
           print(f"refresh to scroll back! (scroll_position : {scroll_position})")

    def refresh_items(self):
        pre_sel = self.comb_file.currentText()
        files = self.get_files_from_dir()
        if files != self.collect_files:
            print("File Changed!!")
            self.collect_files = files
            self.txt_files = [f for f in files if not f.startswith('Doc_')]
            self.comb_file.clear()
            for file in files:
                self.comb_file.addItem(file)
            if pre_sel in files:
                self.comb_file.setCurrentText(pre_sel)

    def get_files_from_dir(self):
        global BOOK_SHELF
        try:
            # dir = os.path.dirname(os.path.abspath(__file__))
            if not os.path.exists(BOOK_SHELF): return []
            files = [f for f in os.listdir(BOOK_SHELF) if os.path.isfile(os.path.join(BOOK_SHELF, f)) and f.endswith('.txt')]
            nums = [f for f in files if re.search(NUMBER, f)]
            unnums = [f for f in files if f not in nums]
            sorted_fs = sorted(nums, key=lambda x: int(re.search(NUMBER, x).group()), reverse=True)
            files = unnums + sorted_fs
            return files
        except PermissionError as e:
            print(f"PermissionError: {e}")
            return []

    def load_novel(self, file_name:str):
        """加载小说内容"""
        try:
            file_path  = os.path.join(BOOK_SHELF,file_name)
            file_path = file_path.replace('\\','/')
            if file_path.endswith('/'): file_path = file_path[0:-1]
            if not os.path.exists(file_path): return ''
            print(file_path)
            # file_path = resource_path(file_path)
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                if file_name.startswith('Doc_'): return ''.join(lines)
                pattern = r"//.*$"
                repeatEmpty = r'[\n]{3,}'
                cleaned_lines = [re.sub(pattern, '', line).strip() for line in lines]
                content = '\n'.join(cleaned_lines)
                content = re.sub(repeatEmpty,'\n\n',content)
                content = re.sub(r'[\n]','\n    ',content)
                return content  # 使用 read 读取整个文件的内容
        except PermissionError as e:
            print(f"PermissionError: {e}")
            return ''

    # def load_custom_font(self, font_path):
    #     """加载自定义字体"""
    #     font_id = QFontDatabase.addApplicationFont(font_path)
    #     if font_id == -1:
    #         print(f"Failed to load font from {font_path}")
    #     else:
    #         font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
    #         self.custom_font_family = font_family

    # def set_fonts(self):
    #     """设置字体大小"""
    #     # font = self.text_edit.font()
    #     # font.setPointSize(size)
    #     font = QFont(self.custom_font_family)
    #     self.text_edit.setFont(font)

    def set_background_image(self, image_path):
        # 创建一个 QLabel 并设置背景图
        label = QLabel(self)
        pixmap = QPixmap(image_path)

        # 使用 QPixmap 创建带有透明度的背景图
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.end()

        label.setPixmap(pixmap)

        # 将 QLabel 大小设置为窗口大小
        label.resize(self.size())
        label.setScaledContents(True)  # 图片缩放以适应窗口大小

    def leaveEvent(self, event):
        self.refresh_mark = True

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            click_x = event.x()
            click_y = event.y()
            window_width = self.width()
            window_height = self.height()

            # if click_y < window_height / 2:
                # 上半部分点击，进行窗口拖动
            self.old_pos = event.globalPos()
            self.RefreshingTxtLoad()

    def RefreshingTxtLoad(self):
        if self.refresh_mark:
            print('Try Refreshing!')
            self.refresh_items()
            self.reload_novel_from_combo(True)
            self.refresh_mark = False
                # print(self.text_edit.document().blockCount())
                # print(self.get_visible_line_count())
                # print(self.get_line_count())
                # self.novel_content = self.set_text_content(READING)
                # self.text_edit.setFixedHeight(self.get_visible_line_count(True))
            # else:
            #     # 下半部分点击，区分左侧和右侧
            #     if click_x < window_width / 2:
            #         self.previous_page()
            #     else:
            #         self.next_page()

    def mouseMoveEvent(self, event):
        # 计算鼠标移动的距离，并移动窗口（仅当在上半部分点击时有效）
        # if event.button() == Qt.LeftButton:
        if self.old_pos:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    # def mouseReleaseEvent(self, event):
    #     # 鼠标释放时重置 old_pos
    #     self.old_pos = None
    #     self.refresh_items()
    #     self.reload_novel_from_combo(True)

    def mouseReleaseEvent(self, event):
        # 鼠标释放时重置 old_pos
        if event.button() == Qt.LeftButton:
            self.old_pos = None

    def enterEvent(self, event):
        self.RefreshingTxtLoad()
        self.update_writing_count()

    # def contextMenuEvent(self, event):
    #     self.refresh_items()
    #     self.reload_novel_from_combo(True)

    def set_text_content(self, filepath):
        """设置文本内容并调整滚动条位置"""
        text = self.load_novel(filepath)
        # self.text_edit.setPlainText(self.pad_text(text))
        return self.pad_text(text)

    def pad_text(self, text):
        """在文本末尾填充空行以补全最后一页"""
        lines = text.split('\n')
        total_lines = len(lines)
        lines_per_page = self.fixed_visible_lines

        # 计算需要填充的空行数
        padding_lines = lines_per_page - (total_lines % lines_per_page)
        if padding_lines != lines_per_page:
            lines.extend([''] * padding_lines)

        return '\n'.join(lines)

    def adjust_scrollbar(self):
        """调整滚动条位置，使其对齐到最近的完整行"""
        scroll_bar = self.text_edit.verticalScrollBar()
        current_value = scroll_bar.value()

        # 调整滚动条位置，使其对齐到最近的完整行
        scroll_bar.setValue(current_value - (current_value % self.text_edit.fontMetrics().lineSpacing()))

    def adjust_line_height(self):
        """调整行高以控制每行显示的可见行数"""
        viewport_height = self.text_edit.viewport().height()
        line_height = viewport_height // self.fixed_visible_lines

        font = self.text_edit.font()
        fontsize = line_height / self.text_edit.fontMetrics().height() * font.pointSizeF()
        print(f"fontsize:{fontsize}")
        font.setPointSizeF(fontsize)
        self.text_edit.setFont(font)

    def get_line_count(self):
        """获取当前显示的行数，包括自动折叠的行数"""
        text_edit = self.text_edit
        document = text_edit.document()

        # 获取文本编辑器的可见区域
        viewport_height = text_edit.viewport().height()
        scroll_bar_value = text_edit.verticalScrollBar().value()
        block = document.begin()
        visible_lines = 0

        # 遍历所有文本块，计算可见的块数量
        while block.isValid():
            layout = block.layout()
            block_rect = layout.boundingRect()
            block_top = block_rect.top() + layout.position().y() - scroll_bar_value
            block_bottom = block_rect.bottom() + layout.position().y() - scroll_bar_value

            if block_top >= 0 and block_bottom <= viewport_height:
                visible_lines += 1
            elif block_top >= viewport_height:
                break
            block = block.next()

        return visible_lines

    def get_visible_line_count(self, fixedheight = False):
        """获取当前显示的行数，包括自动折叠的行数"""
        document = self.text_edit.document()
        total_lines = 0

        cursor = QTextCursor(document)
        cursor.movePosition(QTextCursor.Start)
        viewport_height = self.text_edit.viewport().height()

        while cursor.block().isValid():
            block = cursor.block()
            layout = block.layout()
            if layout:
                block_rect = self.text_edit.cursorRect(cursor)
                if block_rect.top() > viewport_height:
                    break
                if block_rect.bottom() >= 0:
                    total_lines += layout.lineCount()
            cursor.movePosition(QTextCursor.NextBlock)
                    # 检查是否到达最后一个块
            if not cursor.block().next().isValid():
                break
            # print(f"top: {block_rect.top()} -> viewport_height: {viewport_height} -> bottom: {block_rect.bottom()}")
            # n = total_lines if total_lines != 0 else 1
            # print(f"{total_lines}:{viewport_height}-> {math.ceil(675/(n))} -> {675//math.ceil(675/(n))}")
        if fixedheight:
            lineHeight = (self.content_height//math.ceil(self.content_height/total_lines))*math.ceil(self.content_height/total_lines)
            # print(f"lineHeight:{lineHeight}")
            return lineHeight
        return total_lines


class QSSLoader:
    def __init__(self):
        pass

    @staticmethod
    def read_qss_file(qss_file_name):
        qss_file_name = resource_path(qss_file_name)
        with open(qss_file_name, 'r',  encoding='UTF-8') as file:
            return file.read()

QSS_PATH = 'resources/style.qss'


# 示例使用
if __name__ == "__main__":
    # from PyQt5.QtWidgets import QApplication
    # import sys
    style_sheet = QSSLoader.read_qss_file(QSS_PATH)
    app = QApplication(sys.argv)
    icon =  QIcon(ICON_PATH)
    app.setWindowIcon(icon)
    GFont = QFont(load_custom_font())
    # GFont = QFont('微软雅黑')
    GFont.setPointSizeF(8)
    app.setFont(GFont)
    window = MainUI()
    window.setStyleSheet(style_sheet)
    window.setWindowIcon(icon)
    window.show()
    sys.exit(app.exec())

