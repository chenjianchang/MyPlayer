# -*- coding: UTF-8 -*-
# Date: 2021.05.28
# Author: Chen Jianchang
# Email: ribenyuchen@163.com
# Version: 1.0


import json
import webbrowser
from operator import itemgetter  # sort the text boxes in editor
import os
import cv2 as cv
import librosa.display
import matplotlib.pyplot as plt
from PyQt5 import QtCore, QtSvg, QtGui
from PyQt5.QtCore import QPoint, Qt, QUrl, pyqtSignal, QEvent, QObject, pyqtSlot
from PyQt5.QtGui import QColor, QIcon, QImage, QPalette, QPixmap, QTextOption
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import QApplication, QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, \
    QPushButton, QScrollBar, QSlider, QSpinBox, QTextEdit, QToolButton, QVBoxLayout, QWidget, QStyle, QSizePolicy, \
    QFileDialog, QScrollArea
# audio picture
from moviepy.editor import *
from pydub import AudioSegment

# current path
BASE_DIR = os.path.split(os.path.realpath(__file__))[0]
os.chdir(BASE_DIR)


# player window
class Player(QWidget):
    send_open_signal_to_timeline_window = pyqtSignal()
    send_open_signal_to_editor_window = pyqtSignal(str)
    send_position_signal_to_image_frame_in_timeline_window = pyqtSignal(int)  # position parameter

    def __init__(self, name="MyPlayer"):
        super().__init__()

        # set title, icon for the window
        self.setWindowTitle("My Media Player")
        self.setWindowIcon(QIcon('.\\Icon\\player.png'))

        # set a name for config file
        # save the data in that file, and load it when run the application 
        self.name = name
        self.file_name = ""
        self.subtitle_filename = ""
        self.format_list = ['.flv', '.mp4', '.ts']
        # video total time
        self.total_time = 1
        # save subtitle data
        self.subtitle_data = ""

        if os.path.exists('%s.ini' % self.name):
            self.load_location()

        # set the background color of the window
        p = self.palette()
        p.setColor(QPalette.Window, QColor(255, 255, 255))
        self.setPalette(p)

        self.save_current_video_info(True)
        self.init_ui()
        self.show()

    def init_ui(self):
        # create media player object
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        # set signal emition frequency (ms)
        self.mediaPlayer.setNotifyInterval(10)
        # create videowidget object
        self.videowidget = QVideoWidget()
        self.mediaPlayer.setVideoOutput(self.videowidget)
        # create open button
        self.openBtn = QPushButton("Open")
        self.openBtn.setToolTip('open a video file')

        # create button for playing
        self.playBtn = QPushButton()
        self.playBtn.setEnabled(False)
        self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playBtn.setToolTip('play/stop')

        # create slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.setEnabled(False)
        self.slider.setToolTip('slider')

        # create button for cc
        self.ccChBox = QCheckBox()
        self.ccChBox.setChecked(False)
        self.ccChBox.setToolTip('open subtitle')

        # create tool button for editor and timeline
        self.toolBtn = QToolButton()
        self.toolBtn.setIcon(self.style().standardIcon(QStyle.SP_ToolBarHorizontalExtensionButton))
        self.toolBtn.setToolTip('open editor window')
        self.toolBtn.setEnabled(False)
        self.toolBtn.setToolButtonStyle(Qt.ToolButtonIconOnly)

        # create tool button for editor and timeline
        self.toolBtn_timeline = QToolButton()
        self.toolBtn_timeline.setIcon(self.style().standardIcon(QStyle.SP_ToolBarVerticalExtensionButton))
        self.toolBtn_timeline.setToolTip('open timeline window')
        self.toolBtn_timeline.setEnabled(False)
        self.toolBtn_timeline.setToolButtonStyle(Qt.ToolButtonIconOnly)

        # create spinbox for volume control
        self.volBox = QSpinBox()
        self.volBox.setRange(0, 100)
        self.volBox.setValue(50)
        self.volBox.setToolTip('volume')

        # create label
        self.label = QLabel()
        self.label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # create area for subtitle
        self.subtitle = QTextEdit()
        self.subtitle.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.subtitle.setEnabled(False)
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setPlaceholderText("subtitle area")
        if self.ccChBox.isChecked():
            self.subtitle.show()
        else:
            self.subtitle.hide()

        # create horizontal box layout
        hboxLayout = QHBoxLayout()
        hboxLayout.setContentsMargins(0, 0, 0, 0)

        # set widgets to the horizontal box layout
        hboxLayout.addWidget(self.openBtn)
        hboxLayout.addWidget(self.playBtn)
        hboxLayout.addWidget(self.slider)
        hboxLayout.addWidget(self.volBox)
        hboxLayout.addWidget(self.ccChBox)
        hboxLayout.addWidget(self.toolBtn_timeline)
        hboxLayout.addWidget(self.toolBtn)

        # create vbox layout
        vboxLayout = QVBoxLayout()
        vboxLayout.addWidget(self.videowidget)
        vboxLayout.addWidget(self.subtitle)
        vboxLayout.addLayout(hboxLayout)
        vboxLayout.addWidget(self.label)

        self.setLayout(vboxLayout)

        # media player signals
        self.openBtn.clicked.connect(self.open_file)
        self.playBtn.clicked.connect(self.play_video)
        self.slider.sliderMoved.connect(self.set_position)
        self.mediaPlayer.stateChanged.connect(self.mediastate_changed)
        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)
        self.ccChBox.clicked.connect(self.ccCheckBox_changed)
        self.volBox.valueChanged.connect(self.setvol)

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Video")
        if filename != '':
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))
            self.videowidget.setStyleSheet("background-color:black")
            self.playBtn.setEnabled(True)
            self.label.setStyleSheet("background-color: rgb(255, 255, 255); color: black")
            self.label.setAlignment(Qt.AlignRight)
            self.label.setText("open successfully!")

            self.subtitle.setEnabled(True)
            self.subtitle.setStyleSheet("font-family: 'Microsoft YaHei UI'; \
                background-color: rgb(0, 0, 0); font-size: 50px; color: white; selection-color: pink")

            self.slider.setEnabled(True)
            self.toolBtn.setEnabled(True)
            self.toolBtn_timeline.setEnabled(True)

            # save file name of the video
            self.file_name = filename
            support = False
            for f in self.format_list:
                if self.file_name.endswith(f):
                    self.subtitle_filename = self.file_name[0:-len(f)] + ".vtt"
                    support = True
                    break
            if support:
                pass
            else:
                print("the video format is not supported!")
                pass

            if os.path.isfile(self.subtitle_filename):
                with open(self.subtitle_filename, "r") as f:
                    self.subtitle_data = f.readlines()
                    self.subtitle.setText("find available subtitle!")
                    self.subtitle.setAlignment(Qt.AlignCenter)
                self.send_open_signal_to_editor_window.emit(self.subtitle_filename)
            else:
                self.subtitle.setText("no subtitle file found!")  # no significance
                self.subtitle.setAlignment(Qt.AlignCenter)  # no significance
                self.send_open_signal_to_editor_window.emit("clear items")
            # if file is available, send signal to timeline window to init UI
            self.send_open_signal_to_timeline_window.emit()
            self.mediaPlayer.play()
            self.mediaPlayer.pause()
            self.save_current_video_info(False)
            self.setWindowTitle("My Media Player" + "   " + filename)
        else:
            print("no video file was chosen!")

    def play_video(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.set_position(self.slider.value() / (self.slider.maximum()) * self.total_time)
            self.mediaPlayer.play()

    def mediastate_changed(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def position_changed(self, position):
        # send player position to timeline window
        self.send_position_signal_to_image_frame_in_timeline_window.emit(position)
        self.slider.setValue(position)
        self.label.setText("{0}/{1}".format(str(Player.change_position_into_time(position)),
                                            str(Player.change_position_into_time(self.total_time))))
        self.subtitle.setText(self.get_subtitle(position))
        self.subtitle.document().setDefaultTextOption(QTextOption(Qt.AlignCenter))

    def ccCheckBox_changed(self):
        if self.ccChBox.isChecked():
            self.subtitle.show()
        else:
            self.subtitle.hide()

    def setvol(self):
        self.mediaPlayer.setVolume(self.volBox.value())

    def get_subtitle(self, position):
        subtitle_content = ""
        write_or_not = False
        try:
            for each_line in self.subtitle_data:
                if "-->" in each_line:
                    if write_or_not:
                        break
                else:
                    if write_or_not:
                        subtitle_content = subtitle_content + each_line
                    continue
                try:
                    if (int(position) >= int(each_line[0:2]) * 60 * 60 * 1000 + int(each_line[3:5]) * 60 * 1000 + int(each_line[6:8]) * 1000 + int(each_line[9:12])
                        or int(position) == int(each_line[0:2]) * 60 * 60 * 1000 + int(each_line[3:5]) * 60 * 1000 + int(each_line[6:8]) * 1000 + int(each_line[9:12])) \
                            and int(position) < int(each_line[17:19]) * 60 * 60 * 1000 + int(each_line[20:22]) * 60 * 1000 + int(each_line[23:25]) * 1000 + int(each_line[26:29]):
                        write_or_not = True
                        continue
                    else:
                        continue
                except:
                    pass
        except:
            subtitle_content = "the subtitle fails"
        return subtitle_content

    @classmethod
    def change_position_into_time(cls, position):
        return (str(int(int(int(position // 1000) // 60) // 60)).zfill(2)
                + ":" + str(int(int(position // 1000) // 60) - int(int(int(position // 1000) // 60) // 60) * 60).zfill(2)
                + ":" + str(int(position // 1000) - int(int(position // 1000) // 60) * 60 - int(int(int(position // 1000) // 60) // 60) * 3600).zfill(2)
                + "." + str(int(position % 1000)).zfill(3))

    @classmethod
    def change_time_into_position(cls, time):
        """ time is a string format like 00:01:03.600, return it with a millisecond unit value """
        return int(time[0:2]) * 60 * 60 * 1000 + int(time[3:5]) * 60 * 1000 + int(time[6:8]) * 1000 + int(time[9:12])

    def duration_changed(self, duration):
        self.slider.setRange(0, duration)
        self.total_time = duration

    def set_position(self, position):
        self.mediaPlayer.setPosition(position)

    def save_location(self):
        with open('%s.ini' % self.name, 'w') as f:
            data = {'x': self.x(), 'y': self.y(), 'w': self.width(), 'h': self.height()}
            f.write(json.dumps(data))

    def save_current_video_info(self, init=False):
        if init:
            with open('current_video_info.ini', 'w') as f:
                data = {'path_video': "", 'last_path': "", 'duration': 1000}
                f.write(json.dumps(data))
        else:
            with open('current_video_info.ini', 'w') as f:
                data = {'path_video': self.file_name, 'last_path': os.path.dirname(self.file_name),
                        'duration': VideoFileClip(self.file_name).duration}
                f.write(json.dumps(data))

    def closeEvent(self, *args, **kwargs):
        self.save_location()

    def load_location(self):
        with open('%s.ini' % self.name, 'r') as f:
            txt = f.read()
            j = json.loads(txt)
            self.move(j['x'], j['y'])
            self.resize(j['w'], j['h'])

    def refresh_subtitle_data(self):
        with open(self.subtitle_filename, "r") as f:
            self.subtitle_data = f.readlines()

    def handle_errors(self):
        self.playBtn.setEnabled(False)
        self.label.setText("Error: " + self.mediaPlayer.errorString())

    def __del__(self):
        # when class deleted, run this block
        pass


class HoverTracker(QObject):
    positionChanged = pyqtSignal(QPoint)

    def __init__(self, widget):
        super().__init__(widget)
        self._widget = widget
        self.widget.setMouseTracking(True)
        self.widget.installEventFilter(self)

    @property
    def widget(self):
        return self._widget

    def eventFilter(self, obj, event):
        if obj is self.widget and event.type() == QEvent.MouseMove:
            self.positionChanged.emit(event.pos())
        return super().eventFilter(obj, event)


class pic_label(QLabel):
    """ picture label in timeline window """

    def mouseMoveEvent(self, ev):
        return super().mouseMoveEvent(ev)
        # do nothing


class pic_frame(QFrame):
    """ picture frame in timeline window """
    positionChanged = pyqtSignal(QPoint)

    def mouseMoveEvent(self, ev):
        self.positionChanged.emit(ev.pos())
        # print(ev.pos())


# subtitle timeline
class timeline_window(QWidget):
    """ timeline window for viewing audio waveform """
    open_svg_audio_wave = pyqtSignal(str)

    def __init__(self, name="MyPlayer", h=260):
        super().__init__()

        # set title for the window
        self.setWindowTitle("timeline")
        self.setWindowIcon(QIcon('.\\Icon\\timeline.png'))

        # set a name for config file
        # save the data in that file, and load it when run the application 
        self.name = name
        self.window_height = h
        self.split_image_width = 930
        self.image_frame_width = 1
        self.step = 1
        self.duration = 1
        self.image = []  # list for saving Labels in the image_frame
        self.pic_count = 0  # the number of split audios
        self.pic_left = 0  # the duration of the last split audio
        self.svg_width = 1

        if os.path.exists('%s.ini' % self.name):
            self.load_location()
        self.setFixedHeight(self.window_height)

        self.generate = QPushButton(self)
        self.generate.setText("generate")
        self.generate.setToolTip("click to generate the picture")

        self.refresh_picture = QPushButton(self)
        self.refresh_picture.setText("refresh")
        self.refresh_picture.move(160, 0)
        self.refresh_picture.setEnabled(False)
        self.refresh_picture.setToolTip("click to load the picture")

        self.cursor_time = QLineEdit(self)
        self.cursor_time.setGeometry(QtCore.QRect(320, 0, 250, 46))
        self.cursor_time.setStyleSheet("color: #1f77b4")
        self.cursor_time.setEnabled(False)
        self.cursor_time.setAlignment(QtCore.Qt.AlignCenter)
        self.cursor_time.setToolTip("cursor time")

        self.current_time = QLineEdit(self)
        self.current_time.setGeometry(QtCore.QRect(580, 0, 250, 46))
        self.current_time.setStyleSheet("color: red")
        self.current_time.setEnabled(True)
        self.current_time.setAlignment(QtCore.Qt.AlignCenter)
        self.current_time.setToolTip("current time")

        self.image_frame = pic_frame(self)
        self.image_frame.resize(self.width(), 230)
        self.image_frame.lower()

        self.scroll_bar = QScrollBar(self)
        self.scroll_bar.setOrientation(1)
        self.scroll_bar.move(0, 230)
        self.scroll_bar.setGeometry(0, 230, self.width(), 260)
        self.scroll_bar.setStyleSheet("background-color: #1f77b4")
        self.scroll_bar.setEnabled(False)

        self.indicator = QLabel(self.image_frame)
        self.indicator.setStyleSheet("background-color: red")
        self.indicator.resize(3, 116)
        self.indicator.move(self.width() / 2, 230 / 2 - 116 / 2)
        self.indicator.setVisible(False)

        self.open_svg = QPushButton(self)
        self.open_svg.setText("open")
        self.open_svg.move(self.width() - 200, 0)
        self.open_svg.setEnabled(True)
        self.open_svg.setToolTip("click to open an available audio wave")

        self.scroll_bar.valueChanged.connect(self.image_frame_move)
        self.generate.clicked.connect(self.generate_picture)
        self.refresh_picture.clicked.connect(self.set_image_frame)
        self.refresh_picture.clicked.connect(self.update_picture)
        self.image_frame.positionChanged.connect(self.on_position_changed)
        self.open_svg.clicked.connect(self.open_svg_file)

    def open_svg_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Svg")
        if filename != '':
            self.open_svg_audio_wave.emit(filename)

    def init_buttons(self):
        """ after open a video file, init the buttons in the timeline window """
        self.generate.setEnabled(False)  # when open, there are other functions available
        self.refresh_picture.setEnabled(False)
        self.cursor_time.setEnabled(False)

        # remove the temp files
        files = os.listdir('.\\temp\\')
        for file in files:
            if "fig" in file:
                os.remove('.\\temp\\' + file)
            if "audio.mp3" in file:
                os.remove('.\\temp\\' + file)
                os.remove('.\\temp\\split_music\\audio.mp3')
        self.update_picture()
        self.image = []
        self.scroll_bar.setEnabled(False)
        self.indicator.setVisible(False)

    @pyqtSlot(QPoint)
    def on_position_changed(self, p):
        self.cursor_time.setText(
            player.change_position_into_time(int(int(p.x()) / self.image_frame_width * self.duration * 1000)))

    def enable_refresh(self):
        """ after generating the picture, enable the refresh button """
        self.refresh_picture.setEnabled(True)

    def enable_current_time_edit(self):
        """ after loading the picture, enable the time editor """
        self.cursor_time.setEnabled(True)

    def image_frame_move(self):
        """ connect with the scroll bar. when use sliderChange signal, some error occurs """
        self.image_frame.move(
            -self.scroll_bar.value() / self.scroll_bar.maximum() * (self.image_frame_width - self.width()), 0)

    def load_location(self):
        """ set the window property, according to the saved information """
        with open('%s.ini' % self.name, 'r') as f:
            txt = f.read()
            j = json.loads(txt)
            self.move(j['x'], j['y'] + j['h'] + 55)  # 55 is the height of the window title
            self.resize(j['w'], self.window_height)
            self.setFixedWidth(j['w'])

    def set_image_frame(self):
        """ compute and set the size of the image_frame """
        self.image_frame.setGeometry(0, 0, self.image_frame_width, 230)

    def set_image_frame_position(self, position):
        if position / (self.duration * 1000) * self.image_frame_width < self.width() / 2:
            self.image_frame.move(0, 0)
            self.scroll_bar.setValue(0)
            self.indicator.move(int(position / (self.duration * 1000) * self.image_frame_width), 230 / 2 - 116 / 2)
        elif position / (self.duration * 1000) * self.image_frame_width >= self.width() / 2 and position / (
                self.duration * 1000) * self.image_frame_width < self.image_frame_width - self.width() / 2:
            self.image_frame.move(- int(position / (self.duration * 1000) * self.image_frame_width - self.width() / 2),
                                  0)
            self.scroll_bar.setValue((position / (self.duration * 1000) * self.image_frame_width - self.width() / 2) / (
                    self.image_frame_width - self.width()) * self.scroll_bar.maximum())
            self.indicator.move(int(position / (self.duration * 1000) * self.image_frame_width), 230 / 2 - 116 / 2)
        else:
            self.image_frame.move(-self.image_frame_width + self.width(), 0)
            self.scroll_bar.setValue(self.scroll_bar.maximum())
            self.indicator.move(int(position / (self.duration * 1000) * self.image_frame_width), 230 / 2 - 116 / 2)

        # display current time to the editbox
        self.current_time.setText(Player.change_position_into_time(position))

    def update_picture(self):
        """ load the picture onto the Frame (self.image_frame)
            and set the slider, lastly, enable the time editor
        """
        if self.pic_left == 0:
            for i in range(self.pic_count):
                self.image.append(pic_label(self.image_frame))
                self.image[i].resize(self.split_image_width, 230)  # the number is the size of the split image
                self.image[i].move(self.split_image_width * i, 0)
                self.image[i].setPixmap(QPixmap.fromImage(QImage(f".\\temp\\fig{i}.png")))
                self.image[i].show()
        else:
            for i in range(self.pic_count - 1):
                self.image.append(pic_label(self.image_frame))
                self.image[i].resize(930, 230)  # the number is the size of the split image
                self.image[i].move(self.split_image_width * i, 0)
                self.image[i].setPixmap(QPixmap.fromImage(QImage(f".\\temp\\fig{i}.png")))
                self.image[i].show()
            self.image.append(pic_label(self.image_frame))
            self.image[self.pic_count - 1].resize(self.pic_left * 1000 / 5000 * self.split_image_width, 230)
            self.image[self.pic_count - 1].move(self.split_image_width * (self.pic_count - 1), 0)
            self.image[self.pic_count - 1].setPixmap(QPixmap.fromImage(QImage(f".\\temp\\fig{self.pic_count - 1}.png")))
            self.image[self.pic_count - 1].show()

        with open('current_video_info.ini', 'r') as f:
            txt = f.read()
            data = json.loads(txt)
            self.step = ((data[
                              'duration'] // 5 + 1) * self.split_image_width - self.width()) / self.scroll_bar.maximum()
        # self.scroll_bar.setMaximum(101)
        # self.scroll_bar.setRange(0, 100)
        self.cursor_time.setEnabled(True)
        self.scroll_bar.setEnabled(True)
        self.indicator.setVisible(True)
        self.indicator.raise_()

    def split_music(self, begin, end, filepath='.\\temp\\audio.mp3', index=0):
        """ begin(ms), end(ms)"""
        # read the mp3 file
        song = AudioSegment.from_mp3(filepath)
        # cut the mp3 file into a given segment
        song = song[begin: end]
        # save the audio segment
        temp_path = '.\\temp\\split_music\\audio.mp3'
        song.export(temp_path)
        audio_wave_data, sr = librosa.load(temp_path)
        plt.figure(figsize=(30, 3), dpi=40)
        plt.axis('off')
        plt.margins(0, 0)
        librosa.display.waveplot(audio_wave_data, sr)
        plt.savefig(f'.\\temp\\fig{index}.png', bbox_inches="tight", pad_inches=0)

    def get_the_audio_from_file(self):
        """ get the audio from the video file and save it as audio.mp3"""
        with open('current_video_info.ini', 'r') as f:
            txt = f.read()
            data = json.loads(txt)

        video = VideoFileClip(data['path_video'])
        audio = video.audio
        audio.write_audiofile('.\\temp\\audio.mp3')

    def generate_picture(self):
        """ generate the whole picture from the audio.mp3
            and after that, enable the refresh button.
        """
        self.get_the_audio_from_file()

        with open('current_video_info.ini', 'r') as f:
            txt = f.read()
            data = json.loads(txt)
            self.duration = data['duration']

        self.pic_count = int(self.duration // 5)
        self.pic_left = self.duration % 5

        self.scroll_bar.setMaximum(self.duration * 1000)
        self.scroll_bar.setRange(0, (self.duration * 1000))

        if self.pic_count == 0:
            self.split_music(0, 5000)
            self.image_frame_width = self.duration * 1000 / 5000 * self.split_image_width
            # enable the refresh button
            self.refresh_picture.setEnabled(True)
            self.generate.setEnabled(False)
            self.generate.clearFocus()
            self.refresh_picture.setFocus()
            return 0

        if self.pic_left == 0:
            for i in range(0, self.pic_count):
                self.split_music(0 + i * 5000, 5000 + i * 5000, index=i)
            self.image_frame_width = self.pic_count * self.split_image_width
        else:
            self.pic_count += 1
            for i in range(0, self.pic_count - 1):
                self.split_music(0 + i * 5000, 5000 + i * 5000, index=i)

            self.split_music((self.pic_count - 1) * 5000, self.duration * 1000, index=(self.pic_count - 1))
            im_last = cv.imread(f".\\temp\\fig{self.pic_count - 1}.png")
            im_last_resize = cv.resize(im_last, (int(self.pic_left * 1000 / 5000 * self.split_image_width), 92))
            cv.imwrite(f".\\temp\\fig{self.pic_count - 1}.png", im_last_resize)

            self.image_frame_width = (
                                             self.pic_count - 1) * self.split_image_width + self.pic_left * 1000 / 5000 * self.split_image_width

        # enable the refresh button
        self.refresh_picture.setEnabled(True)
        self.generate.setEnabled(False)
        self.generate.clearFocus()
        self.refresh_picture.setFocus()


class qscroll_area(QScrollArea):
    send_move_distance_to_svg_timeline_indicator = pyqtSignal(int)
    get_current_indicator_position = pyqtSignal()
    add_text = pyqtSignal()
    copy_text = pyqtSignal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self.move_flag = ""

    def mousePressEvent(self, a0) -> None:
        if a0.button() == Qt.LeftButton:
            self.move_flag = "Left"
            self.get_current_indicator_position.emit()
            self.mouse_x = a0.pos().x()
            self.setCursor(Qt.PointingHandCursor)
            return super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent) -> None:
        if self.move_flag == "Left":
            # move indicator
            move_x = a0.pos().x() - self.mouse_x
            self.send_move_distance_to_svg_timeline_indicator.emit(move_x)
            self.setCursor(Qt.PointingHandCursor)

    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.setCursor(Qt.ArrowCursor)
        self.move_flag = ""

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        if a0.key() == Qt.Key_A:
            self.add_text.emit()
        if a0.key() == Qt.Key_C:
            self.copy_text.emit()
        return super().keyPressEvent(a0)


class SVG(QtSvg.QSvgWidget):
    send_mouse_position = pyqtSignal(int)

    def __init__(self, path) -> None:
        super().__init__(path)
        self.line_edit = []

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.send_mouse_position.emit(a0.pos().x())
        return super().mouseMoveEvent(a0)


class line_edit_svg(QLineEdit):
    def __init__(self, parent=None):
        super(line_edit_svg, self).__init__(parent)
        self.resize(150, 30)
        self.setPlaceholderText("")
        self.setEnabled(True)
        self.setToolTip("subtitle")
        self.setStyleSheet("border: 2px solid black;color: black;")
        self.setAlignment(Qt.AlignLeft)

    def enterEvent(self, a0: QtCore.QEvent) -> None:
        self.setStyleSheet("background-color:#FFCC00")
        return super().enterEvent(a0)

    def leaveEvent(self, a0: QtCore.QEvent) -> None:
        self.setStyleSheet("border: 2px solid black;color: black;")
        return super().leaveEvent(a0)


class text_frame(QFrame):
    def __init__(self, parent=None) -> None:
        # self.setStyleSheet("background-color:white")
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        pass
        # return super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent) -> None:
        pass
        # return super().mouseMoveEvent(a0)

    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        pass
        # return super().mouseReleaseEvent(a0)

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        pass
        # return super().keyPressEvent(a0)


class Timeline_Svg(QWidget):
    """ timeline window for viewing audio waveform """
    send_indicator_position_to_player_slider = pyqtSignal(int)
    send_text_line_signal_to_editor = pyqtSignal(str)

    def __init__(self, name="MyPlayer", h=260):
        super().__init__()

        # set title for the window
        self.setWindowTitle("timeline")
        self.setWindowIcon(QIcon('.\\Icon\\timeline.png'))

        # set a name for config file
        # save the data in that file, and load it when run the application 
        self.name = name
        self.window_height = h
        self.scrollbar_maximum = 1
        self.svg_width = 1
        self.duration = 1
        self.path = ""
        self.current_svg_indicator_position = 0
        self.text_boxes = []
        self.text_line_position_start = []
        self.text_line_position_end = []
        self.play_indicator_position = 0

        if os.path.exists('%s.ini' % self.name):
            self.load_location()
        self.setFixedHeight(self.window_height)

        self.svg_area = qscroll_area(self)
        self.svg_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.svg_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.svg_area.resize(self.width(), self.height())
        self.svg_area.send_move_distance_to_svg_timeline_indicator.connect(self.move_indicator)
        self.svg_area.get_current_indicator_position.connect(self.get_indicator_position)

        self.open_svg = QPushButton(self)
        self.open_svg.setText("open")
        self.open_svg.move(self.width() - 200, 0)

        self.time = QLineEdit(self)
        self.time.move(30, 0)
        self.time.setText("00:00:00.000")
        self.time.setStyleSheet("color: red")
        self.time.setAlignment(Qt.AlignCenter)
        self.time.setToolTip("play time")

        self.track_time = QLineEdit(self)
        self.track_time.move(330, 0)
        self.track_time.setStyleSheet("color: blue")
        self.track_time.setAlignment(Qt.AlignCenter)
        self.track_time.setToolTip("cursor time")

        self.svg = SVG(".\\Icon\\default.svg")

        self.svg_indicator = QLabel(self.svg)
        self.svg_indicator.setStyleSheet("background-color: red")
        self.svg_indicator.resize(2, self.svg.height())
        self.svg_indicator.move(0, 0)
        self.svg_indicator.setVisible(False)

        self.textframe = text_frame(self)

        self.open_svg.clicked.connect(self.open_file)

    def init_buttons(self):
        self.svg_area.setVisible(False)

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Svg")
        if filename != '':
            self.init_UI(filename)

    def init_UI(self, path):
        self.path = path
        self.svg.load(path)
        self.svg.setMouseTracking(True)
        self.svg_area.setVisible(True)
        self.svg_area.setWidget(self.svg)
        self.svg_area.verticalScrollBar().setValue(int(self.svg_area.verticalScrollBar().maximum() / 2))
        self.scrollbar_maximum = self.svg_area.horizontalScrollBar().maximum()
        self.svg_width = self.svg.width()

        self.svg_indicator.setVisible(True)

        self.svg.send_mouse_position.connect(self.display_time)
        self.svg_area.add_text.connect(self.add_subtitle_line)
        self.svg_area.copy_text.connect(self.copy_cursor_time)
        self.svg_area.horizontalScrollBar().valueChanged.connect(self.move_textframe)

        with open('current_video_info.ini', 'r') as f:
            txt = f.read()
            data = json.loads(txt)
            self.duration = data['duration']

    def add_subtitle_line(self):
        self.send_text_line_signal_to_editor.emit(self.time.text())

    def copy_cursor_time(self):
        clip_board = QApplication.clipboard()
        clip_board.setText(self.track_time.text())

    def display_time(self, x):
        self.track_time.setText(Player.change_position_into_time(x / self.svg_width * self.duration * 1000))

    def get_indicator_position(self):
        self.current_svg_indicator_position = self.svg_indicator.x()

    def load_location(self):
        """ set the window property, according to the saved information """
        with open('%s.ini' % self.name, 'r') as f:
            txt = f.read()
            j = json.loads(txt)
            self.move(j['x'], j['y'] + j['h'] + 55)  # 55 is the height of the window title
            self.resize(j['w'], self.window_height)
            self.setFixedWidth(j['w'])

    def set_position(self, position):
        if position / (self.duration * 1000) * self.svg_width < self.width() / 2:
            self.svg_area.horizontalScrollBar().setValue(0)
            self.svg_indicator.move(int(position / (self.duration * 1000) * self.svg_width), 0)
            self.play_indicator_position = int(position / (self.duration * 1000) * self.svg_width)
        elif position / (self.duration * 1000) * self.svg_width >= self.width() / 2 and position / (
                self.duration * 1000) * self.svg_width < self.svg_width - self.width() / 2:
            self.svg_area.horizontalScrollBar().setValue(
                (position / (self.duration * 1000) * self.svg_width - self.width() / 2) / (
                        self.svg_width - self.width()) * self.scrollbar_maximum)
            self.play_indicator_position = int(position / (self.duration * 1000) * self.svg_width)
            self.svg_indicator.move(int(position / (self.duration * 1000) * self.svg_width), 0)
        else:
            self.svg_area.horizontalScrollBar().setValue(self.scrollbar_maximum)
            self.svg_indicator.move(int(position / (self.duration * 1000) * self.svg_width), 0)
            self.play_indicator_position = int(position / (self.duration * 1000) * self.svg_width)

        for w in self.textframe.children():

            if w.x() <= position / (self.duration * 1000) * self.svg_width and position / (
                    self.duration * 1000) * self.svg_width <= w.x() + w.width():
                w.setStyleSheet("background-color:#FFCC00")
            else:
                w.setStyleSheet("background-color:white")

        # display current time to the editbox
        self.time.setText(Player.change_position_into_time(position))

    def move_indicator(self, int_num):
        if int_num + self.current_svg_indicator_position <= 0:
            self.svg_indicator.move(0, 0)
            self.play_indicator_position = 0
            self.send_indicator_position_to_player_slider.emit(0)
        elif int_num + self.current_svg_indicator_position >= self.svg_width:
            self.svg_indicator.move(self.svg_width, 0)
            self.play_indicator_position = self.svg_width
            self.send_indicator_position_to_player_slider.emit(self.duration * 1000)
        else:
            self.svg_indicator.move(int_num + self.current_svg_indicator_position, 0)
            self.play_indicator_position = int_num + self.current_svg_indicator_position
            self.send_indicator_position_to_player_slider.emit(
                self.duration * 1000 * (int_num + self.current_svg_indicator_position) / self.svg_width)

    def receive_info(self, list1, list2, list3):
        # first, clear all the textbox in svg
        for w in self.textframe.children():
            w.deleteLater()

        self.textframe.resize(self.svg.width(), 230)
        self.textframe.raise_()
        self.textframe.show()

        self.text_boxes = []
        # show all new text boxes
        i = 0
        for t1 in list1:
            self.text_boxes.append(line_edit_svg(self.textframe))
            self.text_boxes[-1].setText(list3[i])
            self.text_boxes[-1].move(
                int(Player.change_time_into_position(t1) / (self.duration * 1000) * self.svg_width),
                int(self.height() / 2 + 20))
            if list2[i] == "00:00:00.000":
                self.text_boxes[-1].show()
                continue
            if Player.change_time_into_position(list2[i]) / (
                    self.duration * 1000) * self.svg_width - Player.change_time_into_position(t1) / (
                    self.duration * 1000) * self.svg_width > 0:
                self.text_boxes[-1].resize(int(Player.change_time_into_position(list2[i]) / (
                        self.duration * 1000) * self.svg_width - Player.change_time_into_position(t1) / (
                                                       self.duration * 1000) * self.svg_width), 30)
                self.text_boxes[-1].show()
            else:
                self.text_boxes[-1].show()
            i += 1
        del list1, list2, list3
        self.refresh_textboxes()
        self.svg_indicator.raise_()

    def move_textframe(self):
        self.textframe.move(self.svg.x(), 0)

    def refresh_textboxes(self):
        for w in self.text_boxes:
            w.show()


class text_item(QFrame):
    change_content_signal = pyqtSignal()
    remove_item = pyqtSignal()

    def __init__(self, time1="00:00:00.000", time2="00:00:00.000", text="hello World!", width=600, height=180, name=""):
        super().__init__()
        self.name = name
        self.time_box1 = QLineEdit()
        self.time_box1.setAlignment(Qt.AlignCenter)
        self.time_box1.setText(time1)
        self.arrow_label = QLabel()
        self.arrow_label.setText(" --> ")
        self.time_box2 = QLineEdit()
        self.time_box2.setAlignment(Qt.AlignCenter)
        self.time_box2.setText(time2)
        self.text_box = QPlainTextEdit()
        # self.text_box = QLabel()
        # self.text_box.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextEditable)

        self.text_box.document().setDefaultTextOption(QTextOption(Qt.AlignCenter))
        self.text_box.setPlainText(text)
        self.text_box.setPlaceholderText("edit here!")
        self.resize(width, height)
        self.setToolTip("right press to delete the item!")

        self.horizontal_layout = QHBoxLayout()
        self.vertical_layout = QVBoxLayout()

        self.horizontal_layout.addWidget(self.time_box1)
        self.horizontal_layout.addWidget(self.arrow_label)
        self.horizontal_layout.addWidget(self.time_box2)

        self.vertical_layout.addLayout(self.horizontal_layout)
        self.vertical_layout.addWidget(self.text_box)
        self.setLayout(self.vertical_layout)

        self.time_box1.editingFinished.connect(self.emit_signal)
        self.time_box2.editingFinished.connect(self.emit_signal)
        self.text_box.textChanged.connect(self.emit_signal)

    def set_value(self, time1="00:00:00.000", time2="00:00:00.000", text="hello World!"):
        self.time_box1.setText(time1)
        self.time_box2.setText(time2)
        self.text_box.setText(text)

    def get_time1(self):
        return self.time_box1.text()

    def get_time2(self):
        return self.time_box2.text()

    def get_text(self):
        return self.text_box.document().toPlainText()

    def get_height(self):
        return self.height()

    def get_label(self):
        return self.arrow_label.text()

    def enterEvent(self, a0: QtCore.QEvent) -> None:
        self.setStyleSheet("background-color: #c8beb7")
        return super().enterEvent(a0)

    def leaveEvent(self, a0: QtCore.QEvent) -> None:
        self.setStyleSheet("background-color: white")
        return super().leaveEvent(a0)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        if a0.button() == Qt.RightButton:
            self.arrow_label.setText("remove!")
            self.remove_item.emit()
        return super().mousePressEvent(a0)

    def emit_signal(self):
        self.change_content_signal.emit()


# subtitle editor
class editor_window(QScrollArea):
    send_item_info_to_timeline_svg = pyqtSignal(list, list, list)
    refresh_subtitle_signal = pyqtSignal()

    def __init__(self, name="MyPlayer", w=800):
        super().__init__()

        # set title for the window
        self.setWindowTitle("subtitle editor")
        self.setWindowIcon(QIcon('.\\Icon\\subtitle_editor'))

        # set a name for config file
        # save the data in that file, and load it when run the application 
        # self.setGeometry(QtCore.QRect(150, 100, 2000, 1476))
        self.name = name
        self.video_file_path = ""
        self.video_directory = ""
        self.window_width = w
        self.item = []
        self.text_box_start_position = []  # millisecond
        self.start_time = []
        self.end_time = []
        self.every_text = []
        self.duration = 1

        if os.path.exists('%s.ini' % self.name):
            self.load_location()

        # set the background color of the window
        p = self.palette()
        p.setColor(QPalette.Window, QColor(255, 255, 255))
        self.setPalette(p)

        self.open = QPushButton(self)
        self.open.setText("open")
        self.open.move(10, 0)
        self.open.clicked.connect(self.open_subtitle_file)

        self.save = QPushButton(self)
        self.save.setText("save")
        self.save.move(170, 0)

        self.help = QPushButton(self)
        self.help.setText("help")
        self.help.move(self.width() - 30, 0)

        self.text_area = QFrame(self)
        self.text_area.setStyleSheet("background-color: white")

        self.setWidget(self.text_area)

        self.p = 1  # vertical position

        self.save.clicked.connect(self.save_file)
        self.help.clicked.connect(self.help_manual)

        self.automatic_open_subtitle = False

    def open_subtitle_file(self, str):
        if str == "clear items":
            for i in self.text_area.children():
                i.deleteLater()
            self.item = []
            self.text_box_start_position = []  # millisecond
            self.start_time = []
            self.end_time = []
            self.every_text = []
            return

        if self.automatic_open_subtitle:
            filename = str
        else:
            filename, _ = QFileDialog.getOpenFileName(self, "Open Subtitle")
        if filename != '' and filename[-3:] == "vtt":
            for i in self.text_area.children():
                i.deleteLater()
            self.item = []
            self.text_box_start_position = []  # millisecond
            self.start_time = []
            self.end_time = []
            self.every_text = []
            text = ""
            write_or_not = False
            with open(filename, "r") as f:
                txt = f.readlines()
            for unit in txt:
                if "-->" in unit:
                    self.start_time.append(unit[0:12])
                    self.text_box_start_position.append(Player.change_time_into_position(unit[0:12]))
                    self.end_time.append(unit[17:29])
                    self.every_text.append(text)
                    text = ""
                    write_or_not = True
                else:
                    if write_or_not:
                        text += unit
            # record the last text line
            self.every_text.append(text)
            text = ""
            self.every_text.pop(0)

            for i in range(len(self.start_time)):
                try:
                    self.item.append(
                        text_item(time1=self.start_time[i], time2=self.end_time[i], text=self.every_text[i]))
                except:
                    pass
            self.display_all_textbox()
        else:
            print("the subtitle format is not supported!")
        if not self.automatic_open_subtitle:
            self.send_item_info_to_timeline_svg.emit(self.start_time, self.end_time, self.every_text)
        self.automatic_open_subtitle = False

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        self.window_width = self.width()
        if len(self.item) == 0:
            self.text_area.resize(self.width(), self.height())
        else:
            self.text_area.resize(self.width(), 60 + len(self.item) * (self.item[-1].get_height() + 10))
        # resize the text_item simultaneously, why use try, because when nothing in it, it will cause fault
        try:
            self.refresh_textbox()
        except:
            pass
        self.help.move(self.width() - 212, 0)
        return super().resizeEvent(a0)

    def add_item(self, str_start_time):
        self.item.append(text_item(time1=str_start_time, time2="00:00:00.000", text="" + "\n" + "\n"))
        self.item[-1].setParent(self.text_area)
        self.item[-1].setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.text_box_start_position.append(Player.change_time_into_position(str(str_start_time)))
        self.start_time.append(str_start_time)
        self.end_time.append("00:00:00.000")
        self.every_text.append("" + "\n" + "\n")
        self.display_all_textbox()
        self.refresh_textbox()
        self.save_signal()
        self.send_item_info_to_timeline_svg.emit(self.start_time, self.end_time, self.every_text)

    def rm_item(self):
        i = 0
        for w in self.item:
            if w.get_label() == "remove!":
                w.deleteLater()
                break
            i += 1
        del self.item[i]
        del self.text_box_start_position[i]
        del self.start_time[i]
        del self.end_time[i]
        del self.every_text[i]
        print(i)
        self.save_signal()

    def display_all_textbox(self):
        """ display all textbox in time ascending mode """
        self.text_area.resize(self.text_area.width(), 60 + len(self.item) * (self.item[-1].get_height() + 10))
        textbox_tuple_list = list(zip(self.text_box_start_position, self.item))
        textbox_tuple_list = sorted(textbox_tuple_list, key=itemgetter(0))

        i = 0
        for _, w in textbox_tuple_list:
            w.setParent(self.text_area)
            w.show()
            w.resize(self.window_width - 70, w.height())
            w.move(10, 60 + i * (self.item[0].height() + 10))
            w.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
            w.change_content_signal.connect(self.save_signal)
            w.remove_item.connect(self.rm_item)
            i += 1

    def refresh_textbox(self):
        """ display all textbox in time ascending mode """
        t1 = []
        it = []
        for i in self.text_area.children():
            t1.append(i.get_time1())
            it.append(i)
        ttl = list(zip(t1, it))
        ttl = sorted(ttl, key=itemgetter(0))
        j = 0
        for _, w in ttl:
            w.setParent(self.text_area)
            w.show()
            w.resize(self.window_width - 70, w.height())
            w.move(10, 60 + j * (self.item[0].height() + 10))
            j += 1

    @staticmethod
    def help_manual():
        webbrowser.open(".\\Icon\\default.svg")

    def save_file(self):
        with open('current_video_info.ini', 'r') as f:
            txt = f.read()
            data = json.loads(txt)
            self.video_directory = data['last_path']
            self.video_file_path = data['path_video']
        t1 = []
        it = []
        for i in self.text_area.children():
            t1.append(i.get_time1())
            it.append(i)

        ttl = list(zip(t1, it))
        ttl = sorted(ttl, key=itemgetter(0))
        f = open(self.video_file_path[0:-3] + 'vtt', 'w')
        f.write("WEBVTT" + "\n")
        f.write("kind: captions" + "\n")
        f.write("language: en-us" + "\n")
        f.write("\n" + "\n")

        for _, w in ttl:
            f.write(str(w.get_time1()) + " " + "-->" + " " + str(w.get_time2()) + "\n")
            f.write(str(w.get_text()))
        f.close()

        self.save.setText("save")
        self.refresh_subtitle_signal.emit()
        self.refresh_textbox()

    def load_location(self):
        with open('%s.ini' % self.name, 'r') as f:
            txt = f.read()
            j = json.loads(txt)
            self.move(j['x'] + j['w'], j['y'])
            self.resize(self.window_width, j['h'])
            self.setFixedHeight(j['h'])
        with open('current_video_info.ini', 'r') as f:
            txt = f.read()
            data = json.loads(txt)
            self.duration = data['duration']

    def save_signal(self):
        self.send_item_info_to_timeline_svg.emit(self.start_time, self.end_time, self.every_text)
        self.save.setText("save*")

    def highlight_text(self, position):
        try:
            for w in self.text_area.children():
                if Player.change_time_into_position(w.get_time1()) <= position < Player.change_time_into_position(w.get_time2()):
                    w.setStyleSheet("background-color: #FFCC00")
                    self.verticalScrollBar().setValue((w.y() - self.height() / 2) / (self.text_area.height() - self.height()) * self.verticalScrollBar().maximum())
                else:
                    w.setStyleSheet("background-color: white")
        except:
            print("no items")

    def load_subtitle(self, str_abc):
        self.automatic_open_subtitle = True
        self.open_subtitle_file(str_abc)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = Player()

    editor = editor_window()
    timeline = timeline_window()
    timeline_svg = Timeline_Svg()

    editor.hide()
    timeline.hide()
    timeline_svg.hide()

    def show_editor_window():
        if editor.isHidden():
            editor.show()
        else:
            editor.hide()

    def show_timeline_window():
        if timeline.isHidden():
            timeline.show()
            player.send_position_signal_to_image_frame_in_timeline_window.connect(timeline.set_image_frame_position)
            player.send_open_signal_to_timeline_window.connect(timeline.init_buttons)
        else:
            timeline.hide()

    def open_another_window():
        player.send_open_signal_to_timeline_window.disconnect(timeline.init_buttons)
        player.send_position_signal_to_image_frame_in_timeline_window.disconnect(timeline.set_image_frame_position)
        player.send_position_signal_to_image_frame_in_timeline_window.connect(timeline_svg.set_position)
        timeline.setVisible(False)
        timeline_svg.show()

    player.toolBtn.clicked.connect(show_editor_window)
    player.toolBtn_timeline.clicked.connect(show_timeline_window)
    player.send_open_signal_to_timeline_window.connect(timeline.init_buttons)
    player.send_open_signal_to_timeline_window.connect(timeline_svg.init_buttons)
    player.send_position_signal_to_image_frame_in_timeline_window.connect(timeline.set_image_frame_position)
    player.send_open_signal_to_editor_window.connect(editor.load_subtitle)
    player.send_position_signal_to_image_frame_in_timeline_window.connect(editor.highlight_text)

    timeline.open_svg_audio_wave.connect(open_another_window)
    timeline.open_svg_audio_wave.connect(timeline_svg.init_UI)

    timeline_svg.send_indicator_position_to_player_slider.connect(player.set_position)
    timeline_svg.send_text_line_signal_to_editor.connect(editor.add_item)

    editor.send_item_info_to_timeline_svg.connect(timeline_svg.receive_info)
    editor.refresh_subtitle_signal.connect(player.refresh_subtitle_data)

    sys.exit(app.exec_())
