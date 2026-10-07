from ...helper.settings import Settings
from ..qt import QtWidgets, QuickGui, SyncedCheckbox
from .entry import DataItem
from .list_view import ListView


class Window(QtWidgets.QDialog):
    def __init__(self, choices: list[DataItem]) -> None:
        super().__init__()

        self.setWindowTitle('Select item')
        self.resize(*Settings.getWinSize('SketchChoice', (650, 450)))

        # Search
        search_bar = QuickGui.search_bar(self)
        chk = SyncedCheckbox('incl. desc', pref='searchSketchDescription')

        # List
        list_view = ListView(choices)
        self.list_view = list_view

        # Buttons
        buttons, self.accept_button = QuickGui.buttons(self, abort=True)

        search = QtWidgets.QHBoxLayout()
        search.addWidget(search_bar)
        search.addWidget(chk)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(search)
        layout.addWidget(list_view)
        layout.addWidget(buttons)

        # interconnections
        search_bar.textChanged.connect(list_view.filter.setQuery)
        search_bar.on_up_down.connect(self.on_up_down)
        chk.on_change.connect(lambda x: list_view.filter.setOptions(desc=x))
        list_view.doubleClicked.connect(self.accept)
        list_view.validated.connect(self.accept_button.setEnabled)
        self.finished.connect(self.save_settings)

        # initial state
        list_view.filter.setOptions(desc=chk.isChecked())

    def save_settings(self, _: int) -> None:
        ''' Persist window size in settings. '''
        Settings.setWinSize('SketchChoice', self)

    def on_up_down(self, up: bool) -> None:  # noqa: FBT001
        ''' React to up-down arrow keys. '''
        idx = self.list_view.currentIndex()
        model = self.list_view.model()
        idx = model.index(idx.row() + (-1 if up else 1), idx.column())
        if idx.isValid():
            self.list_view.setCurrentIndex(idx)
            self.list_view.scrollTo(idx)

    def get_selected(self) -> 'DataItem|None':
        ''' Return selection (if any). '''
        return self.list_view.get_selected()
