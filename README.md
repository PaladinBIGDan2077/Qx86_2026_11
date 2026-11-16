# Qx86

Welcome to the Github repository for Qx86. 
Qx86 is an Intel 8080/Z80 emulator which executes all salient points of Intel 8080/Z80 execution on IBMs quantum computers.

## Background
One of the major obstacles to the adoption of quantum computing is the requirement to define quantum circuits at the quantum gate level. Many programmers are familiar with high-level or low-level programming languages but not quantum gates nor the low-level quantum logic required to derive useful results from quantum computers. The steep learning curve involved when progressing from quantum gates to complex simulations such as Shor’s algorithm has proven too much for many developers. This software addresses this challenge by providing a Software Development Kit (SDK), translation layer, emulator and a framework of techniques for executing Intel 8080/Z80 assembler on a quantum computer, i.e. all salient points of CPU execution, logic, arithmetic and bitwise manipulation will be executed on the quantum computer using quantum circuits. Developers and researchers can use the SDK to write code in Intel 8080/Z80 assembler which is executed locally via traditional emulation and remotely on a quantum computer in parallel. The emulator features side-by-side code execution with visibility of the running quantum circuit and re-usable/overridable methods. This enables programmers to learn, reuse and contrast techniques for performing any traditional CPU based technique/instruction on a quantum computer; e.g. a programmer may know how to multiply and perform checks on a classical CPU but is not able to perform the same tasks in a quantum implementation, this SDK allows the programmer to pick and choose the methods they would like to use to fulfil their requirements.



## Installation and use
Due to the nature of this work, you will need a basic understanding of development, assembler and quantum computers.
Note - The code in this repository has been tested with Python 3.7 to 3.12 on Windows 10. The IBM hardware and Linux terminal updates described below were tested with Qiskit 2.6, qiskit-ibm-runtime 0.52 and qiskit-aer 0.18.

### 1. Install Python
Windows: download and install the latest version of Python, then install the Microsoft Visual C++ runtime.
```
https://www.python.org/downloads/windows/
https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170
```
Linux: use your distribution's Python 3. A virtual environment is recommended:
```
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Qiskit and the other dependencies
```
python -m pip install qiskit qiskit-ibm-runtime qiskit-aer
python -m pip install matplotlib pylatexenc
```
Windows only (Linux and macOS already include curses):
```
python -m pip install windows-curses
```

### 3. Get the files
Clone or download this repository. You need these files in the same folder:
```
Account.py      - Saves your IBM Quantum account on this computer
cpu3.py         - The orchestration script
z80.py          - The Intel 8080/Z80 emulator
q80.py          - The Intel 8080/Z80 emulator with its instructions overridden for execution on a quantum computer
qpu_backend.py  - Chooses where circuits run (local simulator or IBM hardware) and sends jobs to IBM
```

### 4. Try it on the local simulator first
By default Qx86 runs its quantum circuits on the Qiskit Aer simulator on your own computer, so you can test without an IBM account. Make your terminal window full screen (curses stops with an error if the emulator screen does not fit), then run:
```
python cpu3.py
```
This runs the traditional emulator and the quantum emulator in parallel. The pseudo RAM contains an example program which loads the A register with 04h, increments A, pushes AF and then halts. The INC instruction runs as a quantum circuit (method INC2), and both sides should finish with A = 05h.

![image](https://user-images.githubusercontent.com/66572228/199703390-af98205e-d405-4c52-92bf-154daf02605d.png)

To exit the emulator, press the Q key. Every quantum circuit that was built is then printed in the terminal and saved to circuits.txt. (While the emulator is running this text is held back, because on Linux it would otherwise be drawn on top of the emulator screen.)

### 5. Create an IBM Quantum account and API key
IBM's cloud simulators (such as ibmq_qasm_simulator) were retired on 15 May 2024, so running on IBM now means running on real quantum hardware.

1. Sign up or log in at https://quantum.cloud.ibm.com/
2. Create an API key from the dashboard and copy it.
3. Note the name of your instance (for example the default free "Open" plan instance).

### 6. Save your account
Edit Account.py and paste in your API key. Optionally add your instance name to stop the "Instance was not set" warnings:
```python
QiskitRuntimeService.save_account(channel="ibm_quantum_platform", token="YOUR_API_KEY", instance="YOUR_INSTANCE_NAME", overwrite=True)
```
Then run it once:
```
python Account.py
```
Note - The old channel="ibm_quantum" no longer works with current versions of qiskit-ibm-runtime; use "ibm_quantum_platform".

### 7. Switch to IBM hardware
Open qpu_backend.py and change:
```python
QUANTUM_TARGET = "ibm"     # "local" = Aer simulator on this computer, "ibm" = real IBM QPU
IBM_BACKEND = None         # None = least busy QPU, or a name such as "ibm_fez"
MAX_IBM_JOBS = 20          # safety cap, see below
```
You can also set these as environment variables instead of editing the file, for example on Linux:
```
QUANTUM_TARGET=ibm python cpu3.py
```
Run the emulator again. When the program counter reaches the INC instruction (3C) execution pauses while the job waits in IBM's queue. Each job is logged with its job ID in the terminal output and in ibm_jobs.log, and appears under Workloads on the IBM Quantum Platform, e.g.:
```
[Qx86] Sending quantum circuits to IBM backend: ibm_fez
[Qx86] IBM job 1: dbtlrsmhrjis73e7e150 (156 qubits, 2000 shots) - waiting in queue...
[Qx86] IBM job dbtlrsmhrjis73e7e150 done
```
Every quantum instruction (and, for method 1, every individual gate) is a separate IBM job that uses your plan's QPU time. After MAX_IBM_JOBS jobs Qx86 automatically switches to the local simulator for the rest of the run. Set it to 0 to remove the limit.

![image](https://user-images.githubusercontent.com/66572228/199703816-66f6fc91-3521-4a6a-b134-af0d646c28ba.png)

### 8. Choose which instructions run on the quantum computer
For the built-in example programs, edit the Example program section of cpu3.py and un-comment the program and the matching line, e.g. #qpu.QuantumExecute = "INC1"

![image](https://user-images.githubusercontent.com/66572228/199703594-21d78f1e-a9b6-44c6-be81-bdf6e7841f28.png)

The available methods are listed at the top of q80.py (INC1, INC2, ADD2, XOR2, LOAD3, ...).

### 9. Run your own binaries
Assemble your program to a raw binary (for example with Vasm) and pass it on the command line. The optional second argument chooses the quantum method; without it the binary runs fully classically on both emulators.
```
python cpu3.py myprogram.bin INC2
```

![image](https://user-images.githubusercontent.com/66572228/199703991-298904eb-b147-4de0-9e4b-002be4ee2446.png)


## FAQ
- Why does it take so long to execute, I thought quantum computers were fast?<br>
The majority of the delay is due to the queuing mechanism we have to join for execution, but other delays include the latency of the API call and the fact that quantum computers are not designed to perform traditional logic operations.

- Why can’t I run the entire binary on the quantum computer?<br>
As you would have to join a queue for each instruction it would be extremely slow. You may edit the methods in q80.py to do this but each instruction will take circa 30 seconds to call and execute. The MAX_IBM_JOBS setting in qpu_backend.py limits how many jobs one run can send.

- Why do the example specify a INC2, DEC2 etc?<br>
I have included multiple methods for each instruction, method 1 (INC1) calls each gate separately whereas method 2 (INC2) implements a quantum circuit for the entire (where possible) instruction so is much faster.

- Why call it Qx86 when you only have Intel 8080/Z80 compatibility?<br>
Artistic license! Also q80 is a television set and a qx80 is a car so those names were already taken. Intel x86 compatibility is planned but will require more qubits due to the larger internal registers.

- I get an error when I choose a real Quantum computer.<br>
You must choose a quantum computer that meets the minimum requirements, all instructions executed using method 1 require upto 5 qubits whereas all instructions using method 2 require upto 32 qubits.
Also check that you saved your account with channel="ibm_quantum_platform" (step 6). The older backend.run() interface and the ibmq_qasm_simulator cloud simulator have been removed by IBM; qpu_backend.py sends jobs through the current SamplerV2 interface instead.

- The screen is garbled on Linux.<br>
Use the updated cpu3.py, which holds back printed circuits until you exit, and make the terminal window full screen.

- Why turn a $1,000,000 quantum computer into a 40 year old CPU?<br>
The motivation for this SDK is to provide a learning tool and re-useable reference framework, a framework that will help bridge the steep learning curve and enable developers to drive useful results from quantum computers. The framework will show developers that quantum computers can do anything a traditional computer can, just in a different manner. The SDK also prepares the groundwork (via the delivery of the emulators and translation layer) for a possible scenario where the overhead for performing classical computations on a quantum computer is not so large. This is not to say that the value of the SDK is purely theoretical, as even with today’s capability many quantum-based simulations require aspects of traditional logic which are included as re-usable methods within the framework. 
Emulating a CPU was chosen as a goal for this SDK as it provides a provable mechanism for delivering every logic/arithmetic/bitwise function needed in a traditional computer. It was not my aim to reduce a quantum computer to a device only capable of traditional logic-based calculations but describe, prove and demonstrate how to perform those calculations. The logic calculations can be used to form parts of many quantum-based calculations and are found in a framework which developers are familiar with and can readily re-use.
