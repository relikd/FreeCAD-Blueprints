'''
A wild bunch of helper functions which are too small to place somewhere else.
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


def install_examples(toDir: Path) -> None:
    ''' Copy addon-provided examples into user-defined database dir. '''
    shutil.copytree(
        RES_ROOT / 'blueprint-examples',
        toDir / 'Examples',
        dirs_exist_ok=True)


def default_database_dir() -> Path:
    ''' Default database dir - if not overwritten by user. '''
    return _data_dir() / 'FreeCAD-Blueprints' / 'Sketcher'


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


def camel_case_name(string: str, sep: str = ' ') -> str:
    ''' Insert separator between lower case and upper case letters. '''
    rv = ''
    prev = True
    for c in string:
        cur = c.isupper()
        if cur and not prev:
            rv += sep
        prev = cur
        rv += c
    return rv


_DEFAULT_PROPS_CACHE: dict[str, set[str]] = {}


def default_props(*doc_types: str) -> list[set[str]]:
    '''Default properties for document-object (without user-modifications).'''
    if remaining := set(doc_types) - _DEFAULT_PROPS_CACHE.keys():
        import FreeCAD  # noqa: PLC0415
        doc = FreeCAD.newDocument(hidden=True, temp=True)
        rv = [set(doc.addObject(x).PropertiesList) for x in remaining]
        FreeCAD.closeDocument(doc.Name)
        for k, v in zip(remaining, rv):
            _DEFAULT_PROPS_CACHE[k] = v

    # cache results so we don't create new documents on each blueprint load
    return [_DEFAULT_PROPS_CACHE[x] for x in doc_types]
