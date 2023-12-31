from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QLabel, QFontDialog, QFileDialog, QComboBox, QTextEdit,
                               QPushButton, QToolBar, QMessageBox, QDialog, QLineEdit,
                               QTextBrowser, QSizePolicy, QHBoxLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont, QIcon
import sys
import json
from xml.etree import ElementTree as ET

# Global stylesheet
STYLESHEET = '''
    QWidget {
        font-family: Arial;
    }
    QLabel {
        font-weight: bold;
    }
    QPushButton {
        background-color: #0078D7;
        color: white;
        border-radius: 5px;
        padding: 10px;
    }
    QPushButton:hover {
        background-color: #005A9E;
    }
    QComboBox {
        border: 1px solid #0078D7;
        border-radius: 3px;
        padding: 5px;
    }
    QComboBox:editable {
        background: white;
    }
    QComboBox QAbstractItemView {
        border: 1px solid #0078D7;
        background: white;
    }
    QTextEdit {
        border: 1px solid #0078D7;
        border-radius: 3px;
        background-color: #F1F1F1;
    }
'''

class BibleApp(QWidget):
    def __init__(self):
        super(BibleApp, self).__init__()

        layout = QVBoxLayout()

        self.bookComboBox = QComboBox()
        self.chapterComboBox = QComboBox()
        self.verseTextBox = QTextEdit()
        self.titleLabel = QLabel("No Bible Loaded")
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.verseTextBox.setReadOnly(True)

        layout.addWidget(self.titleLabel)
        layout.addWidget(self.bookComboBox)
        self.bookComboBox.setMaximumWidth(150)
        layout.addWidget(self.chapterComboBox)
        self.chapterComboBox.setMaximumWidth(75)
        layout.addWidget(self.verseTextBox)

        self.bookComboBox.currentIndexChanged.connect(self.load_chapters)
        self.chapterComboBox.currentIndexChanged.connect(self.load_verses)

        self.setLayout(layout)
        self.root = None

    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
            self.parent().resize(*settings.get('window_size', [800, 600]))
            self.parent().move(*settings.get('window_position', [100, 100]))

            if settings.get('current_xml_path'):
                self.current_xml_path = settings['current_xml_path']
                tree = ET.parse(self.current_xml_path)
                self.root = tree.getroot()
                self.titleLabel.setText(self.current_xml_path.split("/")[-1].replace(".xml", ""))
                self.bookComboBox.clear()
                for book in self.root.findall(".//b"):
                    book_name = book.get("n")
                    self.bookComboBox.addItem(book_name)
                self.bookComboBox.setCurrentText(settings.get('current_book', ''))
                self.load_chapters()
                self.chapterComboBox.setCurrentText(settings.get('current_chapter', ''))
                self.load_verses()
        except FileNotFoundError:
            pass

    def save_settings(self):
        settings = {
            'window_size': [self.parent().width(), self.parent().height()],
            'window_position': [self.parent().x(), self.parent().y()],
            'font_family': self.verseTextBox.font().family(),
            'font_size': self.verseTextBox.font().pointSize(),
            'current_xml_path': self.current_xml_path,
            'current_book': self.bookComboBox.currentText(),
            'current_chapter': self.chapterComboBox.currentText()
        }
        with open('settings.json', 'w') as f:
            json.dump(settings, f)

    def load_xml(self):
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getOpenFileName(self, "Open Bible File", "", "XML Files (*.xml);;All Files (*)", options=options)
        if filePath:
            self.current_xml_path = filePath
            tree = ET.parse(filePath)
            self.root = tree.getroot()
            self.titleLabel.setText(filePath.split("/")[-1].replace(".xml", ""))
            self.bookComboBox.clear()
            for book in self.root.findall(".//b"):
                book_name = book.get("n")
                self.bookComboBox.addItem(book_name)
            self.load_chapters()

    def load_chapters(self):
        self.chapterComboBox.clear()
        book_name = self.bookComboBox.currentText()
        if self.root:
            for chapter in self.root.findall(f".//b[@n='{book_name}']/c"):
                chapter_num = chapter.get("n")
                self.chapterComboBox.addItem(chapter_num)

    def load_verses(self):
        self.verseTextBox.clear()
        book_name = self.bookComboBox.currentText()
        chapter_number = self.chapterComboBox.currentText()
        if self.root:
            for verse in self.root.findall(f".//b[@n='{book_name}']/c[@n='{chapter_number}']/v"):
                verse_num = verse.get("n")
                verse_text = verse.text
                self.verseTextBox.append(f"<small style='color: #0078D7;'>{verse_num}</small> {verse_text}")

    def change_font(self):
        ok, font = QFontDialog.getFont()
        if ok:
            self.verseTextBox.setFont(QFont(font.family(), font.pointSize()))

    def confirm_exit(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setText("Are you sure you want to exit?")
        msg.setWindowTitle("Exit Confirmation")
        msg.setWindowIcon(QIcon("resources/icon.png"))
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if msg.exec() == QMessageBox.Yes:
            self.save_settings()
            return True
        return False

    def show_about(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("PyBible: a simple Bible reader\nwritten in Python using PySide6.\n\nAuthor: QuantumPixelator\n\nVersion: 1.2.0\n\nLicense: MIT")
        msg.setWindowTitle("About PyBible")
        msg.setWindowIcon(QIcon("resources/icon.png"))
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    # Search functionality
    def show_search(self):
        search_dialog = QDialog(self)
        search_dialog.setWindowTitle("Search")
        search_dialog_layout = QVBoxLayout()
        search_input = QLineEdit()
        search_input.setPlaceholderText("Enter search term...")
        search_button = QPushButton("Search")
        search_result = QTextEdit()
        search_result.setReadOnly(True)

        search_dialog_layout.addWidget(search_input)
        search_dialog_layout.addWidget(search_button)
        search_dialog_layout.addWidget(search_result)
        search_dialog.setLayout(search_dialog_layout)

        def perform_search():
            search_term = search_input.text()
            search_results = self.search_in_xml(self.root, search_term)
            result_count = 0  # Initialize the counter
            results_text = ""
            for result in search_results:
                book = result['Book']
                chapter = result['Chapter']
                verse = result['Verse']
                text = result['Text']
                results_text += f"{book} {chapter}:{verse}\n{text}\n\n"
                result_count += 1  # Increment the counter
            
            results_text = f"Total Results: {result_count}\n\n" + results_text  # Add the counter to the textbox results
            search_result.setText(results_text)

        search_button.clicked.connect(perform_search)
        search_dialog.exec_()

    def search_in_xml(self, root: ET.Element, search_term: str):
        search_results = []
        for book in root.findall('.//b'):
            book_name = book.attrib.get('n', 'Unknown Book')
            for chapter in book.findall('.//c'):
                chapter_number = chapter.attrib.get('n', 'Unknown Chapter')
                for verse in chapter.findall('.//v'):
                    verse_number = verse.attrib.get('n', 'Unknown Verse')
                    verse_text = verse.text if verse.text else ''
                    if search_term.lower() in verse_text.lower():
                        search_results.append({
                            'Book': book_name,
                            'Chapter': chapter_number,
                            'Verse': verse_number,
                            'Text': verse_text
                        })
        return search_results

def get_updated_stylesheet():
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        font_family = settings.get('font_family', 'Arial')
        font_size = settings.get('font_size', 12)
    except FileNotFoundError:
        font_family = 'Arial'  # Default font family if the JSON file is not found
        font_size = 12  # Default font size if the JSON file is not found
    
    text_edit_stylesheet = f'QTextEdit {{ font-family: {font_family}; font-size: {font_size}px; }}'
    
    updated_stylesheet = STYLESHEET + "\n" + text_edit_stylesheet
    
    return updated_stylesheet

if __name__ == "__main__":
    app = QApplication(sys.argv)
    updated_stylesheet = get_updated_stylesheet()  # Get the stylesheet updated with the font from JSON
    app.setStyleSheet(updated_stylesheet) 
    window = QMainWindow()

    toolbar = QToolBar()
    window.addToolBar(Qt.TopToolBarArea, toolbar)

    bible_app = BibleApp()
    window.setCentralWidget(bible_app)

    bible_app.load_settings()
    
    def create_toolbar_spacer(width=10):
        spacer = QWidget()
        spacer.setMinimumWidth(width)
        spacer.setMaximumWidth(width)
        return spacer

    openAction = QAction(QIcon("resources/open_icon.png"), "Open Bible File")
    openAction.triggered.connect(bible_app.load_xml)
    toolbar.addAction(openAction)
    toolbar.addWidget(create_toolbar_spacer())

    fontAction = QAction(QIcon("resources/font_icon.png"), "Change Font")
    fontAction.triggered.connect(bible_app.change_font)
    toolbar.addAction(fontAction)
    toolbar.addWidget(create_toolbar_spacer())
    
    searchAction = QAction(QIcon("resources/search_icon.png"), "Search")
    searchAction.triggered.connect(bible_app.show_search)
    toolbar.addAction(searchAction)
    toolbar.addWidget(create_toolbar_spacer())

    exitAction = QAction(QIcon("resources/exit_icon.png"), "Exit")
    exitAction.triggered.connect(lambda: app.quit() if bible_app.confirm_exit() else None)
    toolbar.addAction(exitAction)
    
    # Add a spacer to push the next button to the right end
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    toolbar.addWidget(spacer)

    # Add "About" icon to the far right
    rightButtonAction = QAction(QIcon("resources/about_icon.png"), "About")
    rightButtonAction.triggered.connect(bible_app.show_about)
    toolbar.addAction(rightButtonAction)

    window.setWindowTitle("PyBible")
    window.setWindowIcon(QIcon("resources/icon.png"))
    window.show()

    app.exec()
    