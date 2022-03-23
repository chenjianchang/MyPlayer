from PySide6.QtWidgets import QScrollArea, QPushButton
from PySide6.QtGui import QIcon, QPalette, QColor
import webbrowser
import sqlite3
import Functions
import os

class editor_window(QScrollArea):
    def __init__(self):
        super().__init__()

        # set title for the window
        self.setWindowTitle("subtitle editor")
        self.setWindowIcon(QIcon('.\\Icon\\subtitle_editor'))
        self.resize(900, 300)
        if os.path.exists('data.db'):
            self.load_location()
        else:
            print("Files missed!")

        # set the background color of the window
        p = self.palette()
        p.setColor(QPalette.Window, QColor(255, 255, 255))
        self.setPalette(p)

        # buttons
        self.open = QPushButton(self)
        self.open.setText("open")
        self.open.move(10, 0)
        # self.open.clicked.connect(self.open_subtitle_file)
        # save
        self.save = QPushButton(self)
        self.save.setText("save")
        self.save.move(100, 0)
        # help
        self.help = QPushButton(self)
        self.help.setText("help")
        self.help.move(self.width() - 100, 0)
        self.help.clicked.connect(self.help_manual)

    def closeEvent(self, event) -> None:
        # save mainwindow's location to database
        sql = f'''UPDATE EDITOR_WINDOW SET ID = 1, X = {self.x()}, Y = {self.y()}, Width = {self.width()}, Height = {self.height()};'''
        Functions.sqlite_update(sql)
        print("The position of the editor window is saved!")
        return super().closeEvent(event)


    def load_location(self):
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute("SELECT X, Y, Width, Height from EDITOR_WINDOW")
        data = c.fetchall()
        self.move(data[0][0], data[0][1])
        self.resize(data[0][2], data[0][3])
        conn.commit()
        conn.close()


    @staticmethod
    def help_manual():
        webbrowser.open(".\\Icon\\default.svg")

if __name__ == "__main__":
    pass