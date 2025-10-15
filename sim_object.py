import torch
from utils import *
import igl

#This is an affine-body-dynamics object
#standard form of q is a 3x4 matrix, vectorized form is row flattened matrix as a 12x1 vector
class SimObject:

    def __init__(self, config: ObjectConfig, sim_device, sim_dtype):

        
        self.sim_thin_shell = True

        if config.geometry_type == "rigid":
            self.vertices, _, _, self.triangles, _, _ = igl.readOBJ(config.mesh)
            self.sim_thin_shell = False
        else:
            print("Only rigid objects supports")
            exit()

        #load transform matrix if it exists, otherwise use identity
        if config.transform:
            self.obj_transform = torch.Tensor(config.transform).to(sim_device).to(sim_dtype)
        else:
            self.obj_transform = torch.eye(4,4, dtype=sim_dtype, device=sim_device)

        if config.initial_velocity:
            self.obj_initial_velocity = torch.Tensor(config.initial_velocity).to(sim_device).to(sim_dtype)
        else:
            self.obj_initial_velocity = torch.zeros(3, dtype=sim_dtype, device=sim_device)

        if config.pinned_dofs:
            if isinstance(config.pinned_dofs, list):
                self.pinned_dofs = torch.tensor(config.pinned_dofs).to(sim_device) 
            else:
                self.pinned_dofs = config.pinned_dofs
        else:
            self.pinned_dofs = None 

        #convert everything to torch tensors
        self.vertices = torch.tensor(self.vertices, dtype=sim_dtype, device=sim_device)
        self.triangles = torch.tensor(self.triangles, dtype=torch.int32, device=sim_device)

        self.rho = config.material.density
        self.params = torch.tensor([config.material.youngs, config.material.poissons], dtype=sim_dtype, device=sim_device)

    def num_dofs(self):
        return 1 #just one dof per object

    def dof_block_size(self):
        return 12 #one affine DOF per object
    
    def ele_block_dim(self):
        return 1 #each  object IS a single element

    def set_initial_dofs(self, q: torch.Tensor, qm1: torch.Tensor,dt: float):
        q[:] = self.obj_transform[0:3,:].reshape((-1,))
        dx = self.obj_transform[0:3,3]  - dt*self.obj_initial_velocity
        qm1[:] = torch.concat((self.obj_transform[0:3,0:3], dx.unsqueeze(1)),dim=1).reshape((-1,))

    def get_deformed_vertices(self, q: torch.Tensor):
        return self.vertices @ q.reshape(3,4)[0:3,0:3].T + q.reshape(3,4)[0:3,3].T


