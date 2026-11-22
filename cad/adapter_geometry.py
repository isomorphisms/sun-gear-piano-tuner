"""Pure geometry and constraints for interchangeable piano-tuner sockets.

No FreeCAD dependency: used by both the native FreeCAD model and an independent
OpenCascade preview builder. Dimensions in millimeters. #2 fit is UNVERIFIED.
"""
from dataclasses import dataclass, replace
import math

STYLES = ('square', 'star')


@dataclass(frozen=True)
class AdapterSpec:
    box_depth: float = 101.6
    exposed_pin_length: float = 12.7
    target_engagement: float = 10.0
    barrel_diameter: float = 15.0
    barrel_length: float = 20.0
    pilot_diameter: float = 8.0
    pilot_length: float = 10.0
    mouth_across_flats: float = 7.05  # fit-study guess, NOT #2 spec
    cavity_depth: float = 11.5
    wall_draft_degrees: float = 4.0

    @property
    def seated_bottom(self):
        return self.exposed_pin_length - self.target_engagement

    @property
    def seated_top(self):
        return self.seated_bottom + self.barrel_length + self.pilot_length

    @property
    def remaining_axial_depth(self):
        return self.box_depth - self.seated_top

    @property
    def roof_across_flats(self):
        return self.mouth_across_flats - 2 * self.cavity_depth * math.tan(math.radians(self.wall_draft_degrees))

    def validate(self):
        values = tuple(getattr(self, x) for x in self.__dataclass_fields__)
        if not all(math.isfinite(x) for x in values):
            raise ValueError('Non-finite dimension')
        if self.box_depth <= 0 or self.exposed_pin_length <= 0:
            raise ValueError('Envelope and exposed pin length must be positive')
        if self.target_engagement <= 0 or self.target_engagement > self.exposed_pin_length:
            raise ValueError('Unachievable target engagement')
        if self.barrel_length <= 0 or self.pilot_length <= 0 or self.barrel_diameter <= 0:
            raise ValueError('Barrel and pilot dimensions must be positive')
        if self.pilot_diameter <= 0 or self.pilot_diameter > self.barrel_diameter:
            raise ValueError('Pilot cannot exceed barrel diameter')
        if self.cavity_depth <= self.target_engagement or self.cavity_depth >= self.barrel_length:
            raise ValueError('Blind cavity needs roof clearance and sound barrel roof')
        if not 0 < self.wall_draft_degrees < 20:
            raise ValueError('Unexpected socket wall draft')
        if self.roof_across_flats <= 0:
            raise ValueError('Taper closes before cavity roof')
        # Square corners and star outer corners both reach mouth_AF / sqrt(2)
        if self.barrel_diameter / 2 - self.mouth_across_flats / math.sqrt(2) < 1.5:
            raise ValueError('Insufficient radial wall at outer socket corners')
        if self.remaining_axial_depth < 0:
            raise ValueError('Model exceeds axial box depth')
        return self


def outline_points(style, across_flats):
    if style not in STYLES:
        raise ValueError('Unknown socket style: ' + repr(style))
    if not math.isfinite(across_flats) or across_flats <= 0:
        raise ValueError('Across-flats must be positive and finite')
    half = across_flats / 2
    if style == 'square':
        return [(-half, -half), (half, -half), (half, half), (-half, half)]
    # Union boundary of two squares: one at 0deg, one rotated by 45deg.
    # Alternating 8 radial peaks and 8 reentrant vertices.
    outer_radius = math.sqrt(2) * half
    inner_radius = math.sqrt(1 + (math.sqrt(2)-1)**2) * half
    return [
        ((outer_radius if i % 2 == 0 else inner_radius) * math.cos(math.radians(i * 22.5)),
         (outer_radius if i % 2 == 0 else inner_radius) * math.sin(math.radians(i * 22.5)))
        for i in range(16)
    ]


def polygon_area(points):
    return 0.5 * abs(sum(
        points[i][0]*points[(i+1) % len(points)][1]
        - points[(i+1) % len(points)][0]*points[i][1]
        for i in range(len(points))
    ))


DEFAULT = AdapterSpec().validate()
