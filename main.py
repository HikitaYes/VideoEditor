import sys, os, time
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QDir, QUrl
from PyQt5.QtWidgets import*
from PyQt5.QtMultimedia import QMediaContent
from workspace import WorkSpace

class Communicate(QObject):
    closeApp = pyqtSignal()

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        QToolTip.setFont(QFont('SansSerif', 10))

        self.c = Communicate()
        self.c.closeApp.connect(self.close)

        self.setWindowTitle('Videomaker')
        self.setWindowIcon(QIcon('icons/video.png'))
        self.center()

        self.workspace = WorkSpace()

        self.widget = self.workspace.widget
        self.setCentralWidget(self.widget)
        self.speedIndexBox = 2

        self.createActions()
        self.showMaximized()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', 'Are you sure to quit?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        if e.key() == Qt.Key_Space:
            self.workspace.play()

    def center(self):
        rectWindow = self.frameGeometry()
        self.move(rectWindow.topLeft())

    def createActions(self):
        openAction = QAction(QIcon(os.path.join('icons', 'open.png')), 'Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.triggered.connect(self.showOpenDialog)

        exitAction = QAction(QIcon(os.path.join('icons', 'exit.png')), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(qApp.quit)

        renderAction = QAction(QIcon(os.path.join('icons', 'render.png')), 'Render', self)
        renderAction.setShortcut('Ctrl+R')
        renderAction.triggered.connect(self.render)

        cutAction = QAction(QIcon(os.path.join('icons', 'scissors.png')), 'Cut', self)
        cutAction.setShortcut('C')
        cutAction.triggered.connect(self.cut)

        delAction = QAction(QIcon(os.path.join('icons', 'delete.png')), 'Delete', self)
        delAction.setShortcut('Delete')
        delAction.triggered.connect(self.delete)

        speedAction = QAction(QIcon(os.path.join('icons', 'speed.png')), 'Change speed', self)
        speedAction.setShortcut('S')
        speedAction.triggered.connect(self.changeSpeed)

        imageAction = QAction(QIcon(os.path.join('icons', 'image.png')), 'Add image', self)
        imageAction.setShortcut('I')
        imageAction.triggered.connect(self.addImage)

        undoAction = QAction(QIcon(os.path.join('icons', 'undo.png')), 'Undo', self)
        undoAction.setShortcut('Ctrl+Z')
        undoAction.triggered.connect(self.undo)

        redoAction = QAction(QIcon(os.path.join('icons', 'redo.png')), 'Redo', self)
        redoAction.setShortcut('Ctrl+Y')
        redoAction.triggered.connect(self.redo)

        menu = self.menuBar()
        file = menu.addMenu('File')
        file.addAction(openAction)
        file.addAction(renderAction)
        file.addAction(exitAction)
        edit = menu.addMenu('Edit')
        edit.addAction(undoAction)
        edit.addAction(redoAction)
        edit.addSeparator()
        edit.addAction(cutAction)
        edit.addAction(delAction)
        edit.addAction(speedAction)
        edit.addAction(imageAction)

        toolBar = self.addToolBar('Cut')
        toolBar.addAction(undoAction)
        toolBar.addAction(redoAction)
        toolBar.addSeparator()
        toolBar.addAction(cutAction)
        toolBar.addAction(delAction)
        toolBar.addAction(speedAction)
        toolBar.addAction(imageAction)

    def showOpenDialog(self):
        fName, filter = QFileDialog.getOpenFileName(self, 'Open file', QDir.current().path())
        if fName != '':
            self.file = fName
            self.workspace.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(fName)))
            self.workspace.playButton.setEnabled(True)
            self.workspace.mediaPlayer.play()

    def cut(self):
        self.workspace.timelineLogic.cut(self.workspace.positionVideo)

    def delete(self):
        self.workspace.timelineLogic.delete()

    def changeSpeed(self):
        values = [0.5, 0.75, 0, 1.25, 1.5, 1.75, 2]
        self.s = SpeedDialog(values.index(self.workspace.timelineLogic.speed))
        self.s.btn.rejected.connect(self.s.close)
        self.s.btn.accepted.connect(self.putSpeed)
        self.s.show()

    def putSpeed(self):
        before = self.workspace.timelineLogic.speed
        speed = self.s.box.currentText()
        if speed == 'Normal':
            after = 0
        else:
            after = float(speed)
        command = SpeedAction(before, after, self.workspace.timelineLogic)
        self.workspace.timelineLogic.undoStack.push(command)
        self.s.close()

    def addImage(self):
        self.image, filter = QFileDialog.getOpenFileName(self, 'Open image', QDir.current().path(), "Image Files (*.png *.jpg)")
        if self.image != '':
            self.i = ImageDialog(self.image)
            self.i.btn.rejected.connect(self.i.close)
            self.i.btn.accepted.connect(self.putImagePos)
            self.i.show()

    def putImagePos(self):
        before = self.workspace.timelineLogic.imageToAdd
        self.i.close()
        id = self.i.group.checkedId()
        btn = self.i.group.button(id)
        posText = btn.text()
        command = ImageAction(before, (self.image, posText), self.workspace.timelineLogic)
        self.workspace.timelineLogic.undoStack.push(command)

    def render(self):
        fullName = QFileDialog.getSaveFileName(self, 'Render', QDir().currentPath(), 'Video(.mp4)')[0]
        while os.path.exists(fullName + '.mp4'):
            message = QMessageBox.warning(self, 'Warning', 'The file with the same name already exists.\nChoose another name.')
            fullName = QFileDialog.getSaveFileName(self, 'Render', QDir().currentPath(), 'Video(.mp4)')[0]
        if fullName != '':
            self.workspace.timelineLogic.render(self.file, fullName)
            message = QMessageBox.information(self, 'Rendering', '<font size=5> Ready! </font>')

    def undo(self):
        self.workspace.timelineLogic.undoStack.undo()

    def redo(self):
        self.workspace.timelineLogic.undoStack.redo()


class SpeedDialog(QDialog):
    def __init__(self, index):
        super().__init__()
        self.setWindowTitle('Speed')
        self.setWindowIcon(QIcon('icons/speed.png'))
        self.setFixedSize(210, 100)

        self.box = QComboBox(self)
        self.box.setStyleSheet('font-size:9pt;')
        self.box.addItems(['0.5', '0.75', 'Normal', '1.25', '1.5', '1.75', '2'])
        self.box.setCurrentIndex(index)

        text = QLabel('Change speed')
        text.setStyleSheet('font-size:9pt')

        self.btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        layout = QHBoxLayout()
        layout.addWidget(text)
        layout.addStretch(1)
        layout.addWidget(self.box)

        vbox = QVBoxLayout()
        vbox.addLayout(layout)
        vbox.addStretch(1)
        vbox.addWidget(self.btn)
        self.setLayout(vbox)


class ImageDialog(QDialog):
    def __init__(self, image):
        super().__init__()
        self.setWindowTitle('Image')
        self.setWindowIcon(QIcon('icons/image.png'))
        self.setMinimumSize(320, 220)

        info = QLabel(f'Image:{image}', self)
        text = QLabel('Select the image position on the video', self)
        self.btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        leftTop = QRadioButton('Left-Top', self)
        top = QRadioButton('Top', self)
        rightTop = QRadioButton('Right-Top', self)
        left = QRadioButton('Left', self)
        center = QRadioButton('Center', self)
        right = QRadioButton('Right', self)
        leftBottom = QRadioButton('Left-Bottom', self)
        bottom = QRadioButton('Bottom', self)
        rightBottom = QRadioButton('Right-Bottom', self)

        self.group = QButtonGroup()
        self.group.addButton(leftTop)
        self.group.addButton(top)
        self.group.addButton(rightTop)
        self.group.addButton(left)
        self.group.addButton(center)
        self.group.addButton(right)
        self.group.addButton(leftBottom)
        self.group.addButton(bottom)
        self.group.addButton(rightBottom)

        vbox1 = QVBoxLayout()
        vbox1.addWidget(leftTop)
        vbox1.addWidget(left)
        vbox1.addWidget(leftBottom)

        vbox2 = QVBoxLayout()
        vbox2.addWidget(top)
        vbox2.addWidget(center)
        vbox2.addWidget(bottom)

        vbox3 = QVBoxLayout()
        vbox3.addWidget(rightTop)
        vbox3.addWidget(right)
        vbox3.addWidget(rightBottom)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox1)
        hbox.addLayout(vbox2)
        hbox.addLayout(vbox3)

        vbox = QVBoxLayout()
        vbox.addWidget(info)
        vbox.addStretch(2)
        vbox.addWidget(text)
        vbox.addStretch(1)
        vbox.addLayout(hbox)
        vbox.addStretch(2)
        vbox.addWidget(self.btn)

        self.setLayout(vbox)


class SpeedAction(QUndoCommand):
    def __init__(self, before, after, logic):
        super().__init__()
        self.before = before
        self.after = after
        self.logic = logic

    def undo(self):
        self.logic.speed = self.before

    def redo(self):
        self.logic.speed = self.after
        self.setText(f'Change speed {self.after}x')


class ImageAction(QUndoCommand):
    def __init__(self, before, after, logic):
        super().__init__()
        self.before = before
        self.after = after
        self.logic = logic

    def undo(self):
        self.logic.imageToAdd = self.before

    def redo(self):
        self.logic.imageToAdd = self.after
        self.setText(f'Add image {os.path.split(self.after[0])[1]} at {self.after[1]}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Window()

    sys.exit(app.exec())
