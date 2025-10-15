import torch
from assignment import *
from given import *
from utils import *
import igl
import warp as wp
import warp.sparse as wsp
from sim_object import *

class Simulator:

    time = 0.0 #current simulation time
    dt = 0.1 #simulation time step
    gravity = None #torch.tensor([0.0, -9.8, 0.0], dtype=sim_dtype, device=sim_device) #default gravitational acceleration
    Mass_matrix = None
    H_energy = None
    H_contact = None #BSR sparse contact hessian
    g_contact = None  #contact gradient 
    g_gravity = None 
    grad_energy = None
    Pinned_matrix = None
    contact_list = None #I'm gonna store contact pairs in here 
    elastic_energy = None

    def __init__(self, config: str, sim_device: str, sim_dtype: str):
        self.config = load_config(config)
        self.objects = []
        self.sim_device = sim_device
        self.sim_dtype = sim_dtype

        #simulator parameters
        self.dt = self.config.timestep
        self.contact_stiffness = self.config.contact_stiffness
        self.contact_threshold = self.config.contact_threshold
        self.gravity = torch.Tensor(self.config.gravity)
        self.max_contact_pairs = self.config.max_contact_pairs
        self.contact_list = wp.array(shape=(self.max_contact_pairs, ), dtype=CollisionResult, device=self.sim_device)
        self.current_num_contacts = torch.tensor([0], dtype=torch.int32, device=self.sim_device)
        self.elastic_energy = torch.tensor([0.0], dtype=self.sim_dtype, device=self.sim_device)
        #load and setup every objet from the config
        obj_index = 0
        for obj in self.config.objects:
            self.objects.append((obj_index,SimObject(obj, sim_device, sim_dtype)))
            obj_index += 1

        #generate warp meshes for each object 
        self.mesh_dict = {} #mesh diectionary because I guess you can't do anything else 
        
        for i in range(len(self.objects)):
           self.mesh_dict[i] = wp.Mesh(points=wp.from_torch(self.objects[i][1].vertices.reshape(-1,3).to(torch.float32),dtype=wp.vec3f), indices=wp.from_torch(self.objects[i][1].triangles.reshape(-1,),dtype=wp.int32))

        #find max number of vertices in any object
        self.max_vertices = torch.Tensor([len(obj[1].vertices) for obj in self.objects]).max()
        self.obj_pair_contact_buffer = wp.array(shape=(self.max_vertices,), dtype=CollisionResult, device=self.sim_device)

    def setup_simulation(self):

        #global q, qm1,E_mat, a_gravity,tet_volumes, Mass_matrix, dXinv, grad_energy, H_blk, H_energy, obj_transform, obj_initial_velocity


        print("Initializing simulation")
        #init quantities needed for simulation
       
        #how many dofs do I have ? 
        self.total_dofs = sum([obj[1].num_dofs() for obj in self.objects])
        self.dof_block_size = self.objects[0][1].dof_block_size()

        print("Initializing Global variables")
        #make global gravity vector for the simulation
        self.g_gravity = torch.zeros((len(self.objects),3,4),dtype=self.sim_dtype, device=self.sim_device)
        self.g_gravity[:, :, 3] = self.gravity
        self.g_gravity = self.g_gravity.reshape((-1,))

        #precompute mass matrix for the scene 
        self.Mass_matrix = block_diagonal_identity(wp.mat((12,12), dtype=wp.float64), 1, 1, self.total_dofs, self.sim_device, self.sim_dtype)
        self.H_energy = block_diagonal_identity(wp.mat((12,12), dtype=wp.float64), 1, 1, self.total_dofs, self.sim_device, self.sim_dtype)
        self.g_energy = torch.zeros((self.total_dofs*self.dof_block_size,), dtype=self.sim_dtype, device=self.sim_device)
        self.q = torch.zeros((self.total_dofs*self.dof_block_size,), dtype=self.sim_dtype, device=self.sim_device)
        self.qm1 = self.q.clone()
        self.volumes = torch.zeros((len(self.objects),), dtype=self.sim_dtype, device=self.sim_device)
        self.global_pinned_dofs = torch.Tensor([]).to(self.sim_dtype).to(self.sim_device)
        self.g_contact = torch.zeros_like(self.q)
        self.H_contact= wsp.bsr_zeros(cols_of_blocks=len(self.objects), rows_of_blocks = len(self.objects), block_type=wp.mat((12,12), dtype=wp.dtype_from_torch(self.q.dtype)), device=wp.device_from_torch(self.q.device))
        self.contact_indices = torch.zeros((4*self.max_contact_pairs, 2), dtype=torch.int32, device=self.sim_device)
        self.contact_hessian_values = torch.zeros((4*self.max_contact_pairs, 12, 12), dtype=self.sim_dtype, device=self.sim_device)

        #fill in mass matrix 
        for i in range(len(self.objects)):

            #compute mass matrix blocks
            indexed_vertices = wp.indexedarray(data=wp.from_torch(self.objects[i][1].vertices, dtype=wp.vec3d), indices=wp.from_torch(self.objects[i][1].triangles.reshape(-1,)))
            wp.launch(mass_matrix_abd_object, dim=self.objects[i][1].triangles.shape[0], \
                inputs=[wp.to_torch(self.Mass_matrix.values)[i,:,:], wp.from_torch(self.volumes[i:(i+1)],dtype=wp.float64), indexed_vertices, self.objects[i][1].rho])

            #initialize global q and qm1
            self.objects[i][1].set_initial_dofs(self.q[i*12:(i+1)*12], self.qm1[i*12:(i+1)*12], self.dt)

            #update pinned dof array
            if self.objects[i][1].pinned_dofs is not None:
                self.global_pinned_dofs = torch.cat([self.global_pinned_dofs, self.objects[i][1].pinned_dofs + i])
            
        
        #setup scene fixed DOF projection matrix
        self.P_pinned = fixed_dof_projection(None, self.q.reshape((-1,12)), self.global_pinned_dofs)

    #reset simulation objects to initial states
    def reset(self):
        
        for i in range(len(self.objects)):
            #initialize global q and qm1
            self.objects[i][1].set_initial_dofs(self.q[i*12:(i+1)*12], self.qm1[i*12:(i+1)*12], self.dt)

    #take one simulation time step
    def step(self):
        
        num_contacts = 0
        num_contact_objects = 0
        self.current_num_contacts[0] = 0  #reset curret number of contacts 


        #find contac pairs between objects
        for obj_a in range(len(self.objects)):
            for obj_b in range(len(self.objects)):
                if obj_a != obj_b:
                    old_num_contacts = num_contacts
                    num_contacts = detect_collisions(self.contact_list, self.current_num_contacts, self.obj_pair_contact_buffer, \
                        self.objects[obj_a][1].vertices, self.mesh_dict[obj_b].id, self.q.reshape((-1,12)), obj_a, obj_b, 0.2, self.contact_threshold)

                    if num_contacts > old_num_contacts:
                        #keep track of sparse matrix contact structure here
                        #if there is a contact between obj_a and obj_b I need to add (obj_a, obj_a), (obj_b, obj_b), (obj_a, obj_b) and (obj_b, obj_a) to the contact hessian sparsity pattern
                        self.contact_indices[num_contact_objects,0] = obj_a
                        self.contact_indices[num_contact_objects,1] = obj_a 
                        self.contact_indices[num_contact_objects+1,0] = obj_b
                        self.contact_indices[num_contact_objects+1,1] = obj_b
                        self.contact_indices[num_contact_objects+2,0] = obj_a
                        self.contact_indices[num_contact_objects+2,1] = obj_b
                        self.contact_indices[num_contact_objects+3,0] = obj_b
                        self.contact_indices[num_contact_objects+3,1] = obj_a
        
                        num_contact_objects += 4
                        
       
       

        #big global solve for everything
        #global q, qm1, q_pred, a_gravity,Mass_matrix,  grad_energy, params, H_blk, H_energy, dt, Pinned_matrix
        self.q_pred = (self.q + (self.q-self.qm1) + self.dt*self.dt*self.g_gravity).detach()

        #define lambda functions for  energy, gradient and hessian
        
        #build contact list between objects 
        def energy_func(q):
            self.elastic_energy[0] = 0.0
            wp.launch(elastic_energy, dim=len(self.objects), \
                inputs=[wp.from_torch(self.elastic_energy, dtype=wp.float64), wp.from_torch(q.reshape((-1,12)), dtype=wp.vec(length=12,dtype=wp.float64)), wp.from_torch(self.volumes, dtype=wp.float64)], \
                device=self.sim_device)
            
            wp.launch(penalty_spring, dim=num_contacts, inputs=[wp.from_torch(self.elastic_energy, dtype=wp.float64), wp.from_torch(q.reshape((-1,12)), dtype=wp.vec(length=12,dtype=wp.float64)), self.contact_list, wp.float64(self.contact_stiffness)])
          

            return self.elastic_energy[0].item()

        def gradient_func(q):
            wp.launch(denergy_dq, dim=len(self.objects), \
                inputs=[wp.from_torch(self.g_energy.reshape((-1,12)),dtype=wp.vec(length=12,dtype=wp.float64)), wp.from_torch(q.reshape((-1,12)), dtype=wp.vec(length=12,dtype=wp.float64)), wp.from_torch(self.volumes, dtype=wp.float64)], \
                device=self.sim_device)

            #fill in contact gradients
            self.g_contact.zero_() #zero out old contact gradients
            
            wp.launch(dpenalty_spring_dq, dim=num_contacts, inputs=[wp.from_torch(self.g_contact.reshape((-1,12)),dtype=wp.vec(length=12,dtype=wp.float64)), wp.from_torch(q.reshape((-1,12)), dtype=wp.vec(length=12,dtype=wp.float64)), self.contact_list, wp.float64(self.contact_stiffness)])
            return self.Mass_matrix@wp.from_torch(q - self.q_pred) + (wp.from_torch(self.g_energy.reshape((-1,12)),dtype=wp.vec(length=12,dtype=wp.float64))+ wp.from_torch(self.g_contact.reshape((-1,12)),dtype=wp.vec(length=12,dtype=wp.float64)))*wp.float64(self.dt*self.dt) 
        
        def hessian_func(q):
            wp.launch(d2energy_dq2, dim=len(self.objects), \
                inputs=[wp.to_torch(self.H_energy.values), wp.from_torch(q.reshape((-1,12)), dtype=wp.vec(length=12,dtype=wp.float64)), wp.from_torch(self.volumes, dtype=wp.float64)], \
                device=self.sim_device)
            
            
            self.contact_hessian_values.zero_()
            #fill in contact hessian 
            wp.launch(d2penalty_spring_dq2, dim=num_contacts, inputs=[self.contact_hessian_values, wp.from_torch(self.q.reshape((-1,12)), dtype=wp.vec(length=12,dtype=wp.float64)), self.contact_list, wp.float64(self.contact_stiffness)])
            

            #allocate sparsity pattern for contact hessian (assuming this doesn't change during newton iterations)
            wsp.bsr_set_from_triplets(self.H_contact, wp.from_torch(self.contact_indices[0:num_contact_objects,0], dtype=wp.int32), wp.from_torch(self.contact_indices[0:num_contact_objects,1], dtype=wp.int32), wp.from_torch(self.contact_hessian_values[0:num_contact_objects,:,:], dtype=wp.mat((12,12), dtype=wp.dtype_from_torch(self.sim_dtype))))


            
            return self.Mass_matrix + self.dt*self.dt*(self.H_energy + self.H_contact)
        

        self.qm1 = self.q.detach().clone()

        #compute new position
        newtons_method(self.q, energy_func, gradient_func, hessian_func, self.P_pinned)
    
    def get_deformed_vertices(self, obj_id: int):
        return self.objects[obj_id][1].get_deformed_vertices(self.q[obj_id*12:(obj_id+1)*12])

    
   
