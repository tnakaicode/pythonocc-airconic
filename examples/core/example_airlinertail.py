# -*- coding: utf-8 -*-
"""
Created on Fri Jan 15 11:39:16 2016

Example script for generating the lifting surfaces for the tail of a
transport aircraft (fin and tailplane external geometry). This uses built-in
tailplane functions from airconics.examples: See
wing_example_transonic_airliner.py for how these functions are implemented

# ==============================================================================
# AirCONICS
# Aircraft CONfiguration through Integrated Cross-disciplinary Scripting
# version 0.2
# Andras Sobester, 2015.
# Bug reports to a.sobester@soton.ac.uk or @ASobester please.
# ==============================================================================

@author: pchambers
"""
if __name__ == '__main__':
    # Initialise the display
    from OCC.Display.SimpleGui import init_display
    display, start_display, add_menu, add_function_to_menu = init_display()

    from airconics.examples.tailplane_example_transonic_airliner import *
    from airconics import liftingsurface
    import airconics.AirCONICStools as act

    from OCC.Core.gp import gp_Ax1, gp_Pnt, gp_Dir

    # Position of the apex of the fin
    P = [36.98-0.49-0.02, 0.0, 2.395-0.141]

    SegmentNo = 101
    ChordFact = 1.01
    ScaleFact = 21.93
#
#    print("Creating Fin...")
    Fin = liftingsurface.LiftingSurface(P, mySweepAngleFunctionFin,
                                        myDihedralFunctionFin,
                                        myTwistFunctionFin,
                                        myChordFunctionFin,
                                        myAirfoilFunctionFin,
                                        SegmentNo=SegmentNo,
                                        ChordFactor=ChordFact,
                                        ScaleFactor=ScaleFact)
#    print("Fin done")
#    Create the rotation axis centered at the apex point in the x direction
    RotAxis = gp_Ax1(gp_Pnt(*P), gp_Dir(1, 0, 0))

    # Having some problem with the fin loft: display some airfoils
    # to figure out what's going on:
#    for section in Fin._Sections:
#        curve = section.Curve.GetObject()
#        curve.Scale(gp_Pnt(0., 0., 0.), ScaleFact)
#        display.DisplayShape(section.Curve, update=True)

    Fin.RotateComponents(RotAxis, 90)
    Fin.Display(display)

#     Position of the apex of the tailplane
    P = [43, 0.000, 1.633+0.02]

    SegmentNo = 101
    ChordFactor = 1.01
    ScaleFactor = 17.3

    print("Creating Tailplane")
    TP = liftingsurface.LiftingSurface(P, mySweepAngleFunctionTP,
                                       myDihedralFunctionTP,
                                       myTwistFunctionTP,
                                       myChordFunctionTP,
                                       myAirfoilFunctionTP,
                                       SegmentNo=SegmentNo,
                                       ChordFactor=ChordFact,
                                       ScaleFactor=ScaleFact)

    TP.Display(display)

    TP2 = TP.MirrorComponents(plane='xz')
    print("Tailplane done")

#     Note: TP2 is a TopoDS_Shape, not a wing and DisplayShape is called as:
    TP2.Display(display)
#
    start_display()
