from PySide6.QtWidgets import QTextEdit, QApplication
from PySide6.QtCore import Signal, Qt, QEvent
import PySide6.QtGui

class subtitle(QTextEdit):
    send_close_signal_to_mainwindow = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("subtitle box")
        self.setEnabled(False)
        self.setAlignment(Qt.AlignCenter)
        self.setPlaceholderText("subtitle area")
        self.setStyleSheet("font-family: 'Microsoft YaHei UI'; \
        background-color: rgb(10,10,10); font-size: 25px; color: white; selection-color: pink")
        self.installEventFilter(self)
        self.window_flag = True
        self.flag = self.windowFlags()
        self.a = self.x()
        self.b = self.y()
        self.w = self.width()
        self.h = self.height()

    def eventFilter(self, widget, event) -> bool:
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Alt:
                if self.window_flag:
                    self.setWindowFlags(Qt.FramelessWindowHint | Qt.WA_AlwaysStackOnTop)
                    self.move(self.a, self.b)
                    self.resize(self.w, self.h)
                    self.show()
                    self.window_flag = False
                else:
                    self.setWindowFlags(self.flag)
                    self.move(self.a, self.b)
                    self.resize(self.w, self.h)
                    self.show()
                    self.window_flag = True

        return super().eventFilter(widget, event)

    def moveEvent(self, event: PySide6.QtGui.QMoveEvent) -> None:
        self.a = self.x()
        self.b = self.y()
        return super().moveEvent(event)

    def resizeEvent(self, e: PySide6.QtGui.QResizeEvent) -> None:
        self.w = self.width()
        self.h = self.height()
        return super().resizeEvent(e)

    def closeEvent(self, event) -> None:
        # send signal to mainwindow to uncheck the cc checkbox
        self.send_close_signal_to_mainwindow.emit()        
        return super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication()

    st = subtitle()
    st.show()

    app.exec()