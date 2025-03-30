# Python Build Helper

## Overview

A python build helper library to compile (obfuscate) and pack Python files using Cython and PyInstaller.

This Python module, `build_helper.py`, provides a set of functions to simplify the process of compiling Python code using Cython and packaging it into a single package using PyInstaller. It allows you to manage the compilation and packaging process with ease, including handling data files, excluding specific files or directories, and specifying hidden imports.

## Features

- **Cython Compilation (Obfuscation)**: Compile (Obfuscate) Python files to C extensions using Cython.
- **PyInstaller Packaging**: Package the compiled files into a single package using PyInstaller.
- **Data File Management**: Include data files and directories in the compilation and packaging process.
- **Exclusion Support**: Exclude specific files or directories from compilation and packaging.
- **Hidden Imports**: Specify additional modules to be included in the package.

## Installation

You can install using `pip`:

```bash
pip install pybulidhelper
```

or you can install from source:

```bash
python setup.py install
```

## Usage

### Compiling Python Files

To compile all Python files in a directory using Cython, you can use the `compile` function:

```python
from build_helper import compile

compile(
    main_file="main.py",
    data_files=["data"],
    exclude_files=["test"],
    source_dir=".",
    intermediate_dir="build",
    dist_dir="dist"
)
```

### Packaging into a Single Package

To package the compiled files into a single package using PyInstaller, you can use the `pack` function:

```python
from build_helper import pack

pack(
    main_file="main.py",
    data_files=["data"],
    exclude_files=["test"],
    hidden_imports=["numpy"],
    executable_name="my_app",
    onefile=True,
    source_dir=".",
    intermediate_dir="build",
    dist_dir="dist"
)
```

> `hidden_imports` is an optional parameter that allows you to specify additional modules to be included in the package. Maybe you have a `requirements.txt` file, instead of specifying each module manually, you can use `hidden_imports_from_requirements="requirements.txt"` to specify the modules in the `requirements.txt` file.
>
> `onefile` is set to `False` by default, but you can set it to `True` to create a single executable file.

### Compiling and Packaging

To perform both compilation and packaging in one step, you can use the `compile_and_pack` function:

```python
from build_helper import compile_and_pack

compile_and_pack(
    main_file="main.py",
    data_files=["data"],
    exclude_files=["test"],
    hidden_imports=["numpy"],
    executable_name="my_app",
    onefile=True,
    source_dir=".",
    compile_intermediate_dir="build/compile",
    compile_dist_dir="build/compile_dist",
    pack_intermediate_dir="build/pack",
    pack_dist_dir="dist"
)
```

## License

This project is licensed under the [MIT License](LICENSE).
