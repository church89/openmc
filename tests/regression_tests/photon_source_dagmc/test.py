from math import pi

import numpy as np
import openmc
import openmc.lib

from tests.testing_harness import PyAPITestHarness


class SourceTestHarness(PyAPITestHarness):
    def _build_inputs(self):
        mat = openmc.Material(name="mat")
        mat.set_density('g/cm3', 0.998207)
        mat.add_element('H', 0.111894)
        mat.add_element('O', 0.888106)
        materials = openmc.Materials([mat])
        materials.export_to_xml()

        assert(openmc.lib._dagmc_enabled())
        h5m_filepath = 'geom.h5m'
        dag_univ = openmc.DAGMCUniverse(h5m_filepath)
        geometry = openmc.Geometry(root=dag_univ)
        geometry.export_to_xml()

        source = openmc.Source()
        source.space = openmc.stats.Point((0, 0, 0))
        source.angle = openmc.stats.Isotropic()
        source.energy = openmc.stats.Discrete([10.0e6], [1.0])
        source.particle = 'photon'

        settings = openmc.Settings()
        settings.particles = 10000
        settings.batches = 1
        settings.photon_transport = True
        settings.electron_treatment = 'ttb'
        settings.cutoff = {'energy_photon' : 1000.0}
        settings.run_mode = 'fixed source'
        settings.source = source
        settings.export_to_xml()

        particle_filter = openmc.ParticleFilter('photon')
        tally = openmc.Tally()
        tally.filters = [particle_filter]
        tally.scores = ['flux', '(n,gamma)']
        tallies = openmc.Tallies([tally])
        tallies.export_to_xml()


def test_photon_source():
    harness = SourceTestHarness('statepoint.1.h5')
    harness.main()
