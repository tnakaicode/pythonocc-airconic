# -*- coding: utf-8 -*-
"""
Airfoil primitive class definitions

Created on Fri Dec  4 13:31:35 2015

@author: pchambers
"""
from OCC.Core.GC import GC_MakeSegment
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_OX, gp_OY

from . import CRMfoil
from . import AirCONICStools as act
from pkg_resources import resource_string, resource_exists
import numpy as np


# Classes
# -----------------------------------------------------------------------------
class Airfoil(object):
    """Class for defining a range of spline-fitted airfoil curves

        Parameters
        ----------
        LeadingEdgePoint : array of float (,3)
            (x, y, z) origin of the airfoil LE

        ChordLength : scalar
            Length of the airfoil chord

        Rotation : scalar
            Angle (deg) at which the base airfoil is inclined (angle of attack,
            rotation around y axis)

        Twist : scalar
            Angle (deg)  at which the base airfoil is twisted
            (dihedral, rotation around x axis)

        SeligProfile : string
            Name of the Selig airfoil: see
            http://m-selig.ae.illinois.edu/ads/coord_database.html

        NACA4Profile : string
            Name of the airfoil in NACA 4 format

        NACA5Profile : string
            Name of the airfoil in NACA 5 format.
            TODO: NACA5 profile not yet implemented

        CRM_Profile : bool
            If true, airfoil profile will be interpolated from Common Research
            Model (CRM). Must also declare 'CRMEpsilon' variable.

        CRM_Epsilon : float
            Spanwise fraction between 0 and 1 to interpolate profile from CRM

        InterpProfile : bool
            If True, a set of points between Af1 and Af2 will be interpolated
            for BSpline curve fitting (see AddInterp2)

        Eps : scalar
            Spanwise coordinate between Eps1 and Eps2 (used if InterpProfile is
            True)

        Af1 : airconics.Airfoil
            The Airfoil located at spanwise location Eps1. Af1.x and Af1.z.
            (used if InterpProfile is True)

        Af2 : airconics.Airfoil
            The Airfoil located at spanwise location Eps2.
            (used if InterpProfile is True)

        Eps1 : scalar
            Spanwise coordinate location of Airfoil Af1. Expected to range from
            0 (root of a lifting surface) to 1 (tip of a lifting surface)
            (used if InterpProfile is True)

        Eps2 : scalar
            Spanwise coordinate location of Airfoil Af2. Expected to range from
            0 (root of a lifting surface) to 1 (tip of a lifting surface), and
            also expected to be greater than Eps1
            (used if InterpProfile is True)

        EnforceSharpTE : bool
            Enforces sharp trailing edge (NACA airfoils only)

        Attributes
        ----------
        points : array of scalar, shape (N, 2)
            The x-z coordinates of points on the airfoils surface

        Curve - OCC.Geom.Geom_BsplineCurve
            The generated airfoil spline

        Notes
        -----
        * NACA5 profiles are not yet supported in OCC_AirCONICS.

        * Preference is that users allow the class constructor to handle
          building the Airfoil i.e. pass all physical definitions as class
          arguments.

        * Although the physical attributes can changed i.e. rotation, twist,
          ChordLength, LeadingEdgePoint etc., it is the users responsibility
          to rebuild the Airfoil with the 'Add***Airfoil' afterwards
        """
    def __init__(self,
                 LeadingEdgePoint=[0., 0., 0.],
                 ChordLength=1,
                 Rotation=0,
                 Twist=0,
                 SeligProfile=None,
                 Naca4Profile=None,
                 Naca5Profile=None,
                 CRMProfile=None,
                 CRM_Epsilon=0.,
                 InterpProfile=None,
                 Epsilon=0, Af1=None, Af2=None, Eps1=0, Eps2=1,
                 EnforceSharpTE=False):

        if CRM_Epsilon:
            CRMProfile = True
        Profiles = [SeligProfile, Naca4Profile, Naca5Profile, CRMProfile]

        assert(sum([1 for prof in Profiles if prof]) < 2),\
            "Ambiguous airfoil: More than one profile has been specified"

        self.LE = LeadingEdgePoint
        self.ChordLength = ChordLength
        self.Rotation = Rotation
        self.Twist = Twist
        self._EnforceSharpTE = EnforceSharpTE

        # Initialise the x and z airfoil surface points as None
        self._points = None

        self._make_airfoil(SeligProfile, Naca4Profile, Naca5Profile,
                           CRMProfile, CRM_Epsilon,
                           InterpProfile, Epsilon, Af1, Af2, Eps1, Eps2)

    @property
    def points(self):
        return self._points

    @points.setter
    def points(self, newpoints):
        # Updating this value recalls the _fitAirfoiltoPoints function. Does
        # not transform the airfoil
        self._points = newpoints
        self._fitAirfoiltoPoints()

    def _make_airfoil(self, SeligProfile, Naca4Profile, Naca5Profile,
                      CRMProfile, CRM_Epsilon,
                      InterpProfile, Epsilon, Af1, Af2, Eps1, Eps2):
        """Selects airfoil 'add' function based on Profile specified """
        if SeligProfile:
            self.AddAirfoilFromSeligFile(SeligProfile)
        elif Naca4Profile:
            self.AddNACA4(Naca4Profile)
        elif Naca5Profile:
            raise NotImplementedError("""This class is not yet
                implemented for Naca 5 digit profiles""")
        elif CRMProfile:
            self.AddCRMLinear(CRM_Epsilon)
        elif InterpProfile:
            self.AddLinear2(Epsilon, Af1, Af2, Eps1, Eps2)
        else:
            # 'Empty' Profile
            print("No Profile specified: Creating 'empty' Airfoil")
            self.Curve = None
            self.Profile = None

    def _fitAirfoiltoPoints(self):
        """ Fits an OCC curve to current airfoil.points.

        airfoil.points should be N by 2, the array of x, z points on the
        airfoil's surface.

        Returns
        -------
        Curve : OCC.Geom.Geom_BSplineCurve
            the generated spline
        """
        N = np.shape(self._points)[0]
        y = np.zeros(N)
        points3d = np.column_stack([self._points[:, 0], y, self._points[:, 1]])
        Curve = act.points_to_bspline(points3d)
        return Curve

    def _AirfoilPointsSeligFormat(self, SeligProfile):
        """Extracts airfoil coordinates from a file

        Assumes input selig files are specified in the Selig format, i.e.,
        header line, followed by x column, z column, from upper trailing edge
        to lower trailing edge.

        Parameters
        ----------
        SeligProfile : string
            The file basename containing the selig profile data

        Returns
        -------
        x - array of float
            x coordinates of airfoil curve

        z - array of float
            z coordinates of airfoil curve
        """
        res_pkg = 'airconics.coord_seligFmt'
        SeligProfile = SeligProfile + '.dat'
        assert(resource_exists(res_pkg, SeligProfile)),\
            "Airfoil database for {} not found.".format(SeligProfile)

        data = resource_string(res_pkg, SeligProfile)
        data = data.split(b'\r\n')[1:-1]
        N = len(data)
        x = np.zeros(N)
        z = np.zeros(N)
        for i, line in enumerate(data):
            vals = line.split()    # vals[0] = x coord, vals[1] = y coord
            x[i] = float(vals[0])
            z[i] = float(vals[1])
        return x, z

    def _NACA4cambercurve(self, MaxCamberLocTenthChord, MaxCamberPercChord):
        """ Generates the camber curve of a NACA 4-digit airfoil

        Paramters
        ---------
        MaxCamberLocTenthChord : int

        MaxCamberPercChord : int

        Returns
        -------

        """
        # Using the original notation of Jacobs et al.(1933)
        xmc     = MaxCamberLocTenthChord / 10.0
        zcammax = MaxCamberPercChord     / 100.0

        # Protect against division by zero on airfoils like NACA0012
        if xmc == 0:
            xmc = 0.2

        # Sampling the chord line
        ChordCoord, NCosPoints = act.coslin(xmc)

        # Compute the two sections of the camber curve and its slope
#        zcam = []
#        dzcamdx = []
        cos_pts = ChordCoord[0:NCosPoints]
        lin_pts = ChordCoord[NCosPoints:]

        zcam = np.hstack(( (zcammax/(xmc ** 2)) * (2*xmc*cos_pts - cos_pts**2),
                           (zcammax/((1-xmc)**2)) * \
                             (1-2*xmc+2*xmc*lin_pts-(lin_pts ** 2)) ))
        
        dzcamdx = np.hstack(( (zcammax/xmc ** 2)*(2*xmc - 2*cos_pts),
                              (zcammax/(1-xmc) ** 2)*(2*xmc - 2*lin_pts) ))

        return ChordCoord, zcam, dzcamdx
        
    def _NACA4halfthickness(self, ChordCoord, MaxThicknessPercChord):
        """Given  a set of ordinates  and  a  maximum thickness value
        (expressed in units of chord) it computes the NACA 4-digit
        half-thickness distribution.  The abscissas must be in the
        range [0,1]."""

        # Max thickness in units of chord
        tmax = MaxThicknessPercChord / 100.0

        # Coefficient tweak to close off the trailing edge if required
        a0 =  0.2969/0.2
        a1 = -0.1260/0.2
        a2 = -0.3516/0.2
        a3 =  0.2843/0.2
        a4 = -0.1015/0.2
        # The highest order term could be fudged to make t(1) = 0, thus
        # producing a sharp trailing edge (NACA4s by definition have a finite
        # thickness TE). However, this is probably better enforced by removing
        # a wedge from the coordinate sets (a generic method). Still, this
        # might be a NACA-specific alternative:
        # t_at_one = a0+a1+a2+a3+a4
        # a4 = a4 - t_at_one

        # Half-thickness polynomial
        t = tmax * (a0*ChordCoord**0.5 + a1*ChordCoord + a2*ChordCoord**2.0 +
                    a3*ChordCoord**3.0 + a4*ChordCoord**4.0)
        return t

    def _camberplusthickness(self, ChordCoord, zcam, dzcamdx, t):
        """Internal function. Adds a thickness distribution to a specified
        camber line. The slope is an input here, because it is usually possible
        to compute it analytically at the same time as the curve itself is
        computed."""

        # Theta angle (slope of the camber curve)
        Theta = np.arctan(dzcamdx)

        xu = ChordCoord - t*np.sin(Theta)
        xl = ChordCoord + t*np.sin(Theta)
        zu = zcam + t*np.cos(Theta)
        zl = zcam - t*np.cos(Theta)

        # Correct small abscissa positioning errors in case of sharp TE
        if self._EnforceSharpTE:
            xu[-1] = ChordCoord[-1]
            xl[-1] = ChordCoord[-1]

        return xu, zu, xl, zl, Theta

    def _mergesurfaces(self, xu, zu, xl, zl):
        """Combine the upper and lower surfaces into one"""

        if self._EnforceSharpTE:
            # Remove wedge to sharpen trailing edge if needed
            zu -= xu*zu[-1]
            zl -= xl*zl[-1]

        # Combine upper and lower (Top surface reversed from right to left)
        x = np.hstack((xu[::-1], xl[1:]))   # Remove duplicate LE point
        z = np.hstack((zu[::-1], zl[1:]))
        return x, z

    def _NACA4digitPnts(self, MaxCamberPercChord, MaxCamberLocTenthChord,
                        MaxThicknessPercChord):
        """Generates a set of points that define a NACA 4-digit airfoil
        
        Parameters
        ----------
        MaxCamberPercChord - int
        MaxCamberLocTenthChord - int
        MaxThicknessPercChord - int

        Returns
        -------
        x - array of x coords on surface of NACA4 airfoil
        z - array of z coords on surface of NACA4 airfoil
        xu - array of x coords on upper surface of NACA4 airfoil
        zu - array of z coords on upper surface of NACA4 airfoil
        xl - array of x coords on lower surface of NACA4 airfoil
        zl - array of z coords on lower surface of NACA4 airfoil
        """

        ChordCoord, zcam, dzcamdx = \
            self._NACA4cambercurve(MaxCamberLocTenthChord, MaxCamberPercChord)

        t = self._NACA4halfthickness(ChordCoord, MaxThicknessPercChord)

        xu, zu, xl, zl, Theta = self._camberplusthickness(ChordCoord, zcam,
                                                          dzcamdx, t)
        # Leading edge radius
        RLE = 1.1019*(MaxThicknessPercChord/100.0)**2.0

        x, z = self._mergesurfaces(xu, zu, xl, zl)

        return x, z, xu, zu, xl, zl, RLE

    def _TransformAirfoil(self):
        """Given a normal airfoil, nose in origin, chord along
        x axis, applies rotations, translation and (soon) smoothing
        """
        # TODO: Smoothing
#        for i in range(self.SmoothingIterations):
#            rs.FairCurve(self.Curve)

        # Can assume that the chord is from 0,0,0 to 1,0,0 before translation
        h_ChordLine = GC_MakeSegment(gp_Pnt(0, 0, 0),
                                   gp_Pnt(1, 0, 0)).Value()
        ChordLine = h_ChordLine

        Curve = self.Curve

#        Scaling:
        Curve.Scale(gp_Pnt(0, 0, 0), self.ChordLength)
        ChordLine.Scale(gp_Pnt(0, 0, 0), self.ChordLength)

#        Rotations - Note that direction is opposite to Rhino
#        Dihedral:
        if self.Rotation:
            Curve.Rotate(gp_OX(), np.radians(self.Rotation))
            ChordLine.Rotate(gp_OX(), np.radians(self.Rotation))

#        Twist:
        if self.Twist:
            Curve.Rotate(gp_OY(), -np.radians(self.Twist))
            ChordLine.Rotate(gp_OY(), -np.radians(self.Twist))

#        Translation:
#        self.Curve = Geom_BSplineCurve_DownCast(Curve.Translated(
#                                                        gp_Vec(*self.LE))
#                                                       )
        Curve.Translate(gp_Vec(*self.LE))
        ChordLine.Translate(gp_Vec(*self.LE))

        self.ChordLine = ChordLine

        return None

    def AddAirfoilFromSeligFile(self, SeligProfile, Smoothing=1):
        """Adds an airfoil generated by fitting a NURBS curve to a set
        of points whose coordinates are given in a Selig formatted file

        Parameters
        ----------
        SeligProfile : string
            base selig airfoil name e.g. 'b707a'.

        Smoothing : int (default=1)
            TODO: Airfoil curve smoothing

        Returns
        -------
        None

        Notes
        -----
        See Selig database online for other available base names
        """
        if type(SeligProfile) != str:
            raise(TypeError, "SeligProfile must be a string")
        assert(SeligProfile != ''), "Selig Profile was found to be empty"

        self.Profile = {'SeligProfile': SeligProfile}
        x, z = self._AirfoilPointsSeligFormat(SeligProfile)
        self._points = np.column_stack([x, z])
        self.Curve = self._fitAirfoiltoPoints()
        self._TransformAirfoil()
        return None

    def AddNACA4(self, Naca4Profile, Smoothing=1):
        """Adds a NACA 4 digit airfoil to the current document

        Parameters
        ----------
        Naca4Profile : string
            Naca 4 profile identifier. Should be length 4 string, however
            also accepts negative camber i.e. '-5310' gives a flipped
            camber airfoil (primarily used for box wing)

        Smoothing - int
            TODO: fair airfoil curve

        Returns
        -------
        None
        """
        if type(Naca4Profile) is not str:
            raise TypeError("NACA 4 Profile must be a string")
        assert(len(Naca4Profile) != 0), \
            "Invalid Naca4, empty string found: should be a 4 digit string"
        if Naca4Profile[0] == '-':
            flip_camber = True
            Naca4Profile = Naca4Profile.lstrip('-')
        else:
            flip_camber = False

        assert(len(Naca4Profile) == 4),\
            "Invalid Naca4 '{}': should be 4 digit string".format(Naca4Profile)

        self.Profile = {'Naca4Profile': Naca4Profile}
        MaxCamberPercChord     = int(Naca4Profile[0])
        if flip_camber:
            MaxCamberPercChord *= -1
        MaxCamberLocTenthChord = int(Naca4Profile[1])
        MaxThicknessPercChord  = int(Naca4Profile[2:])

        x, z, xu, zu, xl, zl, RLE = \
            self._NACA4digitPnts(MaxCamberPercChord,
                                 MaxCamberLocTenthChord,
                                 MaxThicknessPercChord)
        self._points = np.column_stack([x, z])
        self.Curve = self._fitAirfoiltoPoints()
#        if 'Smoothing' in locals():
#            self.SmoothingIterations = Smoothing
        self._TransformAirfoil()
        return None

    def AddCRMLinear(self, CRM_Epsilon, Smoothing=1):
        """Linearly interpolate airfoil curve from CRM

        Parameters
        ----------
        CRM_Epsilon : scalar
            Spanwise coordinate at which to sample the CRM airfoil database
            (range between 0 and 1)

        Smoothing : int
            TODO: Airfoil curve smoothing

        Returns
        -------
        None
        """
        CRM_Epsilon = float(CRM_Epsilon)
        assert(CRM_Epsilon >= 0 and CRM_Epsilon <= 1), \
            """Spanwise Interpolation factor Epsilon Out of range\n
            Should be between 0 and 1, found {}""".format(CRM_Epsilon)

        self.Profile = {'CRM_Epsilon': str(CRM_Epsilon)}
        x, z = CRMfoil.CRMlinear(CRM_Epsilon)
        self._points = np.column_stack([x, z])
        self.Curve = self._fitAirfoiltoPoints()
        # TODO: Smoothing..
#        if 'Smoothing' in locals():
#            self.SmoothingIterations = Smoothing
        self._TransformAirfoil()
        return None

#        def _FiniteTE(self):
#            """Fits a finite trailing edge"""
#

    def AddLinear2(self, Eps, Af1, Af2, Eps1=0, Eps2=1):
        """Interpolates the bspline control points fitted between two other
        Airfoil objects.

        Interpolates the x and z values of an Airfoil at spanwise location Eps
        between Af1 (at Eps1) and Af2 (at Eps2). The BSpline Curve is then
        fitted to the resulting points with Airfoil._fitAirfoiltoPoints, and
        transformed to the orientation specified in self.Rotation, self.Twist,
        self.ChordLength and self.LEPoint via the _TransformAirfoil function.

        Parameters
        ----------
        Eps : scalar
            Spanwise coordinate between Eps1 and Eps2

        Af1 : airconics.Airfoil
            The Airfoil located at spanwise location Eps1. Af1.x and Af1.z

        Af2 : airconics.Airfoil
            The Airfoil located at spanwise location Eps2.

        Eps1 : scalar
            Spanwise coordinate location of Airfoil Af1. Expected to range from
            0 (root of a lifting surface) to 1 (tip of a lifting surface)

        Eps2 : scalar
            Spanwise coordinate location of Airfoil Af2. Expected to range from
            0 (root of a lifting surface) to 1 (tip of a lifting surface), and
            also expected to be greater than Eps1
        """
        # Linearly interpolate curve X,Z points at spanwise location epsilon:

        x = Af1.points[:, 0] * (Eps2 - Eps) / (Eps2 - Eps1) + \
            Af2.points[:, 0] * (Eps - Eps1) / (Eps2 - Eps1)
        z = Af1.points[:, 1] * (Eps2 - Eps) + Af2.points[:, 1] * (Eps - Eps1)

        if Eps == Eps1:
            self.Profile = Af1.Profile
        elif Eps == Eps2:
            self.Profile = Af2.Profile
        else:
            self.Profile = {'Interp': (Eps, Af1.Profile, Eps1, Af2.Profile, Eps2)}
        self._points = np.column_stack([x, z])
        self.Curve = self._fitAirfoiltoPoints()
        self._TransformAirfoil()
