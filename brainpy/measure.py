# -*- coding: utf-8 -*-

import numpy as np

from brainpy import backend
from brainpy import tools
from brainpy.backend import ops

__all__ = [
  'cross_correlation',
  'voltage_fluctuation',
  'raster_plot',
  'firing_rate',
]


@tools.numba_jit
def _cc(states, i, j):
  sqrt_ij = np.sqrt(np.sum(states[i]) * np.sum(states[j]))
  k = 0. if sqrt_ij == 0. else np.sum(states[i] * states[j]) / sqrt_ij
  return k


def cross_correlation(spikes, bin, dt=None):
  """Calculate cross correlation index between neurons.

  The coherence [1]_ between two neurons i and j is measured by their
  cross-correlation of spike trains at zero time lag within a time bin
  of :backend:`\\Delta t = \\tau`. More specifically, suppose that a long
  time interval T is divided into small bins of :backend:`\\Delta t` and
  that two spike trains are given by :backend:`X(l)=` 0 or 1, :backend:`Y(l)=` 0
  or 1, :backend:`l=1,2, \\ldots, K(T / K=\\tau)`. Thus, we define a coherence
  measure for the pair as:

  .. backend::

      \\kappa_{i j}(\\tau)=\\frac{\\sum_{l=1}^{K} X(l) Y(l)}
      {\\sqrt{\\sum_{l=1}^{K} X(l) \\sum_{l=1}^{K} Y(l)}}

  The population coherence measure :backend:`\\kappa(\\tau)` is defined by the
  average of :backend:`\\kappa_{i j}(\\tau)` over many pairs of neurons in the
  network.

  Parameters
  ----------
  spikes :
      The history of spike states of the neuron group.
      It can be easily get via `StateMonitor(neu, ['spike'])`.
  bin : float, int
      The time bin to normalize spike states.
  dt : float, optional
      The time precision.

  Returns
  -------
  cc_index : float
      The cross correlation value which represents the synchronization index.

  References
  ----------
  .. [1] Wang, Xiao-Jing, and György Buzsáki. "Gamma oscillation by synaptic
         inhibition in a hippocampal interneuronal network model." Journal of
         neuroscience 16.20 (1996): 6402-6413.
  """

  dt = backend.get_dt() if dt is None else dt
  bin_size = int(bin / dt)
  num_hist, num_neu = spikes.shape
  num_bin = int(np.ceil(num_hist / bin_size))
  if num_bin * bin_size != num_hist:
    spikes = np.append(spikes, np.zeros((num_bin * bin_size - num_hist, num_neu)), axis=0)
  states = spikes.T.reshape((num_neu, num_bin, bin_size))
  states = (np.sum(states, axis=2) > 0.).astype(np.float_)
  all_k = []
  for i in range(num_neu):
    for j in range(i + 1, num_neu):
      all_k.append(_cc(states, i, j))
  return np.mean(all_k)


@tools.numba_jit
def _var(neu_signal):
  return np.mean(neu_signal * neu_signal) - np.mean(neu_signal) ** 2


def voltage_fluctuation(potentials):
  """Calculate neuronal synchronization via voltage variance.

  The method comes from [1]_ [2]_ [3]_.

  First, average over the membrane potential :backend:`V`

  .. backend::

      V(t) = \\frac{1}{N} \\sum_{i=1}^{N} V_i(t)

  The variance of the time fluctuations of :backend:`V(t)` is

  .. backend::

      \\sigma_V^2 = \\left\\langle \\left[ V(t) \\right]^2 \\right\\rangle_t -
      \\left[ \\left\\langle V(t) \\right\\rangle_t \\right]^2

  where :backend:`\\left\\langle \\ldots \\right\\rangle_t = (1 / T_m) \\int_0^{T_m} dt \\, \\ldots`
  denotes time-averaging over a large time, :backend:`\\tau_m`. After normalization
  of :backend:`\\sigma_V` to the average over the population of the single cell
  membrane potentials

  .. backend::

      \\sigma_{V_i}^2 = \\left\\langle\\left[ V_i(t) \\right]^2 \\right\\rangle_t -
      \\left[ \\left\\langle V_i(t) \\right\\rangle_t \\right]^2

  one defines a synchrony measure, :backend:`\\chi (N)`, for the activity of a system
  of :backend:`N` neurons by:

  .. backend::

      \\chi^2 \\left( N \\right) = \\frac{\\sigma_V^2}{ \\frac{1}{N} \\sum_{i=1}^N
      \\sigma_{V_i}^2}

  Parameters
  ----------
  potentials :
      The membrane potential matrix of the neuron group.

  Returns
  -------
  sync_index : float
      The synchronization index.

  References
  ----------
  .. [1] Golomb, D. and Rinzel J. (1993) Dynamics of globally coupled
         inhibitory neurons with heterogeneity. Phys. Rev. reversal_potential 48:4810-4814.
  .. [2] Golomb D. and Rinzel J. (1994) Clustering in globally coupled
         inhibitory neurons. Physica D 72:259-282.
  .. [3] David Golomb (2007) Neuronal synchrony measures. Scholarpedia, 2(1):1347.
  """

  num_hist, num_neu = potentials.shape
  avg = np.mean(potentials, axis=1)
  avg_var = np.mean(avg * avg) - np.mean(avg) ** 2
  neu_vars = []
  for i in range(num_neu):
    neu_vars.append(_var(potentials[:, i]))
  var_mean = np.mean(neu_vars)
  return avg_var / var_mean if var_mean != 0. else 1.


def raster_plot(sp_matrix, times):
  """Get spike raster plot which displays the spiking activity
  of a group of neurons over time.

  Parameters
  ----------
  sp_matrix : bnp.ndarray
      The matrix which record spiking activities.
  times : bnp.ndarray
      The time steps.

  Returns
  -------
  raster_plot : tuple
      Include (neuron index, spike time).
  """
  elements = np.where(sp_matrix > 0.)
  index = elements[1]
  time = times[elements[0]]
  return index, time


def firing_rate(sp_matrix, width, window='gaussian'):
  """Calculate the mean firing rate over in a neuron group.

  This method is adopted from Brian2.

  The firing rate in trial :backend:`k` is the spike count :backend:`n_{k}^{sp}`
  in an interval of duration :backend:`T` divided by :backend:`T`:

  .. backend::

      v_k = {n_k^{sp} \\over T}

  Parameters
  ----------
  sp_matrix : bnp.ndarray
      The spike matrix which record spiking activities.
  width : int, float
      The width of the ``window`` in millisecond.
  window : str
      The window to use for smoothing. It can be a string to chose a
      predefined window:

      - `flat`: a rectangular,
      - `gaussian`: a Gaussian-shaped window.

      For the `Gaussian` window, the `width` parameter specifies the
      standard deviation of the Gaussian, the width of the actual window
      is `4 * width + dt`.
      For the `flat` window, the width of the actual window
      is `2 * width/2 + dt`.

  Returns
  -------
  rate : numpy.ndarray
      The population rate in Hz, smoothed with the given window.
  """
  # rate
  rate = ops.sum(sp_matrix, axis=1)

  # window
  dt = backend.get_dt()
  if window == 'gaussian':
    width1 = 2 * width / dt
    width2 = int(round(width1))
    window = ops.exp(-ops.arange(-width2, width2 + 1) ** 2 / (width1 ** 2 * 2))
  elif window == 'flat':
    width1 = int(width / 2 / dt) * 2 + 1
    window = ops.ones(width1)
  else:
    raise ValueError('Unknown window type "{}".'.format(window))

  return np.convolve(rate, window / sum(window), mode='same')
