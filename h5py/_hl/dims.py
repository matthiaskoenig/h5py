# This file is part of h5py, a Python interface to the HDF5 library.
#
# http://www.h5py.org
#
# Copyright 2008-2013 Andrew Collette and contributors
#
# License:  Standard 3-clause BSD; see "license.txt" for full license terms
#           and contributor agreement.

from __future__ import absolute_import

import numpy

from .. import h5ds
from . import base
from .base import phil, with_phil
from .dataset import Dataset, readtime_dtype


class DimensionProxy(base.CommonStateObject):

    @property
    @with_phil
    def label(self):
        #return h5ds.get_label(self._id, self._dimension)
        # Produces a segfault for a non-existent label (Fixed in hdf5-1.8.8).
        # Here is a workaround:
        try:
            dset = Dataset(self._id)
            return self._d(dset.attrs['DIMENSION_LABELS'][self._dimension])
        except (KeyError, IndexError):
            return ''
    @label.setter
    @with_phil
    def label(self, val):
        h5ds.set_label(self._id, self._dimension, self._e(val))

    @with_phil
    def __init__(self, id, dimension):
        self._id = id
        self._dimension = dimension

    @with_phil
    def __hash__(self):
        return hash((type(self), self._id, self._dimension))

    @with_phil
    def __eq__(self, other):
        return hash(self) == hash(other)

    @with_phil
    def __iter__(self):
        for k in self.keys():
            yield k

    @with_phil
    def __len__(self):
        return h5ds.get_num_scales(self._id, self._dimension)

    @with_phil
    def __getitem__(self, item):
        if isinstance(item, int):
            scales = []
            def f(dsid):
                scales.append(Dataset(dsid))
            h5ds.iterate(self._id, self._dimension, f, 0)
            return scales[item]
        else:
            def f(dsid):
                if h5ds.get_scale_name(dsid) == self._e(item):
                    return Dataset(dsid)
            res = h5ds.iterate(self._id, self._dimension, f, 0)
            if res is None:
                raise KeyError('%s not found' % item)
            return res

    def attach_scale(self, dset):
        with phil:
            h5ds.attach_scale(self._id, dset.id, self._dimension)

    def detach_scale(self, dset):
        with phil:
            h5ds.detach_scale(self._id, dset.id, self._dimension)

    def items(self):
        with phil:
            scales = []
            def f(dsid):
                scales.append(dsid)
            
            # H5DSiterate raises an error if there are no dimension scales,
            # rather than iterating 0 times.  See #483.
            if len(self) > 0:
                h5ds.iterate(self._id, self._dimension, f, 0)
                
            return [
                (self._d(h5ds.get_scale_name(id)), Dataset(id))
                for id in scales
                ]

    def keys(self):
        with phil:
            return [key for (key, val) in self.items()]

    def values(self):
        with phil:
            return [val for (key, val) in self.items()]

    @with_phil
    def __repr__(self):
        if not self._id:
            return "<Dimension of closed HDF5 dataset>"
        return ('<"%s" dimension %d of HDF5 dataset at %s>'
               % (self.label, self._dimension, id(self._id)))


class DimensionManager(base.MappingWithLock, base.CommonStateObject):

    """
    """

    @with_phil
    def __init__(self, parent):
        """ Private constructor.
        """
        self._id = parent.id

    @with_phil
    def __getitem__(self, index):
        """ Return a Dimension object
        """
        if index > len(self) - 1:
            raise IndexError('Index out of range')
        return DimensionProxy(self._id, index)

    @with_phil
    def __len__(self):
        """ Number of dimensions associated with the dataset. """
        return len(Dataset(self._id).shape)

    @with_phil
    def __iter__(self):
        """ Iterate over the dimensions. """
        for i in range(len(self)):
            yield self[i]

    @with_phil
    def __repr__(self):
        if not self._id:
            return "<Dimensions of closed HDF5 dataset>"
        return "<Dimensions of HDF5 object at %s>" % id(self._id)

    def create_scale(self, dset, name=''):
        with phil:
            h5ds.set_scale(dset.id, self._e(name))
