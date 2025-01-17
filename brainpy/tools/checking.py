# -*- coding: utf-8 -*-

from typing import Union, Sequence, Dict, Callable, Tuple, Type

import jax.numpy as jnp
import numpy as onp

import brainpy.connect as conn
import brainpy.initialize as init
from brainpy.types import Tensor

__all__ = [
  'check_shape_consistency',
  'check_shape_broadcastable',
  'check_batch_shape',
  'check_shape',
  'check_dict_data',
  'check_initializer',
  'check_connector',
  'check_float',
  'check_integer',
  'check_string',
]


def check_shape_consistency(shapes, free_axes=None, return_format_shapes=False):
  assert isinstance(shapes, (tuple, list)), f'Must be a sequence of shape. While we got {shapes}.'
  for shape in shapes:
    assert isinstance(shapes, (tuple, list)), (f'Must be a sequence of shape. While '
                                               f'we got one element is {shape}.')
  dims = onp.unique([len(shape) for shape in shapes])
  if len(dims) > 1:
    raise ValueError(f'The provided shape dimensions are not consistent. ')
  if free_axes is None:
    type_ = 'none'
    free_axes = ()
  elif isinstance(free_axes, (tuple, list)):
    type_ = 'seq'
    free_axes = tuple(free_axes)
  elif isinstance(free_axes, int):
    type_ = 'int'
    free_axes = (free_axes,)
  else:
    raise ValueError
  free_axes = [(dims[0] + axis if axis < 0 else axis) for axis in free_axes]
  all_shapes = []
  for shape in shapes:
    assert isinstance(shapes, (tuple, list)), (f'Must be a sequence of shape. While '
                                               f'we got one element is {shape}.')
    shape = tuple([sh for i, sh in enumerate(shape) if i not in free_axes])
    all_shapes.append(shape)
  unique_shape = tuple(set(all_shapes))
  if len(unique_shape) > 1:
    if len(free_axes):
      raise ValueError(f'The provided shape (without axes of {free_axes}) are not consistent.')
    else:
      raise ValueError(f'The provided shape are not consistent.')
  if return_format_shapes:
    if type_ == 'int':
      free_shapes = tuple([shape[free_axes[0]] for shape in shapes])
    elif type_ == 'seq':
      free_shapes = tuple([tuple([shape[axis] for axis in free_axes]) for shape in shapes])
    else:
      free_shapes = None
    return unique_shape[0], free_shapes


def check_shape_broadcastable(shapes, free_axes=(), return_format_shapes=False):
  """Check whether the given shapes are broadcastable.

  See https://numpy.org/doc/stable/reference/generated/numpy.broadcast.html
  for more details.

  Parameters
  ----------
  shapes
  free_axes
  return_format_shapes

  Returns
  -------

  """
  max_dim = max([len(shape) for shape in shapes])
  shapes = [[1] * (max_dim - len(s)) + list(s) for s in shapes]
  return check_shape_consistency(shapes, free_axes, return_format_shapes)


def check_batch_shape(shape1, shape2, batch_idx=0, mode='raise'):
  """Check whether two shapes are compatible except the batch size axis."""
  assert mode in ['raise', 'bool']
  if len(shape2) != len(shape1):
    if mode == 'raise':
      raise ValueError(f'Dimension mismatch between two shapes. '
                       f'{shape1} != {shape2}')
    else:
      return False
  new_shape1 = list(shape1)
  new_shape2 = list(shape2)
  new_shape1.pop(batch_idx)
  new_shape2.pop(batch_idx)
  if new_shape1 != new_shape2:
    if mode == 'raise':
      raise ValueError(f'Two shapes {shape1} and {shape2} are not '
                       f'consistent when excluding the batch axis '
                       f'{batch_idx}')
    else:
      return False
  return True


def check_shape(all_shapes, free_axes: Union[Sequence[int], int] = -1):
  # check "all_shapes"
  if isinstance(all_shapes, dict):
    all_shapes = tuple(all_shapes.values())
  elif isinstance(all_shapes, (tuple, list)):
    all_shapes = tuple(all_shapes)
  else:
    raise ValueError
  # maximum number of dimension
  max_dim = max([len(shape) for shape in all_shapes])
  all_shapes = [[1] * (max_dim - len(s)) + list(s) for s in all_shapes]
  # check "free_axes"
  type_ = 'seq'
  if isinstance(free_axes, int):
    free_axes = (free_axes,)
    type_ = 'int'
  elif isinstance(free_axes, (tuple, list)):
    free_axes = tuple(free_axes)
  assert isinstance(free_axes, tuple)
  free_axes = [(axis + max_dim if axis < 0 else axis) for axis in free_axes]
  fixed_axes = [i for i in range(max_dim) if i not in free_axes]
  # get all free shapes
  if type_ == 'int':
    free_shape = [shape[free_axes[0]] for shape in all_shapes]
  else:
    free_shape = [[shape[axis] for axis in free_axes] for shape in all_shapes]
  # get all assumed fixed shapes
  fixed_shapes = [[shape[axis] for shape in all_shapes] for axis in fixed_axes]
  max_fixed_shapes = [max(shape) for shape in fixed_shapes]
  # check whether they can broadcast compatible
  for i, shape in enumerate(fixed_shapes):
    if len(set(shape) - {1, max_fixed_shapes[i]}):
      raise ValueError(f'Shapes out of axes {free_axes} are not '
                       f'broadcast compatible: \n'
                       f'{all_shapes}')
  return free_shape, max_fixed_shapes


def check_dict_data(a_dict: Dict,
                    key_type: Union[Type, Tuple[Type, ...]],
                    val_type: Union[Type, Tuple[Type, ...]],
                    name: str = None):
  """Check the dictionary data.
  """
  name = '' if (name is None) else f'"{name}"'
  assert isinstance(a_dict, dict), f'{name} must be a dict, while we got {type(a_dict)}'
  for key, value in a_dict.items():
    assert isinstance(key, key_type), (f'{name} must be a dict of ({key_type}, {val_type}), '
                                       f'while we got ({type(key)}, {type(value)})')
    assert isinstance(value, val_type), (f'{name} must be a dict of ({key_type}, {val_type}), '
                                         f'while we got ({type(key)}, {type(value)})')


def check_initializer(initializer: Union[Callable, init.Initializer, Tensor],
                      name: str = None,
                      allow_none=False):
  """Check the initializer.
  """
  import brainpy.math as bm

  name = '' if name is None else name
  if initializer is None:
    if allow_none:
      return
    else:
      raise ValueError(f'{name} must be an initializer, but we got None.')
  if isinstance(initializer, init.Initializer):
    return
  elif isinstance(initializer, (bm.ndarray, jnp.ndarray)):
    return
  elif callable(initializer):
    return
  else:
    raise ValueError(f'{name} should be an instance of brainpy.init.Initializer, '
                     f'tensor or callable function. While we got {type(initializer)}')


def check_connector(connector: Union[Callable, conn.Connector, Tensor],
                    name: str = None, allow_none=False):
  """Check the connector.
  """
  import brainpy.math as bm

  name = '' if name is None else name
  if connector is None:
    if allow_none:
      return
    else:
      raise ValueError(f'{name} must be an initializer, but we got None.')
  if isinstance(connector, conn.Connector):
    return
  elif isinstance(connector, (bm.ndarray, jnp.ndarray)):
    return
  elif callable(connector):
    return
  else:
    raise ValueError(f'{name} should be an instance of brainpy.conn.Connector, '
                     f'tensor or callable function. While we got {type(connector)}')


def check_float(value: float, name=None, min_bound=None, max_bound=None,
                allow_none=False, allow_int=True):
  """Check float type.

  Parameters
  ----------
  value: Any
  name: optional, str
  min_bound: optional, float
    The allowed minimum value.
  max_bound: optional, float
    The allowed maximum value.
  allow_none: bool
    Whether allow the value is None.
  allow_int: bool
    Whether allow the value be an integer.
  """
  if name is None: name = ''
  if value is None:
    if allow_none:
      return
    else:
      raise ValueError(f'{name} must be a float, but got None')
  if allow_int:
    if not isinstance(value, (float, int)):
      raise ValueError(f'{name} must be a float, but got {type(value)}')
  else:
    if not isinstance(value, float):
      raise ValueError(f'{name} must be a float, but got {type(value)}')
  if min_bound is not None:
    if value < min_bound:
      raise ValueError(f"{name} must be a float bigger than {min_bound}, "
                       f"while we got {value}")
  if max_bound is not None:
    if value > max_bound:
      raise ValueError(f"{name} must be a float smaller than {max_bound}, "
                       f"while we got {value}")


def check_integer(value: int, name=None, min_bound=None, max_bound=None, allow_none=False):
  """Check integer type.

  Parameters
  ----------
  value: int, optional
  name: optional, str
  min_bound: optional, int
    The allowed minimum value.
  max_bound: optional, int
    The allowed maximum value.
  allow_none: bool
    Whether allow the value is None.
  """
  if name is None: name = ''
  if value is None:
    if allow_none:
      return
    else:
      raise ValueError(f'{name} must be an int, but got None')
  if not isinstance(value, int):
    raise ValueError(f'{name} must be an int, but got {type(value)}')
  if min_bound is not None:
    if value < min_bound:
      raise ValueError(f"{name} must be an int bigger than {min_bound}, "
                       f"while we got {value}")
  if max_bound is not None:
    if value > max_bound:
      raise ValueError(f"{name} must be an int smaller than {max_bound}, "
                       f"while we got {value}")


def check_string(value: str, name: str = None, candidates: Sequence[str] = None, allow_none=False):
  """Check string type.
  """
  if name is None: name = ''
  if value is None:
    if allow_none:
      return
    else:
      raise ValueError(f'{name} must be a str, but got None')
  if candidates is not None:
    if value not in candidates:
      raise ValueError(f'{name} must be a str in {candidates}, '
                       f'but we got {value}')
