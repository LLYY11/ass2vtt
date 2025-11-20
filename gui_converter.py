import sys
import os
import re
from typing import List, Tuple
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QListWidget, QFileDialog, QLabel, QLineEdit,
                              QMessageBox, QProgressBar, QGroupBox, QFormLayout)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction, QActionGroup


# 定义语言字典
LANGUAGES = {
    'en': {
        'window_title': 'ASS to VTT Converter',
        'files': 'Files',
        'add_files': 'Add Files',
        'remove_selected': 'Remove Selected',
        'clear_all': 'Clear All',
        'settings': 'Settings',
        'output_suffix': 'Output Suffix:',
        'progress': 'Progress',
        'ready': 'Ready',
        'convert_files': 'Convert Files',
        'select_ass_files': 'Select ASS Files',
        'ass_files': 'ASS Files (*.ass)',
        'warning': 'Warning',
        'no_files_added': 'Please add files to convert.',
        'invalid_suffix': 'Please enter a valid suffix.',
        'converted': 'Converted: {}',
        'conversion_completed': 'Conversion completed!',
        'success': 'Success',
        'all_files_converted': 'All files converted successfully!',
        'error': 'Error',
        'language': 'Language',
        'english': 'English',
        'chinese': '中文'
    },
    'zh': {
        'window_title': 'ASS转VTT转换器',
        'files': '文件',
        'add_files': '添加文件',
        'remove_selected': '删除选中',
        'clear_all': '清空所有',
        'settings': '设置',
        'output_suffix': '输出后缀:',
        'progress': '进度',
        'ready': '就绪',
        'convert_files': '转换文件',
        'select_ass_files': '选择ASS文件',
        'ass_files': 'ASS文件 (*.ass)',
        'warning': '警告',
        'no_files_added': '请添加要转换的文件。',
        'invalid_suffix': '请输入有效的后缀。',
        'converted': '已转换: {}',
        'conversion_completed': '转换完成！',
        'success': '成功',
        'all_files_converted': '所有文件转换成功！',
        'error': '错误',
        'language': '语言',
        'english': 'English',
        'chinese': '中文'
    }
}


class ConversionWorker(QThread):
    progress_updated = Signal(int)  # Signal to update progress
    file_converted = Signal(str)    # Signal when a file is converted
    conversion_finished = Signal()   # Signal when all conversions are finished
    error_occurred = Signal(str)    # Signal when an error occurs

    def __init__(self, files, suffix):
        super().__init__()
        self.files = files
        self.suffix = suffix

    def run(self):
        total_files = len(self.files)
        for i, file_path in enumerate(self.files):
            try:
                self.convert_ass_to_vtt(file_path, self.suffix)
                self.file_converted.emit(os.path.basename(file_path))
                progress = int((i + 1) / total_files * 100)
                self.progress_updated.emit(progress)
            except Exception as e:
                self.error_occurred.emit(f"Error converting {os.path.basename(file_path)}: {str(e)}")

        self.conversion_finished.emit()

    def ass_time_to_vtt_time(self, ass_time: str) -> str:
        """Convert ASS time format to VTT time format"""
        hours, minutes, seconds = ass_time.split(':')
        seconds, centiseconds = seconds.split('.')
        milliseconds = centiseconds + '0'
        vtt_time = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}.{milliseconds}"
        return vtt_time

    def parse_ass_file(self, file_path: str) -> List[Tuple[str, str, str]]:
        """Parse ASS file and extract subtitle events"""
        subtitles = []
        in_events_section = False

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    line = line.strip()

                    if line.startswith('[Events]'):
                        in_events_section = True
                        continue

                    if line.startswith('[') and in_events_section and not line.startswith('[Events]'):
                        break

                    if in_events_section and line.startswith('Dialogue:'):
                        parts = line.split(',', 9)

                        if len(parts) >= 10:
                            start_time = parts[1].strip()
                            end_time = parts[2].strip()
                            raw_text = parts[9].strip() if len(parts) > 9 else ""
                            clean_text = self.clean_ass_formatting(raw_text)
                            subtitles.append((start_time, end_time, clean_text))
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()

                    if line.startswith('[Events]'):
                        in_events_section = True
                        continue

                    if line.startswith('[') and in_events_section and not line.startswith('[Events]'):
                        break

                    if in_events_section and line.startswith('Dialogue:'):
                        parts = line.split(',', 9)

                        if len(parts) >= 10:
                            start_time = parts[1].strip()
                            end_time = parts[2].strip()
                            raw_text = parts[9].strip() if len(parts) > 9 else ""
                            clean_text = self.clean_ass_formatting(raw_text)
                            subtitles.append((start_time, end_time, clean_text))

        return subtitles

    def clean_ass_formatting(self, text: str) -> str:
        """Remove or convert ASS formatting codes to HTML-like tags for VTT"""
        try:
            text = re.sub(r'\{\\[^}]*\}', '', text)
        except re.error:
            result = ""
            i = 0
            while i < len(text):
                if text[i] == '{' and i + 1 < len(text) and text[i+1] == '\\':
                    j = text.find('}', i)
                    if j != -1:
                        i = j + 1
                        continue
                result += text[i]
                i += 1
            text = result

        try:
            text = re.sub(r'\{\\b1?\}([^]*?)\{\\b0\}', r'<b>\1</b>', text)
            text = re.sub(r'\{\\i1?\}([^]*?)\{\\i0\}', r'<i>\1</i>', text)
            text = re.sub(r'\{\\u1?\}([^]*?)\{\\u0\}', r'<u>\1</u>', text)
        except re.error:
            pass

        return text

    def generate_vtt_content(self, subtitles: List[Tuple[str, str, str]]) -> str:
        """Generate VTT formatted content from parsed subtitles"""
        lines = ['WEBVTT FILE', '']

        for i, (start_time, end_time, text) in enumerate(subtitles, 1):
            try:
                vtt_start = self.ass_time_to_vtt_time(start_time)
                vtt_end = self.ass_time_to_vtt_time(end_time)

                lines.append(f"{i}")
                lines.append(f"{vtt_start} --> {vtt_end}")
                lines.append(text)
                lines.append('')
            except Exception:
                continue

        return '\n'.join(lines)

    def convert_ass_to_vtt(self, ass_file_path: str, suffix: str) -> str:
        """Convert ASS file to VTT format with custom suffix"""
        if not os.path.exists(ass_file_path):
            raise FileNotFoundError(f"ASS file not found: {ass_file_path}")

        subtitles = self.parse_ass_file(ass_file_path)
        vtt_content = self.generate_vtt_content(subtitles)

        base_name = os.path.splitext(ass_file_path)[0]
        vtt_file_path = f"{base_name}.{suffix}"

        with open(vtt_file_path, 'w', encoding='utf-8') as f:
            f.write(vtt_content)

        return vtt_file_path


class AssToVttConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_lang = 'en'  # 默认语言为英语
        self.translations = LANGUAGES[self.current_lang]
        self.setWindowTitle(self.translations['window_title'])
        self.setGeometry(100, 100, 600, 500)

        self.files = []
        self.worker = None

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 创建菜单栏
        self.create_menu_bar()

        # File selection group
        self.file_group = QGroupBox(self.translations['files'])
        file_layout = QVBoxLayout(self.file_group)

        self.file_list = QListWidget()
        file_layout.addWidget(self.file_list)

        button_layout = QHBoxLayout()
        self.add_files_btn = QPushButton(self.translations['add_files'])
        self.add_files_btn.clicked.connect(self.add_files)
        self.remove_files_btn = QPushButton(self.translations['remove_selected'])
        self.remove_files_btn.clicked.connect(self.remove_files)
        self.clear_files_btn = QPushButton(self.translations['clear_all'])
        self.clear_files_btn.clicked.connect(self.clear_files)

        button_layout.addWidget(self.add_files_btn)
        button_layout.addWidget(self.remove_files_btn)
        button_layout.addWidget(self.clear_files_btn)
        file_layout.addLayout(button_layout)

        # Settings group
        self.settings_group = QGroupBox(self.translations['settings'])
        settings_layout = QFormLayout(self.settings_group)

        self.suffix_input = QLineEdit("vtt")
        self.suffix_label = QLabel(self.translations['output_suffix'])
        settings_layout.addRow(self.suffix_label, self.suffix_input)

        # Progress group
        self.progress_group = QGroupBox(self.translations['progress'])
        progress_layout = QVBoxLayout(self.progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel(self.translations['ready'])
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.status_label)

        # Convert button
        self.convert_btn = QPushButton(self.translations['convert_files'])
        self.convert_btn.clicked.connect(self.convert_files)
        self.convert_btn.setStyleSheet("QPushButton { font-weight: bold; }")

        # Add groups to main layout
        main_layout.addWidget(self.file_group)
        main_layout.addWidget(self.settings_group)
        main_layout.addWidget(self.progress_group)
        main_layout.addWidget(self.convert_btn)

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # Language menu
        lang_menu = menubar.addMenu(self.translations['language'])
        
        # English action
        english_action = QAction(self.translations['english'], self)
        english_action.setCheckable(True)
        english_action.setChecked(self.current_lang == 'en')
        english_action.triggered.connect(lambda: self.switch_language('en'))
        
        # Chinese action
        chinese_action = QAction(self.translations['chinese'], self)
        chinese_action.setCheckable(True)
        chinese_action.setChecked(self.current_lang == 'zh')
        chinese_action.triggered.connect(lambda: self.switch_language('zh'))
        
        # Group actions so only one can be checked at a time
        lang_group = QActionGroup(self)
        lang_group.addAction(english_action)
        lang_group.addAction(chinese_action)
        
        lang_menu.addAction(english_action)
        lang_menu.addAction(chinese_action)

    def switch_language(self, lang_code):
        """切换界面语言"""
        self.current_lang = lang_code
        self.translations = LANGUAGES[self.current_lang]
        self.retranslate_ui()

    def retranslate_ui(self):
        """更新界面文本"""
        self.setWindowTitle(self.translations['window_title'])
        
        # 更新组框标题
        self.file_group.setTitle(self.translations['files'])
        self.settings_group.setTitle(self.translations['settings'])
        self.progress_group.setTitle(self.translations['progress'])
        
        # 更新按钮文本
        self.add_files_btn.setText(self.translations['add_files'])
        self.remove_files_btn.setText(self.translations['remove_selected'])
        self.clear_files_btn.setText(self.translations['clear_all'])
        self.convert_btn.setText(self.translations['convert_files'])
        
        # 更新标签文本
        self.suffix_label.setText(self.translations['output_suffix'])
        
        # 更新状态标签
        current_text = self.status_label.text()
        if current_text == self.translations['ready'] or current_text in ['Ready', '就绪']:
            self.status_label.setText(self.translations['ready'])
        elif current_text == self.translations['conversion_completed'] or current_text in ['Conversion completed!', '转换完成！']:
            self.status_label.setText(self.translations['conversion_completed'])

    def add_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, self.translations['select_ass_files'], "", self.translations['ass_files']
        )

        for file_path in file_paths:
            if file_path not in self.files:
                self.files.append(file_path)
                self.file_list.addItem(os.path.basename(file_path))

    def remove_files(self):
        selected_items = self.file_list.selectedItems()
        for item in selected_items:
            row = self.file_list.row(item)
            self.file_list.takeItem(row)
            del self.files[row]

    def clear_files(self):
        self.files.clear()
        self.file_list.clear()

    def convert_files(self):
        if not self.files:
            QMessageBox.warning(self, self.translations['warning'], self.translations['no_files_added'])
            return

        suffix = self.suffix_input.text().strip()
        if not suffix:
            QMessageBox.warning(self, self.translations['warning'], self.translations['invalid_suffix'])
            return

        self.convert_btn.setEnabled(False)
        self.add_files_btn.setEnabled(False)
        self.remove_files_btn.setEnabled(False)
        self.clear_files_btn.setEnabled(False)

        self.worker = ConversionWorker(self.files, suffix)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.file_converted.connect(self.file_converted)
        self.worker.conversion_finished.connect(self.conversion_finished)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def file_converted(self, filename):
        self.status_label.setText(self.translations['converted'].format(filename))

    def conversion_finished(self):
        self.convert_btn.setEnabled(True)
        self.add_files_btn.setEnabled(True)
        self.remove_files_btn.setEnabled(True)
        self.clear_files_btn.setEnabled(True)
        self.status_label.setText(self.translations['conversion_completed'])
        QMessageBox.information(self, self.translations['success'], self.translations['all_files_converted'])

    def handle_error(self, error_msg):
        QMessageBox.critical(self, self.translations['error'], error_msg)


def main():
    app = QApplication(sys.argv)
    converter = AssToVttConverter()
    converter.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()