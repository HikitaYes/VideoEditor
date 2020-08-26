from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import*
from PyQt5.QtCore import Qt
from timeline import TimelineLogic

class WorkSpace(QMainWindow):
    def __init__(self):
        super().__init__()
        self.widget = QWidget(self)
        self.positionVideo = 0

        self.createVideo()
        self.createPlayButton()
        self.createPositionSlider()
        self.createTimelineSlider()
        self.createLayout()

    def createVideo(self):
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        self.mediaPlayer.setNotifyInterval(10)
        self.videoWidget = QVideoWidget()

        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)

    def createPlayButton(self):
        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)

    def createPositionSlider(self):
        self.positionSlider = QSlider(Qt.Horizontal, self.widget)
        self.positionSlider.sliderMoved.connect(self.setPosition)

    def createTimelineSlider(self):
        self.timelineSlider = QSlider(Qt.Horizontal, self.widget)
        self.timelineSlider.setTickInterval(100)
        self.timelineSlider.setTickPosition(QSlider.TicksBelow)
        self.timelineSlider.sliderMoved.connect(self.setPosition)

    def createLayout(self):
        self.timelineWidget = QGraphicsView()
        screenSize = QDesktopWidget().availableGeometry()
        self.timelineWidget.setFixedSize(screenSize.width() - 20, screenSize.height() // 8)

        historyBox = QVBoxLayout()
        text = QLabel('<font size=5> History </font>')
        self.undoView = QUndoView()
        historyBox.addWidget(text)
        historyBox.addWidget(self.undoView)
        history = QWidget()
        history.setLayout(historyBox)

        sliderBox = QHBoxLayout()
        sliderBox.addWidget(self.playButton)
        sliderBox.addWidget(self.positionSlider)

        videoBox = QVBoxLayout()
        videoBox.addWidget(self.videoWidget)
        videoBox.addLayout(sliderBox)
        video = QWidget()
        video.setLayout(videoBox)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #d3d3d3 }")
        splitter.addWidget(history)
        splitter.addWidget(video)

        vbox = QVBoxLayout()
        vbox.addWidget(splitter)
        vbox.addWidget(self.timelineSlider)
        vbox.addWidget(self.timelineWidget)

        self.widget.setLayout(vbox)

    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def mediaStateChanged(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def positionChanged(self, position):
        self.positionVideo = position
        self.positionSlider.setValue(position)
        self.timelineSlider.setValue(position)

    def durationChanged(self, duration):
        self.durationVideo = duration
        self.positionSlider.setRange(0, duration)
        self.timelineSlider.setRange(0, duration)

        self.timelineLogic = TimelineLogic(duration)
        self.timelineWidget.setScene(self.timelineLogic.scene)
        self.undoView.setStack(self.timelineLogic.undoStack)

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)