'''
Detect expressions on external objects (VarSet or Sketch property)
'''
from dataclasses import dataclass

from ...helper.utils import default_props, camel_case_name
from .replacer import detect_vars

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from FreeCAD import DocumentObject as DocObj
    from Sketcher import SketchObject as Sketch


@dataclass
class DetectedExpr:
    obj: 'DocObj'  # document object (either `Sketch` or `VarSet`)
    key: str  # string as used by the expression engine
    prop: str  # property name (removed "VarSet." and "." prefix)

    def __post_init__(self):
        # The naming wont work with nested variables.
        # But we don't have support for these anyway.
        self.display_name = camel_case_name(self.prop)
        self.type_id = self.obj.getTypeIdOfProperty(self.prop)


def detect_external(src: 'Sketch') -> list[DetectedExpr]:
    '''Detect if expression engine uses any external references like VarSet.'''
    # find actually used references
    used = detect_vars('|'.join(x for _, x in src.ExpressionEngine if x))

    # find potentially referencable props
    v_ignore, s_ignore = default_props('App::VarSet', 'Sketcher::SketchObject')
    rv = []

    # sketch properties ("name" and ".name")
    sk_props = set(src.PropertiesList) - s_ignore
    for prop in used.intersection(sk_props | {'.' + x for x in sk_props}):
        rv.append(DetectedExpr(src, prop, prop.removeprefix('.')))

    # VarSets ("Name." and "<<Label>>.")
    for varset in src.Document.findObjects('App::VarSet'):
        var_props = set(varset.PropertiesList) - v_ignore
        for prop in used.intersection({n for x in var_props for n in (
                f'{varset.Name}.{x}', f'<<{varset.Label}>>.{x}')}):
            rv.append(DetectedExpr(varset, prop, prop.split('.', 1)[1]))

    rv.sort(key=lambda x: x.display_name.casefold())
    return rv
