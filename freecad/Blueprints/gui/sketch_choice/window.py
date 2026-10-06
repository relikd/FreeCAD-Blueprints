from ...helper.settings import Settings
from ..qt import QtWidgets, QuickGui
from .entry import DataItem
from .list_view import ListView


class Window(QtWidgets.QDialog):
    def __init__(self, choices: list[DataItem]) -> None:
        super().__init__()

        self.setWindowTitle('Select item')
        self.resize(*Settings.getWinSize('SketchChoice', (650, 450)))

        # List
        list_view = ListView(choices)
        list_view.doubleClicked.connect(self.accept)
        self.list_view = list_view

        # Search
        search = QtWidgets.QHBoxLayout()
        search.addWidget(QuickGui.search_bar(self, list_view.filter.setQuery))
        search.addWidget(QuickGui.checkbox(
            'incl. desc', pref='searchSketchDescription',
            # init triggers on_change -> user-preferences are auto-applied
            on_change=lambda x: list_view.filter.setOptions(desc=x)))

        # Buttons
        buttons, self.accept_button = QuickGui.buttons(self, abort=True)
        # auto-enable accept button on selection change
        list_view.validated.connect(self.accept_button.setEnabled)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(search)
        layout.addWidget(list_view)
        layout.addWidget(buttons)

        self.finished.connect(self.save_settings)

    def save_settings(self, _: int) -> None:
        ''' Persist window size in settings. '''
        Settings.setWinSize('SketchChoice', self)

    def get_selected(self) -> 'DataItem|None':
        ''' Return selection (if any). '''
        return self.list_view.get_selected()
