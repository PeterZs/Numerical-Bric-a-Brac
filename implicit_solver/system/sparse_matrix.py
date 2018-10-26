"""
@author: Vincent Bonnet
@description : sparse matrix helpers
"""

from abc import ABCMeta, abstractmethod

import numpy as np
import scipy as sc

class BaseSparseMatrix(object, metaclass=ABCMeta):
    '''
    Interface for sparse matrix
    '''
    def __init__(self, num_rows, num_columns, block_size):
        self.num_rows = num_rows
        self.num_columns = num_columns
        self.block_size = block_size

    @abstractmethod
    def add(self, i, j, data):
        pass

    @abstractmethod
    def sparse_matrix(self):
        pass

class BSRSparseMatrix(BaseSparseMatrix):
    '''
    Helper class to build a BSR matrix
    '''
    def __init__(self, num_rows, num_columns, block_size):
        BaseSparseMatrix.__init__(self, num_rows, num_columns, block_size)
        self.num_entries_per_row = np.zeros(num_columns, dtype=int)
        self.coordinates_indices = [None] * num_rows
        for row_id in range(num_rows):
            self.coordinates_indices[row_id] = {}
        self.total_entries = 0

    def add(self, i, j, data):
        value = self.coordinates_indices[i].get(j, None)
        if value is None:
            self.coordinates_indices[i][j] = data
            self.num_entries_per_row[i] += 1
            self.total_entries += 1
        else:
            value += data

    def sparse_matrix(self):
        column_indices = np.zeros(self.total_entries, dtype=int)
        data = np.zeros((self.total_entries, self.block_size, self.block_size))
        idx = 0
        for row_id in range(self.num_rows):
            for column_id, matrix in sorted(self.coordinates_indices[row_id].items()):
                column_indices[idx] = column_id
                data[idx] = matrix
                idx += 1

        # TODO : The first entry of row_indptr is zero because of the mass matrix in [0,0]
        row_indptr = np.zeros(self.num_rows+1, dtype=int)
        np.add.accumulate(self.num_entries_per_row, out=row_indptr[1:self.num_rows+1])

        return sc.sparse.bsr_matrix((data, column_indices, row_indptr))

class DebugSparseMatrix(BaseSparseMatrix):
    '''
    Helper class to debug the sparse matrix
    It is just a dense matrix
    '''
    def __init__(self, num_rows, num_columns, block_size):
        BaseSparseMatrix.__init__(self, num_rows, num_columns, block_size)
        self.matrix = np.zeros((self.num_rows * self.block_size,
                                self.num_columns * self.block_size))

    def add(self, i, j, data):
        self.matrix[i*self.block_size:i*self.block_size+self.block_size,
                    j*self.block_size:j*self.block_size+self.block_size] += data

    def sparse_matrix(self):
        return sc.sparse.bsr_matrix(self.matrix, blocksize=(self.block_size, self.block_size))