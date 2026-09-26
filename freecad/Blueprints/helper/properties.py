'''
Code related to Sketch obj properties (reading props as string, length, etc.)
'''
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from FreeCAD import PropertyContainer


class Props:
    @staticmethod
    def text(obj: 'PropertyContainer', pstr: str) -> str:
        ''' Calls `getPropertyByName()` '''
        try:
            return obj.getPropertyByName(pstr, 0)
        except AttributeError:
            return ''

    @staticmethod
    def tooltip(obj: 'PropertyContainer', pstr: str) -> str:
        ''' Calls `getDocumentationOfProperty()` '''
        try:
            return obj.getDocumentationOfProperty(pstr)
        except AttributeError:
            return ''
