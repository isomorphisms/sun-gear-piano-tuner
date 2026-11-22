"""Pure geometry for three *pitch-envelope* piano-tuner drive studies.

All dimensions in mm. This is NOT a manufactured gear tooth profile, loaded
bearing arrangement, verified torque path or a pin-fitting claim. The sketches
are designed to reject unbuildable pitch layouts before entering FreeCAD.
"""
from dataclasses import dataclass
import math
from cad.adapter_geometry import DEFAULT, AdapterSpec

MIN_UNSHIFTED_20_DEG_EXTERNAL_TEETH = 17
STUDIES = ('planetary4', 'planetary5', 'compound6')


@dataclass(frozen=True)
class DriveSpec:
    module: float = 0.8  # standard metric module, illustrative only
    face_width: float = 8.0
    axial_gap: float = 3.0
    support_plate: float = 3.0
    coupling_gap: float = 4.0
    casing_margin: float = 3.0
    top_input_stub: float = 4.0  # envelope allowance; no torque-bearing coupling model

    def validate(self):
        for value in vars(self).values():
            if not math.isfinite(value) or value <= 0:
                raise ValueError('Drive dimensions must be finite and positive')
        if self.face_width < 3:
            raise ValueError('Insufficient face-width placeholder')
        return self


@dataclass(frozen=True)
class Disk:
    name: str
    teeth: int
    x: float
    y: float
    z: float
    pitch_radius: float
    face_width: float
    group: str

    @property
    def addendum_radius(self):
        raise AttributeError('Gear-tip geometry not modeled: use pitch_radius or specification module')


def _external_disk(name, teeth, x, y, z, spec, group):
    if teeth < MIN_UNSHIFTED_20_DEG_EXTERNAL_TEETH:
        raise ValueError('External gear requires profile-shift/undercut analysis below 17 teeth')
    return Disk(name, teeth, x, y, z, spec.module*teeth/2, spec.face_width, group)


def _span(disks, module, margin):
    # Conservative illustrative external gear addendum envelope (r_p + m).
    xmin = min(d.x-d.pitch_radius-module for d in disks)-margin
    xmax = max(d.x+d.pitch_radius+module for d in disks)+margin
    ymin = min(d.y-d.pitch_radius-module for d in disks)-margin
    ymax = max(d.y+d.pitch_radius+module for d in disks)+margin
    return xmin, xmax, ymin, ymax


def planetary_layout(ratio, adapter=DEFAULT, drive=DriveSpec(), planet_count=3):
    """Fixed ring / sun input / carrier output; one standard external-tooth stage.

    4:1 -> 18 sun, 18 planet, 54 ring.
    5:1 -> 18 sun, 27 planet, 72 ring.
    """
    adapter.validate(); drive.validate()
    if ratio not in (4, 5) or planet_count != 3:
        raise ValueError('Only validated 3-planet 4:1 and 5:1 studies are supported')
    sun = 18
    ring = sun*(ratio-1)
    planet = (ring-sun)//2
    if ring != sun+2*planet or (sun+ring)%planet_count:
        raise ValueError('Planetary pitch geometry or indexed spacing fails')
    if min(sun, planet) < MIN_UNSHIFTED_20_DEG_EXTERNAL_TEETH:
        raise ValueError('Undercut risk: too few unshifted external teeth')
    center = (sun+planet)*drive.module/2
    planet_tip_radius = planet*drive.module/2 + drive.module
    neighbor_distance = 2*center*math.sin(math.pi/planet_count)
    if neighbor_distance <= 2*planet_tip_radius:
        raise ValueError('Adjacent planets collide at external tip envelopes')
    output_plate_bottom = adapter.seated_top + drive.coupling_gap
    pitch_z = output_plate_bottom + drive.support_plate + drive.axial_gap
    pitch_top = pitch_z + drive.face_width
    top_cover_z = pitch_top + drive.axial_gap
    top_z = top_cover_z + drive.support_plate + drive.top_input_stub
    if top_z > adapter.box_depth:
        raise ValueError('Drive exceeds 101.6-mm axial envelope')
    disks = [_external_disk('Sun',sun,0,0,pitch_z,drive,'input')]
    for i in range(planet_count):
        ang = 2*math.pi*i/planet_count
        disks.append(_external_disk('Planet'+str(i+1),planet,
                                    center*math.cos(ang),center*math.sin(ang),
                                    pitch_z,drive,'planet'))
    ring_pitch = ring*drive.module/2
    casing_radius = ring_pitch + 1.25*drive.module + drive.casing_margin
    # Ensure external tips fit inside casing, but never pretend to validate teeth.
    if center + planet_tip_radius > casing_radius:
        raise ValueError('Planet tip envelope exceeds casing')
    return dict(
        kind='planetary', label=f'{ratio}:1 fixed-ring planetary', ratio=float(ratio),
        input_teeth=sun, planet_teeth=planet, ring_teeth=ring, planet_count=planet_count,
        module=drive.module, disks=tuple(disks), pitch_center_distance=center,
        neighbor_tip_clearance=neighbor_distance-2*planet_tip_radius,
        ring_pitch_radius=ring_pitch, casing_radius=casing_radius,
        xy_bounds=(-casing_radius,casing_radius,-casing_radius,casing_radius),
        support_z=output_plate_bottom, pitch_z=pitch_z, cover_z=top_cover_z,
        top_z=top_z, free_axial=adapter.box_depth-top_z,
        drive=drive, adapter=adapter,
        caveat='Pitch-envelope solids only; no involute teeth, internal teeth, load-bearing bearings, or torque connection.'
    )


def compound_layout(adapter=DEFAULT, drive=DriveSpec()):
    """Two external spur meshes, 18:54 then 24:48 -> +6:1 output.

    The two gear planes have a folded (90 degree) intermediate shaft, so
    there is NO coaxial input/output concentric bearing problem. Input shaft
    is offset from the tuning-pin axis; that transverse clearance is unmeasured.
    """
    adapter.validate(); drive.validate()
    # Equal center distances permit a 90-degree folded outline.
    a,b,c,d = 18,54,24,48
    center1=(a+b)*drive.module/2
    center2=(c+d)*drive.module/2
    if abs(center1-center2)>1e-9:
        raise ValueError('Two folded center distances must match')
    lower_z=adapter.seated_top+drive.coupling_gap+drive.support_plate+drive.axial_gap
    upper_z=lower_z+drive.face_width+drive.axial_gap
    top_z=upper_z+drive.face_width+drive.axial_gap+drive.support_plate+drive.top_input_stub
    if top_z>adapter.box_depth:
        raise ValueError('Compound drive exceeds axial envelope')
    disks=(
        _external_disk('Output48',d,0,0,lower_z,drive,'output'),
        _external_disk('Intermediate24',c,center2,0,lower_z,drive,'intermediate'),
        _external_disk('Intermediate54',b,center2,0,upper_z,drive,'intermediate'),
        _external_disk('Input18',a,center2,center1,upper_z,drive,'input'),
    )
    bounds=_span(disks,drive.module,drive.casing_margin)
    if (a+b)!=(c+d) or a*b*c*d==0:
        raise ValueError('Unusable compound stage counts')
    ratio=(b/a)*(d/c)
    if abs(ratio-6.0)>1e-9:
        raise ValueError('Unexpected compound ratio')
    return dict(
        kind='compound', label='6:1 two-stage folded compound spur', ratio=ratio,
        input_teeth=a, first_driven_teeth=b, second_driver_teeth=c, output_teeth=d,
        disks=disks, stage1_center=center1, stage2_center=center2,
        xy_bounds=bounds, casing_radius=None, ring_pitch_radius=None,
        pitch_z=lower_z, upper_z=upper_z, cover_z=upper_z+drive.face_width+drive.axial_gap,
        support_z=adapter.seated_top+drive.coupling_gap,
        top_z=top_z, free_axial=adapter.box_depth-top_z,
        drive=drive, adapter=adapter, module=drive.module,
        caveat='Pitch-envelope solids only; no involute teeth, bearings, backlash, or qualified torque coupling.'
    )


def make_layout(study, adapter=DEFAULT, drive=DriveSpec()):
    if study == 'planetary4': return planetary_layout(4,adapter,drive)
    if study == 'planetary5': return planetary_layout(5,adapter,drive)
    if study == 'compound6': return compound_layout(adapter,drive)
    raise ValueError('Unknown drive study '+repr(study))


def summary_rows(adapter=DEFAULT,drive=DriveSpec()):
    rows=[]
    for name in STUDIES:
        l=make_layout(name,adapter,drive)
        x0,x1,y0,y1=l['xy_bounds']
        rows.append(dict(name=name,ratio=l['ratio'],
                         width_mm=round(x1-x0,3),depth_mm=round(y1-y0,3),
                         top_mm=round(l['top_z'],3),
                         remaining_axial_mm=round(l['free_axial'],3),
                         note='PITCH ENVELOPE ONLY; dimensions are provisional'))
    return rows
