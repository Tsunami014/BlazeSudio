from BlazeSudio.graphics.miscOps import _ImageBase
from .base import WrapJoints, FindBounds
from ._core import draw_quad, c_direction, c_rotate, ray_polygon_closest_hit, closest_point_on_segments

import math
import numpy as np


def WrapImage(img: _ImageBase,
       shape: list[tuple[int, int | None]],
       top: int | float = 1,
       bottom: int | float = 0,
       limit: bool = True,
       flip: bool = False,
       ):
    """
    Wrap an image!

    Args:
        img (Image, e.g. Op.Image or Op.Rend): The image to wrap
        shape: The shape. This must be a list of (x, forced angle) values, see below 'Shape'
        top (int|float, optional): The position of the top of the wrapped image. See below 'Positioning'. Defaults to 1
        bottom (int|float, optional): The position of the bottom of the wrapped image. See below 'Positioning'. Defaults to 0
        limit (bool, optional): Whether to limit the warp so it MUST be within the height of the image. Making this False may give some very warped results. Constrains the bottom of the image. Defaults to True
        flip (bool, optional): Whether to flip the image. Defaults to False

    Shape:
        - The shape is a list of x values and fixed angles, and must start from 0 and end at the image width.
        - Almost (if not) all forced angles should be None to avoid overconstraining.

    Positioning:
        - When the image is being wrapped, it wraps the width of the image.
        - The top and bottom parameters are the positions of the top and bottom of the image respectively.
        ```
        1 = the width (wrapped) plus a buffer of the image height
        0 = the image width (wrapped)
        -1 = the centroid (or centroid line(s)) of the polygon made by the wrapped image width
        ```
        - Top **must** be >= 0 and bottom **must** be <= 0 and >= -1.
    """
    if top < 0 or bottom > 0 or bottom < -1:
        raise ValueError(
            'Top must be >= 0 and bottom must be <= 0 and >= -1'
        )
    arr = img.arr
    height = arr.shape[0]

    joints, rad = WrapJoints(
        [(i[0], 0) for i in shape],
        [i[1] for i in shape],
        return_radius=True)

    large, small = FindBounds(rad, joints, height)

    segs = list(zip(joints[:-1], joints[1:]))
    n = len(segs)
    seg_angles = [c_direction(*a, *b) for a, b in segs]

    large_arr = np.asarray(large, dtype=np.float64)
    small_arr = np.asarray(small, dtype=np.float64) if small else None

    ray_len = (rad + height) * 2
    points = []
    for idx in range(n):
        joint_pt = segs[idx][0]
        prev_ang, this_ang = seg_angles[idx - 1], seg_angles[idx]
        avg = math.degrees(math.atan2(
            math.sin(this_ang) + math.sin(prev_ang),
            math.cos(this_ang) + math.cos(prev_ang),
        ))

        if top != 0:
            ray_a = c_rotate(*joint_pt, joint_pt[0], joint_pt[1] - ray_len, avg)
            ray_b = c_rotate(*joint_pt, joint_pt[0], joint_pt[1] + ray_len, avg)
            hit = ray_polygon_closest_hit(
                ray_a[0], ray_a[1], ray_b[0], ray_b[1],
                large_arr, joint_pt[0], joint_pt[1],
            )
            outerp = hit if hit is not None else joint_pt
            if top != 1:
                outerp = (
                    (joint_pt[0] - outerp[0]) * top + outerp[0],
                    (joint_pt[1] - outerp[1]) * top + outerp[1],
                )
        else:
            outerp = joint_pt

        if bottom != 0:
            innerp = None
            if small_arr is not None and len(small_arr):
                innerp = closest_point_on_segments(joint_pt[0], joint_pt[1], small_arr)
            if innerp is None:
                innerp = joint_pt
            if bottom != -1:
                innerp = (
                    (innerp[0] - joint_pt[0]) * abs(bottom) + joint_pt[0],
                    (innerp[1] - joint_pt[1]) * abs(bottom) + joint_pt[1],
                )
        else:
            innerp = joint_pt

        points.append((innerp, outerp))

    points.append(points[0])

    all_pts = list(large) + list(points[0]) + [p for pair in points for p in pair]
    minx = min(p[0] for p in all_pts)
    miny = min(p[1] for p in all_pts)

    def _shift(p):
        return (p[0] - minx, p[1] - miny)

    large = [_shift(p) for p in large]
    points = [(_shift(i), _shift(o)) for i, o in points]

    canvas_w = int(math.ceil(max(p[0] for pair in points for p in pair))) + 1
    canvas_h = int(math.ceil(max(p[1] for pair in points for p in pair))) + 1
    canvas = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)

    for idx in range(n):
        x0 = shape[idx][0]
        x1 = shape[idx + 1][0]
        sub = np.ascontiguousarray(
            arr[::-1, x0:x1, :] if flip else arr[:, x0:x1, :],
            dtype=np.uint8,
        )

        innerp1, outerp1 = points[idx]
        innerp2, outerp2 = points[idx + 1]

        if limit:
            phi1 = c_direction(*outerp1, *innerp1)
            innerp1 = c_rotate(*outerp1, outerp1[0], outerp1[1] - height, math.degrees(phi1) + 90)
            phi2 = c_direction(*outerp2, *innerp2)
            innerp2 = c_rotate(*outerp2, outerp2[0], outerp2[1] - height, math.degrees(phi2) + 90)

        quad = (outerp1, outerp2, innerp2, innerp1)
        draw_quad(canvas, quad, sub)

    return canvas
