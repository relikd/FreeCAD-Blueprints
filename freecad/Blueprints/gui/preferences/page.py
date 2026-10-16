from ...helper.settings import Settings
from ..qt import QtWidgets, DirChooser


# technically a `Gui::Dialog::PreferencePage`, but that isn't exposed yet.
class PreferencesPage(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle('General')

        grp = QtWidgets.QGroupBox('Local Collection')
        form = QtWidgets.QFormLayout(grp)

        self.root_dir = DirChooser(btnReveal=True)
        form.addRow('Path', self.root_dir)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(grp)
        layout.addStretch()

    def saveSettings(self) -> None:
        Settings.setString('UserCollectionDir', self.root_dir.value)

    def loadSettings(self) -> None:
        self.root_dir.setValue(str(Settings.databaseDir()))

    # def changeEvent(self, event: QtCore.QEvent) -> None:
    #     pass
