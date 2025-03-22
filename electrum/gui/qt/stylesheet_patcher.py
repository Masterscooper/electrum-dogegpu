"""This is used to patch the QApplication style sheet.
It reads the current stylesheet, appends our modifications and sets the new stylesheet.
"""

import sys

from PyQt5 import QtWidgets


CUSTOM_PATCH_FOR_DARK_THEME = '''
/* 
   Dark theme with a black, maroon, and dark purple color scheme.
   Black serves as the primary background, maroon is used for key accents,
   and dark purple provides the neutral elements formerly in grey.
*/

/* 1) Overall application background and text color */
QWidget {
    background-color: #000000; /* Black background */
    color: #dcdcdc;            /* Light grey text */
}

/* 2) Main window */
QMainWindow {
    background-color: #800000; /* Maroon background */
    border: 2px solid #663399;   /* Dark purple border */
    border-radius: 4px;
}

/* 3) Menubar */
QMenuBar {
    background-color: #4B0082; /* Dark purple */
    color: #dcdcdc;            /* Light grey text */
    border: 2px solid #800000; /* Maroon border */
    border-radius: 4px;
    padding: 2px;
}
QMenuBar::item:selected {
    background-color: #800000; /* Maroon when selected */
    color: #ffffff;            /* White text on selection */
}

/* 4) Drop-down menus */
QMenu {
    background-color: #000000; /* Black */
    color: #dcdcdc;            /* Light grey text */
    border: 2px solid #800000; /* Maroon border */
    border-radius: 4px;
    padding: 4px;
}
QMenu::item:selected {
    background-color: #800000; /* Maroon */
    color: #ffffff;            /* White text */
}

/* 5) Toolbars */
QToolBar {
    background-color: #4B0082; /* Dark purple */
    border: 2px solid #800000; /* Maroon border */
    border-radius: 4px;
    padding: 2px;
}

/* 6) Tabs and tab bars */
QTabWidget::pane {
    background-color: #000000; /* Black */
    border: 2px solid #4B0082; /* Dark purple border */
    border-radius: 4px;
    padding: 2px;
}
QTabBar::tab {
    background-color: #800000; /* Maroon */
    color: #dcdcdc;            /* Light grey text */
    border: 2px solid #663399; /* Dark purple border */
    border-radius: 4px;
    padding: 4px;
    margin: 2px;
}
QTabBar::tab:selected {
    background-color: #4B0082; /* Dark purple */
    color: #ffffff;            /* White text */
}

/* 7) StatusBarButton (e.g., bottom-right icons) */
StatusBarButton {
    background-color: transparent;
    border: 2px solid transparent;
    border-radius: 2px;
    margin: 0px;
    padding: 2px;
}
StatusBarButton:checked {
    border: 2px solid #800000; /* Maroon border */
}
StatusBarButton:pressed,
StatusBarButton:hover {
    border: 2px solid #800000; /* Maroon border */
}

/* 8) Table headers (e.g., transaction history columns) */
QHeaderView::section {
    background-color: #4B0082; /* Dark purple */
    color: #dcdcdc;            /* Light grey text */
    padding: 1px;
    border: 1px solid #800000; /* Maroon border */
    border-radius: 1px;
}

/* 9) Table contents (e.g., transaction history rows) */
QTableView {
    background-color: #000000; /* Black */
    gridline-color: #663399;   /* Dark purple gridlines */
    border: 2px solid #663399; /* Dark purple border */
    border-radius: 4px;
    padding: 0px;
}
QTableView::item:selected {
    background-color: #800000; /* Maroon */
    color: #ffffff;            /* White text */
}

/* 10) Scroll areas, line edits, and combo boxes */
QAbstractScrollArea {
    padding: 0px;
    border: 2px solid #663399; /* Dark purple border */
    border-radius: 4px;
}
QAbstractItemView QLineEdit {
    padding: 0px;
    show-decoration-selected: 1;
}
QComboBox {
    border: 2px solid #663399; /* Dark purple border */
    border-radius: 4px;
    padding: 2px;
}
QComboBox::item:checked {
    font-weight: bold;
    max-height: 30px;
}

/* 11) Push buttons */
QPushButton {
    background-color: #4B0082; /* Dark purple */
    color: #dcdcdc;            /* Light grey text */
    border: 2px solid #800000; /* Maroon border */
    border-radius: 4px;
    padding: 5px 10px;
}
QPushButton:hover {
    background-color: #800000; /* Maroon */
}
QPushButton:pressed {
    background-color: #000000; /* Black */
}
'''

CUSTOM_PATCH_FOR_DEFAULT_THEME_MACOS = '''
/* 
   Gold/brown/orange theme adapted for macOS, matching the Windows and Linux styles.
*/

/* 1) Overall application background and text color for all widgets */
QWidget {
    background-color: #FAE6BE; /* light warm gold */
    color: #000000;           /* black text for contrast */
}

/* 2) Main window specifically */
QMainWindow {
    background-color: #8A6425; /* medium brown */
    border: 3px solid #8A6425;
    border-radius: 8px;
}

/* 3) Menubar */
QMenuBar {
    background-color: #E0AC49; /* golden brown */
    color: #000000;
    border: 3px solid #8A6425;
    border-radius: 8px;
    padding: 2px;
}
QMenuBar::item:selected {
    background-color: #C9983E;
    color: #FFFFFF;
}

/* 4) Drop-down menus */
QMenu {
    background-color: #FAE6BE;
    color: #000000;
    border: 3px solid #8A6425;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item:selected {
    background-color: #EDD08C;
    color: #000000;
}

/* 5) Toolbars */
QToolBar {
    background-color: #E0AC49;
    border: 3px solid #8A6425;
    border-radius: 8px;
    padding: 2px;
}

/* 6) Tabs and tab bars */
QTabWidget::pane {
    background-color: #FAE6BE;
    border: 3px solid #E0AC49;
    border-radius: 8px;
    padding: 2px;
}
QTabBar::tab {
    background-color: #F9D62E;
    color: #000000;
    border: 3px solid #8A6425;
    border-radius: 8px;
    padding: 4px;
    margin: 2px;
}
QTabBar::tab:selected {
    background-color: #C9983E;
    color: #000000;
    border: 3px solid #8A6425;
}

/* 7) StatusBarButton (bottom-right icons) */
StatusBarButton {
    background-color: transparent;
    border: 3px solid transparent;
    border-radius: 4px;
    margin: 0px;
    padding: 2px;
}
StatusBarButton:checked {
    border: 3px solid #E0AC49;
}
StatusBarButton:pressed,
StatusBarButton:hover {
    border: 3px solid #E0AC49;
}

/* 8) Table headers (e.g., transaction history columns) */
QHeaderView::section {
    background-color: #E0AC49;
    color: #000000;
    padding: 1px;
    border: 1px solid #8A6425;
    border-radius: 1px;
}

/* 9) Table contents (e.g., transaction history rows) */
QTableView {
    background-color: #FAE6BE;
    gridline-color: #8A6425;
    border: 3px solid #8A6425;
    border-radius: 8px;
    padding: 0px;
}
QTableView::item:selected {
    background-color: #EDD08C;
    color: #000000;
}

/* 10) Scroll areas, line edits, combo boxes */
QAbstractScrollArea {
    padding: 0px;
    border: 3px solid #8A6425;
    border-radius: 8px;
}
QAbstractItemView QLineEdit {
    padding: 0px;
    show-decoration-selected: 1;
}
QComboBox {
    border: 3px solid #8A6425;
    border-radius: 6px;
    padding: 2px;
}
QComboBox::item:checked {
    font-weight: bold;
    max-height: 30px;
}

/* 11) Push buttons */
QPushButton {
    background-color: #E0AC49;
    color: #000000;
    border: 3px solid #8A6425;
    border-radius: 8px;
    padding: 5px 10px;
}
QPushButton:hover {
    background-color: #C9983E;
}
QPushButton:pressed {
    background-color: #BF8D37;
}
'''


CUSTOM_PATCH_FOR_DEFAULT_THEME_LINUX = '''
/* 
   Gold/brown/orange theme with thicker “cartoonish” lines,
   but default/smaller padding so text isn't clipped.
*/

/* 1) Overall application background and text color for all widgets */
QWidget {
    background-color: #FAE6BE; /* light warm gold */
    color: #000000;           /* black text for contrast */
}

/* 2) Main window specifically */
QMainWindow {
    background-color: #8A6425; /* medium brown */
    border: 3px solid #8A6425;
    border-radius: 8px;
}

/* 3) Menubar (File, Wallet, Tools, Help) */
QMenuBar {
    background-color: #E0AC49; /* golden brown */
    color: #000000;
    border: 3px solid #8A6425;
    border-radius: 8px;
    padding: 2px;
}
QMenuBar::item:selected {
    background-color: #C9983E;
    color: #FFFFFF;
}

/* 4) Drop-down menus */
QMenu {
    background-color: #FAE6BE;
    color: #000000;
    border: 3px solid #8A6425;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item:selected {
    background-color: #EDD08C;
    color: #000000;
}

/* 5) Toolbars (if any) */
QToolBar {
    background-color: #E0AC49;
    border: 3px solid #8A6425;
    border-radius: 8px;
    padding: 2px;
}

/* 6) Tabs and tab bars (History, Send, Receive, etc.) */
QTabWidget::pane {
    background-color: #FAE6BE;
    border: 3px solid #E0AC49;
    border-radius: 8px;
    padding: 2px;
}
QTabBar::tab {
    background-color: #F9D62E;
    color: #000000;
    border: 3px solid #8A6425;
    border-radius: 8px;
    padding: 4px;
    margin: 2px;
}
QTabBar::tab:selected {
    background-color: #C9983E;
    color: #000000;
    border: 3px solid #8A6425;
}

/* 7) StatusBarButton (bottom-right icons) */
StatusBarButton {
    background-color: transparent;
    border: 3px solid transparent;
    border-radius: 4px;
    margin: 0px;
    padding: 2px;
}
StatusBarButton:checked {
    border: 3px solid #E0AC49;
}
StatusBarButton:pressed,
StatusBarButton:hover {
    border: 3px solid #E0AC49;
}

/* 8) Table headers (e.g., transaction history columns) */
QHeaderView::section {
    background-color: #E0AC49;
    color: #000000;
    padding: 1px;
    border: 1px solid #8A6425;
    border-radius: 1px;
}

/* 9) Table contents (e.g., transaction history rows) */
QTableView {
    background-color: #FAE6BE;
    gridline-color: #8A6425;
    border: 3px solid #8A6425;
    border-radius: 8px;
    padding: 0px;
}
QTableView::item:selected {
    background-color: #EDD08C;
    color: #000000;
}

/* 10) Scroll areas, line edits, combo boxes */
QAbstractScrollArea {
    padding: 0px;
    border: 3px solid #8A6425;
    border-radius: 8px;
}
QAbstractItemView QLineEdit {
    padding: 0px;
    show-decoration-selected: 1;
}
QComboBox {
    border: 3px solid #8A6425;
    border-radius: 6px;
    padding: 2px;
}
QComboBox::item:checked {
    font-weight: bold;
    max-height: 30px;
}

/* 11) Push buttons */
QPushButton {
    background-color: #E0AC49;
    color: #000000;
    border: 3px solid #8A6425;
    border-radius: 8px;
    padding: 5px 10px;
}
QPushButton:hover {
    background-color: #C9983E;
}
QPushButton:pressed {
    background-color: #BF8D37;
}
'''

CUSTOM_PATCH_FOR_DEFAULT_THEME_WINDOWS = '''
/* 
   Gold/brown/orange theme with a Windows-specific tweak:
   slightly thinner borders and reduced corner rounding.
*/

/* 1) Overall application background and text color for all widgets */
QWidget {
    background-color: #FAE6BE; /* light warm gold */
    color: #000000;
}

/* 2) Main window specifically */
QMainWindow {
    background-color: #8A6425; /* medium brown */
    border: 2px solid #8A6425;
    border-radius: 4px;
}

/* 3) Menubar */
QMenuBar {
    background-color: #E0AC49; /* golden brown */
    color: #000000;
    border: 2px solid #8A6425;
    border-radius: 4px;
    padding: 2px;
}
QMenuBar::item:selected {
    background-color: #C9983E;
    color: #FFFFFF;
}

/* 4) Drop-down menus */
QMenu {
    background-color: #FAE6BE;
    color: #000000;
    border: 2px solid #8A6425;
    border-radius: 4px;
    padding: 4px;
}
QMenu::item:selected {
    background-color: #EDD08C;
    color: #000000;
}

/* 5) Toolbars */
QToolBar {
    background-color: #E0AC49;
    border: 2px solid #8A6425;
    border-radius: 4px;
    padding: 2px;
}

/* 6) Tabs and tab bars */
QTabWidget::pane {
    background-color: #FAE6BE;
    border: 2px solid #E0AC49;
    border-radius: 4px;
    padding: 2px;
}
QTabBar::tab {
    background-color: #F9D62E;
    color: #000000;
    border: 2px solid #8A6425;
    border-radius: 4px;
    padding: 4px;
    margin: 2px;
}
QTabBar::tab:selected {
    background-color: #C9983E;
    color: #000000;
    border: 2px solid #8A6425;
}

/* 7) StatusBarButton */
StatusBarButton {
    background-color: transparent;
    border: 2px solid transparent;
    border-radius: 2px;
    margin: 0px;
    padding: 2px;
}
StatusBarButton:checked {
    border: 2px solid #E0AC49;
}
StatusBarButton:pressed,
StatusBarButton:hover {
    border: 2px solid #E0AC49;
}

/* 8) Table headers */
QHeaderView::section {
    background-color: #E0AC49;
    color: #000000;
    padding: 1px;
    border: 1px solid #8A6425;
    border-radius: 1px;
}

/* 9) Table contents */
QTableView {
    background-color: #FAE6BE;
    gridline-color: #8A6425;
    border: 2px solid #8A6425;
    border-radius: 4px;
    padding: 0px;
}
QTableView::item:selected {
    background-color: #EDD08C;
    color: #000000;
}

/* 10) Scroll areas, line edits, combo boxes */
QAbstractScrollArea {
    padding: 0px;
    border: 2px solid #8A6425;
    border-radius: 4px;
}
QAbstractItemView QLineEdit {
    padding: 0px;
    show-decoration-selected: 1;
}
QComboBox {
    border: 2px solid #8A6425;
    border-radius: 4px;
    padding: 2px;
}
QComboBox::item:checked {
    font-weight: bold;
    max-height: 30px;
}

/* 11) Push buttons */
QPushButton {
    background-color: #E0AC49;
    color: #000000;
    border: 2px solid #8A6425;
    border-radius: 4px;
    padding: 5px 10px;
}
QPushButton:hover {
    background-color: #C9983E;
}
QPushButton:pressed {
    background-color: #BF8D37;
}
'''

# Example dark theme placeholder (if needed)
# CUSTOM_PATCH_FOR_DARK_THEME = '/* dark theme styles go here */'

def patch_qt_stylesheet(use_dark_theme: bool) -> None:
    import sys
    from PyQt5 import QtWidgets  # or PySide2, depending on your setup

    custom_patch = ""
    if use_dark_theme:
        custom_patch = CUSTOM_PATCH_FOR_DARK_THEME
    else:  # default (light) theme
        if sys.platform == 'darwin':
            # macOS-specific theme (assumed to be defined elsewhere)
            custom_patch = CUSTOM_PATCH_FOR_DEFAULT_THEME_MACOS
        elif sys.platform == 'win32':
            custom_patch = CUSTOM_PATCH_FOR_DEFAULT_THEME_WINDOWS
        else:
            custom_patch = CUSTOM_PATCH_FOR_DEFAULT_THEME_LINUX

    app = QtWidgets.QApplication.instance()
    style_sheet = app.styleSheet() + custom_patch
    app.setStyleSheet(style_sheet)
