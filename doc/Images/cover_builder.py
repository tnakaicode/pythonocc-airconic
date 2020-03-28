# -*- coding: utf-8 -*-
"""
Created on Tue Apr 26 12:10:24 2016

@author: pchambers
"""

from OCC.Core.Graphic3d import Graphic3d_NOM_ALUMINIUM
from OCC.Core.gp import gp_Ax1, gp_Pnt, gp_Dir, gp_Vec

from airconics.examples.wing_example_transonic_airliner import *
import airconics.examples.boxwing as bw
from airconics.base import AirconicsShape, AirconicsCollection
from airconics.examples.tailplane_example_transonic_airliner import *
from airconics import liftingsurface, engine, fuselage_oml
import airconics.AirCONICStools as act

from OCC.Core.Quantity import Quantity_NOC_RED4, Quantity_NOC_WHITE, Quantity_NOC_BLUE4, Quantity_NOC_GRAY
from OCC.Core.Graphic3d import Graphic3d_NOM_SHINY_PLASTIC


def transonic_airliner(display=None,
                       Propulsion=1,
                       EngineDia=2.9,
                       FuselageScaling=[55.902, 55.902, 55.902],
                       NoseLengthRatio=0.182,
                       TailLengthRatio=0.293,
                       WingScaleFactor=44.56,
                       WingChordFactor=1.0,
                       Topology=1,
                       SpanStation1=0.35,
                       SpanStation2=0.675,
                       EngineCtrBelowLE=0.3558,
                       EngineCtrFwdOfLE=0.9837,
                       Scarf_deg=3):
    """
    Parameters
    ----------
    Propulsion - int
        1 - twin
        2 - quad
    EngineDia - float
        Diameter of engine intake highlight
    FuselageScaling - list, length 3
        Fx, Fy, Fz scaling factors of fuselage
    NoseLengthRatio - scalar
        Proportion of forward tapering section of the fuselage 
    TailLengthRatio - scalar
        Proportion of aft tapering section of the fuselage
    WingScaleFactor - scalar
        Scale Factor of the main wing
    WingChordFactor - scalar
        Chord factor of the main wing
    Topology - int
        Topology = 2 should yield a box wing airliner - use with caution
    SpanStation - float
        Inboard engine at this span station
    SpanStation2 - float
        Outboard engine at this span station (ignored if Propulsion=1)
    EngineCtrBelowLE - float
        Engine below leading edge, normalised by the length of the nacelle -
        range: [0.35,0.5]
    EngineCtrFwdOfLE - float
        Engine forward of leading edge, normalised by the length of the nacelle
        range: [0.85,1.5]
    Scarf_deg - scalar # Engine scarf angle
    
    Returns
    -------
    airliner - 'Aircraft' class instance
        The collection of aircraft parts
    
    See also
    --------
    class Aircraft
    """

    try:
        Fus = fuselage_oml.Fuselage(NoseLengthRatio, TailLengthRatio,
                                    Scaling=FuselageScaling,
                                    NoseCoordinates=[0, 0, 0])
    except:
        print ("Fuselage fitting failed - stopping.")
        return None

    FuselageHeight = FuselageScaling[2]*0.105
    FuselageLength = FuselageScaling[0]
    FuselageWidth  = FuselageScaling[1]*0.106

    if Fus['OML'] is None:
        print ("Failed to fit fuselage surface, stopping.")
        return None

#    FSurf = rs.CopyObject(FuselageOMLSurf)

    # Position of the apex of the wing
    if FuselageHeight < 8.0:
         #787:[9.77,0,-0.307]
        WingApex = [0.1748*FuselageLength,0,-0.0523*FuselageHeight]
    else:
        WingApex = [0.1748*FuselageLength,0,-0.1*FuselageHeight] #787:[9.77,0,-0.307]


    # Set up the wing object, including the list of user-defined functions that
    # describe the spanwise variations of sweep, dihedral, etc.
    if Topology == 1:
        NSeg = 10
        Wing = liftingsurface.LiftingSurface(WingApex,
                                             mySweepAngleFunctionAirliner, 
                                             myDihedralFunctionAirliner, 
                                             myTwistFunctionAirliner, 
                                             myChordFunctionAirliner, 
                                             myAirfoilFunctionAirliner,
                                             SegmentNo=NSeg,
                                             ScaleFactor=WingScaleFactor,
                                             ChordFactor=WingChordFactor)
        RootChord = Wing.RootChord
    elif Topology == 2:
        NSeg = 101
        Wing = liftingsurface.LiftingSurface(WingApex,
                                             mySweepAngleFunctionAirliner,
                                             bw.myDihedralFunctionBoxWing,
                                             myTwistFunctionAirliner,
                                             myChordFunctionAirliner,
                                             myAirfoilFunctionAirliner, 
                                             SegmentNo=NSeg,
                                             ScaleFactor=WingScaleFactor,
                                             ChordFactor=WingChordFactor)
        RootChord = Wing.RootChord

    if Topology == 1:
    
        # Add wing to body fairing 
        WTBFXCentre = WingApex[0] + RootChord/2.0 + RootChord*0.1297 # 787: 23.8
        if FuselageHeight < 8.0:
            #Note: I made changes to this in OCC Airconics to get a better fit
            # - Paul
            WTBFZ = RootChord*0.009 #787: 0.2
            WTBFheight = 1.8*0.1212*RootChord #787:2.7
            WTBFwidth = 1.08*FuselageWidth
        else:
    
            WTBFZ = WingApex[2] + 0.005*RootChord
            WTBFheight = 0.09*RootChord 
            WTBFwidth = 1.15*FuselageWidth
    
        WTBFlength = 1.167*RootChord #787:26
        WBF_shape = act.make_ellipsoid([WTBFXCentre, 0, WTBFZ], WTBFlength,
                                        WTBFwidth, WTBFheight)
        WBF = AirconicsShape(components={'WBF': WBF_shape})

#        Trim wing inboard section
        CutCirc = act.make_circle3pt([0,WTBFwidth/4.,-45], [0,WTBFwidth/4.,45], [90,WTBFwidth/4.,0])
        CutCircDisk = act.PlanarSurf(CutCirc)
        Wing['Surface'] = act.TrimShapebyPlane(Wing['Surface'], CutCircDisk)
    elif Topology == 2:
#        Overlapping wing tips
        CutCirc = act.make_circle3pt((0,0,-45), (0,0,45), (90,0,0))
        CutCircDisk = act.PlanarSurf(CutCirc)
        Wing['Surface'] = act.TrimShapebyPlane(Wing['Surface'], CutCircDisk)


#   Engine installation (nacelle and pylon)
    NacelleLength = 1.95*EngineDia
    if Propulsion == 1:
        SpanStations = [SpanStation1]
    elif Propulsion == 2:
        SpanStations = [SpanStation1, SpanStation2]
   
    engines = []
    for i, SpanStation in enumerate(SpanStations):
        EngineSection, Chord = act.CutSect(Wing['Surface'], SpanStation)
        CEP = Chord.EndPoint()
        Centreloc = [CEP.X()-EngineCtrFwdOfLE*NacelleLength,
                    CEP.Y(), 
                    CEP.Z()-EngineCtrBelowLE*NacelleLength]
        eng =  engine.Engine(Chord,
               CentreLocation=Centreloc,
               ScarfAngle=Scarf_deg,
               HighlightRadius=EngineDia/2.0,
               MeanNacelleLength = NacelleLength)

        engines.append(eng)

#    # Script for generating and positioning the fin
#    # Position of the apex of the fin
    P = [0.6524*FuselageLength,0.003,FuselageHeight*0.384]
    #P = [36.47,0.003,2.254]55.902
    
    if Topology == 1:
        ScaleFactor = WingScaleFactor/2.032 #787:21.93
    elif Topology == 2:
        ScaleFactor = WingScaleFactor/3.5 
    
    SegmentNo = 100
    ChordFactor = 1.01#787:1.01
    Fin = liftingsurface.LiftingSurface(P, mySweepAngleFunctionFin,
                                        myDihedralFunctionFin,
                                        myTwistFunctionFin,
                                        myChordFunctionFin,
                                        myAirfoilFunctionFin,
                                        SegmentNo=SegmentNo,
                                        ChordFactor=ChordFactor,
                                        ScaleFactor=ScaleFactor)

#    Create the rotation axis centered at the apex point in the x direction
    RotAxis = gp_Ax1(gp_Pnt(*P), gp_Dir(1, 0, 0))
    
    Fin.RotateComponents(RotAxis, 90)

    if Topology == 1:
#        Tailplane
        P = [0.7692*FuselageLength,0.000,FuselageHeight*0.29]
        SegmentNo = 100
        ChordFactor = 1.01
        ScaleFactor = 0.388*WingScaleFactor #787:17.3
        TP = liftingsurface.LiftingSurface(P,
                                           mySweepAngleFunctionTP, 
                                           myDihedralFunctionTP,
                                           myTwistFunctionTP,
                                           myChordFunctionTP,
                                           myAirfoilFunctionTP,
                                           SegmentNo=SegmentNo,
                                           ChordFactor=ChordFactor,
                                           ScaleFactor=ScaleFactor)


# OCC_AirCONICS Note: Nothing below here implemented in OCC_AirCONICS - See
# Rhino version for this functionality (largely for display only)
#
#    rs.DeleteObjects([EngineSection, Chord])
#    try:
#        rs.DeleteObjects([CutCirc])
#    except:
#        pass
#
#    try:
#        rs.DeleteObjects([CutCircDisk])
#    except:
#        pass
#
#    # Windows
#    
#    # Cockpit windows:    
    CockpitWindowTop = 0.305*FuselageHeight
    
    print("Making Fuselage Windows...")
    
#    solids = Fus.CockpitWindowContours(Height=CockpitWindowTop, Depth=6)
#
##     Cut the windows out:
#    for solid in solids:
#        Fus['OML'] = act.SplitShape(Fus['OML'], solid)
#    
#    
#    print("Cockpit Windows Done.")

    

##
##    (Xmin,Ymin,Zmin,Xmax,Ymax,Zmax) = act.ObjectsExtents([Win1, Win2, Win3, Win4])
    CockpitBulkheadX = NoseLengthRatio*FuselageLength*0.9
##
##    CockpitWallPlane = rs.PlaneFromPoints([CockpitBulkheadX, -15,-15],
##    [CockpitBulkheadX,15,-15],
##    [CockpitBulkheadX,-15,15])
##    
##    CockpitWall = rs.AddPlaneSurface(CockpitWallPlane, 30, 30)
##    
##    if 'WTBF' in locals():
##        rs.TrimBrep(WTBF, CockpitWall)
##
##    rs.DeleteObject(CockpitWall)
#
##    # Window lines
    WIN = [1]
    NOWIN = [0]
##
###    # A typical window pattern (including emergency exit windows)
    WinVec = WIN + 2*NOWIN + 9*WIN + 3*NOWIN + WIN + NOWIN + 24*WIN + 2*NOWIN + WIN + NOWIN + 14*WIN + 2*NOWIN + WIN + 20*WIN + 2*NOWIN + WIN + NOWIN + 20*WIN
    wires = []
    if FuselageHeight < 8.0:
###        # Single deck
        WindowLineHeight = 0.3555*FuselageHeight
        WinX = 0.1157*FuselageLength
        WindowPitch = 0.609
        WinInd = -1
        i = 0
        while WinX < 0.75*FuselageLength:
            WinInd = WinInd + 1
            if WinVec[WinInd] == 1 and WinX > CockpitBulkheadX:
                i=i+1
                print("Generating cabin window {}".format(i))
                WinCenter = [WinX, WindowLineHeight]
                W_wire = Fus.WindowContour(WinCenter)
                wires.append(W_wire)
#                display.DisplayShape(W_wire, color='black')
#                win_port, win_stbd = Fus.MakeWindow(*WinCenter)
#                print(type(win_port), type(win_stbd))
#                
#                display.DisplayShape(win_port, color='Black')
#                display.DisplayShape(win_stbd, color='Black')
#
###                Note: Need to fix makewindow to return windows WinStbd,
##                # WinPort, 
#                Fus.MakeWindow(WinX, WindowLineHeight)
###                act.AssignMaterial(WinStbd,"Plexiglass")
###                act.AssignMaterial(WinPort,"Plexiglass")
            WinX = WinX + WindowPitch
#
#    print("Cabin windows done")



#    else:
#        # TODO: Fuselage big enough to accommodate two decks 
#        # Lower deck
#        WindowLineHeight = 0.17*FuselageHeight #0.166
#        WinX = 0.1*FuselageLength #0.112
#        WindowPitch = 0.609
#        WinInd = 0
#        while WinX < 0.757*FuselageLength:
#            WinInd = WinInd + 1
#            if WinVec[WinInd] == 1 and WinX > CockpitBulkheadX:
#                WinStbd, WinPort, FuselageOMLSurf = fuselage_oml.MakeWindow(FuselageOMLSurf, WinX, WindowLineHeight)
#                act.AssignMaterial(WinStbd,"Plexiglass")
#                act.AssignMaterial(WinPort,"Plexiglass")
#            WinX = WinX + WindowPitch
#        # Upper deck
#        WindowLineHeight = 0.49*FuselageHeight
#        WinX = 0.174*FuselageLength #0.184
#        WinInd = 0
#        while WinX < 0.757*FuselageLength:
#            WinInd = WinInd + 1
#            if WinVec[WinInd] == 1 and WinX > CockpitBulkheadX:
#                WinStbd, WinPort, FuselageOMLSurf = fuselage_oml.MakeWindow(FuselageOMLSurf, WinX, WindowLineHeight)
#                act.AssignMaterial(WinStbd,"Plexiglass")
#                act.AssignMaterial(WinPort,"Plexiglass")
#            WinX = WinX + WindowPitch
#
#
#
#
#
#    act.AssignMaterial(FuselageOMLSurf,"White_composite_external")
#    act.AssignMaterial(WingSurf,"White_composite_external")
#    try:
#        act.AssignMaterial(TPSurf,"ShinyBARedMetal")
#    except:
#        pass
#    act.AssignMaterial(FinSurf,"ShinyBARedMetal")
#    act.AssignMaterial(Win1,"Plexiglass")
#    act.AssignMaterial(Win2,"Plexiglass")
#    act.AssignMaterial(Win3,"Plexiglass")
#    act.AssignMaterial(Win4,"Plexiglass")
#
#
#    # Mirror the geometry as required
    Wing2 = Wing.MirrorComponents(plane='xz')
    try:
        # this try section allows box wing i.e. no tailplane
        TP2 = TP.MirrorComponents(plane='xz')
    except:
        pass

    engines_left = []
    for eng in engines:
        engines_left.append(eng.MirrorComponents(plane='xz'))


#    if Propulsion == 1:
#        for ObjId in EngineStbd:
#            act.MirrorObjectXZ(ObjId)
#        act.MirrorObjectXZ(PylonStbd)
#    elif Propulsion == 2:
#        raise NotImplementedError
#        for ObjId in EngineStbd1:
#            act.MirrorObjectXZ(ObjId)
#        act.MirrorObjectXZ(PylonStbd1)
#        for ObjId in EngineStbd2:
#            act.MirrorObjectXZ(ObjId)
#        act.MirrorObjectXZ(PylonStbd2)


#    Build the return assembly (could change this later based on input 'tree':
    airliner = AirconicsCollection(parts={'Wing_right': Wing,
                                          'Wing_left': Wing2,
                                          'Fuselage': Fus,
                                          'Fin': Fin,
                                          'Tailplane_right': TP,
                                          'Tailplane_left': TP2,
                                          'WBF': WBF})

    # Loop over the engines and write all components:
    for i, eng in enumerate(engines):
        name = 'engine_right' + str(i+1)
        airliner.AddPart(eng, name)
    for i, eng in enumerate(engines_left):
        name = 'engine_left' + str(i+1)
        airliner.AddPart(eng, name)

    return airliner, wires


if __name__ == "__main__":
    from OCC.Display.SimpleGui import init_display
    display, start_display, add_menu, add_function_to_menu = init_display()

    display.View.SetRaytracingMode()   # this might be called by default

#    '787-8'
    Airliner, wires = transonic_airliner(display)

    red = Quantity_NOC_RED4
    white =  Quantity_NOC_WHITE
    blue = Quantity_NOC_BLUE4
    grey = Quantity_NOC_GRAY
    painted = Graphic3d_NOM_SHINY_PLASTIC
    Airliner['Fin'].Display(display, color=red, material=painted)
    Airliner['Tailplane_left'].Display(display, color=red, material=painted)
    Airliner['Tailplane_right'].Display(display, color=red, material=painted)
    
    Airliner['Wing_left'].Display(display, color=white,  material=painted)
    Airliner['Wing_right'].Display(display, color=white,  material=painted)
    Airliner['WBF'].Display(display, color=white,  material=painted)
    
    eng1 = Airliner['engine_left1']
    eng2 = Airliner['engine_right1']
    
    for engine in [eng1, eng2]:
        display.DisplayShape(engine['Spinner'], color='black')
        display.DisplayShape(engine['Nacelle'], color=blue, material=painted)
        display.DisplayShape(engine['BypassDisk'], color=grey, material=painted)
        display.DisplayShape(engine._AirconicsShape__Components.BypassDisk, color=grey, material=painted)
        display.DisplayShape(engine._AirconicsShape__Components.FanDisk, color=grey, material=painted)
        display.DisplayShape(engine._AirconicsShape__Components.TailCone, color=grey, material=painted)
        display.DisplayShape(engine._AirconicsShape__Components.Pylon_symplane, color=white, material=painted)


    Airliner['Fuselage'].Display(display, color=white,  material=painted)

    display.ZoomFactor(10)
    from OCC.Core.V3d import *
#    display.View.SetProj(V3d_XnegYnegZpos)

    display.Repaint()
    from OCC.Core.Graphic3d import Graphic3d_EF_PDF
    display.View.View().Export('./Airliner.pdf', Graphic3d_EF_PDF)
    
    start_display()