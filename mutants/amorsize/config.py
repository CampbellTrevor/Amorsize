"""
Configuration export/import module for saving and loading optimization parameters.

This module allows users to:
- Save optimal configurations to files (JSON/YAML)
- Load configurations and reuse them across runs
- Share configurations between team members
- Track configuration metadata (system info, timestamps, etc.)
"""

import json
import platform
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .system_info import (
    get_available_memory,
    get_multiprocessing_start_method,
    get_physical_cores,
)


class ConfigData:
    """
    Container for configuration data with metadata.

    Stores parallelization parameters along with system information,
    timestamps, and optional user notes for documentation.
    """

    def __init__(
        self,
        n_jobs: int,
        chunksize: int,
        executor_type: str = "process",
        estimated_speedup: float = 1.0,
        function_name: Optional[str] = None,
        data_size: Optional[int] = None,
        avg_execution_time: Optional[float] = None,
        notes: Optional[str] = None,
        system_info: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
        source: str = "optimize"
    ):
        """
        Initialize configuration data.

        Args:
            n_jobs: Number of workers
            chunksize: Items per chunk
            executor_type: 'process' or 'thread'
            estimated_speedup: Expected speedup factor
            function_name: Name of the function (if available)
            data_size: Number of items in dataset
            avg_execution_time: Average time per item (seconds)
            notes: Optional user notes
            system_info: System information (auto-populated if None)
            timestamp: ISO timestamp (auto-populated if None)
            source: Source of configuration ('optimize', 'tune', 'manual')
        """
        self.n_jobs = n_jobs
        self.chunksize = chunksize
        self.executor_type = executor_type
        self.estimated_speedup = estimated_speedup
        self.function_name = function_name
        self.data_size = data_size
        self.avg_execution_time = avg_execution_time
        self.notes = notes
        self.source = source

        # Auto-populate system info if not provided
        if system_info is None:
            self.system_info = _capture_system_info()
        else:
            self.system_info = system_info

        # Auto-populate timestamp if not provided
        if timestamp is None:
            self.timestamp = datetime.now().isoformat()
        else:
            self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format."""
        # Import version dynamically to avoid circular imports
        try:
            from . import __version__
            version = __version__
        except ImportError:
            version = '0.1.0'  # Fallback

        return {
            'n_jobs': self.n_jobs,
            'chunksize': self.chunksize,
            'executor_type': self.executor_type,
            'estimated_speedup': self.estimated_speedup,
            'function_name': self.function_name,
            'data_size': self.data_size,
            'avg_execution_time': self.avg_execution_time,
            'notes': self.notes,
            'source': self.source,
            'system_info': self.system_info,
            'timestamp': self.timestamp,
            'amorsize_version': version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigData':
        """Create configuration from dictionary."""
        return cls(
            n_jobs=data['n_jobs'],
            chunksize=data['chunksize'],
            executor_type=data.get('executor_type', 'process'),
            estimated_speedup=data.get('estimated_speedup', 1.0),
            function_name=data.get('function_name'),
            data_size=data.get('data_size'),
            avg_execution_time=data.get('avg_execution_time'),
            notes=data.get('notes'),
            system_info=data.get('system_info'),
            timestamp=data.get('timestamp'),
            source=data.get('source', 'unknown')
        )

    def __repr__(self) -> str:
        return (
            f"ConfigData(n_jobs={self.n_jobs}, chunksize={self.chunksize}, "
            f"executor_type='{self.executor_type}', source='{self.source}')"
        )

    def __str__(self) -> str:
        lines = [
            f"Configuration ({self.source}):",
            f"  n_jobs:           {self.n_jobs}",
            f"  chunksize:        {self.chunksize}",
            f"  executor_type:    {self.executor_type}",
            f"  estimated_speedup: {self.estimated_speedup:.2f}x"
        ]

        if self.function_name:
            lines.append(f"  function:         {self.function_name}")
        if self.data_size is not None:
            lines.append(f"  data_size:        {self.data_size}")
        if self.avg_execution_time is not None:
            lines.append(f"  avg_time_per_item: {self.avg_execution_time:.6f}s")
        if self.notes:
            lines.append(f"  notes:            {self.notes}")

        lines.append(f"  timestamp:        {self.timestamp}")

        if self.system_info:
            lines.append("\nSystem Information:")
            lines.append(f"  platform:         {self.system_info.get('platform', 'unknown')}")
            lines.append(f"  physical_cores:   {self.system_info.get('physical_cores', '?')}")
            lines.append(f"  start_method:     {self.system_info.get('start_method', 'unknown')}")

        return "\n".join(lines)


def _capture_system_info() -> Dict[str, Any]:
    """Capture current system information."""
    return {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'python_version': platform.python_version(),
        'physical_cores': get_physical_cores(),
        'available_memory': get_available_memory(),
        'start_method': get_multiprocessing_start_method()
    }


def save_config(
    config: ConfigData,
    filepath: Union[str, Path],
    format: str = "auto",
    overwrite: bool = False
) -> None:
    """
    Save configuration to file.

    Args:
        config: ConfigData object to save
        filepath: Path to save file
        format: File format ('json', 'yaml', or 'auto' to detect from extension)
        overwrite: If True, overwrite existing file. If False, raise error.

    Raises:
        FileExistsError: If file exists and overwrite=False
        ValueError: If format is unsupported
        IOError: If file cannot be written

    Examples:
        >>> config = ConfigData(n_jobs=4, chunksize=100)
        >>> save_config(config, 'my_config.json')
        >>> save_config(config, 'my_config.yaml', format='yaml')
    """
    filepath = Path(filepath)

    # Check if file exists
    if filepath.exists() and not overwrite:
        raise FileExistsError(
            f"Configuration file already exists: {filepath}. "
            f"Use overwrite=True to replace it."
        )

    # Detect format from extension if auto
    if format == "auto":
        ext = filepath.suffix.lower()
        if ext in ('.json',):
            format = "json"
        elif ext in ('.yaml', '.yml'):
            format = "yaml"
        else:
            # Default to JSON if extension is unclear
            format = "json"

    # Convert config to dictionary
    data = config.to_dict()

    # Create parent directory if it doesn't exist
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Save to file
    if format == "json":
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    elif format == "yaml":
        try:
            import yaml
            with open(filepath, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        except ImportError:
            raise ImportError(
                "YAML support requires PyYAML. Install it with: pip install pyyaml"
            )
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'json' or 'yaml'.")


def load_config(filepath: Union[str, Path], format: str = "auto") -> ConfigData:
    """
    Load configuration from file.

    Args:
        filepath: Path to configuration file
        format: File format ('json', 'yaml', or 'auto' to detect from extension)

    Returns:
        ConfigData object loaded from file

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If format is unsupported or file is invalid
        IOError: If file cannot be read

    Examples:
        >>> config = load_config('my_config.json')
        >>> print(f"Using n_jobs={config.n_jobs}, chunksize={config.chunksize}")
    """
    filepath = Path(filepath)

    # Check if file exists
    if not filepath.exists():
        raise FileNotFoundError(f"Configuration file not found: {filepath}")

    # Detect format from extension if auto
    if format == "auto":
        ext = filepath.suffix.lower()
        if ext in ('.json',):
            format = "json"
        elif ext in ('.yaml', '.yml'):
            format = "yaml"
        else:
            # Try JSON first as it's more common
            format = "json"

    # Load from file
    try:
        if format == "json":
            with open(filepath, 'r') as f:
                data = json.load(f)
        elif format == "yaml":
            try:
                import yaml
                with open(filepath, 'r') as f:
                    data = yaml.safe_load(f)
            except ImportError:
                raise ImportError(
                    "YAML support requires PyYAML. Install it with: pip install pyyaml"
                )
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'json' or 'yaml'.")

        # Validate required fields
        if not isinstance(data, dict):
            raise ValueError("Configuration file must contain a dictionary/object")

        required_fields = ['n_jobs', 'chunksize']
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            raise ValueError(
                f"Configuration file missing required fields: {', '.join(missing_fields)}"
            )

        # Create ConfigData from dictionary
        return ConfigData.from_dict(data)

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}")
    except Exception as e:
        if "yaml" in str(type(e).__module__).lower():
            raise ValueError(f"Invalid YAML in configuration file: {e}")
        raise


def list_configs(directory: Union[str, Path] = ".") -> list:
    """
    List all configuration files in a directory.

    Args:
        directory: Directory to search (default: current directory)

    Returns:
        List of configuration file paths

    Examples:
        >>> configs = list_configs('configs/')
        >>> for config_path in configs:
        ...     config = load_config(config_path)
        ...     print(f"{config_path}: {config.n_jobs} workers")
    """
    directory = Path(directory)

    if not directory.exists():
        return []

    # Find all JSON and YAML files
    config_files: List[Path] = []
    for ext in ['*.json', '*.yaml', '*.yml']:
        config_files.extend(directory.glob(ext))

    return sorted(config_files)


def get_default_config_dir() -> Path:
    """
    Get default directory for storing configurations.

    Returns:
        Path to default config directory (~/.amorsize/configs)

    The directory is created if it doesn't exist.
    """
    config_dir = Path.home() / '.amorsize' / 'configs'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir
