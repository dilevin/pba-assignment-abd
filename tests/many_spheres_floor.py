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
        
       
        floor = ObjectConfig(
            geometry_type="rigid",
            mesh=str(get_data_directory() / "slab.obj"),
            initial_velocity=[0.0, 0.0, 0.0],  # Moving to the right
            transform=[
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, -1.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0]
            ],
            material=tet_material,
            pinned_dofs=[0]
        )
        
        objects = []

        #make 20 cubes in a vertical stack but staggered in the x direction and add them to the seen with the fixed floor
        for i in range(10):
            sphere = ObjectConfig(
                geometry_type="rigid",
                mesh=str(get_data_directory() / "sphere.obj"),
                initial_velocity=[0.0, 0.0, 0.0],  # Moving to the right
               
                transform=[
                    [1.0, 0.0, 0.0, ((i%2)- 0.5)*0.1],
                    [0.0, 1.0, 0.0, i*0.5],
                    [0.0, 0.0, 1.0, ((i%4)- 0.5)*0.1],
                    [0.0, 0.0, 0.0, 1.0]
                ],
                material=tet_material
            )

            objects.append(sphere)

        objects.append(floor)
            
        # Initialize simulation configuration
        super().__init__(
            objects=objects,
            timestep=0.01,
            gravity=[0.0, -9.8, 0.0],
            contact_stiffness=1e4,
            contact_threshold=1e-2,
            solver_settings=solver_settings
        )
