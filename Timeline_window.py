from PySide6.QtWidgets import QWidget, QGraphicsView
from PySide6 import QtCharts
from PySide6.QtGui import QIcon
import Functions
import sqlite3
import os

class timeline_window(QWidget):
    def __init__(self):
        super().__init__()

        # set title for the window
        self.setWindowTitle("timeline")
        self.setWindowIcon(QIcon('.\\Icon\\timeline_editor.png'))
        
        if os.path.exists('data.db'):
            self.load_location()
        else:
            print("Files missed!")

    def closeEvent(self, event) -> None:
        # save mainwindow's location to database
        sql = f'''UPDATE TIMELINE_WINDOW SET ID = 1, X = {self.x()}, Y = {self.y()}, Width = {self.width()}, Height = {self.height()};'''
        Functions.sqlite_update(sql)
        print("The position of the timeline window is saved!")
        return super().closeEvent(event)

    def load_location(self):
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute("SELECT X, Y, Width, Height from TIMELINE_WINDOW")
        data = c.fetchall()
        self.move(data[0][0], data[0][1])
        self.resize(data[0][2], data[0][3])
        conn.commit()
        conn.close()


if __name__ == "__main__":
    pass