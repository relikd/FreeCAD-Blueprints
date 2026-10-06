from ..pixmap_cache import PixmapCache
from ..qt import QtCore, QtGui, QtWidgets

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from .entry import DataItem
    QIndex = QtCore.QModelIndex | QtCore.QPersistentModelIndex
    QOptions = QtWidgets.QStyleOptionViewItem


THUMB_SIZE: Final = (64, 64)
MARGIN: Final = 4
GAP: Final = (8, 4)


class EntryView(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent: 'QtWidgets.QListView') -> None:
        super().__init__(parent)
        self.view = parent
        self.cache = PixmapCache()
        self.cache.ready.connect(self._thumbnail_ready)

        app_font = QtWidgets.QApplication.font()
        self.title_font = QtGui.QFont(app_font)
        self.title_font.setBold(True)
        self.desc_font = QtGui.QFont(app_font)
        self.desc_font.setItalic(True)

        self.title_height = QtGui.QFontMetrics(self.title_font).height()

    def _thumbnail_ready(self, _key: int) -> None:
        self.view.viewport().update()

    def sizeHint(self, option: 'QOptions', index: 'QIndex') -> 'QtCore.QSize':
        ''' Calculate dynamic row height. '''
        item: DataItem = index.data(QtCore.Qt.ItemDataRole.UserRole)
        w = option.rect.width()
        text_width = w - 2 * MARGIN - THUMB_SIZE[0] - GAP[0]
        text_height = (
            self.title_height
            + GAP[1]
            + QtGui.QFontMetrics(self.desc_font).boundingRect(
                QtCore.QRect(0, 0, max(0, text_width), 0),
                QtCore.Qt.TextFlag.TextWordWrap,
                item.desc,
            ).height()
        )
        return QtCore.QSize(w, max(THUMB_SIZE[1], text_height) + 2 * MARGIN)

    def paint(
        self, painter: 'QtGui.QPainter', option: 'QOptions', index: 'QIndex',
    ) -> None:
        ''' Draw row. '''
        item: DataItem = index.data(QtCore.Qt.ItemDataRole.UserRole)

        # allow selection, focus, hover, etc.
        # style_option = QtWidgets.QStyleOptionViewItem(option)
        # style_option.text = ''
        # style_option.icon = QtGui.QIcon()
        QtWidgets.QApplication.style().drawControl(
            QtWidgets.QStyle.ControlElement.CE_ItemViewItem,
            option, painter, self.view)

        rect = option.rect.adjusted(MARGIN, MARGIN, -MARGIN, -MARGIN)
        x, y, w, h = rect.left(), rect.top(), rect.right(), rect.bottom()

        # thumbnail
        if pixmap := self.cache.get(item.index):
            painter.drawPixmap(x, y, pixmap)
        else:
            self.cache.add(item.index, item.thumbnail)
            painter.fillRect(
                QtCore.QRect(x, y, *THUMB_SIZE), QtGui.QColor(35, 35, 35))

        # title
        x += THUMB_SIZE[0] + GAP[0]
        painter.setFont(self.title_font)
        painter.drawText(
            QtCore.QRect(x, y, w - x, self.title_height),
            item.title)

        # desc
        y += self.title_height + GAP[1]
        painter.setFont(self.desc_font)
        painter.drawText(
            QtCore.QRect(x, y, w - x, h - y),
            QtCore.Qt.TextFlag.TextWordWrap,
            item.desc)
