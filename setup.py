import setuptools

# Read the long - description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Set up the package information
setuptools.setup(
    name="pybuildhelper",
    version="0.0.1",
    author="pax",
    author_email="coolwinding@foxmail.com",
    description="A python build helper library to compile (obfuscate) and pack Python files using Cython and PyInstaller",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xfally/pybuildhelper",
    packages=setuptools.find_packages(),
    install_requires=[
        "Cython",
        "pyinstaller",
        "setuptools",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
