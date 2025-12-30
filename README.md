# Linux Shared Object Function Lister

A small Python tool that lists **native functions** available in a Linux shared object (`.so`) file.

The tool inspects the ELF binary directly and reports functions that are callable via `ctypes.CDLL`, making it suitable as a prototype for IDE features such as Python ↔ C/C++ completion.

---



## Overview

- Parses Linux ELF shared objects (`.so`)
- Lists exported native functions from the dynamic symbol table (`.dynsym`)
- Supports:
  - C functions
  - C++ functions exported with `extern "C"`
- Excludes:
  - static/internal functions
  - imported (undefined) symbols
  - data symbols
  - mangled C++ symbols
- Includes compile-based unit tests

---

## Project Structure
```
.
├── function_lister.py
├── tests/
│   ├── __init__.py
│   └── tests.py
└── README.md
```


## Requirements

- Linux
- Python 3.9+
- `pyelftools`

For tests:
- `gcc` (C tests)
- `g++` (C++ tests)

Install dependency:
```bash
pip install pyelftools
```
## Usage

**Command-line usage**

Run the tool with the path to a shared object:
```bash
python function_lister.py path/to/library.so
```
**Python function**
```python
from function_lister import list_native_functions

functions = list_native_functions("example.so")
```
Output 
```text
['c_add', 'c_hello']
```

## Testing
Tests are implemented using **unittest**. 

**What is tested?**

- Exported C functions are listed
- C++ functions exported with extern "C" are listed
- Mangled C++ functions are excluded
- Static/internal and data symbols are excluded
- Imported symbols are excluded
- Missing files and invalid ELF inputs raise errors

From project root run command:
```bash
python -m unittest -v
```

## Notes

- Mangled C++ symbols are excluded since they are not safely callable via `ctypes`.