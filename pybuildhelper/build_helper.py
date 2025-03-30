import glob
import os
import shutil
import subprocess
import sys
from typing import List, Optional, Tuple

from Cython.Build import cythonize
from setuptools import Extension, setup


def _clean_directory(dir_path: str) -> None:
    """
    Clean the specified directory if it exists.

    Args:
        dir_path (str): The path of the directory to be cleaned.
    """
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path, exist_ok=True)


def _find_py_files(
    source_dir: str, exclude_files: Optional[List[str]] = None
) -> List[str]:
    """
    Find all Python files in the source directory, excluding specified files/directories.

    Args:
        source_dir (str): The root directory to search for Python files.
        exclude_files (Optional[List[str]]): A list of files/directories to exclude (relative to source_dir).

    Returns:
        List[str]: A list of absolute paths to Python files.
    """
    py_files: List[str] = []
    exclude_files = exclude_files or []

    for root, _, files in os.walk(source_dir):
        # Skip excluded directories
        rel_root = os.path.relpath(root, source_dir)
        if any(
            rel_root.startswith(ex) or rel_root == ex
            for ex in exclude_files
            if os.path.isdir(os.path.join(source_dir, ex))
        ):
            continue

        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, source_dir)

                # Skip excluded files
                if not any(
                    rel_path == ex or rel_path.startswith(ex + os.sep)
                    for ex in exclude_files
                ):
                    py_files.append(file_path)

    return py_files


def _find_binary_files(
    source_dir: str, exclude_files: Optional[List[str]] = None
) -> List[Tuple[str, str]]:
    """
    Find all binary files (e.g., .pyd, .so, .dylib) in the source directory.

    Args:
        source_dir (str): The root directory to search for binary files.
        exclude_files (Optional[List[str]]): A list of files/directories to exclude (relative to source_dir).

    Returns:
        List[Tuple[str, str]]: A list of tuples (source_path, dest_dir) for each binary file found.
    """
    binary_exts = ("*.pyd", "*.so", "*.dylib")
    exclude_files = exclude_files or []
    results: List[Tuple[str, str]] = []

    for ext in binary_exts:
        for filepath in glob.glob(os.path.join(source_dir, "**", ext), recursive=True):
            rel_path = os.path.relpath(filepath, source_dir)

            should_exclude = any(
                os.path.normpath(rel_path).startswith(os.path.normpath(ex))
                for ex in exclude_files
            )
            if should_exclude:
                continue

            rel_dir = os.path.relpath(os.path.dirname(filepath), source_dir)
            dest_dir = rel_dir if rel_dir != "." else "."

            results.append((filepath, dest_dir))

    return results


def _copy_data_files(
    source_dir: str, dest_dir: str, data_files: Optional[List[str]] = None
) -> None:
    """
    Copy specified data files/directories from source to destination.

    Args:
        source_dir (str): The root source directory.
        dest_dir (str): The root destination directory.
        data_files (Optional[List[str]]): A list of files/directories to copy (relative to source_dir).
    """
    if not data_files:
        return

    for data in data_files:
        src_path = os.path.join(source_dir, data)
        if not os.path.exists(src_path):
            continue

        dest_path = os.path.join(dest_dir, data)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        if os.path.isdir(src_path):
            shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
        else:
            shutil.copy2(src_path, dest_path)


def _get_hidden_imports_from_requirements(
    requirements_file: str,
) -> List[str]:
    """
    Read hidden imports from a requirements file.

    Args:
        requirements_file (str): The path to the requirements file.

    Returns:
        List[str]: A list of hidden imports.
    """
    hidden_imports: List[str] = []
    with open(requirements_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("-r"):
                # Handle -r option to include requirements from another file
                sub_requirements_file = line.split(" ")[1]
                hidden_imports.extend(
                    _get_hidden_imports_from_requirements(sub_requirements_file)
                )
            elif line:
                # Add package name as hidden import
                hidden_imports.append(line.split("==")[0]) # Ignore version
    return hidden_imports


def compile(
    main_file: Optional[str] = None,
    data_files: Optional[List[str]] = None,
    exclude_files: Optional[List[str]] = None,
    source_dir: str = ".",
    intermediate_dir: str = "build",
    dist_dir: str = "dist",
) -> None:
    """
    Use Cython to compile all Python files in the source directory.

    Args:
        main_file (Optional[str]): The main Python file (relative to source_dir) that won't be compiled but copied.
        data_files (Optional[List[str]]): A list of data files/directories to include (relative to source_dir).
        exclude_files (Optional[List[str]]): A list of files/directories to exclude from compilation (relative to source_dir).
        source_dir (str): The source directory containing Python files.
        intermediate_dir (str): The directory for intermediate build files.
        dist_dir (str): The directory for final compiled files.
    """
    # Clean and create directories
    _clean_directory(intermediate_dir)
    _clean_directory(dist_dir)

    # Find all Python files to compile
    py_files = _find_py_files(source_dir, exclude_files)

    # Exclude main file if specified
    if main_file:
        main_file_path = os.path.join(source_dir, main_file)
        if main_file_path in py_files:
            py_files.remove(main_file_path)

    # Convert Python files to C extensions
    ext_modules: List[Extension] = []
    for py_file in py_files:
        rel_path = os.path.relpath(py_file, source_dir)
        module_name = rel_path.replace(".py", "").replace(os.sep, ".")
        ext_modules.append(Extension(module_name, [py_file]))

    # Compile with Cython
    setup(
        ext_modules=cythonize(
            ext_modules,
            build_dir=intermediate_dir,
            compiler_directives={"language_level": "3"},
        ),
        script_args=["build_ext", "--build-lib", dist_dir],
    )

    # Copy main file if specified
    if main_file:
        shutil.copy2(
            os.path.join(source_dir, main_file), os.path.join(dist_dir, main_file)
        )

    # Copy data files
    _copy_data_files(source_dir, dist_dir, data_files)

    print(f"Compilation complete. Compiled files are in {dist_dir}")


def pack(
    main_file: str,
    data_files: Optional[List[str]] = None,
    exclude_files: Optional[List[str]] = None,
    hidden_imports: Optional[List[str]] = None,
    hidden_imports_from_requirements: Optional[str] = None,
    executable_name: Optional[str] = None,
    onefile: Optional[bool] = False,
    source_dir: str = ".",
    intermediate_dir: str = "build",
    dist_dir: str = "dist",
) -> None:
    """
    Use PyInstaller to pack files into a single package.

    Args:
        main_file (str): The main Python file (relative to source_dir) that will always be packed even exclude_files specifies it.
        data_files (Optional[List[str]]): A list of data files/directories to include (relative to source_dir).
        exclude_files (Optional[List[str]]): A list of files/directories to exclude from package (relative to source_dir).
        hidden_imports (Optional[List[str]]): A list of modules to include in the package (e.g., ['numpy']). This will override hidden_imports_from_requirements.
        hidden_imports_from_requirements (Optional[str]): Path to a requirements.txt file to extract hidden imports. This will be ignored if hidden_imports is provided.
        executable_name (Optional[str]): The name of the final executable.
        onefile (Optional[bool]): If True, create a single executable file. Otherwise, create a directory with dependencies.
        source_dir (str): The source directory containing files to package.
        intermediate_dir (str): The directory for intermediate files.
        dist_dir (str): The directory for final package.
    """
    # Clean directories
    _clean_directory(intermediate_dir)
    _clean_directory(dist_dir)

    # Prepare absolute paths
    abs_source_dir = os.path.abspath(source_dir)
    abs_main_file = os.path.join(abs_source_dir, main_file)

    # Prepare PyInstaller command
    if not executable_name:
        executable_name = os.path.splitext(os.path.basename(main_file))[0]

    cmd: List[str] = [
        "pyinstaller",
        "--name",
        executable_name,
        "--distpath",
        os.path.abspath(dist_dir),
        "--workpath",
        os.path.abspath(intermediate_dir),
        "--specpath",
        os.path.abspath(intermediate_dir),
    ]

    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    # Add binary files
    binary_pairs = _find_binary_files(
        source_dir=os.path.abspath(source_dir), exclude_files=exclude_files
    )
    if binary_pairs:
        for src, dest in binary_pairs:
            cmd.extend(["--add-binary", f"{src}:{dest}"])

    # Add data files
    if data_files:
        for data in data_files:
            src_path = os.path.join(abs_source_dir, data)
            if not os.path.exists(src_path):
                continue

            # Convert to relative path from spec file location
            rel_path = os.path.relpath(src_path, os.path.abspath(intermediate_dir))
            dest_path = os.path.dirname(data)

            if os.path.isdir(src_path):
                # For directories, we need to include all files
                for root, _, files in os.walk(src_path):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_file_path = os.path.relpath(
                            full_path, os.path.abspath(intermediate_dir)
                        )
                        file_dest_path = os.path.relpath(
                            os.path.dirname(full_path), abs_source_dir
                        )
                        cmd.extend(
                            [
                                "--add-data",
                                f"{rel_file_path}:{file_dest_path}",
                            ]
                        )
            else:
                # For single files
                cmd.extend(["--add-data", f"{rel_path}:{dest_path}"])

    # Add exclude files
    if exclude_files:
        for ex in exclude_files:
            # Get module name without .py extension
            module_name = os.path.splitext(ex)[0]
            # Replace path separators with dots
            module_name = module_name.replace(os.sep, ".")
            cmd.extend(["--exclude-module", module_name])

    # Add hidden imports
    if hidden_imports:
        for module in hidden_imports:
            cmd.extend(["--hidden-import", module])
    elif hidden_imports_from_requirements:
        hidden_imports = _get_hidden_imports_from_requirements(
            hidden_imports_from_requirements
        )
        for module in hidden_imports:
            cmd.extend(["--hidden-import", module])

    # Add main script (relative to spec file location)
    rel_main_path = os.path.relpath(abs_main_file, os.path.abspath(intermediate_dir))
    cmd.append(rel_main_path)

    # Change working directory to intermediate_dir to ensure proper path resolution
    original_dir = os.getcwd()
    os.makedirs(intermediate_dir, exist_ok=True)
    os.chdir(intermediate_dir)

    try:
        print("Running PyInstaller with command:")
        print(" ".join(cmd))
        subprocess.run(cmd, check=True)
        print(f"Packaging complete. Package is in {os.path.abspath(dist_dir)}")
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller failed with error: {e}")
        sys.exit(1)
    finally:
        os.chdir(original_dir)  # Always restore original working directory


def compile_and_pack(
    main_file: str,
    data_files: Optional[List[str]] = None,
    exclude_files: Optional[List[str]] = None,
    hidden_imports: Optional[List[str]] = None,
    hidden_imports_from_requirements: Optional[str] = None,
    executable_name: Optional[str] = None,
    onefile: Optional[bool] = False,
    source_dir: str = ".",
    compile_intermediate_dir: str = "build/compile",
    compile_dist_dir: str = "build/compile_dist",
    pack_intermediate_dir: str = "build/pack",
    pack_dist_dir: str = "dist",
) -> None:
    """
    First compile with Cython then pack with PyInstaller.

    Args:
        main_file (str): The main Python file (relative to source_dir) that won't be compiled but packed even exclude_files specifies it.
        data_files (Optional[List[str]]): A list of data files/directories to include (relative to source_dir).
        exclude_files (Optional[List[str]]): A list of files/directories to exclude (relative to source_dir).
        hidden_imports (Optional[List[str]]): A list of modules to include in the package. This will override hidden_imports_from_requirements.
        hidden_imports_from_requirements (Optional[str]): Path to a requirements.txt file to extract hidden imports. This will be ignored if hidden_imports is provided.
        executable_name (Optional[str]): The name of the final executable.
        onefile (Optional[bool]): If True, create a single executable file. Otherwise, create a directory with dependencies.
        source_dir (str): The source directory containing Python files.
        compile_intermediate_dir (str): The intermediate directory for compilation.
        compile_dist_dir (str): The output directory for compiled files.
        pack_intermediate_dir (str): The intermediate directory for packaging.
        pack_dist_dir (str): The output directory for final package.
    """
    # Step 1: Compile with Cython
    compile(
        main_file=main_file,
        data_files=data_files,
        exclude_files=exclude_files,
        source_dir=source_dir,
        intermediate_dir=compile_intermediate_dir,
        dist_dir=compile_dist_dir,
    )

    # Step 2: Package with PyInstaller
    pack(
        main_file=main_file,
        data_files=data_files,
        exclude_files=exclude_files,
        hidden_imports=hidden_imports,
        hidden_imports_from_requirements=hidden_imports_from_requirements,
        executable_name=executable_name,
        onefile=onefile,
        source_dir=compile_dist_dir,
        intermediate_dir=pack_intermediate_dir,
        dist_dir=pack_dist_dir,
    )

    print(f"Compilation and packaging complete. Package is in {pack_dist_dir}")
