"""
Kinematic Jacobian for Affine Body Dynamics

This module computes the kinematic jacobian matrix that relates the configuration
parameters q to the world position of a point on an object. The jacobian is
essential for computing gradients and Hessians of energy functions.

For an affine body with configuration q = [F_00, F_01, F_02, t_0, F_10, F_11, F_12, t_1, F_20, F_21, F_22, t_2],
the world position of a point X in local coordinates is:
    x = F * X + t
where F is the 3x3 deformation gradient and t is the translation vector.

The kinematic jacobian J relates the configuration to the world position:
    x = J * q
where J is a 3x12 matrix.

The jacobian matrix has the structure:
    J = [X[0]  X[1]  X[2]  1    0    0    0    0    0    0    0    0  ]
        [0    0    0    0    X[0] X[1] X[2] 1    0    0    0    0  ]
        [0    0    0    0    0    0    0    0    X[0] X[1] X[2] 1  ]

Parameters:
    X (wp.vec3d): Local coordinates of the point on the object

Returns:
    wp.mat((3,12), dtype): The kinematic jacobian matrix

The jacobian is used in energy gradient and Hessian computations to transform
forces and stiffness from world space to configuration space.
"""

import warp as wp

@wp.func
def kinematic_jacobian(X: wp.vec3d)->wp.mat((3,12), dtype=wp.float64):
    # TODO: Implement the kinematic jacobian computation
    
    # Placeholder to prevent parsing errors
    z = wp.float64(0.0)
    o = wp.float64(1.0)
    J = wp.matrix(z, z, z, z, z, z, z, z, z, z, z, z,
                  z, z, z, z, z, z, z, z, z, z, z, z,
                  z, z, z, z, z, z, z, z, z, z, z, z, shape=(3,12), dtype=wp.float64)
    return J