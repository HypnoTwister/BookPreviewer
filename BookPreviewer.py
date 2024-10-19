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

MainUIHeigthInch = 5.91

PUNCTUATION_STR = r'；：\-，。“”‘’？——！《》￥@#%……&*（）|、~·【】'
LETTERS = 'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'
NUMS = '1234567890'
WEEK = ['周一','周二','周三','周四','周五','周六','周日']
BACKGROUND_PNG = resource_path("resources/background.png")
CUSTOM_FONTS = resource_path("resources/TempFont.ttf")
# ICON_PATH = resource_path("resources/book.ico")
ICON_PATH = resource_path("resources/smartphone.png")
# CSV_COUNTER = resource_path('resources/writingcounter.csv')
CSV_COUNTER = ''

local_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Local')
PRESET_PATH = os.path.join(local_path,'BookPreviewer/preset.txt').replace('\\','/')
BOOK_SHELF = r''

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
    return '等线'

class CustomHLine(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText('')
        self.setObjectName('Hline')
        self.setFixedHeight(1)
        self.setMargin(0)
        self.setContentsMargins(0,0,0,0)

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

    def wheelEvent(self, event):
        # 处理滚轮事件以确保可以滚动
        self.refreshingBlockNum(event)
        super().wheelEvent(event)

    def mouseMoveEvent(self, event):
         # 获取当前点击的block号
        self.refreshingBlockNum(event)
        super().mouseMoveEvent(event)

    def refreshingBlockNum(self, event):
        if isinstance(self.logger, QLabel):
            cursor = self.cursorForPosition(event.pos())
            self.currentBlock = cursor.blockNumber()+1
            self.logger.setText(f'当前:{self.currentBlock}')

class ClickableProgressBar(QProgressBar):
    hover = pyqtSignal(object)  # 修改信号定义，使其接受一个参数

    def __init__(self, parent=None, info=None):
        super().__init__(parent)
        self.info = info  # 存储相关信息

    def enterEvent(self, event):
        self.hover.emit(self.info)  # 发出信号并传递相关信息
        super().enterEvent(event)

class SummaryGraph(QWidget):
    def __init__(self, label, sum = 0, fSize = 12):
        super().__init__()
        self.sum_layout = QVBoxLayout(self)
        self.current_label = QLabel(f"{label}字数")
        self.current_count_label = QLabel("{:,}".format(sum))
        self.sum_layout.addWidget(self.current_label)
        self.sum_layout.addWidget(CustomHLine())
        self.sum_layout.addWidget(self.current_count_label)
        self.current_label.setObjectName('SubGraph')
        self.current_count_label.setObjectName('H1')

        lfont = self.current_label.font()
        lfont.setPixelSize(fSize)
        self.current_label.setFont(lfont)
        lfont.setPixelSize(fSize + 12)
        self.current_count_label.setFont(lfont)

        # self.current_count_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.current_count_label.setContentsMargins(30,0,0,0)

    def setSummary(self, sum, label = ''):
        if label != '': self.current_label.setText(f"{label}字数")
        self.current_count_label.setText("{:,}".format(sum))

def Custom_today(timeshift = 0):
    now = datetime.datetime.now()
    # 计算今天八点的时间
    today_eight_am = datetime.datetime(now.year, now.month, now.day, 8, 0, 0)
    if now < today_eight_am:
        # 如果当前时间在今天八点之前，则返回昨天的八点
        today_eight_am -= datetime.timedelta(days=1)
    if timeshift!=0: today_eight_am += datetime.timedelta(days=timeshift)
    return today_eight_am.date()

class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        # 设置窗口大小和标题
        self.setWindowTitle("Phone Simulator")
        # screen = QApplication.primaryScreen()
        # screen_rect = screen.availableGeometry()
        self.scale = float(self.GetPreset('ScaleSize','1.0'))

        fontfamily = load_custom_font()
        self.GFont = QFont(fontfamily)
        # GFont = QFont('微软雅黑')
        dpi = QGuiApplication.primaryScreen().logicalDotsPerInch()
        self.fontPointSize = MainUIHeigthInch * self.scale * dpi / 80
        self.GFont.setPointSizeF(self.fontPointSize)
        app.setFont(self.GFont)
        self.fontPixSize = int(self.fontPointSize * dpi / 72)
        self.update_book_shelf()
        # self.main_height = int(screen_rect.height() * 0.5)

        self.main_height = int(dpi * MainUIHeigthInch * self.scale)
        self.main_width = int(9.5/20 * self.main_height)
        self.content_width = self.main_width - self.main_width//6
        self.content_height = int(27/32*self.main_height)
        self.edge_spacing = self.main_height//40
        self.head_btn_size = self.main_height//32
        self.setFixedSize(self.main_width, self.main_height)
        self.font_sizes = [6, 20]
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
        self.matched_positions = []
        # Create a QVBoxLayout
        layout = QVBoxLayout(self)
        # 📅📊📈📆🗃️📇📱

        headerline = QVBoxLayout()
        header = QHBoxLayout()
        self.comb_file = QComboBox(self)
        self.collect_files = []
        self.refresh_mark = False
        self.txt_files = []
        self.refresh_items()
        # self.comb_file.setMaximumWidth(self.content_width)
        self.comb_file.setStyleSheet(f'font-family: {fontfamily}; font-size: {self.fontPixSize}px;')

        self.size_sel = QPushButton(f'X{self.scale}')
        self.size_sel.clicked.connect(self.scale_change)
        self.size_sel.setFixedWidth(int(self.fontPointSize * dpi / 24))
        self.size_sel.setFixedHeight(self.head_btn_size)
        self.size_sel.setObjectName('square')
        self.size_sel.setStyleSheet(f'font-family: {fontfamily}; font-size: {self.fontPixSize}px; padding: 0px;')

        # self.size_sel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addSpacing(self.edge_spacing)
        # header.addStretch()
        header.addWidget(self.size_sel)
        header.addWidget(self.comb_file)
        self.btn_open = QPushButton('...')
        self.btn_open.setObjectName('square')
        self.btn_open.setFixedWidth(self.head_btn_size)
        self.btn_open.setFixedHeight(self.head_btn_size)
        self.btn_open.setFont(self.GFont)
        self.btn_open.clicked.connect(self.open_folder)

        self.btn_tabs = QPushButton('A')
        self.btn_tabs.setObjectName('ico')
        self.btn_tabs.setFixedWidth(self.head_btn_size)
        self.btn_tabs.setFixedHeight(self.head_btn_size)
        self.btn_tabs.setFont(self.GFont)
        self.btn_tabs.clicked.connect(self.tab_switching)

        self.btn_close = QPushButton('✕')
        self.btn_close.setObjectName('Warning')
        self.btn_close.setFont(self.GFont)
        self.btn_close.clicked.connect(QApplication.instance().quit)
        self.btn_close.setFixedWidth(self.head_btn_size)
        self.btn_close.setFixedHeight(self.head_btn_size)

        header.addWidget(self.btn_open)
        header.addWidget(self.btn_tabs)
        header.addWidget(self.btn_close)
        header.addSpacing(self.edge_spacing)
        # headerline.addWidget(QLabel(''))
        headerline.addSpacing(self.edge_spacing)
        headerline.addLayout(header)
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
        self.diagram_page_layout = QVBoxLayout()
        self.on_diagrams_header_gui()
        self.on_diagrams_bannar_gui()
        self.on_diagrams_page_gui()
        # content.addStretch()
        content.addSpacing(self.edge_spacing)
        content.addLayout(self.diagram_page_layout)
        content.addSpacing(self.edge_spacing)
        # content.addStretch()
        layout.addLayout(content)
        # ----------------------End----------------------

        self.switch_to_book_content(True)
        layout.addStretch()
        self.setLayout(layout)

    def scale_change(self, event):
        scalesize = self.scale
        if (scalesize < 2.0 and scalesize >= 1.0) or scalesize < 0.9:
            scalesize = self.scale + 0.15
        elif scalesize >= 0.9 and scalesize < 1.0:
            scalesize = self.scale + 0.1
        else: scalesize = 0.45
        self.scale = scalesize
        print(f'X{format(self.scale, ".2f")}')
        self.size_sel.setText(f'X{format(self.scale, ".2f")}')
        self.UpdatePreset('ScaleSize', f'{format(self.scale, ".2f")}')

    def closeEvent(self, event):
        print("Application is being forced to close")
        self.RefreshingTxtLoad()
        self.update_writing_count()
        # self.update_diagrams()
        event.accept()

    def UpdatePreset(self, mark, val):
        content = []
        if os.path.exists(PRESET_PATH):
            with open(PRESET_PATH, 'r', encoding='utf-8') as infile:
                content = infile.readlines()
        newline = f'{mark}:{val}'
        fileExisted = False
        for i in range(len(content)):
            line = content[i]
            k = line.split(':')[0]
            if k == mark:
                content[i] = newline
                fileExisted = True
        if not fileExisted: content += [newline]
        directory = os.path.dirname(PRESET_PATH)
        if not os.path.exists(directory): os.makedirs(directory)
        with open(PRESET_PATH, 'w', encoding='utf-8') as file:
            file.write('\n'.join(content).replace('\n\n','\n'))

    def GetPreset(self, mark, default = ''):
        val = ''
        directory = os.path.dirname(PRESET_PATH)
        if not os.path.exists(PRESET_PATH):
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(PRESET_PATH, 'w', encoding='utf-8') as file:
                file.write('')
        if os.path.exists(directory):
            with open(PRESET_PATH, 'r', encoding='utf-8') as file:
                content = file.readlines()
                for i in range(len(content)):
                    line = content[i]
                    k = ''
                    if ':' in line: k = line.split(':')[0]
                    if k == mark: val = line.replace(f'{k}:','').replace('\n','')
        # print(f"Load Preset: {val}")
        if val == '': return default
        return val

    def UpdateCsvData(self, book_shelf):
        if book_shelf == '': return
        global CSV_COUNTER
        CSV_COUNTER = os.path.join(book_shelf,'data/writingcounter.csv').replace('\\','/')
        if not os.path.exists(CSV_COUNTER):
            csv_dir = os.path.dirname(CSV_COUNTER)
            if not os.path.exists(csv_dir):
                os.makedirs(csv_dir)
            with open(CSV_COUNTER, mode='w', encoding='utf-8') as f:
                writer = csv.writer(f)
                day = Custom_today(-1)
                raw_data = [[str(day), '0']]
                print(f"/////{raw_data}")
                writer.writerows(raw_data)

    def on_diagrams_bannar_gui(self):
        self.info_bannar = QLabel('')
        self.info_bannar.setObjectName('info')
        self.diagram_page_layout.addWidget(self.info_bannar)

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
        self.info_bannar.setVisible(not(visible))
        self.set_layout_vis(self.diagram_page_layout, not(visible))
        self.refresh_graph_widgets_visible(not(visible))
        self.set_layout_vis(self.diagram_head, not(visible))

    def on_diagrams_page_gui(self):
        self.on_today_widget_gui()
        self.on_week_widget_gui()
        self.on_month_widget_gui()
        self.diagram_page_layout.addStretch()

    def on_today_widget_gui(self):
        self.update_writing_count()
        self.today_summary_widget = SummaryGraph('今日', fSize = int(self.fontPixSize))
        self.book_summary_widget = SummaryGraph('全本', fSize = int(self.fontPixSize))
        self.week_summary_widget = SummaryGraph('本周', fSize = int(self.fontPixSize))
        self.month_summary_widget = SummaryGraph('本月', fSize = int(self.fontPixSize))
        self.summaries = QVBoxLayout()
        self.summaries.addWidget(self.today_summary_widget)
        self.summaries.addWidget(self.book_summary_widget)
        self.summaries.addWidget(self.week_summary_widget)
        self.summaries.addWidget(self.month_summary_widget)

        # self.diagram_page_layout.addStretch()
        self.diagram_page_layout.addLayout(self.summaries)
        # self.diagram_page_layout.addStretch()

    def on_diagrams_header_gui(self):
        # self.diagram_head = QHBoxLayout()
        self.diagram_head_widget = QWidget()
        self.diagram_head_widget.setObjectName('diagram_head')
        self.diagram_head = QHBoxLayout(self.diagram_head_widget)

        tab_btn_0 = QPushButton(' 统计 ')
        # tab_btn_0.setFixedWidth((self.content_width-18)//3)

        tab_btn_1 = QPushButton('周视图')
        # tab_btn_1.setFixedWidth((self.content_width-18)//3)

        tab_btn_2 = QPushButton('月视图')
        # tab_btn_2.setFixedWidth((self.content_width-18)//3)

        tab_btn_0.setObjectName('tab')
        tab_btn_1.setObjectName('tab')
        tab_btn_2.setObjectName('tab')

        tab_btn_0.setCheckable(True)
        tab_btn_1.setCheckable(True)
        tab_btn_2.setCheckable(True)

        tab_btn_0.setChecked(True)

        self.btns_tabHeader = QButtonGroup(self)
        self.btns_tabHeader.setExclusive(True)
        # self.btns_tabHeader.buttonToggled.connect(self.on_graph_widget_changed)
        self.btns_tabHeader.buttonClicked.connect(self.on_graph_widget_changed)
        self.btns_tabHeader.addButton(tab_btn_0,0)
        self.btns_tabHeader.addButton(tab_btn_1,1)
        self.btns_tabHeader.addButton(tab_btn_2,2)

        # self.diagram_head.addSpacing(self.edge_spacing)
        # self.diagram_head.addStretch()
        self.diagram_head.addWidget(tab_btn_0)
        self.diagram_head.addWidget(tab_btn_1)
        self.diagram_head.addWidget(tab_btn_2)
        self.diagram_head.setContentsMargins(0,0,0,0)
        spacing = self.edge_spacing-15
        print(f">>>>>>>>{spacing}")
        # self.diagram_head.addStretch()

        # self.diagram_page_layout.addStretch()
        self.diagram_page_layout.addWidget(self.diagram_head_widget)
        # self.diagram_page_layout.addStretch()

    def on_graph_widget_changed(self):
        self.activeMonDay = Custom_today()
        self.activeWeekDay = Custom_today()

        self.refresh_label_week()
        self.refresh_label_month()
        self.build_monthly_data()
        self.update_diagrams()
        self.refresh_graph_widgets_visible(self.btn_tabs.text() != 'A')

    def refresh_graph_widgets_visible(self,vis):
        idx = self.btns_tabHeader.checkedId()
        self.info_bannar.setText('')
        print(f'current tab: {idx}')
        switch_today = (idx == 0) and vis
        switch_week = (idx == 1) and vis
        switch_month = (idx == 2) and vis

        self.set_layout_vis(self.summaries, switch_today)

        self.set_layout_vis(self.week_diagram_layout, switch_week)
        self.week_widget.setVisible(switch_week)
        self.set_layout_vis(self.month_diagram_layout, switch_month)
        self.month_widget.setVisible(switch_month)

    def on_month_widget_gui(self):
        self.activeMonDay = Custom_today()
        self.month_widget = QWidget()
        self.month_diagram_layout = QVBoxLayout()
        self.month_widget.setLayout(self.month_diagram_layout)
        self.month_widget.setObjectName('borderblock')
        # self.month_widget.setFixedWidth(self.content_width)

        btn_last_month = QPushButton('<')
        btn_last_month.setObjectName('next')
        btn_next_month = QPushButton('>')
        btn_next_month.setObjectName('next')
        btn_last_month.clicked.connect(self.on_last_month_clicked)
        btn_next_month.clicked.connect(self.on_next_month_clicked)

        month_header = QHBoxLayout()
        self.lbl_month = QLabel(f'{self.activeMonDay.year}/{self.activeMonDay.month}')
        self.lbl_month.setObjectName('HeaderGraph')
        self.lbl_month.setFixedWidth(self.content_width//2)
        self.lbl_month.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        btn_last_month.setFixedWidth(self.head_btn_size)
        btn_last_month.setFixedHeight(self.head_btn_size)
        btn_next_month.setFixedWidth(self.head_btn_size)
        btn_next_month.setFixedHeight(self.head_btn_size)
        month_header.addStretch()
        month_header.addWidget(btn_last_month)
        month_header.addWidget(self.lbl_month)
        month_header.addWidget(btn_next_month)
        month_header.addStretch()

        self.month_graph = QHBoxLayout()
        self.month_list = QVBoxLayout()
        self.lyt_vbox = QVBoxLayout()
        self.lyt_monthBars = QVBoxLayout()

        self.build_monthly_data()
        self.month_list.addSpacing(6)
        self.lyt_monthBars.addStretch()
        self.lyt_vbox.addSpacing(6)
        self.lyt_vbox.addLayout(self.lyt_monthBars)
        self.month_graph.addLayout(self.month_list)
        self.month_graph.addLayout(self.lyt_vbox)
        self.month_graph.addStretch()

        self.month_diagram_layout.addLayout(month_header)
        self.month_diagram_layout.addWidget(CustomHLine())
        self.month_diagram_layout.addLayout(self.month_graph)

        # self.diagram_page_layout.addStretch()
        self.diagram_page_layout.addWidget(self.month_widget)
        # self.diagram_page_layout.addStretch()

    def build_monthly_data(self):
        for i in reversed(range(self.month_list.count())):
            item = self.month_list.itemAt(i)
            mw = item.widget()
            if mw is not None:
                mw.deleteLater()
            if item is not None:
                self.month_list.removeItem(item)

        for j in reversed(range(self.lyt_monthBars.count())):
            item = self.lyt_monthBars.itemAt(j)
            bw = item.widget()
            if bw is not None:
                bw.deleteLater()
            if item is not None:
                self.lyt_monthBars.removeItem(item)

        # print(f"MonthBar count: {self.lyt_monthBars.count()}")
        month_range = self.get_current_monthdays(self.activeMonDay)
        lastm = 0
        for m in range(month_range):
            currentlbl = (m//3)+1
            if currentlbl == lastm and m!=0: continue
            lastm = currentlbl
            # offset_date = Custom_today() - datetime.timedelta(m)
            lbl_str = str(m+1)
            lbl_dayname = QLabel(lbl_str)
            lbl_dayname.setObjectName('month_day')
            lbl_dayname.setAlignment(Qt.AlignTop)
            # lbl_dayname.setFixedHeight(28)
            lbl_font = self.GFont
            lbl_font.setPixelSize(self.fontPixSize)
            lbl_dayname.setFont(lbl_font)

            self.month_list.addWidget(lbl_dayname)
            # print(f"Add to month list: {lbl_dayname.text()}")
        # self.month_list.addStretch()
        # self.month_list.setFixedWidth(self.content_width*10//100)
        max_barwidth = self.content_width*88//100 - self.edge_spacing

        for i in range(month_range):
            # lbl_bar = QLabel('')
            lbl_bar = ClickableProgressBar()
            lbl_bar.hover.connect(self.on_diagram_bar_hoverring)
            lbl_bar.setTextVisible(False)
            lbl_bar.setFixedWidth(max_barwidth)
            lbl_bar.setFixedHeight(6)
            lbl_bar.setValue(2)
            self.lyt_monthBars.addWidget(lbl_bar)
            # print(f"Add to lyt_monthBars: {lbl_bar.value()}")

        # print(f"MonthBar count -> End: {self.lyt_monthBars.count()}")

    def on_next_month_clicked(self):
        today = Custom_today()
        if (self.activeMonDay.replace(day=1)-today.replace(day=1)) >= datetime.timedelta(days=0):
            print("已经是最新了.")
            return
        if self.activeMonDay.month == 12:
            self.activeMonDay = datetime.date(self.activeMonDay.year + 1, 1, 1)
        else:
            self.activeMonDay = datetime.date(self.activeMonDay.year, self.activeMonDay.month + 1, 1)
        self.refresh_label_month()
        self.build_monthly_data()
        self.update_month_diagram()

    def refresh_label_month(self):
        self.lbl_month.setText(f'{self.activeMonDay.year}/{self.activeMonDay.month}')

    def on_last_month_clicked(self):
        if self.activeMonDay.month == 1 and (self.activeMonDay.year > self.get_record_start().year):
            self.activeMonDay = datetime.date(self.activeMonDay.year - 1, 12, 1)
        elif self.activeMonDay >= self.get_record_start() and self.activeMonDay.month > 1:
            self.activeMonDay = datetime.date(self.activeMonDay.year, self.activeMonDay.month-1, 1)
        else: return
        self.refresh_label_month()
        self.build_monthly_data()
        self.update_month_diagram()

    def get_record_start(self) -> int:
        record_start = datetime.date(2000,1,1)
        if self.records != {} and self.records != None: record_start = list(self.records.keys())[0]
        print(f'获取最早记录：{record_start}')
        return record_start

    def on_next_week_clicked(self):
        if (self.activeWeekDay-Custom_today()) >= datetime.timedelta(0):
            print("已经是最新了.")
            return
        self.activeWeekDay += datetime.timedelta(days=7)
        self.refresh_label_week()
        self.update_week_diagram()

    def on_last_week_clicked(self):
        if (self.activeWeekDay - datetime.timedelta(days=7)) < self.get_record_start():
            print('前面没有了.')
            return
        self.activeWeekDay -= datetime.timedelta(days=7)
        self.refresh_label_week()
        self.update_week_diagram()

    def on_week_widget_gui(self):
        # today = Custom_today()
        self.activeWeekDay = Custom_today()
        self.week_widget = QWidget()
        self.week_diagram_layout = QVBoxLayout()
        self.week_widget.setLayout(self.week_diagram_layout)
        self.week_widget.setObjectName('borderblock')
        # self.week_widget.setFixedWidth(self.content_width)

        week_header = QHBoxLayout()
        self.lbl_week = QLabel('')
        self.refresh_label_week()
        self.lbl_week.setObjectName('HeaderGraph')
        self.lbl_week.setFixedWidth(self.content_width//2)
        self.lbl_week.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        btn_last_week = QPushButton('<')
        btn_last_week.setObjectName('next')
        btn_next_week = QPushButton('>')
        btn_next_week.setObjectName('next')

        btn_last_week.clicked.connect(self.on_last_week_clicked)
        btn_next_week.clicked.connect(self.on_next_week_clicked)

        btn_last_week.setFixedWidth(self.head_btn_size)
        btn_last_week.setFixedHeight(self.head_btn_size)
        btn_next_week.setFixedWidth(self.head_btn_size)
        btn_next_week.setFixedHeight(self.head_btn_size)
        week_header.addStretch()
        week_header.addWidget(btn_last_week)
        week_header.addWidget(self.lbl_week)
        week_header.addWidget(btn_next_week)
        week_header.addStretch()

        self.lyt_weekBars = QVBoxLayout()

        self.build_weekly_gui()

        self.week_diagram_layout.addLayout(week_header)
        self.week_diagram_layout.addWidget(CustomHLine())
        self.week_diagram_layout.addLayout(self.lyt_weekBars)

        # self.diagram_page_layout.addStretch()
        self.diagram_page_layout.addWidget(self.week_widget)
        # self.diagram_page_layout.addStretch()

    def refresh_label_week(self):
        weekfrom = self.activeWeekDay-datetime.timedelta(days=6)
        self.lbl_week.setText(f'{weekfrom.month}/{weekfrom.day}-{self.activeWeekDay.month}/{self.activeWeekDay.day}')

    def build_weekly_gui(self):
        for i in reversed(range(self.lyt_weekBars.count())):
            lyt = self.lyt_weekBars.itemAt(i).layout()
            if lyt is not None:
                for w in reversed(range(lyt.count())):
                    widget = lyt.itemAt(w).widget()
                    if widget is not None:
                        widget.deleteLater()
                lyt.deleteLater()

        for i in range(7):
            linebar = QHBoxLayout()
            lbl_weekname = QLabel('')
            lbl_weekname.setObjectName('SubGraph')
            linebar.addWidget(lbl_weekname)
            lbl_bar = ClickableProgressBar()
            lbl_bar.hover.connect(self.on_diagram_bar_hoverring)
            linebar.addWidget(lbl_bar)
            linebar.addStretch()
            self.lyt_weekBars.addLayout(linebar)

    def on_diagram_bar_hoverring(self, info):
        if info in self.records:
            self.info_bannar.setText(f"{info.month}/{info.day} {self.records[info]}")

    def update_diagrams(self):
        self.records = self.get_records()
        self.update_week_diagram()
        self.update_month_diagram()
        self.update_summary_diagram()

    def update_summary_diagram(self):
        recordlist = list(self.records.values())
        today_sum = 0
        if recordlist != []: today_sum = recordlist[-1]
        self.today_summary_widget.setSummary(today_sum)
        self.book_summary_widget.setSummary(self.current_sum)
        week_sum = self.get_recently_summaries()
        self.week_summary_widget.setSummary(week_sum)
        month_sum = self.get_recently_summaries(self.get_current_monthdays(Custom_today()))
        self.month_summary_widget.setSummary(month_sum)

    def get_recently_summaries(self, day_length = 7):
        recently_date = Custom_today() - datetime.timedelta(days = day_length)
        pre_sum = 0
        record_list = list(self.records.values())
        for i in range(len(record_list)):
            if record_list[i] > pre_sum and list(self.records.keys())[i] < recently_date:
                pre_sum = record_list[i]
        sum = self.current_sum - pre_sum
        return sum

    def update_week_diagram(self):
        # print("Updating Week Graph")
        self.records_in_week = self.filted_date()
        # print(self.records_in_week)
        max_count = max(1,max(self.records_in_week.values(), default=1))
        max_barwidth = self.content_width*88//100 - self.edge_spacing - 8
        today = self.activeWeekDay
        for i in range(7):
            date = today-datetime.timedelta(days=6) + datetime.timedelta(days=i)
            count = self.records_in_week.get(date, 0)

            barname = self.lyt_weekBars.itemAt(i).layout().itemAt(0).widget()
            week_bar = self.lyt_weekBars.itemAt(i).layout().itemAt(1).widget()
            if isinstance(barname, QLabel):
                barname.setText(str(date.day))
                barname.setFixedWidth(self.fontPixSize*2)
            if isinstance(week_bar, QProgressBar):
                week_bar_width = max(1, count*100//max_count) if count > 0 else 0
                week_bar.setMaximum(100)
                week_bar.setTextVisible(True)
                bar_value = f" {count}"

                font_metrics = QFontMetrics(week_bar.font())
                string_width = font_metrics.width(bar_value)//2
                # print(f"date: {date} count: {count} string_width: {string_width}")
                # print(f'blank width:{font_metrics.width(" ")}')

                if week_bar_width<0:
                    week_bar_width = abs(week_bar_width)
                    week_bar.setObjectName('bar-minus')
                elif week_bar_width == 0:
                    week_bar.setObjectName('bar-zero')
                    week_bar.setTextVisible(False)
                # elif i==today.day-1:
                #     week_bar.setObjectName('bar-h')
                else:
                    week_bar.setObjectName('bar')
                week_bar_width = max(2,week_bar_width)
                week_bar.info = date

                if week_bar_width < string_width:
                    offset = math.ceil(week_bar_width/5)+1
                    # print(f"week_bar_width:{week_bar_width} offset: {offset}")
                    bar_value = " " * offset + bar_value

                week_bar.setValue(week_bar_width)
                # week_bar.setValue(string_width)

                week_bar.setFixedWidth(max_barwidth)
                week_bar.setFormat(bar_value)
                week_bar.setAlignment(Qt.AlignmentFlag.AlignVCenter)
                week_bar.style().unpolish(week_bar)
                week_bar.style().polish(week_bar)

    def update_month_diagram(self):
        # print("Updating Month Graph")
        self.records_in_month = self.filted_date('month')
        month_range = self.get_current_monthdays(self.activeMonDay)
        max_count = max(1,max(self.records_in_month.values(), default=1))
        for i in range(month_range):
            date = self.activeMonDay.replace(day=1) + datetime.timedelta(days=i)
            count = self.records_in_month.get(date, 0)
            month_bar = self.lyt_monthBars.itemAt(i).widget()
            if isinstance(month_bar, QProgressBar):
                month_bar_width = count*100//max_count
                month_bar.setMaximum(100)
                if count < 0:
                    month_bar_width = abs(month_bar_width)
                    month_bar.setObjectName('bar-minus')
                elif count == 0:
                    month_bar.setObjectName('bar-zero')
                else:
                    month_bar.setObjectName('bar')
                month_bar.setValue(max(2,month_bar_width))
                month_bar.info = date
                # print(f'month_bar---{date}---{month_bar.value()}/{month_bar.maximum()}, {month_bar.objectName()}')
                month_bar.style().unpolish(month_bar)
                month_bar.style().polish(month_bar)

    def filted_date(self, mode = 'week'):
        if mode == 'week':
            last_monday = self.activeWeekDay - datetime.timedelta(days=6)
            records_in_range = {}
            for k in self.records:
                if k >= last_monday and k <= self.activeWeekDay:
                    records_in_range[k] = self.records[k]
            return records_in_range
        elif mode == 'month':
            first_of_month = self.activeMonDay.replace(day=1)
            days_in_m = self.get_current_monthdays(self.activeMonDay)
            records_in_range = {}
            for k in self.records:
                if k >= first_of_month and k.day <= days_in_m:
                    records_in_range[k] = self.records[k]
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
        if CSV_COUNTER == "" : return date_counts
        with open(CSV_COUNTER, mode='r', newline='') as file:
            reader = csv.reader(file)
            readerlist = list(reader)
            for i in range(len(readerlist)):
            # for row in reader:
                row = readerlist[i]
                # print(f'debug:{row}')
                if row == []: continue
                date_str= row[0]
                count = row[1]
                date = self.get_datetime(date_str)
                added = int(count)
                if i >0 :
                    temp = readerlist[i-1]
                    if temp == []: continue
                    added = added - int(temp[1])
                date_counts[date] = added
        return date_counts
    def get_current_monthdays(self, now):
        # 获取当前日期
        # now = Custom_today()
        # 计算下个月的第一天
        next_month = Custom_today()
        if now.month == 12:
            next_month = datetime.date(now.year + 1, 1, 1)
        else:
            next_month = datetime.date(now.year, now.month + 1, 1)
        # 当前月份的最后一天
        last_day_of_current_month = next_month - datetime.timedelta(days=1)
        days_in_month = last_day_of_current_month.day

        # print(f"当前月份的天数: {days_in_month}")
        return days_in_month

    def update_writing_count(self):
        self.records = self.get_records()
        self.current_sum = self.get_writing_count()
        today = Custom_today()
        new_row = [str(today),str(self.current_sum)]

        if CSV_COUNTER == "": return
        with open(CSV_COUNTER, mode='r', newline='') as file:
            reader = csv.reader(file)
            rows = [line for line in list(reader) if line != []]

        # 修改最后一行或追加新行
        last_date = list(self.records.keys())[-1]
        if today != last_date:
            if new_row != []: rows.append(new_row)
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
                    # content = file.read()
                    # clean_content = content.replace('\n','').replace(' ','')
                    # total += len(clean_content)
                    contents = file.readlines()
                    for line in contents:
                        cleanline_arr = line.split('//')
                        if cleanline_arr is None: continue
                        if len(cleanline_arr)<1: continue
                        cleanline = cleanline_arr[0]
                        cleanline = cleanline.replace('\n','').replace(' ','')
                        total += len(cleanline)
            except:
                continue
        return total

    def on_floating_button1_clicked(self):
        print('btn 1: add')
        presize = self.text_edit.font().pointSizeF()
        targetSize = int(presize) + 1
        self.text_edit_size_add(presize, targetSize)
        afterSize = self.text_edit.font().pointSizeF()
        print(f'Presize:{presize} --> AfterSize:{afterSize}')

    def text_edit_size_add(self, presize, targetSize):
        if targetSize > self.font_sizes[1] or targetSize < self.font_sizes[0]:
            print(f'目标字号超出范围：{targetSize}>>{self.font_sizes}')
            return
        if self.fixed_visible_lines > 2:
            self.fixed_visible_lines -= 1
            self.adjust_scrollbar()
            self.adjust_line_height()
            aftersize = self.text_edit.font().pointSizeF()
            if int(aftersize) < targetSize:
                print(f'{aftersize}不足，递归计算{targetSize}')
                self.text_edit_size_add(presize, targetSize)
        print(f"最终结果：{aftersize}/{targetSize}")

    def on_floating_button2_clicked(self):
        print('btn 2: minus')
        presize = self.text_edit.font().pointSizeF()
        targetSize = int(presize) - 1
        self.text_edit_size_minus(presize, targetSize)
        afterSize = self.text_edit.font().pointSizeF()
        print(f'Presize:{presize} --> AfterSize:{afterSize}')

    def text_edit_size_minus(self, presize, targetSize):
        if targetSize > self.font_sizes[1] or targetSize < self.font_sizes[0]:
            print(f'目标字号超出范围：{targetSize}>>{self.font_sizes}')
            return
        if self.fixed_visible_lines < 100:
            self.fixed_visible_lines += 1
            self.adjust_scrollbar()
            self.adjust_line_height()
            aftersize = self.text_edit.font().pointSizeF()
            if int(aftersize) > targetSize:
                print(f'{aftersize}不足，递归计算{targetSize}')
                self.text_edit_size_minus(presize, targetSize)
        print(f"最终结果：{aftersize}/{targetSize}")


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

    def update_book_shelf(self):
        global BOOK_SHELF
        BOOK_SHELF = self.GetPreset('ShelfPath')
        self.UpdateCsvData(BOOK_SHELF)

    def open_folder(self):
        global BOOK_SHELF
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            BOOK_SHELF = folder_path
            self.refresh_items()
            self.reload_novel_from_combo(True)
            self.UpdatePreset('ShelfPath', folder_path)
            self.UpdateCsvData(BOOK_SHELF)

    def highlight_text(self):
        currentFile = self.comb_file.currentText() + '.txt'
        if currentFile.startswith('Doc_'): return
        # pass
        text = self.text_edit.toPlainText()
        pattern = re.compile(NOT_COMMON)

        # 使用 \g<0> 来引用整个匹配结果
        highlighted_text = pattern.sub(r'<span style="color:red;">\g<0></span>', text)

        # 获取匹配到的位置
        matches = pattern.finditer(text)
        self.matched_positions = [0]+[match.start() for match in matches]+[len(text)-1]
        print(f"matched_positions: {self.matched_positions}")
        # 根据匹配到的位置找到所在的block
        self.matched_blocks = []
        for pos in self.matched_positions:
            for i in range(self.text_edit.document().blockCount()):
                if i+1 in self.matched_blocks: continue
                block = self.text_edit.document().findBlockByNumber(i)
                if block.position()<= pos < block.position() + block.length():
                    self.matched_blocks.append(i+1)
                    break
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
        self.novel_content = self.load_novel(self.comb_file.currentText() + '.txt')
        self.text_edit.setText(self.novel_content)

        self.counter.setText(self.get_counter_label())
        self.highlight_text()

        if keep_scroll:
            # 恢复滚动条位置
           self.text_edit.verticalScrollBar().setValue(scroll_position)
           print(f"refresh to scroll back! (scroll_position : {scroll_position})")

    def refresh_items(self):
        pre_sel = self.comb_file.currentText() + '.txt'
        files = self.get_files_from_dir()
        if files != self.collect_files:
            print("File Changed!!")
            self.collect_files = files
            self.txt_files = [f for f in files if not f.startswith('Doc_')]
            self.comb_file.clear()
            for file in files:
                filename = ''
                if '.' in file : filename = file.split('.')[0]
                if filename != '': self.comb_file.addItem(filename)
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
        self.info_bannar.setText('')

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
        self.update_diagrams()
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
    # global dpi
    style_sheet = QSSLoader.read_qss_file(QSS_PATH)
    app = QApplication(sys.argv)
    icon =  QIcon(ICON_PATH)
    app.setWindowIcon(icon)

    window = MainUI()
    window.setStyleSheet(style_sheet)
    window.setWindowIcon(icon)
    window.show()
    sys.exit(app.exec())

