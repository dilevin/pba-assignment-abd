import warp as wp
import warp.sparse as wps
import torch

def fixed_dof_projection(P_out: wps.BsrMatrix, q: torch.Tensor, fixed_indices: torch.Tensor) -> wps.BsrMatrix:
   
    if P_out is None:
        P_out = wps.bsr_zeros(cols_of_blocks=q.shape[0], rows_of_blocks = (q.shape[0]-fixed_indices.shape[0]), block_type=wp.mat((q.shape[1],q.shape[1]), dtype=wp.dtype_from_torch(q.dtype)), device=wp.device_from_torch(q.device))

    all_dof_indices = torch.Tensor(torch.arange(0, q.shape[0], device=q.device, dtype=torch.int32))
 
    #remove fixed indices from all_vert_indices
    non_fixed_dofs = all_dof_indices[~torch.isin(all_dof_indices, fixed_indices.to(torch.int32).to(q.device))]

    block_col_indices = wp.from_torch(non_fixed_dofs, dtype=wp.int32)
    block_row_indices = wp.from_torch(torch.arange(0,non_fixed_dofs.shape[0], device=q.device, dtype=torch.int32), dtype=wp.int32)
    block_values = wp.from_torch(torch.eye(q.shape[1]).unsqueeze(0).tile((non_fixed_dofs.shape[0],1,1)).to(q.device).to(q.dtype), dtype=wp.mat((q.shape[1],q.shape[1]),dtype=wp.dtype_from_torch(q.dtype)))
    wps.bsr_set_from_triplets(P_out, rows=block_row_indices, columns=block_col_indices, values=block_values)
   
    return P_out


