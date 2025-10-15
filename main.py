# This file constains the main application code for the assignment
# DO NOT MODIFY THIS FILE, to complete the assignment you need
# only correctly modify the files in the ./assignment directory
import polyscope as ps
import polyscope.imgui as psim
import warp as wp
import torch
import argparse 
from assignment import *
from given import *
from utils import *
from simulator import *

wp.init() #initialize warp

sim = None

#Global variables for UI
simulating = False

def simulation_init():

   sim.setup_simulation()

#callback to run one simulation step
def simulation_step():
    sim.step()
    
   

def ui_callback():
    global simulating,q, qm1
    # start top simulation button with text box for end time and dt
    #checkbox for write to USD
    changed_sim, simulating = psim.Checkbox("Start Simulation", simulating)

    #button to run one step of the simulation 
    if psim.Button("Step"):
        sim.step()
        #update the vertices in the mesh
        for i in range(len(sim.objects)):
            ps.get_surface_mesh("mesh"+"_"+str(i)).update_vertex_positions(transform_mesh(sim.objects[i][1].vertices, sim.q[i*12:(i+1)*12]).detach().cpu().numpy())

    #reset button
    if psim.Button("Reset Simulation"):
        print("Resetting Simulation")
        sim.reset()
        for i in range(len(sim.objects)):
            ps.get_surface_mesh("mesh"+"_"+str(i)).update_vertex_positions(transform_mesh(sim.objects[i][1].vertices, sim.q[i*12:(i+1)*12]).detach().cpu().numpy())

        
    
    if simulating:
        sim.step()
        #update the vertices in the mesh
        for i in range(len(sim.objects)):
            ps.get_surface_mesh("mesh"+"_"+str(i)).update_vertex_positions(transform_mesh(sim.objects[i][1].vertices, sim.q[i*12:(i+1)*12]).detach().cpu().numpy())

if __name__ == "__main__":
    #check arguments, load approriate model and test configuration
    parser = argparse.ArgumentParser(description="Physics-Based Animation Assignment program")
    parser.add_argument("--scene", help="Path to the scene file")
    parser.add_argument("--usd_output", help="Path to usd output directory, requires num_steps parameters")
    parser.add_argument("--num_steps", help="Number of steps to simulate", type=int)
    parser.add_argument("--device", help="Device to use", type=str, default="cpu")
    args = parser.parse_args()

    if args.device == "cpu":
        sim_dtype = torch.float64
        sim_device = "cpu"
    elif args.device == "cuda":
        sim_dtype = torch.float64
        sim_device = "cuda"

    sim_device_wp = wp.device_from_torch(sim_device)
    wp.set_device(sim_device_wp)

    if args.scene:
        #check for pinned vertices and build BC projection matrix
       sim = Simulator(args.scene, sim_device, sim_dtype)
    else:
        print("No scene or mesh file provided")
        exit()
        
    simulation_init()

    if args.usd_output:
        if args.num_steps: 
            print("Writing to USD")
          
            w = USDMultiMeshWriter(args.usd_output, fps=1/sim.dt, stage_up="Y", sim_up="Y", write_velocities=True)
            w.open()

            # Register two objects (once)
            for i in range(len(sim.objects)):
                face_counts = 3*torch.ones(sim.objects[i][1].triangles.shape[0], dtype=torch.int32, device=sim.sim_device)
                w.add_mesh("Obj"+"_"+str(i), face_counts=face_counts, face_indices=sim.objects[i][1].triangles.reshape((-1,)).detach().cpu().numpy(), num_points=sim.objects[i][1].vertices.shape[0])
                
            for k in range(args.num_steps):
                print("Step "+str(k))
                sim.step()
                for i in range(len(sim.objects)):
                    w.write_points("Obj"+"_"+str(i), sim.get_deformed_vertices(i).reshape((-1,3)).detach().cpu().numpy(), timecode=k)

            w.close()
                        
            exit()
        else:
            print("Num steps not provided, skipping USD output")
            exit()

    #load mesh into polyscope
    ps.init()
   
    #launch polyscope and display surface mesh
    for i in range(len(sim.objects)):
        ps.register_surface_mesh("mesh"+"_"+str(i), transform_mesh(sim.objects[i][1].vertices, sim.q[i*12:(i+1)*12]).detach().cpu().numpy(), sim.objects[i][1].triangles.detach().cpu().numpy())

    ps.set_user_callback(ui_callback)

    #turn off polyscope ground plane
    ps.set_ground_plane_mode("none")
    ps.show()

