"""
Gradient of Elastic Energy for Affine Body Dynamics

This module computes the gradient of elastic energy with respect to the configuration
parameters q for each object in the simulation. The elastic energy is based on the
Green strain tensor and measures deformation from the rest configuration.

The elastic energy function is:
    E = (k/2) * tr(E²)
where:
    E = (1/2) * (F^T * F - I) is the Green strain tensor
    F is the deformation gradient matrix (3x3)
    k is the elastic stiffness constant (1e8)

Parameters:
    g_out (wp.array): Output array storing gradient vectors (12-DOF per object)
    q (wp.array): Configuration array containing deformation gradients (12-DOF per object)
    volumes (wp.array): Volume array for each object

Configuration Format:
    Each object's q vector contains 12 elements representing the 3x4 transformation matrix:
    [F_00, F_01, F_02, t_0, F_10, F_11, F_12, t_1, F_20, F_21, F_22, t_2]
    where F is the 3x3 deformation gradient and t is the translation vector.

The gradient computation involves taking derivatives of the strain energy with respect
to each component of the deformation gradient F, resulting in a 12-dimensional gradient
vector for each object.
"""

import warp as wp

@wp.kernel
def denergy_dq(g_out: wp.array(dtype=wp.vec(12,dtype=wp.float64)), q: wp.array(dtype=wp.vec(length=12,dtype=wp.float64)), volumes: wp.array(dtype=wp.float64)):
    
    # Each thread processes a single object
    obj_id = wp.tid() 
    
    # TODO: Implement the gradient of elastic energy computation
    
    grad_out = wp.vector(length=12, dtype=wp.float64)

    g_out[obj_id] = grad_out