"""
Setup configuration for Amorsize package.
"""

from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="amorsize",
    version="0.1.0",
    author="Amorsize Contributors",
    description="Dynamic Parallelism Optimizer & Overhead Calculator - Automatically determines optimal n_jobs and chunksize for Python multiprocessing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CampbellTrevor/Amorsize",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="multiprocessing parallelization optimization performance amdahl overhead",
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "full": ["psutil>=5.8.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/CampbellTrevor/Amorsize/issues",
        "Source": "https://github.com/CampbellTrevor/Amorsize",
    },
)
