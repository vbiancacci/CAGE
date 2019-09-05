#!/usr/bin/env python3
"""
"""
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot


def main():
    """
    convention: let's try using the D prefix on our objects
    """
    app = QApplication(sys.argv)
    ex = DCAGE()
    sys.exit(app.exec_())


class DCAGE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('DCAGE: Data acquisition for CAGE')
        self.setGeometry(0, 0, 800, 600)
        self.ctr_widget = DTabWindow(self)
        self.setCentralWidget(self.ctr_widget)
        self.show()


class DTabWindow(QWidget):

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.resize(300,200)

        # Add tabs
        self.tabs.addTab(self.tab1,"Tab 1")
        self.tabs.addTab(self.tab2,"Tab 2")

        # Create first tab
        self.tab1.layout = QVBoxLayout(self)
        self.pushButton1 = QPushButton("PyQt5 button")
        self.tab1.layout.addWidget(self.pushButton1)
        self.tab1.setLayout(self.tab1.layout)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.ctr_widget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())



if __name__=="__main__":
    main()


