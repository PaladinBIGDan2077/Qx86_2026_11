"""
qpu_backend.py - lets Qx86 send its circuits to real IBM quantum hardware.

Why this file exists
--------------------
q80.py was written for the old Qiskit API: every quantum gate does

    circuit = transpile(circuit, QuantumComputer)
    result  = QuantumComputer.run(circuit, shots=shots, memory=True).result()
    memory  = result.get_memory(circuit)

That still works with the local AerSimulator, but IBM removed backend.run()
for its hardware (IBMBackend.run now raises an error) and retired the cloud
simulators (ibmq_qasm_simulator) on 15 May 2024. Jobs must go through the
SamplerV2 primitive instead.

IBMQuantumComputer below wraps SamplerV2 behind the same run()/get_memory()
interface, so none of the ~70 gate methods in q80.py need to change.

Settings
--------
Edit the three values below (or set environment variables of the same name).
"""

import os
import sys

from qiskit import transpile as _qiskit_transpile
from qiskit_aer import AerSimulator

# "local" = Aer simulator on this PC (fast, nothing is sent to IBM)
# "ibm"   = real IBM quantum hardware via your saved account (see Account.py)
QUANTUM_TARGET = os.environ.get("QUANTUM_TARGET", "ibm")

# Name of the IBM QPU to use, e.g. "ibm_brisbane". None = least busy one.
IBM_BACKEND = os.environ.get("IBM_BACKEND") or None

# Safety cap: every quantum gate/instruction call is one IBM job, and each job
# uses your plan's QPU minutes. After this many jobs Qx86 falls back to the
# local simulator for the rest of the run. Set to 0 for no limit.
MAX_IBM_JOBS = int(os.environ.get("MAX_IBM_JOBS", "20"))


def _log(msg):
    # cpu3.py runs under curses, which owns the screen, so log to stderr
    # and to a file you can read afterwards.
    with open("ibm_jobs.log", "a") as f:
        f.write(msg + "\n")
    print(msg, file=sys.stderr)


class _MemoryResult:
    """Mimics the parts of qiskit.result.Result that q80.py uses."""

    def __init__(self, memory):
        self._memory = memory

    def get_memory(self, circuit=None):
        return self._memory

    def get_counts(self, circuit=None):
        counts = {}
        for m in self._memory:
            counts[m] = counts.get(m, 0) + 1
        return counts


class _Job:
    def __init__(self, result):
        self._result = result

    def result(self):
        return self._result


def _memory_from_sampler(pub_result, circuit):
    """Rebuild Aer-style memory strings from a SamplerV2 result.

    Aer formats each shot as the classical registers joined by spaces, last
    register first (e.g. "101 000" for registers c then meas). q80.py indexes
    into those strings, so the layout has to match exactly.
    """
    regs = [getattr(pub_result.data, creg.name).get_bitstrings()
            for creg in circuit.cregs]
    return [" ".join(shot[::-1]) for shot in zip(*regs)]


class IBMQuantumComputer:
    """Drop-in replacement for AerSimulator that runs on IBM hardware."""

    def __init__(self, backend_name=None, max_jobs=MAX_IBM_JOBS):
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
        from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

        service = QiskitRuntimeService()  # uses the account saved by Account.py
        if backend_name:
            self.backend = service.backend(backend_name)
        else:
            self.backend = service.least_busy(operational=True, simulator=False)
        self.pass_manager = generate_preset_pass_manager(
            backend=self.backend, optimization_level=1)
        self.sampler = SamplerV2(mode=self.backend)
        self.local = AerSimulator(method="matrix_product_state")
        self.max_jobs = max_jobs
        self.jobs_sent = 0
        _log(f"[Qx86] Sending quantum circuits to IBM backend: {self.backend.name}")

    def transpile(self, circuit):
        if self._use_local():
            return _qiskit_transpile(circuit, self.local)
        return self.pass_manager.run(circuit)

    def _use_local(self):
        return self.max_jobs and self.jobs_sent >= self.max_jobs

    def run(self, circuit, shots=2000, memory=True, **kwargs):
        if self._use_local():
            return self.local.run(circuit, shots=shots, memory=memory)

        job = self.sampler.run([circuit], shots=shots)
        self.jobs_sent += 1
        _log(f"[Qx86] IBM job {self.jobs_sent}: {job.job_id()} "
             f"({circuit.num_qubits} qubits, {shots} shots) - waiting in queue...")
        pub_result = job.result()[0]
        _log(f"[Qx86] IBM job {job.job_id()} done")
        if self._use_local():
            _log(f"[Qx86] Reached MAX_IBM_JOBS={self.max_jobs}; "
                 "using the local simulator from now on")
        return _Job(_MemoryResult(_memory_from_sampler(pub_result, circuit)))


def make_quantum_computer():
    if QUANTUM_TARGET.lower() == "ibm":
        return IBMQuantumComputer(IBM_BACKEND)
    return AerSimulator(method="matrix_product_state")


def transpile(circuit, backend=None, **kwargs):
    """Replaces qiskit.transpile inside q80.py so IBM circuits are mapped
    onto the real chip's qubits and native gates (required by SamplerV2)."""
    if isinstance(backend, IBMQuantumComputer):
        return backend.transpile(circuit)
    return _qiskit_transpile(circuit, backend, **kwargs)
