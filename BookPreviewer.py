import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import  *
from PyQt5.QtCore import *
import math
import os
import re

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

BACKGROUND_PNG = resource_path("resources/BackgroundMi14.png")
CUSTOM_FONTS = resource_path("resources/MiSans-Normal.ttf")
# ICON_PATH = resource_path("resources/book.ico")
ICON_PATH = resource_path("resources/smartphone.png")


# BOOK_SHELF = os.path.dirname(os.path.abspath(__file__))
BOOK_SHELF = r'D:\Documents\Books\Writing'
# RARE_CHS = r'[\u3400-\u4DBF\uF900-\uFAFF\U00020000-\U0002EBEF]'
COMMON_CHS = r'[\u4E00-\u9FFF\u3400-\u4DBF]'
NOT_COMMON = rf'[^{PUNCTUATION_STR}{LETTERS}{NUMS}\u4E00-\u9FFF \n]'
NUMBER = r'([0-9]+)'

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

        # 加载自定义字体
        self.load_custom_font(CUSTOM_FONTS)

        # 强行控制每行显示的可见行数
        self.fixed_visible_lines = 25  # 例如，固定显示10行

        self.add_floating_buttons()

        self.novel_content = ''

        # Create a QVBoxLayout
        layout = QVBoxLayout(self)
        headerline = QVBoxLayout(self)
        header = QHBoxLayout(self)
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
        self.btn_close = QPushButton('✕')
        self.btn_close.setObjectName('Warning')
        self.btn_close.clicked.connect(QApplication.instance().quit)
        self.btn_close.setFixedWidth(self.head_btn_size)
        self.btn_close.setFixedHeight(self.head_btn_size)

        header.addWidget(self.btn_open)
        header.addWidget(self.btn_close)
        header.addSpacing(self.edge_spacing)
        headerline.addWidget(QLabel(''))
        headerline.addLayout(header)
        headerline.addSpacing(10)
        layout.addLayout(headerline)

        content = QHBoxLayout(self)
        # layout.setGeometry(QRectF())
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

        layout.addLayout(content)
        footer = QHBoxLayout()
        # lbl_count = QLabel('      总字数:')
        self.counter = QLabel(self.get_counter_label())
        self.counter.setContentsMargins(self.edge_spacing,0,0,0)
        self.block_pos=QLabel(f'当前: {self.text_edit.currentBlock}')
        self.block_pos.setContentsMargins(0,0,self.edge_spacing,0)
        self.text_edit.logger = self.block_pos
        # footer.addWidget(lbl_count)
        footer.addWidget(self.counter)
        footer.addWidget(self.block_pos)
        layout.addLayout(footer)
        layout.addStretch()
        # 禁用滚动条
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 让 QTextEdit 不接受鼠标事件
        # self.text_edit.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.lines = self.novel_content.split('\n')

        # 加载文档
        self.comb_file.currentTextChanged.connect(self.reload_novel_from_combo)
        self.comb_file.setCurrentIndex(1)

        # 设置字号
        self.set_fonts()

        # 设置鼠标滚动时一次滚动多行
        scrollbar = self.text_edit.verticalScrollBar()
        scrollbar.setSingleStep(5 * self.text_edit.fontMetrics().height())

        # self.text_edit.setText(self.novel_content)
        self.adjust_scrollbar()
        self.adjust_line_height()

        # self.highlight_rare_ch()
        self.highlight_text()

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

    def load_custom_font(self, font_path):
        """加载自定义字体"""
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            print(f"Failed to load font from {font_path}")
        else:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            self.custom_font_family = font_family

    def set_fonts(self):
        """设置字体大小"""
        # font = self.text_edit.font()
        # font.setPointSize(size)
        font = QFont(self.custom_font_family)
        self.text_edit.setFont(font)

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
    window = MainUI()
    window.setStyleSheet(style_sheet)
    window.setWindowIcon(icon)
    window.show()
    sys.exit(app.exec())

