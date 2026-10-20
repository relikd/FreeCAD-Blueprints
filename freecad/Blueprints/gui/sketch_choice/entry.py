from dataclasses import dataclass

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
        self.desc = str(sk.getPropertyByName('desc', 0))
        self.tooltip = sk.getDocumentationOfProperty('desc')
        self.thumbnail = lambda: sketch_thumbnail(sk)
