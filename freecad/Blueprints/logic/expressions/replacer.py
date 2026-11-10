'''
Read back user-provided form fields and replace existing expressions.
'''
import re

from ..detector.expressions import rx_var_xpath
from .widgets import widget_to_value

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch
    from .form_fields import UserExprField


class Val(NamedTuple):
    value: str
    is_expr: bool


class ExprReplacer(dict[str, Val]):
    def __init__(
        self, fields: list['UserExprField'], dst: 'Sketch', *, resolve: bool,
    ):
        '''Read back user provided values (either expression or raw value).'''
        self.__resolve = resolve
        self.__lists: list[list[float]] = []
        if fields:
            engine = dict(dst.ExpressionEngine)
            for x in fields:
                if exp := engine.get(x.bind_key):
                    self[x.key] = Val(exp, True)
                    continue

                field, value = x.field_or_value
                if field and (val := widget_to_value(field)):
                    self[x.key] = Val(val, False)
                elif value:
                    # store raw list in attribute to be referenced later
                    # see `apply()` below.
                    self[x.key] = Val(f'__list.{len(self.__lists)}', False)
                    self.__lists.append(value)

    def apply(self, expr: str) -> tuple[bool, str]:
        '''
        Find var-ref occurrences and replace with user-provided value.
        Returns `(True, _)` if the source expression is just a single variable
        AND the user-provided expression is a plain value.
        '''
        # TODO: recursively ignore resolve for named-equals
        # no replacements, return immediately with expression unchanged
        if not self:
            return self.__resolve, expr

        # whole expression matches a single variable, auto-resolve it
        if fullmatch := self.get(expr):
            return not fullmatch.is_expr, fullmatch.value

        # first, replace all expression variables
        expr = rx_var_xpath.sub(lambda x, with_end=expr + ' ':
            repl.value if (repl := self.get(x.group())) is not None
            and with_end[x.end()] != '(' else x.group(),
            expr)

        # then replace all list-variables with their respective value
        # generated in `ExprReplacer` (regex should match)
        auto_resolve = self.__resolve or bool(_rx_lists.fullmatch(expr))
        return auto_resolve, _rx_lists.sub(lambda x:
            str(self.__lists[int(x.group(1))][int(x.group(2))]), expr)


# matches "__list.42 [ 0 ]" (list-index, element-index)
_rx_lists = re.compile(r'__list\.([0-9]+)\s*\[\s*([0-9]+)\s*\]')
