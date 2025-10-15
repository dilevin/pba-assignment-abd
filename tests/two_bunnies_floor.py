"""
Two tetrahedra scene configuration.
Two tets with one moving and one pinned for testing.
"""

from data import get_data_directory
from utils import SimulationConfig, ObjectConfig, MaterialConfig, SolverConfig

class BunnyConfig(SimulationConfig):
    """Two tetrahedra scene configuration."""
    
    def __init__(self):
        # Material for both tets
        tet_material = MaterialConfig(
            density=1000.0,
            material_model="NeoHookean",
            youngs=1e8,  # 100 kPa
            poissons=0.3,
        )
        
        # Solver settings
        solver_settings = SolverConfig(
            max_iterations=200,
            tolerance=1e-3
        )
        
       
        bunny = ObjectConfig(
            geometry_type="rigid",
            mesh=str(get_data_directory() / "bunny.obj"),
            initial_velocity=[0.0, 0.0, 0.0],  # Moving to the right
            transform=[
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 2.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0]
            ],
            material=tet_material
        )

        bunny_two = ObjectConfig(
            geometry_type="rigid",
            mesh=str(get_data_directory() / "bunny.obj"),
            initial_velocity=[0.0, 0.0, 0.0],  # Moving to the right
            transform=[
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 3.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0]
            ],
            material=tet_material
        )

        floor = ObjectConfig(
            geometry_type="rigid",
            mesh=str(get_data_directory() / "slab.obj"),
            initial_velocity=[0.0, 0.0, 0.0],  # Moving to the right
            transform=[
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0]
            ],
            material=tet_material,
            pinned_dofs=[0]
        )
        
        # Initialize simulation configuration
        super().__init__(
            objects=[floor, bunny, bunny_two],
            timestep=0.01,
            gravity=[0.0, -9.8, 0.0],
            contact_stiffness=1e4,
            contact_threshold=1e-2,
            solver_settings=solver_settings
        )
