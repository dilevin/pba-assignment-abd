"""
Mesh Transformation for Affine Body Dynamics

This module transforms mesh vertices from local coordinates to world coordinates
using the affine transformation defined by the object's configuration parameters.

For an affine body with configuration q_obj representing a 3x4 transformation matrix,
the transformation is:
    x_world = F * x_local + t
where:
    F is the 3x3 deformation gradient matrix (rotation and scaling)
    t is the 3x1 translation vector
    x_local are the local coordinates of mesh vertices
    x_world are the transformed world coordinates

The configuration q_obj is reshaped from a 12-element vector to a 3x4 matrix:
    q_obj = [F_00, F_01, F_02, t_0, F_10, F_11, F_12, t_1, F_20, F_21, F_22, t_2]
    reshaped to: [[F_00, F_01, F_02, t_0],
                  [F_10, F_11, F_12, t_1],
                  [F_20, F_21, F_22, t_2]]

Parameters:
    vertices (torch.Tensor): Input mesh vertices in local coordinates (N x 3)
    q_obj (torch.Tensor): Object configuration parameters (12-element vector)

Returns:
    torch.Tensor: Transformed vertices in world coordinates (N x 3)

The transformation is applied to all vertices simultaneously using matrix operations,
making it efficient for large meshes.
"""

import torch

def transform_mesh(vertices: torch.Tensor, q_obj: torch.Tensor):
    
    # TODO: Implement the mesh transformation
    # 1. Reshape q_obj from 12-element vector to 3x4 matrix
    # 2. Extract the 3x3 deformation gradient F (first 3 columns)
    # 3. Extract the 3x1 translation vector t (last column)
    # 4. Apply transformation: x_world = vertices @ F.T + t.T
    
    # Placeholder to prevent parsing errors
    return vertices