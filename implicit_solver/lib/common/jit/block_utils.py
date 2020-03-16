"""
@author: Vincent Bonnet
@description : Datablock jitted utility methods
"""

import math
import numba
import numpy as np

@numba.njit
def empty_block_handles():
    return numba.typed.List.empty_list(numba.int32)

@numba.njit
def empty_block(block_dtype):
    block = np.empty(1, dtype=block_dtype)
    block[0]['blockInfo_active'] = False
    block[0]['blockInfo_numElements'] = 0
    return block

@numba.njit
def get_inactive_block_handles(blocks):
    handles = empty_block_handles()
    for block_index in range(len(blocks)):
        if blocks[block_index][0]['blockInfo_active'] == False:
            handles.append(block_index)
    return handles

@numba.njit
def compute_num_elements(blocks, block_handles = None):
    num_elements = 0

    if block_handles is None:
        for block_container in blocks:
            block_data = block_container[0]
            if block_data['blockInfo_active']:
                num_elements += block_data['blockInfo_numElements']
    else:
        for block_handle in block_handles:
            block_container = blocks[block_handle]
            block_data = block_container[0]
            if block_data['blockInfo_active']:
                num_elements += block_data['blockInfo_numElements']

    return num_elements

@numba.njit
def append_blocks(blocks, block_dtype, reuse_inactive_block, num_elements, block_size):
    inactive_block_handles = empty_block_handles()
    block_handles = empty_block_handles()

    # collect inactive block ids
    if reuse_inactive_block:
        inactive_block_handles = get_inactive_block_handles(blocks)

    # append blocks
    n_blocks = math.ceil(num_elements / block_size)
    for block_index in range(n_blocks):

        block_handle = -1
        block_container = None

        if reuse_inactive_block and len(inactive_block_handles) > 0:
            # reuse blocks
            block_handle = inactive_block_handles.pop(0)
            block_container = blocks[block_handle]
        else:
            # allocate a new block
            block_handle = len(blocks)
            block_container = empty_block(block_dtype)
            blocks.append(block_container)

        begin_index = block_index * block_size
        block_n_elements = min(block_size, num_elements-begin_index)
        block_container[0]['blockInfo_numElements'] = block_n_elements
        block_container[0]['blockInfo_active'] = True

        # add block id to result
        block_handles.append(block_handle)

    return block_handles
