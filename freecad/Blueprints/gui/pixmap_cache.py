'''
Code responsible for generating thumbnails in a worker thread.
'''
from typing import Callable

from .qt import QtCore, QtGui

PixmapFactory = Callable[[], QtGui.QPixmap]
PixmapSource = QtGui.QPixmap | PixmapFactory


class _Signals(QtCore.QObject):
    ready: QtCore.Signal = QtCore.Signal(int, QtGui.QPixmap)


class _PixmapTask(QtCore.QRunnable):
    def __init__(self, key: int, factory: PixmapFactory):
        super().__init__()
        self.key = key
        self.factory = factory
        self.signals = _Signals()

    def run(self) -> None:
        pixmap = self.factory()
        self.signals.ready.emit(self.key, pixmap)


class PixmapCache(QtCore.QObject):
    ''' Lazy load / generate sketch thumbnails in a worker thread. '''
    ready: QtCore.Signal = QtCore.Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.values: dict[int, QtGui.QPixmap] = {}
        self.loading: set[int] = set()
        self.pool = QtCore.QThreadPool.globalInstance()

    def get(self, key: int) -> 'QtGui.QPixmap|None':
        return self.values.get(key)

    def add(self, key: int, generator: PixmapFactory) -> None:
        if key not in self.loading:
            self.loading.add(key)
            task = _PixmapTask(key, generator)
            task.signals.ready.connect(self._finished)
            self.pool.start(task)

    def _finished(self, key: int, pixmap: QtGui.QPixmap) -> None:
        self.values[key] = pixmap
        self.loading.discard(key)
        self.ready.emit(key)
