'''
A wild bunch of helper functions which are too small to place somewhere else.

All `FreeCAD` and `Qt` imports are "on-first-use".
This way, importing `utils` does not import a whole feature suite.
'''
import sys
import shutil
from os import environ
from pathlib import Path
# Audited: subprocess calls use fixed argument lists and no shell (B404)
from subprocess import run  # nosec B404  # noqa: S404

RES_ROOT = Path(__file__).parent.parent / 'resources'


def _data_dir() -> Path:
    ''' Return user-wide app-data dir. '''
    if sys.platform == 'win32':
        if var := environ.get('LOCALAPPDATA'):
            return Path(var)
        return Path.home() / 'AppData' / 'Local'

    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support'

    if var := environ.get('XDG_DATA_HOME'):
        return Path(var)
    return Path.home() / '.local' / 'share'


def _install_examples(toDir: Path) -> None:
    ''' Copy addon-provided examples into user-defined database dir. '''
    shutil.copytree(
        RES_ROOT / 'blueprint-examples',
        toDir / 'Examples',
        dirs_exist_ok=True)


def get_user_collection() -> Path:
    ''' If uninitialized, copy bundled examples. Return path to collection. '''
    # TODO: make path configurable in preferences
    root = _data_dir() / 'FreeCAD-Blueprints' / 'Sketcher'
    if not root.exists():
        _install_examples(root)
    return root


def open_in_file_manager(path: Path) -> None:
    ''' Open system file browser and select chosen file (or dir). '''
    path = path.resolve()  # will also replace with backslashes on win
    args: list[str | Path] = []

    if sys.platform == 'win32':
        cmddir = environ.get('SYSTEMROOT') or environ.get('WINDIR')
        args = [(Path(cmddir) / 'explorer.exe') if cmddir else 'explorer.exe']
        if path.is_dir():
            args.append('/select,')
        args.append(path)
    elif sys.platform == 'darwin':
        cmd = '/usr/bin/open'
        args = [cmd, path] if path.is_dir() else [cmd, '-R', path]
    else:
        if cmd := shutil.which('xdg-open'):
            args = [cmd, path.parent if path.is_dir() else path]

    if args:
        # Audited: fixed arguments, resolved cmds (B603)
        run(args, check=False)  # nosec B603  # noqa: S603
