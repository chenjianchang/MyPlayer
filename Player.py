from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout,
                                QPushButton, QStyle, QSlider, QCheckBox, QToolButton,
                                QSpinBox, QSizePolicy, QLabel, QFileDialog)                       
from PySide6.QtGui import QIcon, QPalette, QColor, QTextOption
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, QUrl, Slot
from Subtitle import subtitle
from Editor_window import editor_window
from Timeline_window import timeline_window
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

        # set title, icon, and size for the window
        self.setWindowTitle("Player")
        self.setWindowIcon(QIcon('.\\Icon\\player.png'))
        available_geometry = self.screen().availableGeometry()
        self.resize(available_geometry.width()*2/3, available_geometry.height()*2/3)

        if os.path.exists('data.db'):
            self.load_location()
        else:
            print("Files missed!")
        
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
        self.volBox = QPushButton()
        self.volBox.setToolTip('Volume')
        self.volBox.setEnabled(False)
        self.volBox.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        self.volBox_flag = 1

        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(50)
        self.vol_slider.setToolTip(f"volume is {self.vol_slider.value()}")
        # create area for subtitle
        self.subtitle_box = subtitle()
        self.subtitle_box.setFixedWidth(self.width())
        self.subtitle_box.send_close_signal_to_mainwindow.connect(self.uncheck_ccChBox)
        # create other windows
        self.editor_window = editor_window()
        self.timeline_window = timeline_window()

        if self.ccChBox.isChecked():
            self.subtitle_box.show()
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
        horizontal_layout.addWidget(self.vol_slider)
        horizontal_layout.setStretch(2, 5)
        horizontal_layout.setStretch(7, 1)
        
        vertical_layout.addWidget(self._video_widget)
        vertical_layout.addLayout(horizontal_layout)
        vertical_layout.addWidget(self.status_label)

        # set layout
        self.setLayout(vertical_layout)

        # media player signals
        self.ccChBox.clicked.connect(self.ccCheckBox_changed)
        self.volBox.clicked.connect(self.volBox_change_icon)
        self.openBtn.clicked.connect(self.open_file)
        self.playBtn.clicked.connect(self.play_video)
        self._player.playbackStateChanged.connect(self.media_state_changed)
        self._player.positionChanged.connect(self.position_changed)
        self._player.durationChanged.connect(self.duration_changed)
        self.slider.sliderMoved.connect(self.set_position)
        self.toolBtn_editor.clicked.connect(self.show_editor_window)
        self.toolBtn_timeline.clicked.connect(self.show_timeline_window)
        self.vol_slider.valueChanged.connect(self.setvol)

    def open_file(self):
        self._ensure_stopped()
        filename, _ = QFileDialog.getOpenFileName(self)
        if filename != '':
            self._player.setSource(QUrl.fromLocalFile(filename))
            self.playBtn.setEnabled(True)
            self.status_label.setStyleSheet("background-color: rgb(255, 255, 255); color: black")
            self.status_label.setAlignment(Qt.AlignRight)
            self.status_label.setText("open successfully!")

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
            sql = '''UPDATE CURRENT_VIDEO_INFO SET PATH_VIDEO = "", LAST_PATH = "", DURATION = 1000;'''
            Functions.sqlite_update(sql)
        else:
            sql = f'''UPDATE CURRENT_VIDEO_INFO SET PATH_VIDEO = {self.file_name}, LAST_PATH = {os.path.dirname(self.file_name)}, DURATION = {VideoFileClip(self.file_name).duration};'''
            Functions.sqlite_update(sql)     

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
        self._audio_output.setVolume(self.vol_slider.value()/100)
        self.vol_slider.setToolTip(f"volume is {self.vol_slider.value()}")

    def set_position(self, position):
        self._player.setPosition(position)
 
    def ccCheckBox_changed(self):
        if self.ccChBox.isChecked():
            self.subtitle_box.show()
        else:
            self.subtitle_box.hide()

    def volBox_change_icon(self):
        if self.volBox_flag == 1:
            self.volBox.setIcon(self.style().standardIcon(QStyle.SP_MediaVolumeMuted))
            self.vol_slider.setEnabled(False)
            self._audio_output.setVolume(0)

            self.volBox_flag = 2
        else:
            self.volBox.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
            self.vol_slider.setEnabled(True)
            self.setvol()
            self.volBox_flag = 1


    def media_state_changed(self):
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
  
    def closeEvent(self, event) -> None:
        # save mainwindow's location to database
        sql = f'''UPDATE MAIN_WINDOW SET ID = 1, X = {self.x()}, Y = {self.y()}, Width = {self.width()}, Height = {self.height()};'''
        Functions.sqlite_update(sql)

        self._ensure_stopped()
        return super().closeEvent(event)

    def load_location(self):
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute("SELECT X, Y, Width, Height from MAIN_WINDOW")
        data = c.fetchall()
        self.move(data[0][0], data[0][1])
        self.resize(data[0][2], data[0][3])
        conn.commit()
        conn.close()

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

    @Slot()
    def show_timeline_window(self):
        if self.timeline_window.isHidden():
            self.timeline_window.show()
        else:
            self.timeline_window.hide()

    def __del__(self):
        # when class deleted, run this block
        pass


if __name__ == "__main__":
    pass    