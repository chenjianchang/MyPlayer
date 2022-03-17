from PySide6.QtWidgets import QScrollArea, QPushButton
from PySide6.QtGui import QIcon, QPalette, QColor
import webbrowser

class editor_window(QScrollArea):
    def __init__(self, w = 800):
        super().__init__()

        # set title for the window
        self.setWindowTitle("subtitle editor")
        self.setWindowIcon(QIcon('.\\Icon\\subtitle_editor'))
        self.resize(900, 300)

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



    @staticmethod
    def help_manual():
        webbrowser.open(".\\Icon\\default.svg")

if __name__ == "__main__":
    pass