# -*- coding: UTF-8 -*-
# Date: 2022.03.16
# Author: Shaolang
# Email: 463505965@qq.com
# Version: 1.1


from PySide6.QtWidgets import (QWidget, QApplication, QHBoxLayout, QVBoxLayout,
                                QPushButton, QStyle, QSlider, QCheckBox, QToolButton,
                                QSpinBox, QSizePolicy, QLabel, QFileDialog)                       
from PySide6.QtGui import QIcon, QPalette, QColor, QTextOption
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, QUrl, Slot
from Subtitle import subtitle
from Editor_window import editor_window
import sqlite3
import os, sys
from moviepy.editor import *
import Functions


# current path
BASE_DIR = os.path.split(os.path.realpath(__file__))[0]
os.chdir(BASE_DIR)


class MainWindow(QWidget):
    # send_open_signal_to_timeline_window = pyqtSignal()
    # send_open_signal_to_editor_window = pyqtSignal(str)
    # send_position_signal_to_image_frame_in_timeline_window = pyqtSignal(int)  # position parameter
    def __init__(self):
        super().__init__()

        # connect to database
        self.conn = sqlite3.connect('data.db')
        print ("connect database successfully!")
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS INFO
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
        self.conn.commit()
        self.conn.close()

        # set title, icon, and size for the window
        self.setWindowTitle("Player")
        self.setWindowIcon(QIcon('.\\Icon\\player.png'))
        available_geometry = self.screen().availableGeometry()
        self.resize(available_geometry.width()*2/3, available_geometry.height()*2/3)

        if os.path.exists('data.db'):
            self.load_location()
        
        # set the background color of the window
        p = self.palette()
        p.setColor(QPalette.Window, QColor(100, 100, 100))
        self.setPalette(p)

        # current video info
        self.file_name = ""
        self.subtitle_filename = ""
        self.format_list = ['.flv', '.mp4', '.ts']
        # video total time
        self.total_time = 1
        self.save_current_video_info(True)

        # save subtitle data
        self.subtitle_data = ""

        # all widgets, private attributes
        # playlist
        self._playlist = [] # FIXME 6.3: Replace by QMediaPlaylist?
        self._playlist_index = -1
        # player and audio output
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self._video_widget = QVideoWidget()
        self._player.setVideoOutput(self._video_widget)
        self._player.errorOccurred.connect(self._player_error)
        # create open button
        self.openBtn = QPushButton("Open")
        self.openBtn.setToolTip("Open a video file")
        # create button for playing
        self.playBtn = QPushButton()
        self.playBtn.setEnabled(False)
        self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playBtn.setToolTip('Play/Stop')
        # create slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.setEnabled(False)
        self.slider.setToolTip('Moment')
        # create button for cc
        self.ccChBox = QCheckBox()
        self.ccChBox.setChecked(False)
        self.ccChBox.setEnabled(False)
        self.ccChBox.setToolTip('Open subtitle')
        # create tool button for editor and timeline
        self.toolBtn_editor = QToolButton()
        self.toolBtn_editor.setIcon(self.style().standardIcon(QStyle.SP_ToolBarHorizontalExtensionButton))
        self.toolBtn_editor.setToolTip('Open editor window')
        self.toolBtn_editor.setEnabled(False)
        self.toolBtn_editor.setToolButtonStyle(Qt.ToolButtonIconOnly)
        # create tool button for editor and timeline
        self.toolBtn_timeline = QToolButton()
        self.toolBtn_timeline.setIcon(self.style().standardIcon(QStyle.SP_ToolBarVerticalExtensionButton))
        self.toolBtn_timeline.setToolTip('Open timeline window')
        self.toolBtn_timeline.setEnabled(False)
        self.toolBtn_timeline.setToolButtonStyle(Qt.ToolButtonIconOnly)
        # create spinbox for volume control
        self.volBox = QSpinBox()
        self.volBox.setRange(0, 100)
        self.volBox.setValue(50)
        self.volBox.setEnabled(False)
        self.volBox.setToolTip('Volume')
        # create area for subtitle
        self.subtitle_box = subtitle()
        self.subtitle_box.setEnabled(False)
        self.subtitle_box.setFixedWidth(self.width())
        self.subtitle_box.setAlignment(Qt.AlignCenter)
        self.subtitle_box.setPlaceholderText("subtitle area")
        self.subtitle_box.send_close_signal_to_mainwindow.connect(self.uncheck_ccChBox)
        # create editor window
        self.editor_window = editor_window()
        
        if self.ccChBox.isChecked():
            self.subtitle_box.show()
            # self.subtitle_box.setFixedWidth(self.width())
        else:
            self.subtitle_box.hide()
        # create label
        self.status_label = QLabel()
        self.status_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        
        # initialize the UI and show it
        self.init_ui()
        self.show()


    def init_ui(self):
        # create layout
        vertical_layout = QVBoxLayout()
        vertical_layout.setContentsMargins(0, 0, 0, 0)
        horizontal_layout = QHBoxLayout()
        horizontal_layout.setContentsMargins(0, 0, 0, 0)
        # add widgets
        horizontal_layout.addWidget(self.openBtn)
        horizontal_layout.addWidget(self.playBtn)
        horizontal_layout.addWidget(self.slider)
        horizontal_layout.addWidget(self.ccChBox)
        horizontal_layout.addWidget(self.toolBtn_editor)
        horizontal_layout.addWidget(self.toolBtn_timeline)
        horizontal_layout.addWidget(self.volBox)

        vertical_layout.addWidget(self._video_widget)
        vertical_layout.addLayout(horizontal_layout)
        vertical_layout.addWidget(self.status_label)

        # set layout
        self.setLayout(vertical_layout)

        # media player signals
        self.ccChBox.clicked.connect(self.ccCheckBox_changed)
        self.volBox.valueChanged.connect(self._audio_output.setVolume)
        self.openBtn.clicked.connect(self.open_file)
        self.playBtn.clicked.connect(self.play_video)
        self._player.playbackStateChanged.connect(self.media_state_changed)
        self.volBox.valueChanged.connect(self.setvol)
        self._player.positionChanged.connect(self.position_changed)
        self._player.durationChanged.connect(self.duration_changed)
        self.slider.sliderMoved.connect(self.set_position)
        self.toolBtn_editor.clicked.connect(self.show_editor_window)


    def open_file(self):
        self._ensure_stopped()
        filename, _ = QFileDialog.getOpenFileName(self)
        if filename != '':
            self._player.setSource(QUrl.fromLocalFile(filename))
            self.playBtn.setEnabled(True)
            self.status_label.setStyleSheet("background-color: rgb(255, 255, 255); color: black")
            self.status_label.setAlignment(Qt.AlignRight)
            self.status_label.setText("open successfully!")

            self.subtitle_box.setEnabled(True)
            self.subtitle_box.setStyleSheet("font-family: 'Microsoft YaHei UI'; \
            background-color: rgb(0, 0, 0); font-size: 25px; color: white; selection-color: pink")
            # update buttons
            self.slider.setEnabled(True)
            self.toolBtn_editor.setEnabled(True)
            self.toolBtn_timeline.setEnabled(True)
            self.ccChBox.setEnabled(True)
            self.volBox.setEnabled(True)

            # save file name of the video and subtitle file
            # judge whether the video format is supported
            self.file_name = filename
            support = False
            for f in self.format_list:
                if self.file_name.endswith(f):
                    self.subtitle_filename = self.file_name[0:-len(f)] + ".vtt"
                    support = True
                    break
            # whether the video is supported
            if support:
                pass
            else:
                self.status_label.setText("the video format is not supported!")
            
            # whether the subtitle file exists
            if os.path.isfile(self.subtitle_filename):
                with open(self.subtitle_filename, "r") as f:
                    self.subtitle_data = f.readlines()
                    self.subtitle_box.setText("find available subtitle!")
                    self.subtitle_box.setAlignment(Qt.AlignCenter)
                # self.send_open_signal_to_editor_window.emit(self.subtitle_filename)
            else:
                self.subtitle_box.setText("no subtitle file found!")  # no significance
                self.subtitle_box.setAlignment(Qt.AlignCenter)  # no significance
                # self.send_open_signal_to_editor_window.emit("clear items")
                # if file is available, send signal to timeline window to init UI
                # self.send_open_signal_to_timeline_window.emit()
                self._player.play()
                self._player.pause()
                self.save_current_video_info(False)
                self.setWindowTitle("My Media Player" + "   " + filename)
        else:
            self.status_label.setText("no video file was chosen!")

    def save_current_video_info(self, init = False):
        # save current video infomation
        if init:
            self.conn = sqlite3.connect('data.db')
            c = self.conn.cursor()
            c.execute('''UPDATE CURRENT_VIDEO_INFO SET PATH_VIDEO = "", LAST_PATH = "", DURATION = 1000;''')
            print ("have saved current video info!")
            self.conn.commit()
            self.conn.close()
        else:
            self.conn = sqlite3.connect('data.db')
            c = self.conn.cursor()
            c.execute(f'''UPDATE CURRENT_VIDEO_INFO SET PATH_VIDEO = {self.file_name}, LAST_PATH = {os.path.dirname(self.file_name)}, DURATION = {VideoFileClip(self.file_name).duration};''')
            print ("update current video info successfully!")
            self.conn.commit()
            self.conn.close()        

    def position_changed(self, position):
        # send player position to timeline window
        # self.send_position_signal_to_image_frame_in_timeline_window.emit(position)
        self.slider.setValue(position)
        self.status_label.setText("{0}/{1}".format(str(Functions.change_position_into_time(position)),
                                            str(Functions.change_position_into_time(self.total_time))))
        self.subtitle_box.setText(Functions.get_subtitle(position, self.subtitle_data))
        self.subtitle_box.document().setDefaultTextOption(QTextOption(Qt.AlignCenter))
   
    def duration_changed(self, duration):
        self.slider.setRange(0, duration)
        self.total_time = duration

    @Slot()
    def uncheck_ccChBox(self):
        # when close subtitle_box, uncheck the ccChBox
        self.ccChBox.setChecked(False)

    # def refresh_subtitle_data(self):
    #     with open(self.subtitle_filename, "r") as f:
    #         self.subtitle_data = f.readlines()

    # def handle_errors(self):
    #     self.playBtn.setEnabled(False)
    #     self.label.setText("Error: " + self.mediaPlayer.errorString())

    def play_video(self):
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
        else:
            self._player.setPosition(int(self.slider.value() / (self.slider.maximum()) * self.total_time))
            self._player.play()

    def setvol(self):
        self._audio_output.setVolume(self.volBox.value())

    def set_position(self, position):
        self._player.setPosition(position)
 
    def ccCheckBox_changed(self):
        if self.ccChBox.isChecked():
            self.subtitle_box.show()
        else:
            self.subtitle_box.hide()


    def media_state_changed(self):
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        
    def closeEvent(self, event) -> None:
        # save mainwindow's location to database
        self.conn = sqlite3.connect('data.db')
        c = self.conn.cursor()
        c.execute(f'''UPDATE INFO SET ID = 1, X = {self.x()}, Y = {self.y()}, Width = {self.width()}, Height = {self.height()};''')
        print ("update the mainwindow's location successfully!")
        self.conn.commit()
        self.conn.close()

        self._ensure_stopped()
        return super().closeEvent(event)

    def load_location(self):
        self.conn = sqlite3.connect('data.db')
        c = self.conn.cursor()
        c.execute("SELECT X, Y, Width, Height  from INFO")
        data = c.fetchall()
        self.move(data[0][0], data[0][1])
        self.resize(data[0][2], data[0][3])
        self.conn.commit()
        self.conn.close()

    @Slot()
    def _ensure_stopped(self):
        if self._player.playbackState() != QMediaPlayer.StoppedState:
            self._player.stop()

    @Slot(QMediaPlayer.Error, str)
    def _player_error(self, error, error_string):
        print(error_string, file = sys.stderr)
        self.status_label.setText(error_string)

    @Slot()
    def show_editor_window(self):
        if self.editor_window.isHidden():
            self.editor_window.show()
        else:
            self.editor_window.hide()

    def __del__(self):
        # when class deleted, run this block
        pass


if __name__ == "__main__":
    app = QApplication()
    win = MainWindow()
    app.exec()
    