'''
Read back user-provided form fields and replace existing expressions.
'''
import re

from .widgets import widget_to_value

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch
    from .form_fields import UserExprField


_rx = re.compile(r'[\w_.<>]+')


def detect_vars(expr: str) -> set[str]:
    ''' Detect external expression references. '''
    # excluding "name()" (command calls)
    expr += ' '  # make sure there is an end char for `!= '('`
    return {x.group() for x in _rx.finditer(expr) if expr[x.end()] != '('}


class Val(NamedTuple):
    value: str
    is_expr: bool


class ExprReplacer(dict[str, Val]):
    def __init__(self, fields: list['UserExprField'], dst: 'Sketch') -> None:
        '''Read back user provided values (either expression or raw value).'''
        if fields:
            engine = dict(dst.ExpressionEngine)
            for x in fields:
                if exp := engine.get(x.bind_key):
                    self[x.key] = Val(exp, True)
                elif val := widget_to_value(x.field):
                    self[x.key] = Val(val, False)

    def apply(self, expr: str) -> tuple[bool, str]:
        '''
        Find var-ref occurrences and replace with user-provided value.
        Returns `(True, _)` if the source expression is just a single variable
        AND the user-provided expression is a plain value.
        '''
        if not self:
            return False, expr
        if fullmatch := self.get(expr):
            return not fullmatch.is_expr, fullmatch.value
        return False, _rx.sub(lambda x, with_end=expr + ' ':
            repl.value if (repl := self.get(x.group())) is not None
            and with_end[x.end()] != '(' else x.group(),
            expr)
