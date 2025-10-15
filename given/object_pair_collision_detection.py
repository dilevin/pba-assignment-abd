from sympy.core.logic import Or
import warp as wp
import torch 

# Collision detection result structure
@wp.struct
class CollisionResult:
    ref_pos_1: wp.vec3d #vertex position in undeformed space of object 1
    ref_pos_2: wp.vec3d #vertex position in undeformed space of object 2
    closest_point: wp.vec3d  # closest point on mesh 2
    contact_normal: wp.vec3d  # contact normal
    is_valid: wp.int32  # flag indicating if contact is valid
    distance: wp.float64  # signed distance to mesh 2
    object1_id: wp.int32  # ID of object 1 (querying object)
    object2_id: wp.int32  # ID of object 2 (target object)

@wp.kernel
def object_pair_collision_detection(
    # Input mesh data for object 1 (querying vertices)
    mesh1_vertices: wp.array(dtype=wp.vec3d),
    
    # Input mesh data for object 2 (target mesh)
    mesh2_id: wp.uint64,  # Warp mesh ID for object 2
    
    # Global generalized coordinates (affine transforms for all objects)
    global_q: wp.array(dtype=wp.vec(length=12,dtype=wp.float64)),
    
    # Object IDs for collision results
    object1_object_id: wp.int32,  # object ID for object 1
    object2_object_id: wp.int32,  # object ID for object 2
    
    # Collision detection parameters
    max_distance: wp.float64,
    epsilon: wp.float64,
    
    # Output arrays
    collision_results: wp.array(dtype=CollisionResult)
):
    # Get thread index (one thread per vertex in mesh 1)
    tid = wp.tid()
    
    # Check bounds
    if tid >= mesh1_vertices.shape[0]:
        return
    
    # Extract affine transform for object 1 (3x4 matrix stored as 12 doubles)
    # q format: [R00, R01, R02, tx, R10, R11, R12, ty, R20, R21, R22, tz]
    q1_start = object1_object_id
    A1 = wp.mat33d(
        global_q[q1_start][0], global_q[q1_start][1], global_q[q1_start][2],
        global_q[q1_start][4], global_q[q1_start][5], global_q[q1_start][6], 
        global_q[q1_start][8], global_q[q1_start][9], global_q[q1_start][10]
    )

    t1 = wp.vec3d(global_q[q1_start][3], global_q[q1_start][7], global_q[q1_start][11])
    
    # Transform vertex from object 1's local space to world space
    local_vertex = mesh1_vertices[tid]
    world_vertex = A1 @ local_vertex + t1
    
    # Extract affine transform for object 2
    q2_start = object2_object_id
    A2 = wp.mat33d(
        global_q[q2_start][0], global_q[q2_start][1], global_q[q2_start][2],
        global_q[q2_start][4], global_q[q2_start][5], global_q[q2_start][6],
        global_q[q2_start][8], global_q[q2_start][9], global_q[q2_start][10]
    )
    t2 = wp.vec3d(global_q[q2_start][3], global_q[q2_start][7], global_q[q2_start][11])
    
    # Transform world vertex to object 2's local space for query
    A2_inv = wp.inverse(A2) 
    local_query_point = A2_inv * (world_vertex - t2)
    
    # Query closest point on mesh 2 using mesh_query_point_sign_normal
    query_result = wp.mesh_query_point_sign_normal(
        id=mesh2_id,
        point=wp.vector(wp.float32(local_query_point[0]), wp.float32(local_query_point[1]), wp.float32(local_query_point[2]), length=3,dtype=wp.float32),
        max_dist=wp.float32(max_distance),
        epsilon=wp.float32(epsilon)
    )
    
    # Transform results back to world space
    world_closest_point = A2 * wp.vec3d(wp.mesh_eval_position(mesh2_id, query_result.face, query_result.u, query_result.v)) + t2
    world_normal = wp.transpose(A2_inv)*wp.vec3d(wp.mesh_eval_face_normal(mesh2_id, query_result.face))
    
    # Store collision result
    result = CollisionResult()
    result.ref_pos_1 = local_vertex 
    result.ref_pos_2 = wp.vec3d(wp.mesh_eval_position(mesh2_id, query_result.face, query_result.u, query_result.v))
    result.closest_point = world_closest_point
    result.contact_normal = world_normal
    result.distance = wp.length(world_vertex - world_closest_point) # I want positive distance when there's penetration
    result.object1_id = object1_object_id
    result.object2_id = object2_object_id
    
    result.is_valid = wp.int32(1) if (result.distance <= epsilon  and query_result.sign < 0) else wp.int32(0)
    
    collision_results[tid] = result

# Helper function to launch the collision detection kernel
def detect_collisions(
    collision_results: wp.array(dtype=CollisionResult),
    current_num_contacts: torch.Tensor,
    collision_buffer: wp.array(dtype=CollisionResult),
    mesh1_vertices: wp.array(dtype=wp.vec3d), 
    mesh2_id: wp.uint64,
    global_q: wp.array(dtype=wp.vec(length=12,dtype=wp.float64)),
    object1_object_id: wp.int32,
    object2_object_id: wp.int32,
    max_distance: wp.float64 = 1.0,
    epsilon: wp.float64 = 1e-3
):
    """
    Launch collision detection between two objects.
    
    Args:
        mesh1_vertices: Vertices of object 1 (querying mesh)
        mesh1_triangles: Triangles of object 1
        mesh1_id: Warp mesh ID for object 1
        mesh2_vertices: Vertices of object 2 (target mesh) 
        mesh2_triangles: Triangles of object 2
        mesh2_id: Warp mesh ID for object 2
        global_q: Global generalized coordinates array
        object1_start_idx: Starting index in global_q for object 1's transform
        object2_start_idx: Starting index in global_q for object 2's transform
        object1_object_id: Object ID for object 1 (stored in collision results)
        object2_object_id: Object ID for object 2 (stored in collision results)
        max_distance: Maximum distance for mesh queries
        epsilon: Small value for distance comparisons
        
    Returns:
        wp.array: Array of CollisionResult structs
    """
    num_vertices = mesh1_vertices.shape[0]
    
    wp.launch(
        kernel=object_pair_collision_detection,
        dim=num_vertices,
        inputs=[
            mesh1_vertices,
            mesh2_id,
            global_q, 
            object1_object_id, object2_object_id,
            max_distance, epsilon, collision_buffer
        ]
    )
    

    @wp.kernel
    def reduce_collision_buffer(num_collisions: wp.array(dtype=wp.int32), collision_results: wp.array(dtype=CollisionResult), collision_buffer: wp.array(dtype=CollisionResult)):
        tid = wp.tid()

        if tid >= collision_buffer.shape[0] or collision_buffer[tid].is_valid == 0:
            return #do nothing, we're out of bounda

        idx = wp.atomic_add(num_collisions, 0, 1) #add one to num_collisions and store prev value which is index for this collision into results array

        if idx < collision_results.shape[0]:
            collision_results[idx] = collision_buffer[tid]


    #collision buffer stores a contact for each vertex in mesh 1the collision buffer
    #some of those contacts are invalid, so we need to reduce the collision buffer into the collision results
    #using a fast parallel reduction scheme
    #valid contacts are marked in the collision buffer using the is_valid flag in the CollisionResult struct
    wp.launch(reduce_collision_buffer, dim=collision_buffer.shape[0], inputs=[current_num_contacts, collision_results, collision_buffer])

    #step one is to compute indices for valid contacts by  computing  the cumuative sum of the is valid flags
    #step two is to insert the valid contacts into tne appropriate positions in collision_results and return the new number of contacts
    #step three is to return the new number of contacts
    return current_num_contacts.item()


