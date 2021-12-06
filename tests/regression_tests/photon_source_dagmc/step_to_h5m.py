###############################################################################
# Converting step files to h5m file to be read by openmc

# Note, the fork below of the cad_to_h5m repo needs to be used for this script to work
# https://github.com/LukeLabrie/cad_to_h5m/tree/transforms_and_graveyards
###############################################################################


from cad_to_h5m import cad_to_h5m
import numpy as np

#scaling factor
scale = 1.

cad_to_h5m(h5m_filename= 'geom.h5m',
            cubit_path="/opt/Coreform-Cubit-2021.5/bin/",
            files_with_tags=[{"material_tag": "mat",
                             "cad_filename": "geom.step",
                             "transforms":{'scale':scale}},
                            ],
                        faceting_tolerance = 1e-3,
                        surface_reflectivity_name = "vacuum",
                        graveyard = 1e11*scale
                        )
