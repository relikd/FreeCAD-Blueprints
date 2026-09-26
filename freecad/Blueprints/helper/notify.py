'''
Code related to (visually) notifying the user.

All `FreeCAD` and `Qt` imports are "on-first-use".
This way, importing `Notify` wont import a whole feature suite.
Most of these function calls will propbably only run in error state.
'''


class Notify:
    @staticmethod
    def err(title: str, msg: str) -> None:
        ''' Show error dialog with simple "Ok" button. '''
        from .qt import QtWidgets  # noqa: PLC0415
        QtWidgets.QMessageBox.critical(None, title, msg)

    @staticmethod
    def warn(title: str, msg: str) -> None:
        ''' Show warning dialog with simple "Ok" button. '''
        from .qt import QtWidgets  # noqa: PLC0415
        QtWidgets.QMessageBox.warning(None, title, msg)

    @staticmethod
    def ask(title: str, msg: str) -> bool:
        ''' Ask Yes/No question. Returns `True` if user replied with "Yes". '''
        from .qt import QtWidgets  # noqa: PLC0415
        ans = QtWidgets.QMessageBox.question(None, title, msg)
        return ans == QtWidgets.QMessageBox.StandardButton.Yes

    @staticmethod
    def status(msg: str, *, timeout: int = 5) -> None:
        ''' Show message in status bar. '''
        import FreeCADGui  # noqa: PLC0415
        FreeCADGui.getMainWindow().statusBar().showMessage(msg, timeout * 1000)

    class Log:
        @staticmethod
        def err(msg: str) -> None:
            ''' `Console.PrintError(msg + '\\n')` '''
            from FreeCAD import Console  # noqa: PLC0415
            Console.PrintError(msg + '\n')

        @staticmethod
        def warn(msg: str) -> None:
            ''' `Console.PrintWarning(msg + '\\n')` '''
            from FreeCAD import Console  # noqa: PLC0415
            Console.PrintWarning(msg + '\n')
