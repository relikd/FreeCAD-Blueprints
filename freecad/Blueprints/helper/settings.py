'''
Code related to accessing and persisting user settings.
'''
from pathlib import Path
from typing import TYPE_CHECKING

from .utils import default_database_dir

if TYPE_CHECKING:
    from FreeCAD import ParameterGrp
    from ..gui.qt import QtWidgets


class Settings:
    @staticmethod
    def databaseDir() -> Path:
        ''' User configured `UserCollectionDir` or fallback to default dir. '''
        if custom := Settings.getString('UserCollectionDir'):
            return Path(custom)
        return default_database_dir()

    #################################################

    @staticmethod
    def getBool(key: str) -> bool:
        return _cfg().GetBool(key, False)

    @staticmethod
    def setBool(key: str, flag: bool) -> None:  # noqa: FBT001
        return _cfg().SetBool(key, flag)

    @staticmethod
    def getString(key: str) -> str:
        return _cfg().GetString(key, '')

    @staticmethod
    def setString(key: str, value: str) -> None:
        return _cfg().SetString(key, value)

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

    class View:
        @staticmethod
        def background_color() -> tuple[int, int, int, int]:
            val = _cfg('View').GetUnsigned('BackgroundColor')
            r = (val >> 24) & 0xff
            g = (val >> 16) & 0xff
            b = (val >> 8) & 0xff
            a = val & 0xff
            return r, g, b, a


#################################################
# Helper
#################################################

def _cfg(name: str = 'Mod/Blueprints') -> 'ParameterGrp':
    import FreeCAD  # noqa: PLC0415
    return FreeCAD.ParamGet(  # type: ignore[return-value]
        'User parameter:BaseApp/Preferences/' + name)
