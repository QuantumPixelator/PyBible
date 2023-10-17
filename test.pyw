from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QFontDialog, QFileDialog, QComboBox, QTextEdit, QPushButton, QToolBar, QMessageBox, QDialog, QLineEdit, QTextBrowser
from PySide6.QtCore import Qt, QUrl, QSettings
from PySide6.QtGui import QAction, QFont, QIcon
import sys
from xml.etree import ElementTree as ET

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
        layout.addWidget(self.chapterComboBox)
        layout.addWidget(self.verseTextBox)

        self.bookComboBox.currentIndexChanged.connect(self.load_chapters)
        self.chapterComboBox.currentIndexChanged.connect(self.load_verses)

        self.setLayout(layout)
        self.root = None
        self.last_opened_file = None

        # Load settings
        self.settings = QSettings("MyCompany", "PyBible")
        self.restore_settings()

    def closeEvent(self, event):
        # Save settings when the application is closed
        self.save_settings()
        event.accept()

    def save_settings(self):
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.endGroup()
        self.settings.setValue("lastOpenedFile", self.last_opened_file)
        self.settings.setValue("lastSelectedBook", self.bookComboBox.currentIndex())
        self.settings.setValue("lastSelectedChapter", self.chapterComboBox.currentIndex())
        self.settings.setValue("lastSelectedVerse", self.verseTextBox.verticalScrollBar().value())

    def restore_settings(self):
        self.settings.beginGroup("MainWindow")
        self.restoreGeometry(self.settings.value("geometry", self.saveGeometry()))
        self.restoreState(self.settings.value("windowState", self.saveState()))
        self.settings.endGroup()
        self.last_opened_file = self.settings.value("lastOpenedFile")
        self.bookComboBox.setCurrentIndex(int(self.settings.value("lastSelectedBook", 0)))
        self.chapterComboBox.setCurrentIndex(int(self.settings.value("lastSelectedChapter", 0)))
        self.verseTextBox.verticalScrollBar().setValue(int(self.settings.value("lastSelectedVerse", 0)))

    def change_font(self):
        ok, font = QFontDialog.getFont()
        if ok:
            self.verseTextBox.setFont(QFont(font.family(), font.pointSize()))

    def load_verses(self):
        self.verseTextBox.clear()
        book_name = self.bookComboBox.currentText()
        chapter_number = self.chapterComboBox.currentText()
        if self.root:
            for verse in self.root.findall(f".//b[@n='{book_name}']/c[@n='{chapter_number}']/v"):
                verse_num = verse.get("n")
                verse_text = verse.text
                self.verseTextBox.append(f"<small style='color: #0078D7;'>{verse_num}</small> {verse_text}")

    def load_chapters(self):
        self.chapterComboBox.clear()
        book_name = self.bookComboBox.currentText()
        if self.root:
            for chapter in self.root.findall(f".//b[@n='{book_name}']/c"):
                chapter_num = chapter.get("n")
                self.chapterComboBox.addItem(chapter_num)

    def load_xml(self):
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getOpenFileName(self, "Open Bible File", "", "XML Files (*.xml);;All Files (*)", options=options)
        if filePath:
            tree = ET.parse(filePath)
            self.root = tree.getroot()
            self.titleLabel.setText(filePath.split("/")[-1].replace(".xml", ""))
            self.bookComboBox.clear()
            for book in self.root.findall(".//b"):
                book_name = book.get("n")
                self.bookComboBox.addItem(book_name)
            self.load_chapters()

    def confirm_exit(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setText("Are you sure you want to exit?")
        msg.setWindowTitle("Exit Confirmation")
        msg.setWindowIcon(QIcon("icon.png"))
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        return msg.exec() == QMessageBox.Yes

    def search_verses(self, query):
        search_results = []
        if self.root:
            for verse in self.root.findall(".//v"):
                verse_text = verse.text if verse.text else ""
                verse_text = verse_text.strip()
                if query.lower() in verse_text.lower():
                    chapter_element = verse.getparent()  # Directly navigate to the parent
                    book_element = chapter_element.getparent() if chapter_element else None  # Navigate to the grandparent
                    
                    if book_element is not None and chapter_element is not None:
                        book = book_element.get("n")
                        chapter = chapter_element.get("n")
                        verse_num = verse.get("n")
                        search_results.append(f"{book} {chapter}:{verse_num} - {verse_text}")
        return search_results

    def show_search_dialog(self):
        dialog = QDialog()
        dialog.setWindowTitle("Search")
        dialog.setWindowIcon(QIcon("icon.png"))
        
        layout = QVBoxLayout()
        self.searchInput = QLineEdit()
        searchButton = QPushButton("Search")
        self.searchResults = QTextBrowser()
        self.searchResults.setOpenExternalLinks(False)
        self.searchResults.anchorClicked.connect(self.go_to_verse)
        
        layout.addWidget(self.searchInput)
        layout.addWidget(searchButton)
        layout.addWidget(self.searchResults)
        
        dialog.setLayout(layout)
        searchButton.clicked.connect(self.perform_search)
        dialog.exec()

    def perform_search(self):
        query = self.searchInput.text()
        print(f"Performing search for query: {query}")  # Debug print
        results = self.search_verses(query)
        print(f"Search results: {results}")  # Debug print
        self.searchResults.clear()
        for result in results:
            self.searchResults.append(result)

    def go_to_verse(self, url):
        parts = url.toString().split("://")[1].split("/")
        book, chapter, verse = parts

        index = self.bookComboBox.findText(book)
        if index >= 0:
            self.bookComboBox.setCurrentIndex(index)

        index = self.chapterComboBox.findText(chapter)
        if index >= 0:
            self.chapterComboBox.setCurrentIndex(index)

        self.load_verses()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = QMainWindow()

    toolbar = QToolBar()
    window.addToolBar(Qt.TopToolBarArea, toolbar)

    bible_app = BibleApp()

    openAction = QAction(QIcon("open_icon.png"), "Open Bible File")
    openAction.triggered.connect(bible_app.load_xml)
    toolbar.addAction(openAction)

    fontAction = QAction(QIcon("font_icon.png"), "Change Font")
    fontAction.triggered.connect(bible_app.change_font)
    toolbar.addAction(fontAction)

    searchAction = QAction(QIcon("search_icon.png"), "Search")
    searchAction.triggered.connect(bible_app.show_search_dialog)
    toolbar.addAction(searchAction)

    exitAction = QAction(QIcon("exit_icon.png"), "Exit")
    exitAction.triggered.connect(lambda: app.quit() if bible_app.confirm_exit() else None)
    toolbar.addAction(exitAction)

    window.setWindowTitle("PyBible")
    window.setWindowIcon(QIcon("icon.png"))
    window.setCentralWidget(bible_app)
    window.resize(800, 600)
    window.show()

    app.exec()
