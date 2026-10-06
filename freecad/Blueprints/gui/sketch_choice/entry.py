from dataclasses import dataclass

from ...helper.properties import Props
from ..pixmap_cache import PixmapFactory
from ..thumbnail import sketch_thumbnail

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Sketcher import SketchObject as Sketch


@dataclass
class DataItem:
    index: int
    title: str
    desc: str
    tooltip: str
    thumbnail: PixmapFactory

    def __init__(self, args: tuple[int, 'Sketch']) -> None:
        self.index, sk = args
        self.title = sk.Label
        self.desc = Props.text(sk, 'desc')
        self.tooltip = Props.tooltip(sk, 'desc')
        self.thumbnail = lambda: sketch_thumbnail(sk)
