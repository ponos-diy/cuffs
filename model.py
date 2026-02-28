import sys
import math
import dataclasses
from typing import Literal

from muscad import E, EE, T, TT, Cube, Volume, Cylinder, Part, Sphere, Circle, Square, Text, Polygon, Object, Union
from muscad_tools import screws

from util import InvalidParameterException


if sys.platform == 'emscripten':
    # direct import is not possible, since we need to download the files manually
    includes = {
        #"internal": "./internal.py",
        }
else:
    pass

class RoundedRect(Part):
    def init(self, w, h, r):
        for x_s in (-1, 1):
            for y_s in (-1, 1):
                self.add_child(Circle(d=2*r).align(center_x=x_s*(w/2-r), center_y=y_s*(h/2-r)))
        self.add_child(Square(w-2*r, h))
        self.add_child(Square(w, h-2*r))

def exception_default(l, exception_type, default=None):
    try:
        return l()
    except exception_type:
        return default

def property_if_available(obj, property_name: str):
    return exception_default(lambda: getattr(obj, property_name), TypeError)


def get_with_fallback(*args):
    for arg in args:
        if arg is not None:
            return arg
    return None


def derive_dimension_parameter(child, prop: str, override: float):
    return get_with_fallback(override, property_if_available(child, prop))



class OverriddenBounding(Object):
    def __init__(self, child, width=None, depth=None, height=None, left=None, right=None, front=None, back=None, top=None, bottom=None):
        self.child = child

        self._left = derive_dimension_parameter(child, "left", left)
        self._right = derive_dimension_parameter(child, "right", right)
        self._back = derive_dimension_parameter(child, "back", back)
        self._front = derive_dimension_parameter(child, "front", front)
        self._top = derive_dimension_parameter(child, "top", top)
        self._bottom = derive_dimension_parameter(child, "bottom", bottom)

        assert self._left is not None
        assert self._right is not None
        assert self._back is not None
        assert self._front is not None
        assert self._top is not None
        assert self._bottom is not None

    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right

    @property
    def back(self):
        return self._back

    @property
    def front(self):
        return self._front

    @property
    def top(self):
        return self._top

    @property
    def bottom(self):
        return self._bottom

    def render(self):
        return self.child.render()

@dataclasses.dataclass
class HingeInfo:
    style: Literal["outer", "inner"]
    bolt: screws.Metric
    nut: bool

def invert_hinge_info(i: HingeInfo):
    d = dataclasses.asdict(i)
    d["style"] = {
        "outer": "inner",
        "inner": "outer",
        }[d["style"]]
    return HingeInfo(**d)

class Cuff(Part):
    def corner(self, rect: RoundedRect, corner_r):
        size = (rect.depth+corner_r)
        return OverriddenBounding(rect.align(back=corner_r).z_rotate(90).rotational_extrude(90.0, segments=100).y_rotate(-90).x_rotate(90), back=0, front=size, bottom=-size, top=0)
    def round_end(self, rect: RoundedRect):
        obj = (rect.z_rotate(90) - Square(rect.depth+EE, rect.width+EE).align(left=0)).rotational_extrude(360.0, segments=100).y_rotate(-90).x_rotate(90)
        r = rect.depth/2
        return OverriddenBounding(obj, back=-r, front=r, top=r, bottom=-r)

    def hinge_cutout(self, info: HingeInfo, length, thickness, cut_width):
        c = Cube(length/3+cut_width, thickness*2, thickness+EE)
        if info.style == "outer":
            cs = c
        elif info.style == "inner":
            cs = c.align(right=length/2+E)
            cs += cs.x_mirror()
        else:
            raise NotImplementedError()
        bolt = screws.Screw(length=length+EE, metric=info.bolt, standard=screws.Standard.din7984, recessed=True)#.debug()
        if info.nut:
            bolt.add_nut()
        screw = bolt.y_rotate(90).translate(x=length/2)
        return cs + screw

    def bottom_fill(self, width, length, corner_r, chamfer_r, thickness):
        base = Volume(width=length, depth=width+2*thickness, height=corner_r+thickness).fillet_height(chamfer_r)
        c = Cylinder(d=corner_r*2+thickness, h=length+EE).y_rotate(90).align(center_z=base.top, front=width/2+thickness/2)
        bottom = Volume(width=length+EE, depth=width-2*corner_r, height=corner_r+thickness/2).align(top=base.top+E)
        base -= c + c.y_mirror() + bottom
        return base.align(bottom=-thickness)

    def bottom_fill_side(self, width, length, corner_r, chamfer_r, thickness):
        base = Volume(width=length, depth=(width+2*thickness)/2, height=corner_r+thickness, front=0).fillet_depth(chamfer_r, bottom=True)
        base = Volume(width=length, depth=(width+2*thickness)/2, height=corner_r+thickness, front=0).fillet_depth(chamfer_r, bottom=True)
        c = Cylinder(d=corner_r*2+thickness, h=length+EE).y_rotate(90).align(center_z=base.top, front=width/2+thickness/2)
        bottom = Volume(width=length+EE, depth=width-2*corner_r, height=corner_r+thickness/2).align(top=base.top+E)
        base -= c + c.y_mirror() + bottom
        return base.align(bottom=-thickness)


    def init(self, width, height, length, thickness, corner_r, chamfer_r, hinge_1: HingeInfo, hinge_2: HingeInfo, hinge_clearance: float=TT, height_offset=0.0, invert_height_offset: bool|None=None, adapter: bool=False, fill_bottom: Literal["none", "side", "both", "auto"]="auto"):
        invert_height_offset = (not adapter) if invert_height_offset is None else invert_height_offset

        if invert_height_offset:
            height_offset = -height_offset

        assert abs(height_offset) <= height/2-corner_r
        inner_width = width - 2*corner_r
        locking_center = height/2 + height_offset

        rect = RoundedRect(length, thickness, chamfer_r)

        bottom = rect.y_linear_extrude(distance=inner_width).align(top=0)
        corner = self.corner(rect, corner_r).align(back=bottom.front, bottom=bottom.bottom)
        side = rect.z_linear_extrude(distance=locking_center-corner_r).align(back=width/2, bottom=corner.top)

        end = self.round_end(rect).align(center_z=side.top, center_y=side.center_y)

        s = corner + side + end
        h1 = self.hinge_cutout(hinge_1, length, thickness, cut_width=hinge_clearance).translate(y=end.center_y, z=end.center_z)
        h2 = self.hinge_cutout(hinge_2, length, thickness, cut_width=hinge_clearance).translate(y=end.center_y, z=end.center_z)

        self.add_child(bottom)
        self.add_child(s)
        self.add_hole(h1)
        self.add_hole(h2.y_mirror())
        self.add_child(s.y_mirror())

        if adapter:
            self.add_hole(Adapter(screws.Metric.m5, thickness=thickness))

        if fill_bottom == "auto":
            fill_bottom = "both" if adapter else "none"
        if fill_bottom == "both":
            self.add_child(self.bottom_fill(width=width, length=length, corner_r=corner_r, chamfer_r=chamfer_r, thickness=thickness))
        if fill_bottom == "side":
            self.add_child(self.bottom_fill_side(width=width, length=length, corner_r=corner_r, chamfer_r=chamfer_r, thickness=thickness))

class Adapter(Part):
    def init(self, metric: screws.Metric, thickness, hole_distance=20.0):
        bolt = screws.Screw(length=thickness+EE, metric=metric, standard=screws.Standard.din912, recessed=True)
        bolts = Union()
        for x_s in (-1, 1):
            for y_s in (-1, 1):
                bolts += bolt.align(center_x=x_s*hole_distance/2, center_y=y_s*hole_distance/2)
        self.add_child(bolts)

class Magnet(Part):
    def init(self):
        magnet = Volume(width=80.0, depth=32.0, height=20.0, top=0.0)
        screw = screws.Screw(length=30.0, metric=screws.Metric.m4, standard=screws.Standard.din912, recessed=True).add_nut(over_length=200.0).align(center_x=35.0)
        cable = Cylinder(d=5.0, h=10.0).y_rotate(90).align(right=magnet.left, center_y=magnet.front-8.0, center_z=magnet.top-11.0)
        self.add_child(magnet)
        self.add_misc(screw + screw.x_mirror())
        self.add_misc(cable)

magnet_holder_width = 100.0

class MagnetHolder(Part):
    def init(self, full_height: float, length: float, chamfer_r: float):
        magnet = Magnet().align(top=full_height)
        assert full_height >= 35.0
        thickness = (length - magnet.depth)/2
        assert chamfer_r <= thickness
        root = Volume(width=magnet_holder_width, depth=length, height=full_height, bottom=0.0).fillet_height(chamfer_r).fillet_width(chamfer_r, top=True)
        root -= Volume(width=magnet.width+TT, depth=magnet.depth+TT, height=magnet.height+TT, top=root.top+E)
        root -= magnet
        cable_cutout = Cylinder(d=6.0, h=30.0).y_rotate(90).align(right=magnet.left, center_y=magnet.front-8.0, center_z=magnet.top-13.0)
        cable_cutout += Volume(bottom=cable_cutout.center_z, left=cable_cutout.left, right=cable_cutout.right, front=cable_cutout.front, back=cable_cutout.back, top=root.top+E)
        root -= cable_cutout

        foot_screw = screws.Screw(length=10.0+EE, metric=screws.Metric.m5, standard=screws.Standard.din912, over_length=200.0).translate(z=10.0).align(center_y=root.front-length/4, left=magnet.right+1.0)
        foot_screws = foot_screw + foot_screw.y_mirror()
        foot_screws = foot_screws + foot_screws.x_mirror()

        self.add_child(root)
        self.add_hole(foot_screws)


class AnchorPlate(Part):
    def init(self):
        root = Volume(width=75.0, depth=34.0, height=11.0)
        screw = screws.Screw(length=40.0, metric=screws.Metric.m8, standard=screws.Standard.din7991, recessed=True).add_nut(position=20.0, over_length=200.0)
        self.add_child(root)
        self.add_misc(screw)

class AnchorHolder(Part):
    def init(self, full_height: float, length: float, chamfer_r: float, side_connected: bool=False):
        plate = AnchorPlate().align(top=full_height)
        root = Volume(width=magnet_holder_width, depth=length, height=full_height-E, bottom=0.0).fillet_height(chamfer_r, right=True)
        if side_connected:
            root.fillet_width(chamfer_r, bottom=True)
        if not side_connected:
            root.fillet_height(chamfer_r, left=True)
            foot_screw = screws.Screw(length=10.0+EE, metric=screws.Metric.m5, standard=screws.Standard.din912, over_length=200.0).translate(z=10.0).align(center_y=root.front-length/4, right=root.right-2.0)
            foot_screws = foot_screw + foot_screw.y_mirror()
            foot_screws = foot_screws + foot_screws.x_mirror()
            self.add_hole(foot_screws)

        self.add_child(root)
        self.add_hole(plate)


class CuffBottomWithMagnet(Part):
    def init(self, **kwargs):
        self.add_child(Cuff(**kwargs))

class CuffTopWithAnchorPlate(Part):
    def init(self, **kwargs):
        cuff = Cuff(**kwargs, fill_bottom="side")
        holder = AnchorHolder(full_height=kwargs["height"]/2+kwargs["thickness"], **filter_dict(kwargs, ["length", "chamfer_r"]), side_connected=True).z_rotate(-90).align(front=cuff.back, bottom=cuff.bottom)
        self.add_child(cuff)
        self.add_child(holder)


def filter_dict(d: dict, keys):
    return {k: v for k, v in d.items() if k in keys}

def padding_holder(thickness, length, width, chamfer_r, padding_length, show_padding=False, **kwargs):
    material = 3.0
    profile_height = length/2 # TODO
    top_height = thickness + material + 10.0
    cuff = Volume(width=width+2*thickness+2.0, depth=length+TT, bottom=0-E, top=top_height+E)
    padding = Volume(width=cuff.width, depth=padding_length+E, bottom=-profile_height+material, back=cuff.front-E, top=top_height+E)
    root = Volume(width=cuff.width+2*material, back=cuff.back-material, front=padding.front+material, bottom=-profile_height, top=top_height).fillet_depth(chamfer_r, top=True).fillet_height(chamfer_r)
    profile_cutout = Volume(front=cuff.front, back=root.back-E, width=root.width+EE, top=0, bottom=root.bottom-E)
    back_cutout = Volume(width=width, back=root.back-E, front=cuff.back+E, top=root.top+E, bottom=root.bottom-E).reverse_fillet_top(chamfer_r)
    front_cutout = Volume(width=width, front=root.front+E, back=padding.front-E, top=root.top+E, bottom=padding.bottom+material).reverse_fillet_top(chamfer_r)
    result = (root - padding - cuff - profile_cutout - back_cutout - front_cutout).color("grey")
    if show_padding:
        result += padding.color("blue")
    return result

def generate(
        width: float,
        height: float,
        corner_radius: float,
        height_offset: float,
        fill_bottom: Literal["both", "none"],
        ) -> list[tuple[str, str]]:
    params = dict(
            thickness=15.0,
            length=40.0,
            chamfer_r=3,
            hinge_clearance=0.5,
            width=width,
            height=height,
            corner_r=corner_radius,
            height_offset=height_offset,
            )
    hinge = HingeInfo(style="outer", bolt=screws.Metric.m4, nut=True)
    hinge_inverted = invert_hinge_info(hinge)
    bottom = Cuff(**params, hinge_1=hinge, hinge_2=hinge, adapter=True, fill_bottom=fill_bottom)
    top = Cuff(**params, hinge_1=hinge_inverted, hinge_2=hinge_inverted)
    holder = padding_holder(**params, padding_length=100.0)
    _ = MagnetHolder(full_height=params["height"]/2+params["thickness"], **filter_dict(params, ["length", "chamfer_r"]))
    _ = AnchorHolder(full_height=params["height"]/2+params["thickness"], **filter_dict(params, ["length", "chamfer_r"]))
    _ = CuffTopWithAnchorPlate(**params, hinge_1=hinge_inverted, hinge_2=hinge_inverted)

    return [
            ("top", str(top)),
            ("bottom", str(bottom)),
            ("padding_holder", str(holder)),
            ]


