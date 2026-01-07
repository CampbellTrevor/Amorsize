"""
Setup configuration for Amorsize package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="amorsize",
    version="0.1.0",
    author="Amorsize Contributors",
    description="Dynamic Parallelism Optimizer & Overhead Calculator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CampbellTrevor/Amorsize",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        # psutil is optional but recommended
    ],
    extras_require={
        "full": ["psutil>=5.8.0"],
        "dev": ["pytest>=7.0.0", "pytest-cov>=3.0.0"],
    },
)
