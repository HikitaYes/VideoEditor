from PyQt5.QtWidgets import QGraphicsScene, QGraphicsItem, QGraphicsRectItem, QDesktopWidget, QUndoStack, QUndoCommand
from PyQt5.QtGui import QBrush, QPen, QColor, QCursor, QTransform
from PyQt5.QtCore import Qt, QRectF, QPointF
import os, tempfile

class TimelineBlock(QGraphicsRectItem):
    def __init__(self, rect, start, duration, scene, blocks, durationVideo, stack):
        super().__init__(rect)
        self.start = start
        self.duration = duration
        self.durationVideo = durationVideo
        self.scene = scene
        self.blocks = blocks
        self.stack = stack
        self.brush = QBrush(Qt.cyan)
        self.brush.setColor(QColor(0, 100, 255, 95))
        self.pen = QPen(self.brush, 0)
        self.mousePressCoord = QPointF(0, 0)
        self.setFlag(QGraphicsItem.ItemIsSelectable)

    def draw(self):
        self.setPen(self.pen)
        self.setBrush(self.brush)
        self.scene.addItem(self)

    def mouseMoveEvent(self, event):
        self.setSelected(False)
        x = event.scenePos().x() - self.mousePressCoord.x() + self.itemPressCoord.x()
        if x + self.rect().width() >= self.scene.width():
            x = self.scene.width() - self.rect().width()
        if x <= 0:
            x = 0

        index = self.blocks.index(self)
        if index < len(self.blocks) - 1 and x + self.rect().width() + 15 >= self.blocks[index + 1].scenePos().x():
            x = self.blocks[index + 1].scenePos().x() - self.rect().width() - 2
        if index > 0 and x - 15 <= self.blocks[index - 1].scenePos().x() + self.blocks[index - 1].rect().width():
            x = self.blocks[index - 1].scenePos().x() + self.blocks[index - 1].rect().width() + 2

        position = QPointF(x, self.pos().y())
        self.setPos(position)

    def mousePressEvent(self, event):
        self.mousePressCoord = event.scenePos()
        self.itemPressCoord = self.scenePos()
        self.setCursor(QCursor(Qt.ClosedHandCursor))
        self.setOpacity(0.8)
        if self.isSelected():
            self.setSelected(False)
        else:
            self.setSelected(True)

    def mouseReleaseEvent(self, event):
        self.setCursor(QCursor(Qt.ArrowCursor))
        self.setOpacity(1)
        if event.scenePos() != self.mousePressCoord:
            command = MoveAction(self.itemPressCoord, self.scenePos(), self)
            self.stack.push(command)


class TimelineLogic:
    def __init__(self, duration=0):
        screenSize = QDesktopWidget().availableGeometry()
        self.width = screenSize.width() - 30
        self.height = screenSize.height() // 8 - 10
        self.durationVideo = duration
        self.speed = 0
        self.imageToAdd = ('', '')

        self.scene = QGraphicsScene(0, 0, self.width, self.height)
        self.timeLineBlocks = []
        self.undoStack = QUndoStack()

        block = TimelineBlock(QRectF(0, 0, self.width, self.height), 0, duration, self.scene, self.timeLineBlocks, duration, self.undoStack)
        block.setPos(0, 0)
        self.timeLineBlocks.append(block)
        block.draw()

    def cut(self, position):
        x = position * self.width / self.durationVideo
        item = self.scene.itemAt(x, 10, QTransform())
        if not item or x == 0:
            return
        index = self.timeLineBlocks.index(item)

        command = CutAction(position, index, self)
        self.undoStack.push(command)

    def delete(self):
        blocksToDel = []
        for block in self.timeLineBlocks:
            if block.isSelected():
                blocksToDel.append(block)

        indexes = [self.timeLineBlocks.index(block) for block in blocksToDel]

        command = DeleteAction(blocksToDel, indexes, self)
        self.undoStack.push(command)

    def render(self, file, output):
        with tempfile.TemporaryDirectory() as temp:
            i = 0
            for block in self.timeLineBlocks:
                cmd = self.getCutCmd(block.start / 1000, block.duration / 1000, file, i, temp)
                os.system(cmd)
                i += 1
            with open(os.path.join(temp, 'files.txt'), 'w') as files:
                files.writelines('\n'.join([f"file '{os.path.join(temp, str(file))}.mp4'" for file in range(i)]))

            if self.speed != 0:
                cuted = os.path.join(temp, str(i))
                os.system(f'ffmpeg -f concat -safe 0 -i {files.name} -c copy {cuted}.mp4')
                if self.imageToAdd != ('', ''):
                    out = os.path.join(temp, str(i + 1))
                else:
                    out = output
                os.system(f'ffmpeg -i {cuted}.mp4 -filter_complex "[0:v]setpts={1 / self.speed}*PTS[v];[0:a]atempo={self.speed}[a]" -map "[v]" -map "[a]" {out}.mp4')
                i += 1

            if self.imageToAdd != ('', ''):
                image, textPos = self.imageToAdd
                textToCmd = {
                    'Left-Top': self.getCmdPos('0', '0'),
                    'Top': self.getCmdPos('w/2', '0'),
                    'Right-Top': self.getCmdPos('w', '0'),
                    'Left': self.getCmdPos('0', 'h/2'),
                    'Center': self.getCmdPos('w/2', 'h/2'),
                    'Right': self.getCmdPos('w', 'h/2'),
                    'Left-Bottom': self.getCmdPos('0', 'h'),
                    'Bottom': self.getCmdPos('w/2', 'h'),
                    'Right-Bottom': self.getCmdPos('w', 'h')
                }
                pos = textToCmd[textPos]

                speeded = os.path.join(temp, str(i))
                if self.speed == 0:
                    os.system(f'ffmpeg -f concat -safe 0 -i {files.name} -c copy {speeded}.mp4')
                os.system(f'ffmpeg -i {speeded}.mp4 -i {image} -filter_complex "[0:v][1:v]overlay={pos}" {output}.mp4')

            if self.speed == 0 and self.imageToAdd == ('', ''):
                os.system(f'ffmpeg -f concat -safe 0 -i {files.name} -c copy {output}.mp4')

    def getCutCmd(self, start, duration, file, result, dir):
        return f'ffmpeg -ss {start} -i {file} -t {duration} {os.path.join(dir, str(result))}.mp4'

    def getCmdPos(self, width, height):
        x = '0'
        y = '0'
        if width != '0':
            x = f'main_{width}-overlay_{width}'
        if height != '0':
            y = f'main_{height}-overlay_{height}'
        return x + ':' + y


class CutAction(QUndoCommand):
    def __init__(self, position, index, logic):
        super().__init__('Cut')
        self.position = position
        self.index = index
        self.logic = logic

    def undo(self):
        blockLeft = self.logic.timeLineBlocks[self.index]
        blockRight = self.logic.timeLineBlocks[self.index + 1]
        rect = QRectF(0, 0, blockLeft.rect().width() + blockRight.rect().width() + 2, blockLeft.rect().height())

        block = TimelineBlock(rect, blockLeft.start, blockLeft.duration + blockRight.duration, self.logic.scene, self.logic.timeLineBlocks, self.logic.durationVideo, self.logic.undoStack)
        block.setPos(blockLeft.scenePos())

        self.logic.timeLineBlocks.pop(self.index)
        self.logic.timeLineBlocks.pop(self.index)
        self.logic.timeLineBlocks.insert(self.index, block)

        self.logic.scene.removeItem(blockLeft)
        self.logic.scene.removeItem(blockRight)
        block.draw()

    def redo(self):
        x = self.position * self.logic.width / self.logic.durationVideo
        item = self.logic.timeLineBlocks[self.index]

        self.logic.timeLineBlocks.pop(self.index)

        rectLeft = QRectF(0, 0, x - item.scenePos().x() - 1, self.logic.height)
        rectRight = QRectF(0, 0, item.rect().width() - rectLeft.width() - 2, self.logic.height)
        blockLeft = TimelineBlock(rectLeft, item.start, self.position - item.start, self.logic.scene, self.logic.timeLineBlocks, self.logic.durationVideo, self.logic.undoStack)
        blockLeft.setPos(item.scenePos().x(), 0)
        blockRight = TimelineBlock(rectRight, self.position + 1, item.start + item.duration - self.position, self.logic.scene, self.logic.timeLineBlocks, self.logic.durationVideo, self.logic.undoStack)
        blockRight.setPos(x + 1, 0)

        self.logic.timeLineBlocks.insert(self.index, blockLeft)
        self.logic.timeLineBlocks.insert(self.index + 1, blockRight)
        self.logic.scene.removeItem(item)
        blockLeft.draw()
        blockRight.draw()


class DeleteAction(QUndoCommand):
    def __init__(self, blocks, indexes, logic):
        super().__init__('Delete')
        self.blocks = blocks
        self.indexes = indexes
        self.logic = logic

    def undo(self):
        for block in self.blocks:
            self.logic.timeLineBlocks.insert(self.indexes[self.blocks.index(block)], block)
            block.draw()

    def redo(self):
        blocksToDel = [self.logic.timeLineBlocks[index] for index in self.indexes]
        for block in blocksToDel:
            self.logic.timeLineBlocks.remove(block)
            self.logic.scene.removeItem(block)


class MoveAction(QUndoCommand):
    def __init__(self, before, after, block):
        super().__init__('Move')
        self.before = before
        self.after = after
        self.block = block

    def undo(self):
        self.block.setPos(self.before)

    def redo(self):
        self.block.setPos(self.after)
