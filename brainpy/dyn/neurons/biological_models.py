# -*- coding: utf-8 -*-

import brainpy.math as bm
from brainpy.integrators.joint_eq import JointEq
from brainpy.integrators.ode import odeint
from brainpy.dyn.base import NeuGroup

__all__ = [
  'HH',
  'MorrisLecar',
]


class HH(NeuGroup):
  r"""Hodgkin–Huxley neuron model.

  **Model Descriptions**

  The Hodgkin-Huxley (HH; Hodgkin & Huxley, 1952) model [1]_ for the generation of
  the nerve action potential is one of the most successful mathematical models of
  a complex biological process that has ever been formulated. The basic concepts
  expressed in the model have proved a valid approach to the study of bio-electrical
  activity from the most primitive single-celled organisms such as *Paramecium*,
  right through to the neurons within our own brains.

  Mathematically, the model is given by,

  .. math::

      C \frac {dV} {dt} = -(\bar{g}_{Na} m^3 h (V &-E_{Na})
      + \bar{g}_K n^4 (V-E_K) + g_{leak} (V - E_{leak})) + I(t)

      \frac {dx} {dt} &= \alpha_x (1-x)  - \beta_x, \quad x\in {\rm{\{m, h, n\}}}

      &\alpha_m(V) = \frac {0.1(V+40)}{1-\exp(\frac{-(V + 40)} {10})}

      &\beta_m(V) = 4.0 \exp(\frac{-(V + 65)} {18})

      &\alpha_h(V) = 0.07 \exp(\frac{-(V+65)}{20})

      &\beta_h(V) = \frac 1 {1 + \exp(\frac{-(V + 35)} {10})}

      &\alpha_n(V) = \frac {0.01(V+55)}{1-\exp(-(V+55)/10)}

      &\beta_n(V) = 0.125 \exp(\frac{-(V + 65)} {80})

  The illustrated example of HH neuron model please see `this notebook <../neurons/HH_model.ipynb>`_.

  The Hodgkin–Huxley model can be thought of as a differential equation system with
  four state variables, :math:`V_{m}(t),n(t),m(t)`, and :math:`h(t)`, that change
  with respect to time :math:`t`. The system is difficult to study because it is a
  nonlinear system and cannot be solved analytically. However, there are many numeric
  methods available to analyze the system. Certain properties and general behaviors,
  such as limit cycles, can be proven to exist.

  *1. Center manifold*

  Because there are four state variables, visualizing the path in phase space can
  be difficult. Usually two variables are chosen, voltage :math:`V_{m}(t)` and the
  potassium gating variable :math:`n(t)`, allowing one to visualize the limit cycle.
  However, one must be careful because this is an ad-hoc method of visualizing the
  4-dimensional system. This does not prove the existence of the limit cycle.

  .. image:: ../../../../_static/Hodgkin_Huxley_Limit_Cycle.png
      :align: center

  A better projection can be constructed from a careful analysis of the Jacobian of
  the system, evaluated at the equilibrium point. Specifically, the eigenvalues of
  the Jacobian are indicative of the center manifold's existence. Likewise, the
  eigenvectors of the Jacobian reveal the center manifold's orientation. The
  Hodgkin–Huxley model has two negative eigenvalues and two complex eigenvalues
  with slightly positive real parts. The eigenvectors associated with the two
  negative eigenvalues will reduce to zero as time :math:`t` increases. The remaining
  two complex eigenvectors define the center manifold. In other words, the
  4-dimensional system collapses onto a 2-dimensional plane. Any solution
  starting off the center manifold will decay towards the *center manifold*.
  Furthermore, the limit cycle is contained on the center manifold.

  *2. Bifurcations*

  If the injected current :math:`I` were used as a bifurcation parameter, then the
  Hodgkin–Huxley model undergoes a Hopf bifurcation. As with most neuronal models,
  increasing the injected current will increase the firing rate of the neuron.
  One consequence of the Hopf bifurcation is that there is a minimum firing rate.
  This means that either the neuron is not firing at all (corresponding to zero
  frequency), or firing at the minimum firing rate. Because of the all-or-none
  principle, there is no smooth increase in action potential amplitude, but
  rather there is a sudden "jump" in amplitude. The resulting transition is
  known as a `canard <http://www.scholarpedia.org/article/Canards>`_.

  .. image:: ../../../../_static/Hodgkins_Huxley_bifurcation_by_I.gif
     :align: center

  The following image shows the bifurcation diagram of the Hodgkin–Huxley model
  as a function of the external drive :math:`I` [3]_. The green lines show the amplitude
  of a stable limit cycle and the blue lines indicate unstable limit-cycle behaviour,
  both born from Hopf bifurcations. The solid red line shows the stable fixed point
  and the black line shows the unstable fixed point.

  .. image:: ../../../../_static/Hodgkin_Huxley_bifurcation.png
     :align: center

  **Model Examples**

  .. plot::
    :include-source: True

    >>> import brainpy as bp
    >>> group = bp.dyn.HH(2)
    >>> runner = bp.dyn.DSRunner(group, monitors=['V'], inputs=('input', 10.))
    >>> runner.run(200.)
    >>> bp.visualize.line_plot(runner.mon.ts, runner.mon.V, show=True)

  .. plot::
    :include-source: True

    >>> import brainpy as bp
    >>> import matplotlib.pyplot as plt
    >>>
    >>> group = bp.dyn.HH(2)
    >>>
    >>> I1 = bp.inputs.spike_input(sp_times=[500., 550., 1000, 1030, 1060, 1100, 1200], sp_lens=5, sp_sizes=5., duration=2000, )
    >>> I2 = bp.inputs.spike_input(sp_times=[600.,       900, 950, 1500], sp_lens=5, sp_sizes=5., duration=2000, )
    >>> I1 += bp.math.random.normal(0, 3, size=I1.shape)
    >>> I2 += bp.math.random.normal(0, 3, size=I2.shape)
    >>> I = bp.math.stack((I1, I2), axis=-1)
    >>>
    >>> runner = bp.dyn.DSRunner(group, monitors=['V'], inputs=('input', I, 'iter'))
    >>> runner.run(2000.)
    >>>
    >>> fig, gs = bp.visualize.get_figure(1, 1, 3, 8)
    >>> fig.add_subplot(gs[0, 0])
    >>> plt.plot(runner.mon.ts, runner.mon.V[:, 0])
    >>> plt.plot(runner.mon.ts, runner.mon.V[:, 1] + 130)
    >>> plt.xlim(10, 2000)
    >>> plt.xticks([])
    >>> plt.yticks([])
    >>> plt.show()


  **Model Parameters**

  ============= ============== ======== ====================================
  **Parameter** **Init Value** **Unit** **Explanation**
  ------------- -------------- -------- ------------------------------------
  V_th          20.            mV       the spike threshold.
  C             1.             ufarad   capacitance.
  E_Na          50.            mV       reversal potential of sodium.
  E_K           -77.           mV       reversal potential of potassium.
  E_leak        54.387         mV       reversal potential of unspecific.
  g_Na          120.           msiemens conductance of sodium channel.
  g_K           36.            msiemens conductance of potassium channel.
  g_leak        .03            msiemens conductance of unspecific channels.
  ============= ============== ======== ====================================

  **Model Variables**

  ================== ================= =========================================================
  **Variables name** **Initial Value** **Explanation**
  ------------------ ----------------- ---------------------------------------------------------
  V                        -65         Membrane potential.
  m                        0.05        gating variable of the sodium ion channel.
  n                        0.32        gating variable of the potassium ion channel.
  h                        0.60        gating variable of the sodium ion channel.
  input                     0          External and synaptic input current.
  spike                    False       Flag to mark whether the neuron is spiking.
  t_last_spike       -1e7               Last spike time stamp.
  ================== ================= =========================================================

  **References**

  .. [1] Hodgkin, Alan L., and Andrew F. Huxley. "A quantitative description
         of membrane current and its application to conduction and excitation
         in nerve." The Journal of physiology 117.4 (1952): 500.
  .. [2] https://en.wikipedia.org/wiki/Hodgkin%E2%80%93Huxley_model
  .. [3] Ashwin, Peter, Stephen Coombes, and Rachel Nicks. "Mathematical
         frameworks for oscillatory network dynamics in neuroscience."
         The Journal of Mathematical Neuroscience 6, no. 1 (2016): 1-92.
  """

  def __init__(self, size, ENa=50., gNa=120., EK=-77., gK=36., EL=-54.387, gL=0.03,
               V_th=20., C=1.0, method='exp_auto', name=None):
    # initialization
    super(HH, self).__init__(size=size, name=name)

    # parameters
    self.ENa = ENa
    self.EK = EK
    self.EL = EL
    self.gNa = gNa
    self.gK = gK
    self.gL = gL
    self.C = C
    self.V_th = V_th

    # variables
    self.m = bm.Variable(0.5 * bm.ones(self.num))
    self.h = bm.Variable(0.6 * bm.ones(self.num))
    self.n = bm.Variable(0.32 * bm.ones(self.num))
    self.V = bm.Variable(bm.zeros(self.num))
    self.input = bm.Variable(bm.zeros(self.num))
    self.spike = bm.Variable(bm.zeros(self.num, dtype=bool))
    self.t_last_spike = bm.Variable(bm.ones(self.num) * -1e7)

    # integral
    self.integral = odeint(method=method, f=self.derivative)

  def dm(self, m, t, V):
    alpha = 0.1 * (V + 40) / (1 - bm.exp(-(V + 40) / 10))
    beta = 4.0 * bm.exp(-(V + 65) / 18)
    dmdt = alpha * (1 - m) - beta * m
    return dmdt

  def dh(self, h, t, V):
    alpha = 0.07 * bm.exp(-(V + 65) / 20.)
    beta = 1 / (1 + bm.exp(-(V + 35) / 10))
    dhdt = alpha * (1 - h) - beta * h
    return dhdt

  def dn(self, n, t, V):
    alpha = 0.01 * (V + 55) / (1 - bm.exp(-(V + 55) / 10))
    beta = 0.125 * bm.exp(-(V + 65) / 80)
    dndt = alpha * (1 - n) - beta * n
    return dndt

  def dV(self, V, t, m, h, n, I_ext):
    I_Na = (self.gNa * m ** 3.0 * h) * (V - self.ENa)
    I_K = (self.gK * n ** 4.0) * (V - self.EK)
    I_leak = self.gL * (V - self.EL)
    dVdt = (- I_Na - I_K - I_leak + I_ext) / self.C
    return dVdt

  @property
  def derivative(self):
    return JointEq([self.dV, self.dm, self.dh, self.dn])

  def update(self, _t, _dt):
    V, m, h, n = self.integral(self.V, self.m, self.h, self.n, _t, self.input, dt=_dt)
    self.spike.value = bm.logical_and(self.V < self.V_th, V >= self.V_th)
    self.t_last_spike.value = bm.where(self.spike, _t, self.t_last_spike)
    self.V.value = V
    self.m.value = m
    self.h.value = h
    self.n.value = n
    self.input[:] = 0.


class MorrisLecar(NeuGroup):
  r"""The Morris-Lecar neuron model.

  **Model Descriptions**

  The Morris-Lecar model [1]_ (Also known as :math:`I_{Ca}+I_K`-model)
  is a two-dimensional "reduced" excitation model applicable to
  systems having two non-inactivating voltage-sensitive conductances.
  This model was named after Cathy Morris and Harold Lecar, who
  derived it in 1981. Because it is two-dimensional, the Morris-Lecar
  model is one of the favorite conductance-based models in computational neuroscience.

  The original form of the model employed an instantaneously
  responding voltage-sensitive Ca2+ conductance for excitation and a delayed
  voltage-dependent K+ conductance for recovery. The equations of the model are:

  .. math::

      \begin{aligned}
      C\frac{dV}{dt} =& -  g_{Ca} M_{\infty} (V - V_{Ca})- g_{K} W(V - V_{K}) -
                        g_{Leak} (V - V_{Leak}) + I_{ext} \\
      \frac{dW}{dt} =& \frac{W_{\infty}(V) - W}{ \tau_W(V)}
      \end{aligned}

  Here, :math:`V` is the membrane potential, :math:`W` is the "recovery variable",
  which is almost invariably the normalized :math:`K^+`-ion conductance, and
  :math:`I_{ext}` is the applied current stimulus.

  **Model Examples**

  .. plot::
    :include-source: True

    >>> import brainpy as bp
    >>>
    >>> group = bp.dyn.MorrisLecar(1)
    >>> runner = bp.dyn.DSRunner(group, monitors=['V', 'W'], inputs=('input', 100.))
    >>> runner.run(1000)
    >>>
    >>> fig, gs = bp.visualize.get_figure(2, 1, 3, 8)
    >>> fig.add_subplot(gs[0, 0])
    >>> bp.visualize.line_plot(runner.mon.ts, runner.mon.W, ylabel='W')
    >>> fig.add_subplot(gs[1, 0])
    >>> bp.visualize.line_plot(runner.mon.ts, runner.mon.V, ylabel='V', show=True)


  **Model Parameters**

  ============= ============== ======== =======================================================
  **Parameter** **Init Value** **Unit** **Explanation**
  ------------- -------------- -------- -------------------------------------------------------
  V_Ca          130            mV       Equilibrium potentials of Ca+.(mV)
  g_Ca          4.4            \        Maximum conductance of corresponding Ca+.(mS/cm2)
  V_K           -84            mV       Equilibrium potentials of K+.(mV)
  g_K           8              \        Maximum conductance of corresponding K+.(mS/cm2)
  V_Leak        -60            mV       Equilibrium potentials of leak current.(mV)
  g_Leak        2              \        Maximum conductance of leak current.(mS/cm2)
  C             20             \        Membrane capacitance.(uF/cm2)
  V1            -1.2           \        Potential at which M_inf = 0.5.(mV)
  V2            18             \        Reciprocal of slope of voltage dependence of M_inf.(mV)
  V3            2              \        Potential at which W_inf = 0.5.(mV)
  V4            30             \        Reciprocal of slope of voltage dependence of W_inf.(mV)
  phi           0.04           \        A temperature factor. (1/s)
  V_th          10             mV       The spike threshold.
  ============= ============== ======== =======================================================

  **Model Variables**

  ================== ================= =========================================================
  **Variables name** **Initial Value** **Explanation**
  ------------------ ----------------- ---------------------------------------------------------
  V                  -20               Membrane potential.
  W                  0.02              Gating variable, refers to the fraction of
                                       opened K+ channels.
  input              0                 External and synaptic input current.
  spike              False             Flag to mark whether the neuron is spiking.
  t_last_spike       -1e7              Last spike time stamp.
  ================== ================= =========================================================

  **References**

  .. [1] Meier, Stephen R., Jarrett L. Lancaster, and Joseph M. Starobin.
         "Bursting regimes in a reaction-diffusion system with action
         potential-dependent equilibrium." PloS one 10.3 (2015):
         e0122401.
  .. [2] http://www.scholarpedia.org/article/Morris-Lecar_model
  .. [3] https://en.wikipedia.org/wiki/Morris%E2%80%93Lecar_model
  """

  def __init__(self, size, V_Ca=130., g_Ca=4.4, V_K=-84., g_K=8., V_leak=-60.,
               g_leak=2., C=20., V1=-1.2, V2=18., V3=2., V4=30., phi=0.04,
               V_th=10., method='exp_auto', name=None):
    # initialization
    super(MorrisLecar, self).__init__(size=size,  name=name)

    # params
    self.V_Ca = V_Ca
    self.g_Ca = g_Ca
    self.V_K = V_K
    self.g_K = g_K
    self.V_leak = V_leak
    self.g_leak = g_leak
    self.C = C
    self.V1 = V1
    self.V2 = V2
    self.V3 = V3
    self.V4 = V4
    self.phi = phi
    self.V_th = V_th

    # vars
    self.W = bm.Variable(bm.ones(self.num) * 0.02)
    self.V = bm.Variable(bm.zeros(self.num))
    self.input = bm.Variable(bm.zeros(self.num))
    self.spike = bm.Variable(bm.zeros(self.num, dtype=bool))
    self.t_last_spike = bm.Variable(bm.ones(self.num) * -1e7)

    # integral
    self.integral = odeint(method=method, f=self.derivative)

  def dV(self, V, t, W, I_ext):
    M_inf = (1 / 2) * (1 + bm.tanh((V - self.V1) / self.V2))
    I_Ca = self.g_Ca * M_inf * (V - self.V_Ca)
    I_K = self.g_K * W * (V - self.V_K)
    I_Leak = self.g_leak * (V - self.V_leak)
    dVdt = (- I_Ca - I_K - I_Leak + I_ext) / self.C
    return dVdt

  def dW(self, W, t, V):
    tau_W = 1 / (self.phi * bm.cosh((V - self.V3) / (2 * self.V4)))
    W_inf = (1 / 2) * (1 + bm.tanh((V - self.V3) / self.V4))
    dWdt = (W_inf - W) / tau_W
    return dWdt

  @property
  def derivative(self):
    return JointEq([self.dV, self.dW])

  def update(self, _t, _dt):
    V, self.W.value = self.integral(self.V, self.W, _t, self.input, dt=_dt)
    spike = bm.logical_and(self.V < self.V_th, V >= self.V_th)
    self.t_last_spike.value = bm.where(spike, _t, self.t_last_spike)
    self.V.value = V
    self.spike.value = spike
    self.input[:] = 0.
