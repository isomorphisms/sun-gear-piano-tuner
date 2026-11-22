"""FreeCAD-native pitch-envelope assemblies, NOT cut/mold-ready gear solids.

The three layouts contain coaxial pitch disks and annular ring/clearance
references, all with genuine OpenCascade shapes in real FreeCAD documents.
Teeth, keyed output coupling, reaction fixture, loaded bearings and backlash
are deliberately excluded until measured requirements exist.
"""
from pathlib import Path
import FreeCAD as App
import Part
from cad.adapter_geometry import DEFAULT
from cad.drive_geometry import DriveSpec, STUDIES, make_layout
from cad.freecad_adapter import build_adapter


def _feature(doc, group, name, label, shape, rgb=None, transparency=0):
    obj = doc.addObject('Part::Feature', name)
    obj.Label = label
    obj.Shape = shape
    if shape.isNull() or not shape.isValid():
        raise RuntimeError('Invalid FreeCAD reference geometry: '+name)
    group.addObject(obj)
    if App.GuiUp and rgb:
        obj.ViewObject.ShapeColor = rgb
        obj.ViewObject.Transparency = transparency
    return obj


def _annulus(outer_radius,inner_radius,height,z):
    a=Part.makeCylinder(outer_radius,height,App.Vector(0,0,z))
    b=Part.makeCylinder(inner_radius,height,App.Vector(0,0,z))
    return a.cut(b)


def build_drive(study, style='square', adapter=DEFAULT, drive=DriveSpec(), document_name=None):
    """Return (document, adapter_body, layout, generated_features).

    Shape objects are *pitch/reference envelopes*, not an actual gear mesh.
    FreeCAD's own solid geometry is generated and tested; this does not imply
    correct tooth contact, backlash, load capacity or physical fit.
    """
    if study not in STUDIES: raise ValueError('Unknown study')
    layout=make_layout(study,adapter,drive)
    name=document_name or ('SunGearDrive_'+study+'_'+style)
    doc,adapter_body,_=build_adapter(style,adapter,document_name=name)
    features={}
    try:
        group=doc.addObject('App::DocumentObjectGroup','DrivePitchReferences')
        group.Label='Reference-only gear pitches / not manufactured teeth'
        group.addProperty('App::PropertyString','DesignStatus','Notes')
        group.DesignStatus='PITCH ENVELOPES. No involute teeth, torque path, bearings or backlash verified.'
        group.addProperty('App::PropertyString','StudyType','Notes')
        group.StudyType=study
        group.addProperty('App::PropertyFloat','IdealInputToOutputRatio','Kinematics')
        group.IdealInputToOutputRatio=layout['ratio']
        group.addProperty('App::PropertyLength','AxialTop','Envelopes')
        group.AxialTop=layout['top_z']
        group.addProperty('App::PropertyLength','RemainingAxial','Envelopes')
        group.RemainingAxial=layout['free_axial']
        x0,x1,y0,y1=layout['xy_bounds']
        group.addProperty('App::PropertyLength','WidthXY','Envelopes')
        group.WidthXY=x1-x0
        group.addProperty('App::PropertyLength','DepthXY','Envelopes')
        group.DepthXY=y1-y0
        group.addProperty('App::PropertyString','EnvelopeWidthStatus','Notes')
        group.EnvelopeWidthStatus='NOT MEASURED on piano; footprint not accepted.'
        # Mesh pitch circles, as thin solid disks: matched pairs touch at pitch.
        # They intentionally do not possess teeth, roots or fillets.
        for disk in layout['disks']:
            shape=Part.makeCylinder(disk.pitch_radius,drive.face_width,
                                    App.Vector(disk.x,disk.y,disk.z))
            obj=_feature(doc,group,disk.name+'Pitch',
                         disk.name+' / '+str(disk.teeth)+'T pitch reference (NOT gear teeth)',
                         shape,{'input':(.77,.28,.22),'output':(.22,.62,.70),
                                'intermediate':(.7,.55,.20),'planet':(.4,.58,.8)}.get(disk.group))
            obj.addProperty('App::PropertyInteger','NominalTeeth','Reference')
            obj.NominalTeeth=disk.teeth
            obj.addProperty('App::PropertyLength','PitchRadius','Reference')
            obj.PitchRadius=disk.pitch_radius
            features[disk.name]=obj
        if layout['kind']=='planetary':
            r=layout['ring_pitch_radius']; casing=layout['casing_radius']
            features['Ring'] = _feature(doc,group,'RingPitchShell',
                'Fixed-ring housing envelope; NOT internal teeth',
                _annulus(casing,r,drive.face_width,layout['pitch_z']),(.45,.45,.52),65)
            # Fixed annular casing support and movable carrier reference below gears.
            plate_r=r-2*drive.module
            features['Carrier'] = _feature(doc,group,'CarrierOutputReference',
                'Carrier output plate; shaft/bearings unspecified',
                Part.makeCylinder(plate_r,drive.support_plate,App.Vector(0,0,layout['support_z'])),
                (.20,.68,.68),25)
            features['CaseBase']=_feature(doc,group,'CaseBaseAnnulus',
                'Fixed case support annulus; load path unspecified',
                _annulus(casing,plate_r,drive.support_plate,layout['support_z']),(.38,.38,.4),80)
            features['CaseCap']=_feature(doc,group,'CaseTopAnnulus',
                'Fixed cap pitch envelope; not a bearing seat',
                _annulus(casing,drive.module*6,drive.support_plate,layout['cover_z']),(.38,.38,.4),80)
        else:
            # A single orthogonal folded outline avoids a falsely coaxial
            # input/output shaft arrangement. No housing manufactured here.
            xmin,xmax,ymin,ymax=layout['xy_bounds']
            bottom=layout['support_z']
            # FreeCAD edge-wires for full package bounding prism, not a solid.
            corners=[App.Vector(xmin,ymin,bottom),App.Vector(xmax,ymin,bottom),
                     App.Vector(xmax,ymax,bottom),App.Vector(xmin,ymax,bottom)]
            features['Package']=_feature(doc,group,'CompoundXYFrame',
                'Total XY footprint: width and depth not yet known to fit piano',
                Part.makePolygon(corners+[corners[0]]),(.50,.5,.5))
        # Top axial bound and input stub are schematic references, with
        # no assertion that shafts, couplers or housings can be made.
        if layout['kind']=='planetary':
            shaft_x=shaft_y=0.0
        else:
            shaft_x=layout['stage2_center'];shaft_y=layout['stage1_center']
        features['InputStub']=_feature(doc,group,'InputStub',
            'Input shaft clearance cylinder (no keyed drive connection)',
            Part.makeCylinder(2.5,drive.top_input_stub,
                App.Vector(shaft_x,shaft_y,layout['top_z']-drive.top_input_stub)),(.9,.35,.2),30)
        doc.recompute()
        if not adapter_body.Shape.isValid() or len(adapter_body.Shape.Solids)!=1:
            raise RuntimeError('Reference assembly invalidated adapter body')
        if layout['top_z']>adapter.box_depth:
            raise RuntimeError('Drive violates axial envelope')
        return doc,adapter_body,layout,features
    except Exception:
        App.closeDocument(doc.Name)
        raise


def export_drive(study,style,directory,adapter=DEFAULT,drive=DriveSpec()):
    directory=Path(directory).resolve();directory.mkdir(parents=True,exist_ok=True)
    doc,body,layout,features=build_drive(study,style,adapter,drive)
    try:
        name='sun_gear_'+study+'_'+style+'_layout_v2'
        native=directory/(name+'.FCStd')
        step=directory/(name+'.step')
        doc.recompute()
        doc.saveAs(str(native))
        # Valid solids only; internal pitch/reference solids are separate STEP
        # objects, and are explicitly NOT accurate gear teeth.
        solids=[body]+[f for f in features.values() if len(f.Shape.Solids)]
        Part.export(solids,str(step))
        return str(native),str(step)
    finally:
        App.closeDocument(doc.Name)
