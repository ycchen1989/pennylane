# Copyright 2018 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
r"""
Embeddings
==========

**Module name:** :mod:`pennylane.templates.embeddings`

.. currentmodule:: pennylane.templates.embeddings

This module provides quantum circuit architectures that can serve as an embedding of inputs
(represented by the gate parameters) into a quantum state (see also Schuld & Killoran 2019
:cite:`schuld2019`).

Provided embeddings
--------------------

For qubit architectures:
************************

.. autosummary::

    AngleEmbedding
    AmplitudeEmbedding
    BasisEmbedding

For continuous-variable architectures:
**************************************

.. autosummary::

    SqueezingEmbedding
    DisplacementEmbedding

Code details
^^^^^^^^^^^^
"""
#pylint: disable-msg=too-many-branches,too-many-arguments,protected-access
from pennylane import RX, RY, RZ, BasisState, Squeezing, Displacement, QubitStateVector


def AngleEmbedding(features, n_wires, rotation='X'):
    """
    Uses the entries of `features` as rotation angles of qubits.

    The details of the strategy are defined by the `rotation` parameter:
     * `rotation = 'X'` uses the features to chronologically apply Pauli-X rotations to qubits
     * `rotation = 'Y'` uses the features to chronologically apply Pauli-Y rotations to qubits
     * `rotation = 'Z'` uses the features to chronologically apply Pauli-Z rotations to qubits
     * `rotation = 'XY'` performs the 'X' strategy using the first `n_wires` features, and the 'Y' strategy using the
        remaining qubits
     * `rotation = 'XY'` performs the 'X' strategy using the first `n_wires` features, the 'Y' strategy using the
        next `n_wires` features, and the 'Z' strategy using the remaining features

    If there are fewer entries in `features` than rotations prescribed by the strategy, the circuit does not apply the
    remaining rotation gates.
    If there are fewer rotations than entries in `features`, the circuit will not use the remaining features.

    This embedding method can also be used to encode a binary sequence into a basis state. Choose rotation='X'
    and features that contain an angle of :math:`\pi /2` where a qubit has to be prepared in state 1.

    Args:
        features (array): Input array of shape (N, ), where N is the number of input features to embed
        n_wires (int): Number of qubits in the circuit
        rotation (str): Strategy of embedding

    """
    if rotation == 'XYZ':
        if len(features) > 3 * n_wires:
            raise ValueError("Number of features to embed cannot be larger than 3*num_wires, "
                             "but is {}.".format(len(features)))

        for op in range(len(features)):
            if op < n_wires:
                RX(features[op], wires=op)
            elif op < 2*n_wires:
                RY(features[op], wires=op)
            else:
                RZ(features[op], wires=op)

    if rotation == 'XY':
        if len(features) > 2 * n_wires:
            raise ValueError("Number of features to embed cannot be larger than 2*num_wires, "
                             "but is {}.".format(len(features)))

        for op in range(len(features)):
            if op < n_wires:
                RX(features[op], wires=op)
            else:
                RY(features[op], wires=op)

    else:
        if len(features) > n_wires:
            raise ValueError("Number of features to embed cannot be larger than num_wires, "
                             "but is {}.".format(len(features)))
        if rotation == 'X':
            for op in range(len(features)):
                RX(features[op], wires=op)

        elif rotation == 'Y':
            for op in range(len(features)):
                RY(features[op], wires=op)

        elif rotation == 'Z':
            for op in range(len(features)):
                RZ(features[op], wires=op)


def BasisEmbedding(basis_state, n_qubits):
    """
    Prepares a quantum state in the state `basis_state'.

    For example, for `basis_state' = [0, 1, 0], the quantum system will be prepared in state :math:`|010 \rangle `.

    .. note:: BasisEmbedding uses PennyLane's :fun:`BasisState()` and only works in conjunction with
              devices that implement this function.
    Args:
        features (array): Input array of shape (N, ), where N is the number of input features to embed
        n_qubits (int): Number of qubits in the circuit
    """
    if n_qubits != len(basis_state):
        raise ValueError("BasisEmbedding requires a feature vector of size n_qubits which is {}, "
                         "got {}.".format(n_qubits, len(basis_state)))
    BasisState(basis_state, wires=range(n_qubits))


def AmplitudeEmbedding(features, n_qubits):
    """
    Prepares a quantum state whose amplitude vector is given by `features`.

    `features` has to be an array representing a 1-d vector of unit length and with 2**`n_qubits` entries.

    .. note:: AmplitudeEmbedding uses PennyLane's :fun:`QubitStateVector()` and only works in conjunction with
              devices that implement this function.

    Args:
        features (array): Input array of shape (N, ), where N is the number of input features to embed
        n_qubits (int): Number of qubits in the circuit
    """

    if 2**n_qubits != len(features):
        raise ValueError("AmplitudeEmbedding requires a feature vector of size 2**n_qubits which is {}, "
                         "got {}.".format(2**n_qubits, len(features)))

    QubitStateVector(features, wires=range(n_qubits))


def SqueezingEmbedding(features, n_wires, execution='amplitude', c=0.1):
    """
    Encodes the entries of `features` into the squeezing phases :math:`\phi` or amplitudes :math:`r` of the modes of
    a continuous-variable quantum state.

    The mathematical definition of the squeezing gate is given by the operator

    ..math::
            S(z) = \exp\left(\frac{r}{2}\left(e^{-i\phi}\a^2 -e^{i\phi}{\ad}^{2} \right) \right),

    where :math:`\a` and :math:`\ad` are the bosonic creation and annihilation operators.

    `features` has to be an array of `n_wires` floats.

    Args:
        features (array): Binary sequence to encode
        n_wires (int): Number of qubits in the circuit
        execution (str): 'phase' encodes the input into the phase of single-mode squeezing, while
                         'amplitude' uses the amplitude.
        c (float): parameter setting the value of the phase of all squeezing gates if execution='amplitude', or the
                   amplitude of all squeezing gates if execution='phase' to a constant.
    """

    if n_wires != len(features):
        raise ValueError("SqueezingEmbedding requires a feature vector of size n_wires which is {}"
                         ", got {}.".format(n_wires, len(features)))

    for i in range(n_wires):
        if execution == 'amplitude':
            Squeezing(features[i], c, wires=i)
        elif execution == 'phase':
            Squeezing(c, features[i], wires=i)
        else:
            raise ValueError("Execution strategy {} not known. Has to be 'phase' or 'amplitude'.".format(execution))


def DisplacementEmbedding(features, n_wires, execution='amplitude', c=0.1):
    """
    Encodes the entries of `features` into the displacement phases :math:`\phi` or amplitudes :math:`r` of the modes of
    a continuous-variable quantum state.

    The mathematical definition of the displacement gate is given by the operator

    ..math::
            D(\alpha) = \exp(r (e^{i\phi}\ad -e^{-i\phi}\a)),

    where :math:`\a` and :math:`\ad` are the bosonic creation and annihilation operators.

    `features` has to be an array of `n_wires` floats.

    Args:
        features (array): Binary sequence to encode
        n_wires (int): Number of qubits in the circuit
        execution (str): 'phase' encodes the input into the phase of single-mode squeezing, while
                         'amplitude' uses the amplitude.
        c (float): parameter setting the value of the phase of all squeezing gates if execution='amplitude', or the
                   amplitude of all squeezing gates if execution='phase' to a constant.
    """

    if n_wires != len(features):
        raise ValueError("DisplacementEmbedding requires a feature vector of size n_wires which is {}, "
                         "got {}.".format(n_wires, len(features)))

    for i in range(n_wires):
        if execution == 'amplitude':
            Displacement(features[i], c, wires=i)
        elif execution == 'phase':
            Displacement(c, features[i], wires=i)
        else:
            raise ValueError("Execution strategy {} not known. Has to be 'phase' or 'amplitude'.".format(execution))