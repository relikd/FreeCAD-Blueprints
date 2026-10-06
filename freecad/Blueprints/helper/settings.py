'''
Code related to accessing and persisting user settings.
'''
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from FreeCAD import ParameterGrp
    from ..gui.qt import QtWidgets


def _cfg() -> 'ParameterGrp':
    import FreeCAD  # noqa: PLC0415
    return FreeCAD.ParamGet(  # type: ignore[return-value]
        'User parameter:BaseApp/Preferences/Mod/Blueprints',
    )


class Settings:
    @staticmethod
    def load() -> 'ParameterGrp':
        return _cfg()

    @staticmethod
    def getBool(key: str) -> bool:
        return _cfg().GetBool(key, False)

    @staticmethod
    def setBool(key: str, flag: bool) -> None:  # noqa: FBT001
        return _cfg().SetBool(key, flag)

    @staticmethod
    def getWinSize(name: str, fallback: tuple[int, int]) -> tuple[int, int]:
        ''' Min size: `(100, 100)` '''
        parts = _cfg().GetString('winSize_' + name, '').split('x')
        if len(parts) == 2:
            try:
                w, h = [max(int(x), 100) for x in parts]
                return w, h
            except ValueError:
                pass
        return fallback

    @staticmethod
    def setWinSize(name: str, win: 'QtWidgets.QDialog') -> None:
        _cfg().SetString('winSize_' + name, f'{win.width()}x{win.height()}')
