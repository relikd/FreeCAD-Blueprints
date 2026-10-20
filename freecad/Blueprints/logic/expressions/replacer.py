'''
Read back user-provided form fields and replace existing expressions.
'''
import re
from dataclasses import dataclass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch
    from .form_fields import UserExprField


_rx = re.compile(r'[\w_.<>]+')


def detect_vars(expr: str) -> set[str]:
    ''' Detect external expression references. '''
    # excluding "name()" (command calls)
    expr += ' '  # make sure there is an end char for `!= '('`
    return {x.group() for x in _rx.finditer(expr) if expr[x.end()] != '('}


@dataclass
class ExprReplacer:
    expr_map: dict[str, str]

    def __init__(self, fields: list['UserExprField'], dst: 'Sketch') -> None:
        '''Read back user provided values (either expression or raw value).'''
        if fields:
            engine = dict(dst.ExpressionEngine)
            self.expr_map = {
                x.key: engine.get(x.bind_key) or x.value() for x in fields
            }
        else:
            self.expr_map = {}

    def apply(self, expr: str) -> str:
        ''' Find var-ref occurrences and replace with user-provided value. '''
        if not self.expr_map:
            return expr
        return _rx.sub(lambda x, with_end=expr + ' ':
            repl if (repl := self.expr_map.get(x.group())) is not None
            and with_end[x.end()] != '(' else x.group(),
            expr)
