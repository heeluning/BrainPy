# -*- coding: utf-8 -*-

from typing import Dict, Optional, Any

from brainpy.math import activations
from brainpy.nn.base import Node
from brainpy.nn.constants import PASS_ONLY_ONE

__all__ = [
  'Activation'
]


class Activation(Node):
  """Activation node.

  Parameters
  ----------
  activation : str
    The name of the activation function.
  fun_setting : optional, dict
    The settings for the activation function.
  """

  data_pass_type = PASS_ONLY_ONE

  def __init__(self,
               activation: str = 'relu',
               fun_setting: Optional[Dict[str, Any]] = None,
               name: str = None,
               **kwargs):
    if name is None:
      name = self.unique_name(type_=f'{activation}_activation')
    super(Activation, self).__init__(name=name, **kwargs)

    self._activation = activations.get(activation)
    self._fun_setting = dict() if (fun_setting is None) else fun_setting
    assert isinstance(self._fun_setting, dict), '"fun_setting" must be a dict.'

  def init_ff(self):
    self.set_output_shape(self.feedforward_shapes)

  def forward(self, ff, **kwargs):
    return self._activation(ff, **self._fun_setting)
