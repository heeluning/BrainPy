# -*- coding: utf-8 -*-

import math as pm
import warnings

import brainpy.math as bm
from brainpy import tools
from brainpy.base.base import Base
from brainpy.base.collector import Collector
from brainpy.errors import ModelBuildError
from brainpy.connect import TwoEndConnector, MatConn, IJConn
from brainpy.integrators.base import Integrator

__all__ = [
  'DynamicalSystem',
  'Container',
  'Network',
  'ConstantDelay',
  'NeuGroup',
  'TwoEndConn',
]

_error_msg = 'Unknown type of the update function: {} ({}). ' \
             'Currently, BrainPy only supports: \n' \
             '1. function \n' \
             '2. function name (str) \n' \
             '3. tuple/dict of functions \n' \
             '4. tuple of function names \n'


class DynamicalSystem(Base):
  """Base Dynamical System class.

  Any object has step functions will be a dynamical system.
  That is to say, in BrainPy, the essence of the dynamical system
  is the "step functions".

  Parameters
  ----------
  name : str, optional
      The name of the dynamic system.
  """

  def __init__(self, name=None):
    super(DynamicalSystem, self).__init__(name=name)

  @property
  def steps(self):
    warnings.warn('.steps has been deprecated since version 2.0.3.', DeprecationWarning)
    return {}

  def ints(self, method='absolute'):
    """Collect all integrators in this node and the children nodes.

    Parameters
    ----------
    method : str
      The method to access the integrators.

    Returns
    -------
    collector : Collector
      The collection contained (the path, the integrator).
    """
    nodes = self.nodes(method=method)
    gather = Collector()
    for node_path, node in nodes.items():
      for k in dir(node):
        v = getattr(node, k)
        if isinstance(v, Integrator):
          gather[f'{node_path}.{k}' if node_path else k] = v
    return gather

  def child_ds(self, method='absolute', include_self=False):
    """Return the children instance of dynamical systems.

    This is a shortcut function to get all children dynamical system
    in this object. For example:

    >>> import brainpy as bp
    >>>
    >>> class Net(bp.DynamicalSystem):
    >>>   def __init__(self, **kwargs):
    >>>     super(Net, self).__init__(**kwargs)
    >>>     self.A = bp.NeuGroup(10)
    >>>     self.B = bp.NeuGroup(20)
    >>>
    >>>   def update(self, _t, _dt):
    >>>     for node in self.child_ds().values():
    >>>        node.update(_t, _dt)
    >>>
    >>> net = Net()
    >>> net.child_ds()
    {'NeuGroup0': <brainpy.simulation.brainobjects.neuron.NeuGroup object at 0x000001ABD4FF02B0>,
    'NeuGroup1': <brainpy.simulation.brainobjects.neuron.NeuGroup object at 0x000001ABD74E5670>}

    Parameters
    ----------
    method : str
      The method to access the children nodes.
    include_self : bool
      Whether include the self dynamical system.

    Returns
    -------
    collector: Collector
      A Collector includes all children systems.
    """
    nodes = self.nodes(method=method).subset(DynamicalSystem).unique()
    if not include_self:
      if method == 'absolute':
        nodes.pop(self.name)
      elif method == 'relative':
        nodes.pop('')
      else:
        raise ValueError(f'Unknown access method: {method}')
    return nodes

  def register_constant_delay(self, key, size, delay, dtype=None):
    """Register a constant delay, whose update method will be appended into
    the ``self.steps`` in this host class.

    Parameters
    ----------
    key : str
      The delay name.
    size : int, list of int, tuple of int
      The delay data size.
    delay : int, float, ndarray
      The delay time, with the unit same with `brainpy.math.get_dt()`.
    dtype : optional
      The data type.

    Returns
    -------
    delay : ConstantDelay
        An instance of ConstantDelay.
    """
    if not hasattr(self, 'steps'):
      raise ModelBuildError('Please initialize the super class first before '
                            'registering constant_delay. \n\n'
                            'super(YourClassName, self).__init__(**kwargs)')
    if not key.isidentifier(): raise ValueError(f'{key} is not a valid identifier.')
    cdelay = ConstantDelay(size=size,
                           delay=delay,
                           name=f'{self.name}_delay_{key}',
                           dtype=dtype)
    return cdelay

  def __call__(self, *args, **kwargs):
    """The shortcut to call ``update`` methods."""
    return self.update(*args, **kwargs)

  def update(self, _t, _dt):
    """The function to specify the updating rule.
    Assume any dynamical system depends on the time variable ``t`` and
    the time step ``dt``.
    """
    raise NotImplementedError('Must implement "update" function by user self.')


class Container(DynamicalSystem):
  """Container object which is designed to add other instances of DynamicalSystem.

  Parameters
  ----------
  steps : tuple of function, tuple of str, dict of (str, function), optional
      The step functions.
  monitors : tuple, list, Monitor, optional
      The monitor object.
  name : str, optional
      The object name.
  show_code : bool
      Whether show the formatted code.
  ds_dict : dict of (str, )
      The instance of DynamicalSystem with the format of "key=dynamic_system".
  """

  def __init__(self, *ds_tuple, name=None, **ds_dict):
    super(Container, self).__init__(name=name)

    # children dynamical systems
    self.implicit_nodes = Collector()
    for ds in ds_tuple:
      if not isinstance(ds, DynamicalSystem):
        raise ModelBuildError(f'{self.__class__.__name__} receives instances of '
                              f'DynamicalSystem, however, we got {type(ds)}.')
      if ds.name in self.implicit_nodes:
        raise ValueError(f'{ds.name} has been paired with {ds}. Please change a unique name.')
    self.register_implicit_nodes({node.name: node for node in ds_tuple})
    for key, ds in ds_dict.items():
      if not isinstance(ds, DynamicalSystem):
        raise ModelBuildError(f'{self.__class__.__name__} receives instances of '
                              f'DynamicalSystem, however, we got {type(ds)}.')
      if key in self.implicit_nodes:
        raise ValueError(f'{key} has been paired with {ds}. Please change a unique name.')
    self.register_implicit_nodes(ds_dict)

  def update(self, _t, _dt):
    """Step function of a network.

    In this update function, the update functions in children systems are
    iteratively called.
    """
    for node in self.child_ds().values():
      node.update(_t, _dt)

  def __getattr__(self, item):
    child_ds = super(Container, self).__getattribute__('implicit_nodes')
    if item in child_ds:
      return child_ds[item]
    else:
      return super(Container, self).__getattribute__(item)


class Network(Container):
  """Base class to model network objects, an alias of Container.

  Network instantiates a network, which is aimed to load
  neurons, synapses, and other brain objects.

  Parameters
  ----------
  name : str, Optional
    The network name.
  monitors : optional, list of str, tuple of str
    The items to monitor.
  ds_tuple :
    A list/tuple container of dynamical system.
  ds_dict :
    A dict container of dynamical system.
  """

  def __init__(self, *ds_tuple, name=None, **ds_dict):
    super(Network, self).__init__(*ds_tuple, name=name, **ds_dict)


class ConstantDelay(DynamicalSystem):
  """Class used to model constant delay variables.

  This class automatically supports batch size on the last axis. For example, if
  you run batch with the size of (10, 100), where `100` are batch size, then this
  class can automatically support your batched data.
  For examples,

  >>> import brainpy as bp
  >>> bp.dyn.ConstantDelay(size=(10, 100), delay=10.)

  This class also support nonuniform delays.

  >>> bp.dyn.ConstantDelay(size=100, delay=bp.math.random.random(100) * 4 + 10)

  Parameters
  ----------
  size : int, list of int, tuple of int
    The delay data size.
  delay : int, float, function, ndarray
    The delay time. With the unit of `dt`.
  dt: float, optional
    The time precision.
  name : optional, str
    The name of the dynamic system.
  """

  def __init__(self, size, delay, dtype=None, dt=None, **kwargs):
    # dt
    self.dt = bm.get_dt() if dt is None else dt

    # data size
    if isinstance(size, int): size = (size,)
    if not isinstance(size, (tuple, list)):
      raise ModelBuildError(f'"size" must a tuple/list of int, but we got {type(size)}: {size}')
    self.size = tuple(size)

    # delay time length
    self.delay = delay

    # data and operations
    if isinstance(delay, (int, float)):  # uniform delay
      self.uniform_delay = True
      self.num_step = int(pm.ceil(delay / self.dt)) + 1
      self.out_idx = bm.Variable(bm.array([0], dtype=bm.uint32))
      self.in_idx = bm.Variable(bm.array([self.num_step - 1], dtype=bm.uint32))
      self.data = bm.Variable(bm.zeros((self.num_step,) + self.size, dtype=dtype))

    else:  # non-uniform delay
      self.uniform_delay = False
      if not len(self.size) == 1:
        raise NotImplementedError(f'Currently, BrainPy only supports 1D heterogeneous '
                                  f'delays, while we got the heterogeneous delay with '
                                  f'{len(self.size)}-dimensions.')
      self.num = tools.size2num(size)
      if bm.ndim(delay) != 1:
        raise ModelBuildError(f'Only support a 1D non-uniform delay. '
                              f'But we got {delay.ndim}D: {delay}')
      if delay.shape[0] != self.size[0]:
        raise ModelBuildError(f"The first shape of the delay time size must "
                              f"be the same with the delay data size. But "
                              f"we got {delay.shape[0]} != {self.size[0]}")
      delay = bm.around(delay / self.dt)
      self.diag = bm.array(bm.arange(self.num), dtype=bm.int_)
      self.num_step = bm.array(delay, dtype=bm.uint32) + 1
      self.in_idx = bm.Variable(self.num_step - 1)
      self.out_idx = bm.Variable(bm.zeros(self.num, dtype=bm.uint32))
      self.data = bm.Variable(bm.zeros((self.num_step.max(),) + size, dtype=dtype))

    super(ConstantDelay, self).__init__(**kwargs)

  @property
  def oldest(self):
    return self.pull()

  @property
  def latest(self):
    if self.uniform_delay:
      return self.data[self.in_idx[0]]
    else:
      return self.data[self.in_idx, self.diag]

  def pull(self):
    if self.uniform_delay:
      return self.data[self.out_idx[0]]
    else:
      return self.data[self.out_idx, self.diag]

  def push(self, value):
    if self.uniform_delay:
      self.data[self.in_idx[0]] = value
    else:
      self.data[self.in_idx, self.diag] = value

  def update(self, _t=None, _dt=None, **kwargs):
    """Update the delay index."""
    self.in_idx[:] = (self.in_idx + 1) % self.num_step
    self.out_idx[:] = (self.out_idx + 1) % self.num_step

  def reset(self):
    """Reset the variables."""
    self.in_idx[:] = self.num_step - 1
    self.out_idx[:] = 0
    self.data[:] = 0


class NeuGroup(DynamicalSystem):
  """Base class to model neuronal groups.

  There are several essential attributes:

  - ``size``: the geometry of the neuron group. For example, `(10, )` denotes a line of
    neurons, `(10, 10)` denotes a neuron group aligned in a 2D space, `(10, 15, 4)` denotes
    a 3-dimensional neuron group.
  - ``num``: the flattened number of neurons in the group. For example, `size=(10, )` => \
    `num=10`, `size=(10, 10)` => `num=100`, `size=(10, 15, 4)` => `num=600`.

  Parameters
  ----------
  size : int, tuple of int, list of int
    The neuron group geometry.
  name : optional, str
    The name of the dynamic system.
  """

  def __init__(self, size, name=None):
    # size
    if isinstance(size, (list, tuple)):
      if len(size) <= 0:
        raise ModelBuildError('size must be int, or a tuple/list of int.')
      if not isinstance(size[0], int):
        raise ModelBuildError('size must be int, or a tuple/list of int.')
      size = tuple(size)
    elif isinstance(size, int):
      size = (size,)
    else:
      raise ModelBuildError('size must be int, or a tuple/list of int.')
    self.size = size
    self.num = tools.size2num(size)

    # initialize
    super(NeuGroup, self).__init__(name=name)

  def update(self, _t, _dt):
    """The function to specify the updating rule.

    Parameters
    ----------
    _t : float
      The current time.
    _dt : float
      The time step.
    """
    raise NotImplementedError(f'Subclass of {self.__class__.__name__} must '
                              f'implement "update" function.')


class TwoEndConn(DynamicalSystem):
  """Base class to model two-end synaptic connections.

  Parameters
  ----------
  pre : NeuGroup
      Pre-synaptic neuron group.
  post : NeuGroup
      Post-synaptic neuron group.
  conn : optional, math.ndarray, dict of (str, math.ndarray), TwoEndConnector
      The connection method between pre- and post-synaptic groups.
  name : str, optional
      The name of the dynamic system.
  """

  def __init__(self, pre, post, conn=None, name=None):
    # pre or post neuron group
    # ------------------------
    if not isinstance(pre, NeuGroup):
      raise ModelBuildError('"pre" must be an instance of NeuGroup.')
    if not isinstance(post, NeuGroup):
      raise ModelBuildError('"post" must be an instance of NeuGroup.')
    self.pre = pre
    self.post = post

    # connectivity
    # ------------
    if isinstance(conn, TwoEndConnector):
      self.conn = conn(pre.size, post.size)
    elif isinstance(conn, bm.ndarray):
      if (pre.num, post.num) != conn.shape:
        raise ModelBuildError(f'"conn" is provided as a matrix, and it is expected '
                              f'to be an array with shape of (pre.num, post.num) = '
                              f'{(pre.num, post.num)}, however we got {conn.shape}')
      self.conn = MatConn(conn_mat=conn)
    elif isinstance(conn, dict):
      if not ('i' in conn and 'j' in conn):
        raise ModelBuildError(f'"conn" is provided as a dict, and it is expected to '
                              f'be a dictionary with "i" and "j" specification, '
                              f'however we got {conn}')
      self.conn = IJConn(i=conn['i'], j=conn['j'])
    elif conn is None:
      self.conn = conn
    else:
      raise ModelBuildError(f'Unknown "conn" type: {conn}')

    # initialize
    # ----------
    super(TwoEndConn, self).__init__(name=name)

  def check_pre_attrs(self, *attrs):
    """Check whether pre group satisfies the requirement."""
    if not hasattr(self, 'pre'):
      raise ModelBuildError('Please call __init__ function first.')
    for attr in attrs:
      if not isinstance(attr, str):
        raise ValueError(f'Must be string. But got {attr}.')
      if not hasattr(self.pre, attr):
        raise ModelBuildError(f'{self} need "pre" neuron group has attribute "{attr}".')

  def check_post_attrs(self, *attrs):
    """Check whether post group satisfies the requirement."""
    if not hasattr(self, 'post'):
      raise ModelBuildError('Please call __init__ function first.')
    for attr in attrs:
      if not isinstance(attr, str):
        raise ValueError(f'Must be string. But got {attr}.')
      if not hasattr(self.post, attr):
        raise ModelBuildError(f'{self} need "pre" neuron group has attribute "{attr}".')
