# -*- coding: utf-8 -*-

import jax.numpy as jnp

from brainpy.base.base import Base
from brainpy.errors import MathError
from brainpy.math import numpy_ops as ops
from brainpy.math.jaxarray import Variable

__all__ = [
  # schedulers
  'make_schedule',
  'Scheduler',
  'Constant',
  'ExponentialDecay',
  'InverseTimeDecay',
  'PolynomialDecay',
  'PiecewiseConstant',
]

# learning rate schedules #
# ----------------------- #


def make_schedule(scalar_or_schedule):
  if isinstance(scalar_or_schedule, Scheduler):
    return scalar_or_schedule
  elif isinstance(scalar_or_schedule, (int, float)):
    return Constant(scalar_or_schedule)
  else:
    raise TypeError(type(scalar_or_schedule))


class Scheduler(Base):
  """The learning rate scheduler."""

  def __init__(self, lr):
    super(Scheduler, self).__init__()

    assert isinstance(lr, (float, int))
    self.lr = lr
    self.step = Variable(ops.array([0]))

  def update(self):
    self.step += 1

  def __call__(self, i=None):
    raise NotImplementedError


class Constant(Scheduler):
  def __call__(self, i=None):
    return self.lr


class ExponentialDecay(Scheduler):
  def __init__(self, lr, decay_steps, decay_rate):
    super(ExponentialDecay, self).__init__(lr=lr)
    self.decay_steps = decay_steps
    self.decay_rate = decay_rate

  def __call__(self, i=None):
    i = self.step[0] if i is None else i
    return self.lr * self.decay_rate ** (i / self.decay_steps)


class InverseTimeDecay(ExponentialDecay):
  def __init__(self, lr, decay_steps, decay_rate, staircase=False):
    super(InverseTimeDecay, self).__init__(lr, decay_steps, decay_rate)
    self.staircase = staircase

  def __call__(self, i=None):
    i = self.step[0] if i is None else i
    if self.staircase:
      return self.lr / (1 + self.decay_rate * ops.floor(i / self.decay_steps).value)
    else:
      return self.lr / (1 + self.decay_rate * i / self.decay_steps)


class PolynomialDecay(Scheduler):
  def __init__(self, lr, decay_steps, final_lr, power=1.0):
    super(PolynomialDecay, self).__init__(lr)
    self.decay_steps = decay_steps
    self.final_lr = final_lr
    self.power = power

  def __call__(self, i=None):
    i = self.step[0] if i is None else i
    i = ops.minimum(i, self.decay_steps).value
    step_mult = (1 - i / self.decay_steps) ** self.power
    return step_mult * (self.lr - self.final_lr) + self.final_lr


class PiecewiseConstant(Scheduler):
  def __init__(self, boundaries, values):
    super(PiecewiseConstant, self).__init__(0.)

    boundaries = jnp.array(boundaries)
    values = jnp.array(values)
    if not boundaries.ndim == values.ndim == 1:
      raise MathError("boundaries and values must be sequences")
    if not boundaries.shape[0] == values.shape[0] - 1:
      raise MathError("boundaries length must be one shorter than values length")
    self.boundaries = boundaries
    self.values = values

  def __call__(self, i=None):
    i = self.step[0] if i is None else i
    return self.values[ops.sum(i > self.boundaries)]
