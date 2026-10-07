from ...helper.utils import get_user_collection
from ..qt import QtWidgets
from .window import FileBrowser
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def open_blueprint_browser() -> 'Path|None':
    root = get_user_collection()

    dialog = FileBrowser(root)

    if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        if path := dialog.get_selected():
            dialog.deleteLater()
            return path
    dialog.deleteLater()
    return None
