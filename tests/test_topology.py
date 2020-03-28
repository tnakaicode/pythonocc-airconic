# -*- coding: utf-8 -*-
#
# Tests for airconics topology class. Note that no geometry is required for
# most of these tests, are therefore the geometry construction is skipped.
#
# @Author: p-chambers
# @Date:   2016-07-21 16:25:37
# @Last Modified by:   p-chambers
# @Last Modified time: 2016-07-25 14:19:00
import pytest
from airconics.topology import Topology
from airconics.fuselage_oml import Fuselage
from airconics.engine import Engine
from airconics.liftingsurface import LiftingSurface
from OCC.Core.gp import gp_Ax2

@pytest.fixture(params=[
    # a list of topologies and expected flattened lisp expressions
    ('conventional', 'E(L, |L, L(P))'),
    ('thunderbolt_a10', 'E(|P, L(L), L)'),
    ('predator', 'E(P, L, |L, L)'),
    ('proteus', 'E(|P, L, L(E(L, L, L)))')
])
def example_topos(request):
    """Return both the topology object and the resulting string for a set of
    topologies"""
    topo_type = request.param[0]
    if topo_type == 'conventional':
        # Create mock components, without generating any geometry
        fus = Fuselage(construct_geometry=False)
        fin = LiftingSurface(construct_geometry=False)
        tailplane = LiftingSurface(construct_geometry=False)
        mirror_pln = gp_Ax2()
        wing = LiftingSurface(construct_geometry=False)
        engine = Engine(construct_geometry=False)

        # For now we must manually add parts and affinities
        topo = Topology()
        topo.AddPart(fus, 'Fuselage', 3)
        topo.AddPart(fin, 'fin', 0)
        topo.AddPart(mirror_pln, 'mirror_pln', 0)
        topo.AddPart(tailplane, 'tailplane', 0)
        topo.AddPart(wing, 'wing', 1)
        topo.AddPart(engine, 'engine', 0)

    if topo_type == 'thunderbolt_a10':
        fus = Fuselage(construct_geometry=False)
        mirror_pln = gp_Ax2()
        engine = Engine(construct_geometry=False)
        wing = LiftingSurface(construct_geometry=False)
        tailplane = LiftingSurface(construct_geometry=False)
        tail_fin = LiftingSurface(construct_geometry=False)

        topo = Topology()
        topo.AddPart(fus, 'Fuselage', 3)
        topo.AddPart(mirror_pln, 'mirror', 0)
        topo.AddPart(engine, 'powerplant', 0)
        topo.AddPart(tailplane, 'Tailplane', 1)
        topo.AddPart(tail_fin, "Tail fin", 0)
        topo.AddPart(wing, "wing", 0)


    if topo_type == 'predator':
        # Create mock components, without generating any geometry
        fus = Fuselage(construct_geometry=False)
        engine = Engine(construct_geometry=False)
        fin = LiftingSurface(construct_geometry=False)
        mirror_pln = gp_Ax2()
        wing = LiftingSurface(construct_geometry=False)
        Vfin = LiftingSurface(construct_geometry=False)

        # For now we must manually add parts and affinities
        topo = Topology()
        topo.AddPart(fus, 'Fuselage', 4)
        topo.AddPart(engine, 'engine', 0)
        topo.AddPart(fin, 'fin', 0)
        topo.AddPart(mirror_pln, 'mirror_pln', 0)
        topo.AddPart(wing, 'wing', 0)
        topo.AddPart(Vfin, 'V-Fin', 0)

    if topo_type == 'proteus':
        fus = Fuselage(construct_geometry=False)
        mirror_pln = gp_Ax2()
        engine = Engine(construct_geometry=False)
        wing = LiftingSurface(construct_geometry=False)
        wing_in = LiftingSurface(construct_geometry=False)
        tailplane = LiftingSurface(construct_geometry=False)
        pod = Fuselage(construct_geometry=False)
        finup = LiftingSurface(construct_geometry=False)
        findown = LiftingSurface(construct_geometry=False)
        wing_out = LiftingSurface(construct_geometry=False)


        topo = Topology()
        topo.AddPart(fus, 'Fuselage', 3)
        topo.AddPart(mirror_pln, 'mirror', 0)
        topo.AddPart(engine, 'powerplant', 0)
        topo.AddPart(wing, "wing", 0)
        topo.AddPart(wing_in, "TP/inbbd wing", 1)
        topo.AddPart(pod, 'Pod/tail boom', 3)
        topo.AddPart(wing_out, "outbd wing", 0)
        topo.AddPart(finup, "Fin (up)", 0)        
        topo.AddPart(findown, "Fin (dwn)", 0)

    return topo, request.param[1]


@pytest.mark.xfail
def test_topology_validation():
    """Test that correct topologies are allowed, and invalid topologies raise
    an error"""
    raise NotImplementedError


def test_topology_str(example_topos):
    """Test that the overridden __str__ method produces the correct LISP tree
    for a few example topology trees
    """

    # Add object, name and affinity to the topology
    topo, expected_string = example_topos

    # Pytest should print out the two strings here if different (use -v flag)
    assert(str(topo) == expected_string)


@pytest.mark.xfail()
def test_topology_graphviz_dot():
    raise NotImplementedError
