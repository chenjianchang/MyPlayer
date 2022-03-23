# -*- coding: UTF-8 -*-
# Date: 2022.03.16
# Author: Shaolang
# Email: 463505965@qq.com
# Version: 1.2

from PySide6.QtWidgets import QApplication
import Player
import sqlite3

def initialize_database():
    # create correct daba.db
    # connect to database
    conn = sqlite3.connect('data.db')
    print ("connect database successfully!")
    c = conn.cursor()
    # create tables if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS MAIN_WINDOW
                (ID     INT NOT NULL,
                    X      INT NOT NULL,
                    Y      INT NOT NULL,
                    Width  INT NOT NULL,
                    Height INT NOT NULL);''')
    c.execute('''CREATE TABLE IF NOT EXISTS TIMELINE_WINDOW
                (ID     INT NOT NULL,
                    X      INT NOT NULL,
                    Y      INT NOT NULL,
                    Width  INT NOT NULL,
                    Height INT NOT NULL);''')
    c.execute('''CREATE TABLE IF NOT EXISTS EDITOR_WINDOW
                (ID     INT NOT NULL,
                    X      INT NOT NULL,
                    Y      INT NOT NULL,
                    Width  INT NOT NULL,
                    Height INT NOT NULL);''')
    c.execute('''CREATE TABLE IF NOT EXISTS PLAYLIST
                (NAME TEXT NOT NULL);''')
    c.execute('''CREATE TABLE IF NOT EXISTS CURRENT_VIDEO_INFO
                (PATH_VIDEO TEXT NOT NULL,
                    LAST_PATH  TEXT NOT NULL,
                    DURATION   INT  NOT NULL);''')
    print ("the tables are ready!")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    app = QApplication()
    initialize_database()
    win = Player.MainWindow()
    app.exec()