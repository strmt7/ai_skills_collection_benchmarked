# Official Guidance

- `pybind11` exceptions docs:
  `py::error_already_set` is the correct C++ exception type when Python code
  raises during a C++ callback or other Python-object operation.
- `pybind11` exceptions docs:
  `pybind11::stop_iteration` maps to Python `StopIteration` and is intended for
  custom iterator implementations.
- `pybind11` exceptions docs:
  `noexcept` functions must catch and discard or log Python exceptions instead
  of letting them escape.
- `pybind11` functions docs:
  explicit argument policy matters when `None` handling is part of the public
  contract.

Primary references:

- https://pybind11.readthedocs.io/en/stable/advanced/exceptions.html
- https://pybind11.readthedocs.io/en/stable/advanced/functions.html
