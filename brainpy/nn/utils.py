# -*- coding: utf-8 -*-

from typing import Union, Sequence, Dict, Any, Callable

import jax.numpy as jnp
import numpy as onp

import brainpy.math as bm
from brainpy.initialize import Initializer
from brainpy.tools.others import to_size
from brainpy.types import Tensor, Shape

__all__ = [
  'tensor_sum',
  'init_param',
  'check_rnn_data_batch_size',
  'check_rnn_data_time_step',
]


def tensor_sum(values: Union[Sequence[Tensor], Dict[Any, Tensor], Tensor]):
  if isinstance(values, (bm.ndarray, jnp.ndarray)):
    return values
  if isinstance(values, dict):
    values = list(values.values())
  elif isinstance(values, (tuple, list)):
    values = list(values)
  else:
    raise ValueError('Unknown types of tensors.')
  res = values[0]
  for v in values[1:]:
    res = res + v
  return res


def init_param(param: Union[Callable, Initializer, bm.ndarray, jnp.ndarray],
               size: Shape):
  """Initialize parameters.

  Parameters
  ----------
  param: callable, Initializer, bm.ndarray, jnp.ndarray
    The initialization of the parameter.
    - If it is None, the created parameter will be None.
    - If it is a callable function :math:`f`, the ``f(size)`` will be returned.
    - If it is an instance of :py:class:`brainpy.init.Initializer``, the ``f(size)`` will be returned.
    - If it is a tensor, then this function check whether ``tensor.shape`` is equal to the given ``size``.
  size: int, sequence of int
    The shape of the parameter.
  """
  size = to_size(size)
  if param is None:
    return None
  elif callable(param):
    param = param(size)
  elif isinstance(param, (onp.ndarray, jnp.ndarray)):
    param = bm.asarray(param)
  elif isinstance(param, (bm.JaxArray,)):
    param = param
  else:
    raise ValueError(f'Unknown param type {type(param)}: {param}')
  assert param.shape == size, f'"param.shape" is not the required size {size}'
  return param


def check_rnn_data_batch_size(data: Dict, num_batch=None):
  if len(data) == 1:
    batch_size = list(data.values())[0].shape[0]
  else:
    batches = []
    for key, val in data.items():
      batches.append(val.shape[0])
    if len(set(batches)) != 1:
      raise ValueError('Batch sizes are not consistent among the given data. '
                       f'Got {set(batches)}. We expect only one batch size.')
    batch_size = batches[0]
  if (num_batch is not None) and batch_size != num_batch:
    raise ValueError(f'Batch size is not consistent with the expected {batch_size} != {num_batch}')
  return batch_size


def check_rnn_data_time_step(data: Dict, num_step=None):
  if len(data) == 1:
    time_step = list(data.values())[0].shape[1]
  else:
    steps = []
    for key, val in data.items():
      steps.append(val.shape[1])
    if len(set(steps)) != 1:
      raise ValueError('Time steps are not consistent among the given data. '
                       f'Got {set(steps)}. We expect only one time step.')
    time_step = steps[0]
  if (num_step is not None) and time_step != num_step:
    raise ValueError(f'Time step is not consistent with the expected {time_step} != {num_step}')
  return time_step
