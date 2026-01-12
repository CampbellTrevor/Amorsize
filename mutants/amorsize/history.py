"""
History module for tracking and comparing optimization results over time.

This module provides functionality to:
- Save comparison results to disk with metadata
- Load and filter historical results
- Compare results across different runs or systems
- Track performance trends and detect regressions
"""

import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .comparison import ComparisonConfig, ComparisonResult
from .system_info import (
    get_available_memory,
    get_multiprocessing_start_method,
    get_physical_cores,
)
from inspect import signature as _mutmut_signature
from typing import Annotated
from typing import Callable
from typing import ClassVar


MutantDict = Annotated[dict[str, Callable], "Mutant"]


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None):
    """Forward call to original or mutated function, depending on the environment"""
    import os
    mutant_under_test = os.environ['MUTANT_UNDER_TEST']
    if mutant_under_test == 'fail':
        from mutmut.__main__ import MutmutProgrammaticFailException
        raise MutmutProgrammaticFailException('Failed programmatically')      
    elif mutant_under_test == 'stats':
        from mutmut.__main__ import record_trampoline_hit
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__)
        result = orig(*call_args, **call_kwargs)
        return result
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_'
    if not mutant_under_test.startswith(prefix):
        result = orig(*call_args, **call_kwargs)
        return result
    mutant_name = mutant_under_test.rpartition('.')[-1]
    if self_arg is not None:
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs)
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs)
    return result


class HistoryEntry:
    """
    Container for a single historical result entry.

    Attributes:
        id: Unique identifier for this entry
        name: User-provided name for this result
        timestamp: ISO 8601 timestamp when result was saved
        result: The ComparisonResult object
        function_name: Name of the function that was compared
        data_size: Size of the dataset
        system_info: System information at time of measurement
        metadata: Additional user-provided metadata
    """

    def xǁHistoryEntryǁ__init____mutmut_orig(
        self,
        id: str,
        name: str,
        timestamp: str,
        result: ComparisonResult,
        function_name: str,
        data_size: int,
        system_info: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.name = name
        self.timestamp = timestamp
        self.result = result
        self.function_name = function_name
        self.data_size = data_size
        self.system_info = system_info
        self.metadata = metadata or {}

    def xǁHistoryEntryǁ__init____mutmut_1(
        self,
        id: str,
        name: str,
        timestamp: str,
        result: ComparisonResult,
        function_name: str,
        data_size: int,
        system_info: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = None
        self.name = name
        self.timestamp = timestamp
        self.result = result
        self.function_name = function_name
        self.data_size = data_size
        self.system_info = system_info
        self.metadata = metadata or {}

    def xǁHistoryEntryǁ__init____mutmut_2(
        self,
        id: str,
        name: str,
        timestamp: str,
        result: ComparisonResult,
        function_name: str,
        data_size: int,
        system_info: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.name = None
        self.timestamp = timestamp
        self.result = result
        self.function_name = function_name
        self.data_size = data_size
        self.system_info = system_info
        self.metadata = metadata or {}

    def xǁHistoryEntryǁ__init____mutmut_3(
        self,
        id: str,
        name: str,
        timestamp: str,
        result: ComparisonResult,
        function_name: str,
        data_size: int,
        system_info: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.name = name
        self.timestamp = None
        self.result = result
        self.function_name = function_name
        self.data_size = data_size
        self.system_info = system_info
        self.metadata = metadata or {}

    def xǁHistoryEntryǁ__init____mutmut_4(
        self,
        id: str,
        name: str,
        timestamp: str,
        result: ComparisonResult,
        function_name: str,
        data_size: int,
        system_info: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.name = name
        self.timestamp = timestamp
        self.result = None
        self.function_name = function_name
        self.data_size = data_size
        self.system_info = system_info
        self.metadata = metadata or {}

    def xǁHistoryEntryǁ__init____mutmut_5(
        self,
        id: str,
        name: str,
        timestamp: str,
        result: ComparisonResult,
        function_name: str,
        data_size: int,
        system_info: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.name = name
        self.timestamp = timestamp
        self.result = result
        self.function_name = None
        self.data_size = data_size
        self.system_info = system_info
        self.metadata = metadata or {}

    def xǁHistoryEntryǁ__init____mutmut_6(
        self,
        id: str,
        name: str,
        timestamp: str,
        result: ComparisonResult,
        function_name: str,
        data_size: int,
        system_info: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.name = name
        self.timestamp = timestamp
        self.result = result
        self.function_name = function_name
        self.data_size = None
        self.system_info = system_info
        self.metadata = metadata or {}

    def xǁHistoryEntryǁ__init____mutmut_7(
        self,
        id: str,
        name: str,
        timestamp: str,
        result: ComparisonResult,
        function_name: str,
        data_size: int,
        system_info: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.name = name
        self.timestamp = timestamp
        self.result = result
        self.function_name = function_name
        self.data_size = data_size
        self.system_info = None
        self.metadata = metadata or {}

    def xǁHistoryEntryǁ__init____mutmut_8(
        self,
        id: str,
        name: str,
        timestamp: str,
        result: ComparisonResult,
        function_name: str,
        data_size: int,
        system_info: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.name = name
        self.timestamp = timestamp
        self.result = result
        self.function_name = function_name
        self.data_size = data_size
        self.system_info = system_info
        self.metadata = None

    def xǁHistoryEntryǁ__init____mutmut_9(
        self,
        id: str,
        name: str,
        timestamp: str,
        result: ComparisonResult,
        function_name: str,
        data_size: int,
        system_info: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.name = name
        self.timestamp = timestamp
        self.result = result
        self.function_name = function_name
        self.data_size = data_size
        self.system_info = system_info
        self.metadata = metadata and {}
    
    xǁHistoryEntryǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁHistoryEntryǁ__init____mutmut_1': xǁHistoryEntryǁ__init____mutmut_1, 
        'xǁHistoryEntryǁ__init____mutmut_2': xǁHistoryEntryǁ__init____mutmut_2, 
        'xǁHistoryEntryǁ__init____mutmut_3': xǁHistoryEntryǁ__init____mutmut_3, 
        'xǁHistoryEntryǁ__init____mutmut_4': xǁHistoryEntryǁ__init____mutmut_4, 
        'xǁHistoryEntryǁ__init____mutmut_5': xǁHistoryEntryǁ__init____mutmut_5, 
        'xǁHistoryEntryǁ__init____mutmut_6': xǁHistoryEntryǁ__init____mutmut_6, 
        'xǁHistoryEntryǁ__init____mutmut_7': xǁHistoryEntryǁ__init____mutmut_7, 
        'xǁHistoryEntryǁ__init____mutmut_8': xǁHistoryEntryǁ__init____mutmut_8, 
        'xǁHistoryEntryǁ__init____mutmut_9': xǁHistoryEntryǁ__init____mutmut_9
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁHistoryEntryǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁHistoryEntryǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁHistoryEntryǁ__init____mutmut_orig)
    xǁHistoryEntryǁ__init____mutmut_orig.__name__ = 'xǁHistoryEntryǁ__init__'

    def xǁHistoryEntryǁto_dict__mutmut_orig(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "function_name": self.function_name,
            "data_size": self.data_size,
            "system_info": self.system_info,
            "metadata": self.metadata,
            "result": self._serialize_result()
        }

    def xǁHistoryEntryǁto_dict__mutmut_1(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "XXidXX": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "function_name": self.function_name,
            "data_size": self.data_size,
            "system_info": self.system_info,
            "metadata": self.metadata,
            "result": self._serialize_result()
        }

    def xǁHistoryEntryǁto_dict__mutmut_2(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "ID": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "function_name": self.function_name,
            "data_size": self.data_size,
            "system_info": self.system_info,
            "metadata": self.metadata,
            "result": self._serialize_result()
        }

    def xǁHistoryEntryǁto_dict__mutmut_3(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "XXnameXX": self.name,
            "timestamp": self.timestamp,
            "function_name": self.function_name,
            "data_size": self.data_size,
            "system_info": self.system_info,
            "metadata": self.metadata,
            "result": self._serialize_result()
        }

    def xǁHistoryEntryǁto_dict__mutmut_4(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "NAME": self.name,
            "timestamp": self.timestamp,
            "function_name": self.function_name,
            "data_size": self.data_size,
            "system_info": self.system_info,
            "metadata": self.metadata,
            "result": self._serialize_result()
        }

    def xǁHistoryEntryǁto_dict__mutmut_5(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "XXtimestampXX": self.timestamp,
            "function_name": self.function_name,
            "data_size": self.data_size,
            "system_info": self.system_info,
            "metadata": self.metadata,
            "result": self._serialize_result()
        }

    def xǁHistoryEntryǁto_dict__mutmut_6(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "TIMESTAMP": self.timestamp,
            "function_name": self.function_name,
            "data_size": self.data_size,
            "system_info": self.system_info,
            "metadata": self.metadata,
            "result": self._serialize_result()
        }

    def xǁHistoryEntryǁto_dict__mutmut_7(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "XXfunction_nameXX": self.function_name,
            "data_size": self.data_size,
            "system_info": self.system_info,
            "metadata": self.metadata,
            "result": self._serialize_result()
        }

    def xǁHistoryEntryǁto_dict__mutmut_8(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "FUNCTION_NAME": self.function_name,
            "data_size": self.data_size,
            "system_info": self.system_info,
            "metadata": self.metadata,
            "result": self._serialize_result()
        }

    def xǁHistoryEntryǁto_dict__mutmut_9(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "function_name": self.function_name,
            "XXdata_sizeXX": self.data_size,
            "system_info": self.system_info,
            "metadata": self.metadata,
            "result": self._serialize_result()
        }

    def xǁHistoryEntryǁto_dict__mutmut_10(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "function_name": self.function_name,
            "DATA_SIZE": self.data_size,
            "system_info": self.system_info,
            "metadata": self.metadata,
            "result": self._serialize_result()
        }

    def xǁHistoryEntryǁto_dict__mutmut_11(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "function_name": self.function_name,
            "data_size": self.data_size,
            "XXsystem_infoXX": self.system_info,
            "metadata": self.metadata,
            "result": self._serialize_result()
        }

    def xǁHistoryEntryǁto_dict__mutmut_12(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "function_name": self.function_name,
            "data_size": self.data_size,
            "SYSTEM_INFO": self.system_info,
            "metadata": self.metadata,
            "result": self._serialize_result()
        }

    def xǁHistoryEntryǁto_dict__mutmut_13(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "function_name": self.function_name,
            "data_size": self.data_size,
            "system_info": self.system_info,
            "XXmetadataXX": self.metadata,
            "result": self._serialize_result()
        }

    def xǁHistoryEntryǁto_dict__mutmut_14(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "function_name": self.function_name,
            "data_size": self.data_size,
            "system_info": self.system_info,
            "METADATA": self.metadata,
            "result": self._serialize_result()
        }

    def xǁHistoryEntryǁto_dict__mutmut_15(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "function_name": self.function_name,
            "data_size": self.data_size,
            "system_info": self.system_info,
            "metadata": self.metadata,
            "XXresultXX": self._serialize_result()
        }

    def xǁHistoryEntryǁto_dict__mutmut_16(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "function_name": self.function_name,
            "data_size": self.data_size,
            "system_info": self.system_info,
            "metadata": self.metadata,
            "RESULT": self._serialize_result()
        }
    
    xǁHistoryEntryǁto_dict__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁHistoryEntryǁto_dict__mutmut_1': xǁHistoryEntryǁto_dict__mutmut_1, 
        'xǁHistoryEntryǁto_dict__mutmut_2': xǁHistoryEntryǁto_dict__mutmut_2, 
        'xǁHistoryEntryǁto_dict__mutmut_3': xǁHistoryEntryǁto_dict__mutmut_3, 
        'xǁHistoryEntryǁto_dict__mutmut_4': xǁHistoryEntryǁto_dict__mutmut_4, 
        'xǁHistoryEntryǁto_dict__mutmut_5': xǁHistoryEntryǁto_dict__mutmut_5, 
        'xǁHistoryEntryǁto_dict__mutmut_6': xǁHistoryEntryǁto_dict__mutmut_6, 
        'xǁHistoryEntryǁto_dict__mutmut_7': xǁHistoryEntryǁto_dict__mutmut_7, 
        'xǁHistoryEntryǁto_dict__mutmut_8': xǁHistoryEntryǁto_dict__mutmut_8, 
        'xǁHistoryEntryǁto_dict__mutmut_9': xǁHistoryEntryǁto_dict__mutmut_9, 
        'xǁHistoryEntryǁto_dict__mutmut_10': xǁHistoryEntryǁto_dict__mutmut_10, 
        'xǁHistoryEntryǁto_dict__mutmut_11': xǁHistoryEntryǁto_dict__mutmut_11, 
        'xǁHistoryEntryǁto_dict__mutmut_12': xǁHistoryEntryǁto_dict__mutmut_12, 
        'xǁHistoryEntryǁto_dict__mutmut_13': xǁHistoryEntryǁto_dict__mutmut_13, 
        'xǁHistoryEntryǁto_dict__mutmut_14': xǁHistoryEntryǁto_dict__mutmut_14, 
        'xǁHistoryEntryǁto_dict__mutmut_15': xǁHistoryEntryǁto_dict__mutmut_15, 
        'xǁHistoryEntryǁto_dict__mutmut_16': xǁHistoryEntryǁto_dict__mutmut_16
    }
    
    def to_dict(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁHistoryEntryǁto_dict__mutmut_orig"), object.__getattribute__(self, "xǁHistoryEntryǁto_dict__mutmut_mutants"), args, kwargs, self)
        return result 
    
    to_dict.__signature__ = _mutmut_signature(xǁHistoryEntryǁto_dict__mutmut_orig)
    xǁHistoryEntryǁto_dict__mutmut_orig.__name__ = 'xǁHistoryEntryǁto_dict'

    def xǁHistoryEntryǁ_serialize_result__mutmut_orig(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "configs": [
                {
                    "name": config.name,
                    "n_jobs": config.n_jobs,
                    "chunksize": config.chunksize,
                    "executor_type": config.executor_type
                }
                for config in self.result.configs
            ],
            "execution_times": self.result.execution_times,
            "speedups": self.result.speedups,
            "best_config_index": self.result.best_config_index,
            "recommendations": self.result.recommendations
        }

    def xǁHistoryEntryǁ_serialize_result__mutmut_1(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "XXconfigsXX": [
                {
                    "name": config.name,
                    "n_jobs": config.n_jobs,
                    "chunksize": config.chunksize,
                    "executor_type": config.executor_type
                }
                for config in self.result.configs
            ],
            "execution_times": self.result.execution_times,
            "speedups": self.result.speedups,
            "best_config_index": self.result.best_config_index,
            "recommendations": self.result.recommendations
        }

    def xǁHistoryEntryǁ_serialize_result__mutmut_2(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "CONFIGS": [
                {
                    "name": config.name,
                    "n_jobs": config.n_jobs,
                    "chunksize": config.chunksize,
                    "executor_type": config.executor_type
                }
                for config in self.result.configs
            ],
            "execution_times": self.result.execution_times,
            "speedups": self.result.speedups,
            "best_config_index": self.result.best_config_index,
            "recommendations": self.result.recommendations
        }

    def xǁHistoryEntryǁ_serialize_result__mutmut_3(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "configs": [
                {
                    "XXnameXX": config.name,
                    "n_jobs": config.n_jobs,
                    "chunksize": config.chunksize,
                    "executor_type": config.executor_type
                }
                for config in self.result.configs
            ],
            "execution_times": self.result.execution_times,
            "speedups": self.result.speedups,
            "best_config_index": self.result.best_config_index,
            "recommendations": self.result.recommendations
        }

    def xǁHistoryEntryǁ_serialize_result__mutmut_4(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "configs": [
                {
                    "NAME": config.name,
                    "n_jobs": config.n_jobs,
                    "chunksize": config.chunksize,
                    "executor_type": config.executor_type
                }
                for config in self.result.configs
            ],
            "execution_times": self.result.execution_times,
            "speedups": self.result.speedups,
            "best_config_index": self.result.best_config_index,
            "recommendations": self.result.recommendations
        }

    def xǁHistoryEntryǁ_serialize_result__mutmut_5(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "configs": [
                {
                    "name": config.name,
                    "XXn_jobsXX": config.n_jobs,
                    "chunksize": config.chunksize,
                    "executor_type": config.executor_type
                }
                for config in self.result.configs
            ],
            "execution_times": self.result.execution_times,
            "speedups": self.result.speedups,
            "best_config_index": self.result.best_config_index,
            "recommendations": self.result.recommendations
        }

    def xǁHistoryEntryǁ_serialize_result__mutmut_6(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "configs": [
                {
                    "name": config.name,
                    "N_JOBS": config.n_jobs,
                    "chunksize": config.chunksize,
                    "executor_type": config.executor_type
                }
                for config in self.result.configs
            ],
            "execution_times": self.result.execution_times,
            "speedups": self.result.speedups,
            "best_config_index": self.result.best_config_index,
            "recommendations": self.result.recommendations
        }

    def xǁHistoryEntryǁ_serialize_result__mutmut_7(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "configs": [
                {
                    "name": config.name,
                    "n_jobs": config.n_jobs,
                    "XXchunksizeXX": config.chunksize,
                    "executor_type": config.executor_type
                }
                for config in self.result.configs
            ],
            "execution_times": self.result.execution_times,
            "speedups": self.result.speedups,
            "best_config_index": self.result.best_config_index,
            "recommendations": self.result.recommendations
        }

    def xǁHistoryEntryǁ_serialize_result__mutmut_8(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "configs": [
                {
                    "name": config.name,
                    "n_jobs": config.n_jobs,
                    "CHUNKSIZE": config.chunksize,
                    "executor_type": config.executor_type
                }
                for config in self.result.configs
            ],
            "execution_times": self.result.execution_times,
            "speedups": self.result.speedups,
            "best_config_index": self.result.best_config_index,
            "recommendations": self.result.recommendations
        }

    def xǁHistoryEntryǁ_serialize_result__mutmut_9(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "configs": [
                {
                    "name": config.name,
                    "n_jobs": config.n_jobs,
                    "chunksize": config.chunksize,
                    "XXexecutor_typeXX": config.executor_type
                }
                for config in self.result.configs
            ],
            "execution_times": self.result.execution_times,
            "speedups": self.result.speedups,
            "best_config_index": self.result.best_config_index,
            "recommendations": self.result.recommendations
        }

    def xǁHistoryEntryǁ_serialize_result__mutmut_10(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "configs": [
                {
                    "name": config.name,
                    "n_jobs": config.n_jobs,
                    "chunksize": config.chunksize,
                    "EXECUTOR_TYPE": config.executor_type
                }
                for config in self.result.configs
            ],
            "execution_times": self.result.execution_times,
            "speedups": self.result.speedups,
            "best_config_index": self.result.best_config_index,
            "recommendations": self.result.recommendations
        }

    def xǁHistoryEntryǁ_serialize_result__mutmut_11(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "configs": [
                {
                    "name": config.name,
                    "n_jobs": config.n_jobs,
                    "chunksize": config.chunksize,
                    "executor_type": config.executor_type
                }
                for config in self.result.configs
            ],
            "XXexecution_timesXX": self.result.execution_times,
            "speedups": self.result.speedups,
            "best_config_index": self.result.best_config_index,
            "recommendations": self.result.recommendations
        }

    def xǁHistoryEntryǁ_serialize_result__mutmut_12(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "configs": [
                {
                    "name": config.name,
                    "n_jobs": config.n_jobs,
                    "chunksize": config.chunksize,
                    "executor_type": config.executor_type
                }
                for config in self.result.configs
            ],
            "EXECUTION_TIMES": self.result.execution_times,
            "speedups": self.result.speedups,
            "best_config_index": self.result.best_config_index,
            "recommendations": self.result.recommendations
        }

    def xǁHistoryEntryǁ_serialize_result__mutmut_13(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "configs": [
                {
                    "name": config.name,
                    "n_jobs": config.n_jobs,
                    "chunksize": config.chunksize,
                    "executor_type": config.executor_type
                }
                for config in self.result.configs
            ],
            "execution_times": self.result.execution_times,
            "XXspeedupsXX": self.result.speedups,
            "best_config_index": self.result.best_config_index,
            "recommendations": self.result.recommendations
        }

    def xǁHistoryEntryǁ_serialize_result__mutmut_14(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "configs": [
                {
                    "name": config.name,
                    "n_jobs": config.n_jobs,
                    "chunksize": config.chunksize,
                    "executor_type": config.executor_type
                }
                for config in self.result.configs
            ],
            "execution_times": self.result.execution_times,
            "SPEEDUPS": self.result.speedups,
            "best_config_index": self.result.best_config_index,
            "recommendations": self.result.recommendations
        }

    def xǁHistoryEntryǁ_serialize_result__mutmut_15(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "configs": [
                {
                    "name": config.name,
                    "n_jobs": config.n_jobs,
                    "chunksize": config.chunksize,
                    "executor_type": config.executor_type
                }
                for config in self.result.configs
            ],
            "execution_times": self.result.execution_times,
            "speedups": self.result.speedups,
            "XXbest_config_indexXX": self.result.best_config_index,
            "recommendations": self.result.recommendations
        }

    def xǁHistoryEntryǁ_serialize_result__mutmut_16(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "configs": [
                {
                    "name": config.name,
                    "n_jobs": config.n_jobs,
                    "chunksize": config.chunksize,
                    "executor_type": config.executor_type
                }
                for config in self.result.configs
            ],
            "execution_times": self.result.execution_times,
            "speedups": self.result.speedups,
            "BEST_CONFIG_INDEX": self.result.best_config_index,
            "recommendations": self.result.recommendations
        }

    def xǁHistoryEntryǁ_serialize_result__mutmut_17(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "configs": [
                {
                    "name": config.name,
                    "n_jobs": config.n_jobs,
                    "chunksize": config.chunksize,
                    "executor_type": config.executor_type
                }
                for config in self.result.configs
            ],
            "execution_times": self.result.execution_times,
            "speedups": self.result.speedups,
            "best_config_index": self.result.best_config_index,
            "XXrecommendationsXX": self.result.recommendations
        }

    def xǁHistoryEntryǁ_serialize_result__mutmut_18(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "configs": [
                {
                    "name": config.name,
                    "n_jobs": config.n_jobs,
                    "chunksize": config.chunksize,
                    "executor_type": config.executor_type
                }
                for config in self.result.configs
            ],
            "execution_times": self.result.execution_times,
            "speedups": self.result.speedups,
            "best_config_index": self.result.best_config_index,
            "RECOMMENDATIONS": self.result.recommendations
        }
    
    xǁHistoryEntryǁ_serialize_result__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁHistoryEntryǁ_serialize_result__mutmut_1': xǁHistoryEntryǁ_serialize_result__mutmut_1, 
        'xǁHistoryEntryǁ_serialize_result__mutmut_2': xǁHistoryEntryǁ_serialize_result__mutmut_2, 
        'xǁHistoryEntryǁ_serialize_result__mutmut_3': xǁHistoryEntryǁ_serialize_result__mutmut_3, 
        'xǁHistoryEntryǁ_serialize_result__mutmut_4': xǁHistoryEntryǁ_serialize_result__mutmut_4, 
        'xǁHistoryEntryǁ_serialize_result__mutmut_5': xǁHistoryEntryǁ_serialize_result__mutmut_5, 
        'xǁHistoryEntryǁ_serialize_result__mutmut_6': xǁHistoryEntryǁ_serialize_result__mutmut_6, 
        'xǁHistoryEntryǁ_serialize_result__mutmut_7': xǁHistoryEntryǁ_serialize_result__mutmut_7, 
        'xǁHistoryEntryǁ_serialize_result__mutmut_8': xǁHistoryEntryǁ_serialize_result__mutmut_8, 
        'xǁHistoryEntryǁ_serialize_result__mutmut_9': xǁHistoryEntryǁ_serialize_result__mutmut_9, 
        'xǁHistoryEntryǁ_serialize_result__mutmut_10': xǁHistoryEntryǁ_serialize_result__mutmut_10, 
        'xǁHistoryEntryǁ_serialize_result__mutmut_11': xǁHistoryEntryǁ_serialize_result__mutmut_11, 
        'xǁHistoryEntryǁ_serialize_result__mutmut_12': xǁHistoryEntryǁ_serialize_result__mutmut_12, 
        'xǁHistoryEntryǁ_serialize_result__mutmut_13': xǁHistoryEntryǁ_serialize_result__mutmut_13, 
        'xǁHistoryEntryǁ_serialize_result__mutmut_14': xǁHistoryEntryǁ_serialize_result__mutmut_14, 
        'xǁHistoryEntryǁ_serialize_result__mutmut_15': xǁHistoryEntryǁ_serialize_result__mutmut_15, 
        'xǁHistoryEntryǁ_serialize_result__mutmut_16': xǁHistoryEntryǁ_serialize_result__mutmut_16, 
        'xǁHistoryEntryǁ_serialize_result__mutmut_17': xǁHistoryEntryǁ_serialize_result__mutmut_17, 
        'xǁHistoryEntryǁ_serialize_result__mutmut_18': xǁHistoryEntryǁ_serialize_result__mutmut_18
    }
    
    def _serialize_result(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁHistoryEntryǁ_serialize_result__mutmut_orig"), object.__getattribute__(self, "xǁHistoryEntryǁ_serialize_result__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _serialize_result.__signature__ = _mutmut_signature(xǁHistoryEntryǁ_serialize_result__mutmut_orig)
    xǁHistoryEntryǁ_serialize_result__mutmut_orig.__name__ = 'xǁHistoryEntryǁ_serialize_result'

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoryEntry":
        """Create HistoryEntry from dictionary."""
        # Reconstruct ComparisonResult
        result_data = data["result"]
        configs = [
            ComparisonConfig(
                name=c["name"],
                n_jobs=c["n_jobs"],
                chunksize=c["chunksize"],
                executor_type=c["executor_type"]
            )
            for c in result_data["configs"]
        ]

        result = ComparisonResult(
            configs=configs,
            execution_times=result_data["execution_times"],
            speedups=result_data["speedups"],
            best_config_index=result_data["best_config_index"],
            recommendations=result_data.get("recommendations", [])
        )

        return cls(
            id=data["id"],
            name=data["name"],
            timestamp=data["timestamp"],
            result=result,
            function_name=data["function_name"],
            data_size=data["data_size"],
            system_info=data["system_info"],
            metadata=data.get("metadata", {})
        )


def x_get_system_fingerprint__mutmut_orig() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1024**3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_1() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "XXplatformXX": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1024**3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_2() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "PLATFORM": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1024**3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_3() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "XXsystemXX": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1024**3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_4() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "SYSTEM": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1024**3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_5() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "XXmachineXX": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1024**3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_6() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "MACHINE": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1024**3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_7() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "XXprocessorXX": platform.processor(),
        "python_version": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1024**3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_8() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "PROCESSOR": platform.processor(),
        "python_version": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1024**3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_9() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "XXpython_versionXX": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1024**3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_10() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "PYTHON_VERSION": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1024**3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_11() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "XXphysical_coresXX": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1024**3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_12() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "PHYSICAL_CORES": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1024**3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_13() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "XXavailable_memory_gbXX": get_available_memory() / (1024**3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_14() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "AVAILABLE_MEMORY_GB": get_available_memory() / (1024**3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_15() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "available_memory_gb": get_available_memory() * (1024**3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_16() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1024 * 3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_17() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1025**3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_18() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1024**4),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_19() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1024**3),
        "XXmultiprocessing_start_methodXX": get_multiprocessing_start_method()
    }


def x_get_system_fingerprint__mutmut_20() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.

    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1024**3),
        "MULTIPROCESSING_START_METHOD": get_multiprocessing_start_method()
    }

x_get_system_fingerprint__mutmut_mutants : ClassVar[MutantDict] = {
'x_get_system_fingerprint__mutmut_1': x_get_system_fingerprint__mutmut_1, 
    'x_get_system_fingerprint__mutmut_2': x_get_system_fingerprint__mutmut_2, 
    'x_get_system_fingerprint__mutmut_3': x_get_system_fingerprint__mutmut_3, 
    'x_get_system_fingerprint__mutmut_4': x_get_system_fingerprint__mutmut_4, 
    'x_get_system_fingerprint__mutmut_5': x_get_system_fingerprint__mutmut_5, 
    'x_get_system_fingerprint__mutmut_6': x_get_system_fingerprint__mutmut_6, 
    'x_get_system_fingerprint__mutmut_7': x_get_system_fingerprint__mutmut_7, 
    'x_get_system_fingerprint__mutmut_8': x_get_system_fingerprint__mutmut_8, 
    'x_get_system_fingerprint__mutmut_9': x_get_system_fingerprint__mutmut_9, 
    'x_get_system_fingerprint__mutmut_10': x_get_system_fingerprint__mutmut_10, 
    'x_get_system_fingerprint__mutmut_11': x_get_system_fingerprint__mutmut_11, 
    'x_get_system_fingerprint__mutmut_12': x_get_system_fingerprint__mutmut_12, 
    'x_get_system_fingerprint__mutmut_13': x_get_system_fingerprint__mutmut_13, 
    'x_get_system_fingerprint__mutmut_14': x_get_system_fingerprint__mutmut_14, 
    'x_get_system_fingerprint__mutmut_15': x_get_system_fingerprint__mutmut_15, 
    'x_get_system_fingerprint__mutmut_16': x_get_system_fingerprint__mutmut_16, 
    'x_get_system_fingerprint__mutmut_17': x_get_system_fingerprint__mutmut_17, 
    'x_get_system_fingerprint__mutmut_18': x_get_system_fingerprint__mutmut_18, 
    'x_get_system_fingerprint__mutmut_19': x_get_system_fingerprint__mutmut_19, 
    'x_get_system_fingerprint__mutmut_20': x_get_system_fingerprint__mutmut_20
}

def get_system_fingerprint(*args, **kwargs):
    result = _mutmut_trampoline(x_get_system_fingerprint__mutmut_orig, x_get_system_fingerprint__mutmut_mutants, args, kwargs)
    return result 

get_system_fingerprint.__signature__ = _mutmut_signature(x_get_system_fingerprint__mutmut_orig)
x_get_system_fingerprint__mutmut_orig.__name__ = 'x_get_system_fingerprint'


def x__generate_id__mutmut_orig(name: str, timestamp: str) -> str:
    """Generate a unique ID for a history entry."""
    hash_input = f"{name}_{timestamp}".encode('utf-8')
    return hashlib.sha256(hash_input).hexdigest()[:12]


def x__generate_id__mutmut_1(name: str, timestamp: str) -> str:
    """Generate a unique ID for a history entry."""
    hash_input = None
    return hashlib.sha256(hash_input).hexdigest()[:12]


def x__generate_id__mutmut_2(name: str, timestamp: str) -> str:
    """Generate a unique ID for a history entry."""
    hash_input = f"{name}_{timestamp}".encode(None)
    return hashlib.sha256(hash_input).hexdigest()[:12]


def x__generate_id__mutmut_3(name: str, timestamp: str) -> str:
    """Generate a unique ID for a history entry."""
    hash_input = f"{name}_{timestamp}".encode('XXutf-8XX')
    return hashlib.sha256(hash_input).hexdigest()[:12]


def x__generate_id__mutmut_4(name: str, timestamp: str) -> str:
    """Generate a unique ID for a history entry."""
    hash_input = f"{name}_{timestamp}".encode('UTF-8')
    return hashlib.sha256(hash_input).hexdigest()[:12]


def x__generate_id__mutmut_5(name: str, timestamp: str) -> str:
    """Generate a unique ID for a history entry."""
    hash_input = f"{name}_{timestamp}".encode('utf-8')
    return hashlib.sha256(None).hexdigest()[:12]


def x__generate_id__mutmut_6(name: str, timestamp: str) -> str:
    """Generate a unique ID for a history entry."""
    hash_input = f"{name}_{timestamp}".encode('utf-8')
    return hashlib.sha256(hash_input).hexdigest()[:13]

x__generate_id__mutmut_mutants : ClassVar[MutantDict] = {
'x__generate_id__mutmut_1': x__generate_id__mutmut_1, 
    'x__generate_id__mutmut_2': x__generate_id__mutmut_2, 
    'x__generate_id__mutmut_3': x__generate_id__mutmut_3, 
    'x__generate_id__mutmut_4': x__generate_id__mutmut_4, 
    'x__generate_id__mutmut_5': x__generate_id__mutmut_5, 
    'x__generate_id__mutmut_6': x__generate_id__mutmut_6
}

def _generate_id(*args, **kwargs):
    result = _mutmut_trampoline(x__generate_id__mutmut_orig, x__generate_id__mutmut_mutants, args, kwargs)
    return result 

_generate_id.__signature__ = _mutmut_signature(x__generate_id__mutmut_orig)
x__generate_id__mutmut_orig.__name__ = 'x__generate_id'


def x_get_history_dir__mutmut_orig() -> Path:
    """
    Get the directory where history files are stored.

    Returns:
        Path to history directory (creates if doesn't exist)
    """
    # Store in user's home directory under .amorsize/history
    home = Path.home()
    history_dir = home / ".amorsize" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def x_get_history_dir__mutmut_1() -> Path:
    """
    Get the directory where history files are stored.

    Returns:
        Path to history directory (creates if doesn't exist)
    """
    # Store in user's home directory under .amorsize/history
    home = None
    history_dir = home / ".amorsize" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def x_get_history_dir__mutmut_2() -> Path:
    """
    Get the directory where history files are stored.

    Returns:
        Path to history directory (creates if doesn't exist)
    """
    # Store in user's home directory under .amorsize/history
    home = Path.home()
    history_dir = None
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def x_get_history_dir__mutmut_3() -> Path:
    """
    Get the directory where history files are stored.

    Returns:
        Path to history directory (creates if doesn't exist)
    """
    # Store in user's home directory under .amorsize/history
    home = Path.home()
    history_dir = home / ".amorsize" * "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def x_get_history_dir__mutmut_4() -> Path:
    """
    Get the directory where history files are stored.

    Returns:
        Path to history directory (creates if doesn't exist)
    """
    # Store in user's home directory under .amorsize/history
    home = Path.home()
    history_dir = home * ".amorsize" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def x_get_history_dir__mutmut_5() -> Path:
    """
    Get the directory where history files are stored.

    Returns:
        Path to history directory (creates if doesn't exist)
    """
    # Store in user's home directory under .amorsize/history
    home = Path.home()
    history_dir = home / "XX.amorsizeXX" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def x_get_history_dir__mutmut_6() -> Path:
    """
    Get the directory where history files are stored.

    Returns:
        Path to history directory (creates if doesn't exist)
    """
    # Store in user's home directory under .amorsize/history
    home = Path.home()
    history_dir = home / ".AMORSIZE" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def x_get_history_dir__mutmut_7() -> Path:
    """
    Get the directory where history files are stored.

    Returns:
        Path to history directory (creates if doesn't exist)
    """
    # Store in user's home directory under .amorsize/history
    home = Path.home()
    history_dir = home / ".amorsize" / "XXhistoryXX"
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def x_get_history_dir__mutmut_8() -> Path:
    """
    Get the directory where history files are stored.

    Returns:
        Path to history directory (creates if doesn't exist)
    """
    # Store in user's home directory under .amorsize/history
    home = Path.home()
    history_dir = home / ".amorsize" / "HISTORY"
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def x_get_history_dir__mutmut_9() -> Path:
    """
    Get the directory where history files are stored.

    Returns:
        Path to history directory (creates if doesn't exist)
    """
    # Store in user's home directory under .amorsize/history
    home = Path.home()
    history_dir = home / ".amorsize" / "history"
    history_dir.mkdir(parents=None, exist_ok=True)
    return history_dir


def x_get_history_dir__mutmut_10() -> Path:
    """
    Get the directory where history files are stored.

    Returns:
        Path to history directory (creates if doesn't exist)
    """
    # Store in user's home directory under .amorsize/history
    home = Path.home()
    history_dir = home / ".amorsize" / "history"
    history_dir.mkdir(parents=True, exist_ok=None)
    return history_dir


def x_get_history_dir__mutmut_11() -> Path:
    """
    Get the directory where history files are stored.

    Returns:
        Path to history directory (creates if doesn't exist)
    """
    # Store in user's home directory under .amorsize/history
    home = Path.home()
    history_dir = home / ".amorsize" / "history"
    history_dir.mkdir(exist_ok=True)
    return history_dir


def x_get_history_dir__mutmut_12() -> Path:
    """
    Get the directory where history files are stored.

    Returns:
        Path to history directory (creates if doesn't exist)
    """
    # Store in user's home directory under .amorsize/history
    home = Path.home()
    history_dir = home / ".amorsize" / "history"
    history_dir.mkdir(parents=True, )
    return history_dir


def x_get_history_dir__mutmut_13() -> Path:
    """
    Get the directory where history files are stored.

    Returns:
        Path to history directory (creates if doesn't exist)
    """
    # Store in user's home directory under .amorsize/history
    home = Path.home()
    history_dir = home / ".amorsize" / "history"
    history_dir.mkdir(parents=False, exist_ok=True)
    return history_dir


def x_get_history_dir__mutmut_14() -> Path:
    """
    Get the directory where history files are stored.

    Returns:
        Path to history directory (creates if doesn't exist)
    """
    # Store in user's home directory under .amorsize/history
    home = Path.home()
    history_dir = home / ".amorsize" / "history"
    history_dir.mkdir(parents=True, exist_ok=False)
    return history_dir

x_get_history_dir__mutmut_mutants : ClassVar[MutantDict] = {
'x_get_history_dir__mutmut_1': x_get_history_dir__mutmut_1, 
    'x_get_history_dir__mutmut_2': x_get_history_dir__mutmut_2, 
    'x_get_history_dir__mutmut_3': x_get_history_dir__mutmut_3, 
    'x_get_history_dir__mutmut_4': x_get_history_dir__mutmut_4, 
    'x_get_history_dir__mutmut_5': x_get_history_dir__mutmut_5, 
    'x_get_history_dir__mutmut_6': x_get_history_dir__mutmut_6, 
    'x_get_history_dir__mutmut_7': x_get_history_dir__mutmut_7, 
    'x_get_history_dir__mutmut_8': x_get_history_dir__mutmut_8, 
    'x_get_history_dir__mutmut_9': x_get_history_dir__mutmut_9, 
    'x_get_history_dir__mutmut_10': x_get_history_dir__mutmut_10, 
    'x_get_history_dir__mutmut_11': x_get_history_dir__mutmut_11, 
    'x_get_history_dir__mutmut_12': x_get_history_dir__mutmut_12, 
    'x_get_history_dir__mutmut_13': x_get_history_dir__mutmut_13, 
    'x_get_history_dir__mutmut_14': x_get_history_dir__mutmut_14
}

def get_history_dir(*args, **kwargs):
    result = _mutmut_trampoline(x_get_history_dir__mutmut_orig, x_get_history_dir__mutmut_mutants, args, kwargs)
    return result 

get_history_dir.__signature__ = _mutmut_signature(x_get_history_dir__mutmut_orig)
x_get_history_dir__mutmut_orig.__name__ = 'x_get_history_dir'


def x_save_result__mutmut_orig(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_1(
    result: ComparisonResult,
    name: str,
    function_name: str = "XXunknownXX",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_2(
    result: ComparisonResult,
    name: str,
    function_name: str = "UNKNOWN",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_3(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 1,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_4(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = None
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_5(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() - "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_6(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(None).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_7(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "XXZXX"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_8(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_9(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = None
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_10(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(None, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_11(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, None)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_12(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_13(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, )
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_14(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = None

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_15(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = None

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_16(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=None,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_17(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=None,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_18(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=None,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_19(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=None,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_20(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=None,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_21(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=None,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_22(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=None,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_23(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=None
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_24(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_25(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_26(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_27(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_28(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_29(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_30(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_31(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_32(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = None
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_33(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = None
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_34(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = None

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_35(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir * filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_36(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(None, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_37(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, None) as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_38(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open('w') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_39(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, ) as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_40(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'XXwXX') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_41(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'W') as f:
        json.dump(entry.to_dict(), f, indent=2)

    return entry_id


def x_save_result__mutmut_42(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(None, f, indent=2)

    return entry_id


def x_save_result__mutmut_43(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), None, indent=2)

    return entry_id


def x_save_result__mutmut_44(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=None)

    return entry_id


def x_save_result__mutmut_45(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(f, indent=2)

    return entry_id


def x_save_result__mutmut_46(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), indent=2)

    return entry_id


def x_save_result__mutmut_47(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, )

    return entry_id


def x_save_result__mutmut_48(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.

    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store

    Returns:
        ID of the saved entry

    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()

    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )

    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename

    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=3)

    return entry_id

x_save_result__mutmut_mutants : ClassVar[MutantDict] = {
'x_save_result__mutmut_1': x_save_result__mutmut_1, 
    'x_save_result__mutmut_2': x_save_result__mutmut_2, 
    'x_save_result__mutmut_3': x_save_result__mutmut_3, 
    'x_save_result__mutmut_4': x_save_result__mutmut_4, 
    'x_save_result__mutmut_5': x_save_result__mutmut_5, 
    'x_save_result__mutmut_6': x_save_result__mutmut_6, 
    'x_save_result__mutmut_7': x_save_result__mutmut_7, 
    'x_save_result__mutmut_8': x_save_result__mutmut_8, 
    'x_save_result__mutmut_9': x_save_result__mutmut_9, 
    'x_save_result__mutmut_10': x_save_result__mutmut_10, 
    'x_save_result__mutmut_11': x_save_result__mutmut_11, 
    'x_save_result__mutmut_12': x_save_result__mutmut_12, 
    'x_save_result__mutmut_13': x_save_result__mutmut_13, 
    'x_save_result__mutmut_14': x_save_result__mutmut_14, 
    'x_save_result__mutmut_15': x_save_result__mutmut_15, 
    'x_save_result__mutmut_16': x_save_result__mutmut_16, 
    'x_save_result__mutmut_17': x_save_result__mutmut_17, 
    'x_save_result__mutmut_18': x_save_result__mutmut_18, 
    'x_save_result__mutmut_19': x_save_result__mutmut_19, 
    'x_save_result__mutmut_20': x_save_result__mutmut_20, 
    'x_save_result__mutmut_21': x_save_result__mutmut_21, 
    'x_save_result__mutmut_22': x_save_result__mutmut_22, 
    'x_save_result__mutmut_23': x_save_result__mutmut_23, 
    'x_save_result__mutmut_24': x_save_result__mutmut_24, 
    'x_save_result__mutmut_25': x_save_result__mutmut_25, 
    'x_save_result__mutmut_26': x_save_result__mutmut_26, 
    'x_save_result__mutmut_27': x_save_result__mutmut_27, 
    'x_save_result__mutmut_28': x_save_result__mutmut_28, 
    'x_save_result__mutmut_29': x_save_result__mutmut_29, 
    'x_save_result__mutmut_30': x_save_result__mutmut_30, 
    'x_save_result__mutmut_31': x_save_result__mutmut_31, 
    'x_save_result__mutmut_32': x_save_result__mutmut_32, 
    'x_save_result__mutmut_33': x_save_result__mutmut_33, 
    'x_save_result__mutmut_34': x_save_result__mutmut_34, 
    'x_save_result__mutmut_35': x_save_result__mutmut_35, 
    'x_save_result__mutmut_36': x_save_result__mutmut_36, 
    'x_save_result__mutmut_37': x_save_result__mutmut_37, 
    'x_save_result__mutmut_38': x_save_result__mutmut_38, 
    'x_save_result__mutmut_39': x_save_result__mutmut_39, 
    'x_save_result__mutmut_40': x_save_result__mutmut_40, 
    'x_save_result__mutmut_41': x_save_result__mutmut_41, 
    'x_save_result__mutmut_42': x_save_result__mutmut_42, 
    'x_save_result__mutmut_43': x_save_result__mutmut_43, 
    'x_save_result__mutmut_44': x_save_result__mutmut_44, 
    'x_save_result__mutmut_45': x_save_result__mutmut_45, 
    'x_save_result__mutmut_46': x_save_result__mutmut_46, 
    'x_save_result__mutmut_47': x_save_result__mutmut_47, 
    'x_save_result__mutmut_48': x_save_result__mutmut_48
}

def save_result(*args, **kwargs):
    result = _mutmut_trampoline(x_save_result__mutmut_orig, x_save_result__mutmut_mutants, args, kwargs)
    return result 

save_result.__signature__ = _mutmut_signature(x_save_result__mutmut_orig)
x_save_result__mutmut_orig.__name__ = 'x_save_result'


def x_load_result__mutmut_orig(entry_id: str) -> Optional[HistoryEntry]:
    """
    Load a specific result from history by ID.

    Args:
        entry_id: ID of the entry to load

    Returns:
        HistoryEntry object, or None if not found

    Example:
        >>> entry = load_result("a1b2c3d4e5f6")
        >>> if entry:
        ...     print(f"Result: {entry.name} from {entry.timestamp}")
    """
    history_dir = get_history_dir()
    filepath = history_dir / f"{entry_id}.json"

    if not filepath.exists():
        return None

    with open(filepath, 'r') as f:
        data = json.load(f)

    return HistoryEntry.from_dict(data)


def x_load_result__mutmut_1(entry_id: str) -> Optional[HistoryEntry]:
    """
    Load a specific result from history by ID.

    Args:
        entry_id: ID of the entry to load

    Returns:
        HistoryEntry object, or None if not found

    Example:
        >>> entry = load_result("a1b2c3d4e5f6")
        >>> if entry:
        ...     print(f"Result: {entry.name} from {entry.timestamp}")
    """
    history_dir = None
    filepath = history_dir / f"{entry_id}.json"

    if not filepath.exists():
        return None

    with open(filepath, 'r') as f:
        data = json.load(f)

    return HistoryEntry.from_dict(data)


def x_load_result__mutmut_2(entry_id: str) -> Optional[HistoryEntry]:
    """
    Load a specific result from history by ID.

    Args:
        entry_id: ID of the entry to load

    Returns:
        HistoryEntry object, or None if not found

    Example:
        >>> entry = load_result("a1b2c3d4e5f6")
        >>> if entry:
        ...     print(f"Result: {entry.name} from {entry.timestamp}")
    """
    history_dir = get_history_dir()
    filepath = None

    if not filepath.exists():
        return None

    with open(filepath, 'r') as f:
        data = json.load(f)

    return HistoryEntry.from_dict(data)


def x_load_result__mutmut_3(entry_id: str) -> Optional[HistoryEntry]:
    """
    Load a specific result from history by ID.

    Args:
        entry_id: ID of the entry to load

    Returns:
        HistoryEntry object, or None if not found

    Example:
        >>> entry = load_result("a1b2c3d4e5f6")
        >>> if entry:
        ...     print(f"Result: {entry.name} from {entry.timestamp}")
    """
    history_dir = get_history_dir()
    filepath = history_dir * f"{entry_id}.json"

    if not filepath.exists():
        return None

    with open(filepath, 'r') as f:
        data = json.load(f)

    return HistoryEntry.from_dict(data)


def x_load_result__mutmut_4(entry_id: str) -> Optional[HistoryEntry]:
    """
    Load a specific result from history by ID.

    Args:
        entry_id: ID of the entry to load

    Returns:
        HistoryEntry object, or None if not found

    Example:
        >>> entry = load_result("a1b2c3d4e5f6")
        >>> if entry:
        ...     print(f"Result: {entry.name} from {entry.timestamp}")
    """
    history_dir = get_history_dir()
    filepath = history_dir / f"{entry_id}.json"

    if filepath.exists():
        return None

    with open(filepath, 'r') as f:
        data = json.load(f)

    return HistoryEntry.from_dict(data)


def x_load_result__mutmut_5(entry_id: str) -> Optional[HistoryEntry]:
    """
    Load a specific result from history by ID.

    Args:
        entry_id: ID of the entry to load

    Returns:
        HistoryEntry object, or None if not found

    Example:
        >>> entry = load_result("a1b2c3d4e5f6")
        >>> if entry:
        ...     print(f"Result: {entry.name} from {entry.timestamp}")
    """
    history_dir = get_history_dir()
    filepath = history_dir / f"{entry_id}.json"

    if not filepath.exists():
        return None

    with open(None, 'r') as f:
        data = json.load(f)

    return HistoryEntry.from_dict(data)


def x_load_result__mutmut_6(entry_id: str) -> Optional[HistoryEntry]:
    """
    Load a specific result from history by ID.

    Args:
        entry_id: ID of the entry to load

    Returns:
        HistoryEntry object, or None if not found

    Example:
        >>> entry = load_result("a1b2c3d4e5f6")
        >>> if entry:
        ...     print(f"Result: {entry.name} from {entry.timestamp}")
    """
    history_dir = get_history_dir()
    filepath = history_dir / f"{entry_id}.json"

    if not filepath.exists():
        return None

    with open(filepath, None) as f:
        data = json.load(f)

    return HistoryEntry.from_dict(data)


def x_load_result__mutmut_7(entry_id: str) -> Optional[HistoryEntry]:
    """
    Load a specific result from history by ID.

    Args:
        entry_id: ID of the entry to load

    Returns:
        HistoryEntry object, or None if not found

    Example:
        >>> entry = load_result("a1b2c3d4e5f6")
        >>> if entry:
        ...     print(f"Result: {entry.name} from {entry.timestamp}")
    """
    history_dir = get_history_dir()
    filepath = history_dir / f"{entry_id}.json"

    if not filepath.exists():
        return None

    with open('r') as f:
        data = json.load(f)

    return HistoryEntry.from_dict(data)


def x_load_result__mutmut_8(entry_id: str) -> Optional[HistoryEntry]:
    """
    Load a specific result from history by ID.

    Args:
        entry_id: ID of the entry to load

    Returns:
        HistoryEntry object, or None if not found

    Example:
        >>> entry = load_result("a1b2c3d4e5f6")
        >>> if entry:
        ...     print(f"Result: {entry.name} from {entry.timestamp}")
    """
    history_dir = get_history_dir()
    filepath = history_dir / f"{entry_id}.json"

    if not filepath.exists():
        return None

    with open(filepath, ) as f:
        data = json.load(f)

    return HistoryEntry.from_dict(data)


def x_load_result__mutmut_9(entry_id: str) -> Optional[HistoryEntry]:
    """
    Load a specific result from history by ID.

    Args:
        entry_id: ID of the entry to load

    Returns:
        HistoryEntry object, or None if not found

    Example:
        >>> entry = load_result("a1b2c3d4e5f6")
        >>> if entry:
        ...     print(f"Result: {entry.name} from {entry.timestamp}")
    """
    history_dir = get_history_dir()
    filepath = history_dir / f"{entry_id}.json"

    if not filepath.exists():
        return None

    with open(filepath, 'XXrXX') as f:
        data = json.load(f)

    return HistoryEntry.from_dict(data)


def x_load_result__mutmut_10(entry_id: str) -> Optional[HistoryEntry]:
    """
    Load a specific result from history by ID.

    Args:
        entry_id: ID of the entry to load

    Returns:
        HistoryEntry object, or None if not found

    Example:
        >>> entry = load_result("a1b2c3d4e5f6")
        >>> if entry:
        ...     print(f"Result: {entry.name} from {entry.timestamp}")
    """
    history_dir = get_history_dir()
    filepath = history_dir / f"{entry_id}.json"

    if not filepath.exists():
        return None

    with open(filepath, 'R') as f:
        data = json.load(f)

    return HistoryEntry.from_dict(data)


def x_load_result__mutmut_11(entry_id: str) -> Optional[HistoryEntry]:
    """
    Load a specific result from history by ID.

    Args:
        entry_id: ID of the entry to load

    Returns:
        HistoryEntry object, or None if not found

    Example:
        >>> entry = load_result("a1b2c3d4e5f6")
        >>> if entry:
        ...     print(f"Result: {entry.name} from {entry.timestamp}")
    """
    history_dir = get_history_dir()
    filepath = history_dir / f"{entry_id}.json"

    if not filepath.exists():
        return None

    with open(filepath, 'r') as f:
        data = None

    return HistoryEntry.from_dict(data)


def x_load_result__mutmut_12(entry_id: str) -> Optional[HistoryEntry]:
    """
    Load a specific result from history by ID.

    Args:
        entry_id: ID of the entry to load

    Returns:
        HistoryEntry object, or None if not found

    Example:
        >>> entry = load_result("a1b2c3d4e5f6")
        >>> if entry:
        ...     print(f"Result: {entry.name} from {entry.timestamp}")
    """
    history_dir = get_history_dir()
    filepath = history_dir / f"{entry_id}.json"

    if not filepath.exists():
        return None

    with open(filepath, 'r') as f:
        data = json.load(None)

    return HistoryEntry.from_dict(data)


def x_load_result__mutmut_13(entry_id: str) -> Optional[HistoryEntry]:
    """
    Load a specific result from history by ID.

    Args:
        entry_id: ID of the entry to load

    Returns:
        HistoryEntry object, or None if not found

    Example:
        >>> entry = load_result("a1b2c3d4e5f6")
        >>> if entry:
        ...     print(f"Result: {entry.name} from {entry.timestamp}")
    """
    history_dir = get_history_dir()
    filepath = history_dir / f"{entry_id}.json"

    if not filepath.exists():
        return None

    with open(filepath, 'r') as f:
        data = json.load(f)

    return HistoryEntry.from_dict(None)

x_load_result__mutmut_mutants : ClassVar[MutantDict] = {
'x_load_result__mutmut_1': x_load_result__mutmut_1, 
    'x_load_result__mutmut_2': x_load_result__mutmut_2, 
    'x_load_result__mutmut_3': x_load_result__mutmut_3, 
    'x_load_result__mutmut_4': x_load_result__mutmut_4, 
    'x_load_result__mutmut_5': x_load_result__mutmut_5, 
    'x_load_result__mutmut_6': x_load_result__mutmut_6, 
    'x_load_result__mutmut_7': x_load_result__mutmut_7, 
    'x_load_result__mutmut_8': x_load_result__mutmut_8, 
    'x_load_result__mutmut_9': x_load_result__mutmut_9, 
    'x_load_result__mutmut_10': x_load_result__mutmut_10, 
    'x_load_result__mutmut_11': x_load_result__mutmut_11, 
    'x_load_result__mutmut_12': x_load_result__mutmut_12, 
    'x_load_result__mutmut_13': x_load_result__mutmut_13
}

def load_result(*args, **kwargs):
    result = _mutmut_trampoline(x_load_result__mutmut_orig, x_load_result__mutmut_mutants, args, kwargs)
    return result 

load_result.__signature__ = _mutmut_signature(x_load_result__mutmut_orig)
x_load_result__mutmut_orig.__name__ = 'x_load_result'


def x_list_results__mutmut_orig(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_1(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = None
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_2(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = None

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_3(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob(None):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_4(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("XX*.jsonXX"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_5(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.JSON"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_6(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(None, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_7(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, None) as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_8(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open('r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_9(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, ) as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_10(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'XXrXX') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_11(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'R') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_12(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = None
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_13(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(None)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_14(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = None

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_15(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(None)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_16(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None and name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_17(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is not None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_18(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.upper() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_19(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() not in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_20(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.upper():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_21(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(None)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_22(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            break

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_23(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=None, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_24(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=None)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_25(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_26(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, )

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_27(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: None, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_28(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=False)

    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_29(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is None:
        entries = entries[:limit]

    return entries


def x_list_results__mutmut_30(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.

    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned

    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)

    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []

    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)

            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue

    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply limit if provided
    if limit is not None:
        entries = None

    return entries

x_list_results__mutmut_mutants : ClassVar[MutantDict] = {
'x_list_results__mutmut_1': x_list_results__mutmut_1, 
    'x_list_results__mutmut_2': x_list_results__mutmut_2, 
    'x_list_results__mutmut_3': x_list_results__mutmut_3, 
    'x_list_results__mutmut_4': x_list_results__mutmut_4, 
    'x_list_results__mutmut_5': x_list_results__mutmut_5, 
    'x_list_results__mutmut_6': x_list_results__mutmut_6, 
    'x_list_results__mutmut_7': x_list_results__mutmut_7, 
    'x_list_results__mutmut_8': x_list_results__mutmut_8, 
    'x_list_results__mutmut_9': x_list_results__mutmut_9, 
    'x_list_results__mutmut_10': x_list_results__mutmut_10, 
    'x_list_results__mutmut_11': x_list_results__mutmut_11, 
    'x_list_results__mutmut_12': x_list_results__mutmut_12, 
    'x_list_results__mutmut_13': x_list_results__mutmut_13, 
    'x_list_results__mutmut_14': x_list_results__mutmut_14, 
    'x_list_results__mutmut_15': x_list_results__mutmut_15, 
    'x_list_results__mutmut_16': x_list_results__mutmut_16, 
    'x_list_results__mutmut_17': x_list_results__mutmut_17, 
    'x_list_results__mutmut_18': x_list_results__mutmut_18, 
    'x_list_results__mutmut_19': x_list_results__mutmut_19, 
    'x_list_results__mutmut_20': x_list_results__mutmut_20, 
    'x_list_results__mutmut_21': x_list_results__mutmut_21, 
    'x_list_results__mutmut_22': x_list_results__mutmut_22, 
    'x_list_results__mutmut_23': x_list_results__mutmut_23, 
    'x_list_results__mutmut_24': x_list_results__mutmut_24, 
    'x_list_results__mutmut_25': x_list_results__mutmut_25, 
    'x_list_results__mutmut_26': x_list_results__mutmut_26, 
    'x_list_results__mutmut_27': x_list_results__mutmut_27, 
    'x_list_results__mutmut_28': x_list_results__mutmut_28, 
    'x_list_results__mutmut_29': x_list_results__mutmut_29, 
    'x_list_results__mutmut_30': x_list_results__mutmut_30
}

def list_results(*args, **kwargs):
    result = _mutmut_trampoline(x_list_results__mutmut_orig, x_list_results__mutmut_mutants, args, kwargs)
    return result 

list_results.__signature__ = _mutmut_signature(x_list_results__mutmut_orig)
x_list_results__mutmut_orig.__name__ = 'x_list_results'


def x_delete_result__mutmut_orig(entry_id: str) -> bool:
    """
    Delete a result from history.

    Args:
        entry_id: ID of the entry to delete

    Returns:
        True if deleted, False if not found

    Example:
        >>> if delete_result("a1b2c3d4e5f6"):
        ...     print("Deleted successfully")
    """
    history_dir = get_history_dir()
    filepath = history_dir / f"{entry_id}.json"

    if filepath.exists():
        filepath.unlink()
        return True

    return False


def x_delete_result__mutmut_1(entry_id: str) -> bool:
    """
    Delete a result from history.

    Args:
        entry_id: ID of the entry to delete

    Returns:
        True if deleted, False if not found

    Example:
        >>> if delete_result("a1b2c3d4e5f6"):
        ...     print("Deleted successfully")
    """
    history_dir = None
    filepath = history_dir / f"{entry_id}.json"

    if filepath.exists():
        filepath.unlink()
        return True

    return False


def x_delete_result__mutmut_2(entry_id: str) -> bool:
    """
    Delete a result from history.

    Args:
        entry_id: ID of the entry to delete

    Returns:
        True if deleted, False if not found

    Example:
        >>> if delete_result("a1b2c3d4e5f6"):
        ...     print("Deleted successfully")
    """
    history_dir = get_history_dir()
    filepath = None

    if filepath.exists():
        filepath.unlink()
        return True

    return False


def x_delete_result__mutmut_3(entry_id: str) -> bool:
    """
    Delete a result from history.

    Args:
        entry_id: ID of the entry to delete

    Returns:
        True if deleted, False if not found

    Example:
        >>> if delete_result("a1b2c3d4e5f6"):
        ...     print("Deleted successfully")
    """
    history_dir = get_history_dir()
    filepath = history_dir * f"{entry_id}.json"

    if filepath.exists():
        filepath.unlink()
        return True

    return False


def x_delete_result__mutmut_4(entry_id: str) -> bool:
    """
    Delete a result from history.

    Args:
        entry_id: ID of the entry to delete

    Returns:
        True if deleted, False if not found

    Example:
        >>> if delete_result("a1b2c3d4e5f6"):
        ...     print("Deleted successfully")
    """
    history_dir = get_history_dir()
    filepath = history_dir / f"{entry_id}.json"

    if filepath.exists():
        filepath.unlink()
        return False

    return False


def x_delete_result__mutmut_5(entry_id: str) -> bool:
    """
    Delete a result from history.

    Args:
        entry_id: ID of the entry to delete

    Returns:
        True if deleted, False if not found

    Example:
        >>> if delete_result("a1b2c3d4e5f6"):
        ...     print("Deleted successfully")
    """
    history_dir = get_history_dir()
    filepath = history_dir / f"{entry_id}.json"

    if filepath.exists():
        filepath.unlink()
        return True

    return True

x_delete_result__mutmut_mutants : ClassVar[MutantDict] = {
'x_delete_result__mutmut_1': x_delete_result__mutmut_1, 
    'x_delete_result__mutmut_2': x_delete_result__mutmut_2, 
    'x_delete_result__mutmut_3': x_delete_result__mutmut_3, 
    'x_delete_result__mutmut_4': x_delete_result__mutmut_4, 
    'x_delete_result__mutmut_5': x_delete_result__mutmut_5
}

def delete_result(*args, **kwargs):
    result = _mutmut_trampoline(x_delete_result__mutmut_orig, x_delete_result__mutmut_mutants, args, kwargs)
    return result 

delete_result.__signature__ = _mutmut_signature(x_delete_result__mutmut_orig)
x_delete_result__mutmut_orig.__name__ = 'x_delete_result'


def x_compare_entries__mutmut_orig(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_1(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = None
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_2(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(None)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_3(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = None

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_4(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(None)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_5(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None and entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_6(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is not None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_7(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is not None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_8(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = None
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_9(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = None

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_10(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = None
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_11(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = None

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_12(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = None
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_13(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 + best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_14(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = None
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_15(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 + best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_16(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = None

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_17(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) / 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_18(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) * best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_19(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 + best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_20(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 101 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_21(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 >= 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_22(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 1 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_23(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 1.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_24(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = None

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_25(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") or entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_26(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get(None) == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_27(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("XXplatformXX") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_28(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("PLATFORM") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_29(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") != entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_30(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get(None) and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_31(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("XXplatformXX") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_32(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("PLATFORM") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_33(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get(None) == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_34(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("XXphysical_coresXX") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_35(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("PHYSICAL_CORES") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_36(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") != entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_37(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get(None)
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_38(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("XXphysical_coresXX")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_39(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("PHYSICAL_CORES")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_40(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "XXentry1XX": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_41(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "ENTRY1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_42(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "XXidXX": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_43(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "ID": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_44(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "XXnameXX": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_45(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "NAME": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_46(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "XXtimestampXX": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_47(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "TIMESTAMP": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_48(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "XXbest_strategyXX": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_49(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "BEST_STRATEGY": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_50(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "XXspeedupXX": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_51(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "SPEEDUP": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_52(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "XXexecution_timeXX": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_53(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "EXECUTION_TIME": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_54(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "XXsystemXX": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_55(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "SYSTEM": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_56(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "XXentry2XX": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_57(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "ENTRY2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_58(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "XXidXX": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_59(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "ID": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_60(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "XXnameXX": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_61(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "NAME": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_62(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "XXtimestampXX": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_63(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "TIMESTAMP": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_64(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "XXbest_strategyXX": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_65(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "BEST_STRATEGY": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_66(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "XXspeedupXX": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_67(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "SPEEDUP": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_68(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "XXexecution_timeXX": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_69(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "EXECUTION_TIME": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_70(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "XXsystemXX": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_71(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "SYSTEM": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_72(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "XXcomparisonXX": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_73(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "COMPARISON": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_74(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "XXspeedup_deltaXX": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_75(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "SPEEDUP_DELTA": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_76(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "XXtime_delta_secondsXX": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_77(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "TIME_DELTA_SECONDS": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_78(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "XXtime_delta_percentXX": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_79(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "TIME_DELTA_PERCENT": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_80(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "XXsame_systemXX": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_81(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "SAME_SYSTEM": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_82(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "XXis_regressionXX": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_83(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "IS_REGRESSION": time_delta > 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_84(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta >= 0  # Slower is a regression
        }
    }


def x_compare_entries__mutmut_85(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.

    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry

    Returns:
        Dictionary containing comparison data, or None if either entry not found

    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)

    if entry1 is None or entry2 is None:
        return None

    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]

    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]

    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0

    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )

    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 1  # Slower is a regression
        }
    }

x_compare_entries__mutmut_mutants : ClassVar[MutantDict] = {
'x_compare_entries__mutmut_1': x_compare_entries__mutmut_1, 
    'x_compare_entries__mutmut_2': x_compare_entries__mutmut_2, 
    'x_compare_entries__mutmut_3': x_compare_entries__mutmut_3, 
    'x_compare_entries__mutmut_4': x_compare_entries__mutmut_4, 
    'x_compare_entries__mutmut_5': x_compare_entries__mutmut_5, 
    'x_compare_entries__mutmut_6': x_compare_entries__mutmut_6, 
    'x_compare_entries__mutmut_7': x_compare_entries__mutmut_7, 
    'x_compare_entries__mutmut_8': x_compare_entries__mutmut_8, 
    'x_compare_entries__mutmut_9': x_compare_entries__mutmut_9, 
    'x_compare_entries__mutmut_10': x_compare_entries__mutmut_10, 
    'x_compare_entries__mutmut_11': x_compare_entries__mutmut_11, 
    'x_compare_entries__mutmut_12': x_compare_entries__mutmut_12, 
    'x_compare_entries__mutmut_13': x_compare_entries__mutmut_13, 
    'x_compare_entries__mutmut_14': x_compare_entries__mutmut_14, 
    'x_compare_entries__mutmut_15': x_compare_entries__mutmut_15, 
    'x_compare_entries__mutmut_16': x_compare_entries__mutmut_16, 
    'x_compare_entries__mutmut_17': x_compare_entries__mutmut_17, 
    'x_compare_entries__mutmut_18': x_compare_entries__mutmut_18, 
    'x_compare_entries__mutmut_19': x_compare_entries__mutmut_19, 
    'x_compare_entries__mutmut_20': x_compare_entries__mutmut_20, 
    'x_compare_entries__mutmut_21': x_compare_entries__mutmut_21, 
    'x_compare_entries__mutmut_22': x_compare_entries__mutmut_22, 
    'x_compare_entries__mutmut_23': x_compare_entries__mutmut_23, 
    'x_compare_entries__mutmut_24': x_compare_entries__mutmut_24, 
    'x_compare_entries__mutmut_25': x_compare_entries__mutmut_25, 
    'x_compare_entries__mutmut_26': x_compare_entries__mutmut_26, 
    'x_compare_entries__mutmut_27': x_compare_entries__mutmut_27, 
    'x_compare_entries__mutmut_28': x_compare_entries__mutmut_28, 
    'x_compare_entries__mutmut_29': x_compare_entries__mutmut_29, 
    'x_compare_entries__mutmut_30': x_compare_entries__mutmut_30, 
    'x_compare_entries__mutmut_31': x_compare_entries__mutmut_31, 
    'x_compare_entries__mutmut_32': x_compare_entries__mutmut_32, 
    'x_compare_entries__mutmut_33': x_compare_entries__mutmut_33, 
    'x_compare_entries__mutmut_34': x_compare_entries__mutmut_34, 
    'x_compare_entries__mutmut_35': x_compare_entries__mutmut_35, 
    'x_compare_entries__mutmut_36': x_compare_entries__mutmut_36, 
    'x_compare_entries__mutmut_37': x_compare_entries__mutmut_37, 
    'x_compare_entries__mutmut_38': x_compare_entries__mutmut_38, 
    'x_compare_entries__mutmut_39': x_compare_entries__mutmut_39, 
    'x_compare_entries__mutmut_40': x_compare_entries__mutmut_40, 
    'x_compare_entries__mutmut_41': x_compare_entries__mutmut_41, 
    'x_compare_entries__mutmut_42': x_compare_entries__mutmut_42, 
    'x_compare_entries__mutmut_43': x_compare_entries__mutmut_43, 
    'x_compare_entries__mutmut_44': x_compare_entries__mutmut_44, 
    'x_compare_entries__mutmut_45': x_compare_entries__mutmut_45, 
    'x_compare_entries__mutmut_46': x_compare_entries__mutmut_46, 
    'x_compare_entries__mutmut_47': x_compare_entries__mutmut_47, 
    'x_compare_entries__mutmut_48': x_compare_entries__mutmut_48, 
    'x_compare_entries__mutmut_49': x_compare_entries__mutmut_49, 
    'x_compare_entries__mutmut_50': x_compare_entries__mutmut_50, 
    'x_compare_entries__mutmut_51': x_compare_entries__mutmut_51, 
    'x_compare_entries__mutmut_52': x_compare_entries__mutmut_52, 
    'x_compare_entries__mutmut_53': x_compare_entries__mutmut_53, 
    'x_compare_entries__mutmut_54': x_compare_entries__mutmut_54, 
    'x_compare_entries__mutmut_55': x_compare_entries__mutmut_55, 
    'x_compare_entries__mutmut_56': x_compare_entries__mutmut_56, 
    'x_compare_entries__mutmut_57': x_compare_entries__mutmut_57, 
    'x_compare_entries__mutmut_58': x_compare_entries__mutmut_58, 
    'x_compare_entries__mutmut_59': x_compare_entries__mutmut_59, 
    'x_compare_entries__mutmut_60': x_compare_entries__mutmut_60, 
    'x_compare_entries__mutmut_61': x_compare_entries__mutmut_61, 
    'x_compare_entries__mutmut_62': x_compare_entries__mutmut_62, 
    'x_compare_entries__mutmut_63': x_compare_entries__mutmut_63, 
    'x_compare_entries__mutmut_64': x_compare_entries__mutmut_64, 
    'x_compare_entries__mutmut_65': x_compare_entries__mutmut_65, 
    'x_compare_entries__mutmut_66': x_compare_entries__mutmut_66, 
    'x_compare_entries__mutmut_67': x_compare_entries__mutmut_67, 
    'x_compare_entries__mutmut_68': x_compare_entries__mutmut_68, 
    'x_compare_entries__mutmut_69': x_compare_entries__mutmut_69, 
    'x_compare_entries__mutmut_70': x_compare_entries__mutmut_70, 
    'x_compare_entries__mutmut_71': x_compare_entries__mutmut_71, 
    'x_compare_entries__mutmut_72': x_compare_entries__mutmut_72, 
    'x_compare_entries__mutmut_73': x_compare_entries__mutmut_73, 
    'x_compare_entries__mutmut_74': x_compare_entries__mutmut_74, 
    'x_compare_entries__mutmut_75': x_compare_entries__mutmut_75, 
    'x_compare_entries__mutmut_76': x_compare_entries__mutmut_76, 
    'x_compare_entries__mutmut_77': x_compare_entries__mutmut_77, 
    'x_compare_entries__mutmut_78': x_compare_entries__mutmut_78, 
    'x_compare_entries__mutmut_79': x_compare_entries__mutmut_79, 
    'x_compare_entries__mutmut_80': x_compare_entries__mutmut_80, 
    'x_compare_entries__mutmut_81': x_compare_entries__mutmut_81, 
    'x_compare_entries__mutmut_82': x_compare_entries__mutmut_82, 
    'x_compare_entries__mutmut_83': x_compare_entries__mutmut_83, 
    'x_compare_entries__mutmut_84': x_compare_entries__mutmut_84, 
    'x_compare_entries__mutmut_85': x_compare_entries__mutmut_85
}

def compare_entries(*args, **kwargs):
    result = _mutmut_trampoline(x_compare_entries__mutmut_orig, x_compare_entries__mutmut_mutants, args, kwargs)
    return result 

compare_entries.__signature__ = _mutmut_signature(x_compare_entries__mutmut_orig)
x_compare_entries__mutmut_orig.__name__ = 'x_compare_entries'


def x_clear_history__mutmut_orig() -> int:
    """
    Clear all history entries.

    Returns:
        Number of entries deleted

    Warning:
        This cannot be undone!

    Example:
        >>> count = clear_history()
        >>> print(f"Deleted {count} entries")
    """
    history_dir = get_history_dir()
    count = 0

    for filepath in history_dir.glob("*.json"):
        try:
            filepath.unlink()
            count += 1
        except OSError:
            # Skip files that can't be deleted
            continue

    return count


def x_clear_history__mutmut_1() -> int:
    """
    Clear all history entries.

    Returns:
        Number of entries deleted

    Warning:
        This cannot be undone!

    Example:
        >>> count = clear_history()
        >>> print(f"Deleted {count} entries")
    """
    history_dir = None
    count = 0

    for filepath in history_dir.glob("*.json"):
        try:
            filepath.unlink()
            count += 1
        except OSError:
            # Skip files that can't be deleted
            continue

    return count


def x_clear_history__mutmut_2() -> int:
    """
    Clear all history entries.

    Returns:
        Number of entries deleted

    Warning:
        This cannot be undone!

    Example:
        >>> count = clear_history()
        >>> print(f"Deleted {count} entries")
    """
    history_dir = get_history_dir()
    count = None

    for filepath in history_dir.glob("*.json"):
        try:
            filepath.unlink()
            count += 1
        except OSError:
            # Skip files that can't be deleted
            continue

    return count


def x_clear_history__mutmut_3() -> int:
    """
    Clear all history entries.

    Returns:
        Number of entries deleted

    Warning:
        This cannot be undone!

    Example:
        >>> count = clear_history()
        >>> print(f"Deleted {count} entries")
    """
    history_dir = get_history_dir()
    count = 1

    for filepath in history_dir.glob("*.json"):
        try:
            filepath.unlink()
            count += 1
        except OSError:
            # Skip files that can't be deleted
            continue

    return count


def x_clear_history__mutmut_4() -> int:
    """
    Clear all history entries.

    Returns:
        Number of entries deleted

    Warning:
        This cannot be undone!

    Example:
        >>> count = clear_history()
        >>> print(f"Deleted {count} entries")
    """
    history_dir = get_history_dir()
    count = 0

    for filepath in history_dir.glob(None):
        try:
            filepath.unlink()
            count += 1
        except OSError:
            # Skip files that can't be deleted
            continue

    return count


def x_clear_history__mutmut_5() -> int:
    """
    Clear all history entries.

    Returns:
        Number of entries deleted

    Warning:
        This cannot be undone!

    Example:
        >>> count = clear_history()
        >>> print(f"Deleted {count} entries")
    """
    history_dir = get_history_dir()
    count = 0

    for filepath in history_dir.glob("XX*.jsonXX"):
        try:
            filepath.unlink()
            count += 1
        except OSError:
            # Skip files that can't be deleted
            continue

    return count


def x_clear_history__mutmut_6() -> int:
    """
    Clear all history entries.

    Returns:
        Number of entries deleted

    Warning:
        This cannot be undone!

    Example:
        >>> count = clear_history()
        >>> print(f"Deleted {count} entries")
    """
    history_dir = get_history_dir()
    count = 0

    for filepath in history_dir.glob("*.JSON"):
        try:
            filepath.unlink()
            count += 1
        except OSError:
            # Skip files that can't be deleted
            continue

    return count


def x_clear_history__mutmut_7() -> int:
    """
    Clear all history entries.

    Returns:
        Number of entries deleted

    Warning:
        This cannot be undone!

    Example:
        >>> count = clear_history()
        >>> print(f"Deleted {count} entries")
    """
    history_dir = get_history_dir()
    count = 0

    for filepath in history_dir.glob("*.json"):
        try:
            filepath.unlink()
            count = 1
        except OSError:
            # Skip files that can't be deleted
            continue

    return count


def x_clear_history__mutmut_8() -> int:
    """
    Clear all history entries.

    Returns:
        Number of entries deleted

    Warning:
        This cannot be undone!

    Example:
        >>> count = clear_history()
        >>> print(f"Deleted {count} entries")
    """
    history_dir = get_history_dir()
    count = 0

    for filepath in history_dir.glob("*.json"):
        try:
            filepath.unlink()
            count -= 1
        except OSError:
            # Skip files that can't be deleted
            continue

    return count


def x_clear_history__mutmut_9() -> int:
    """
    Clear all history entries.

    Returns:
        Number of entries deleted

    Warning:
        This cannot be undone!

    Example:
        >>> count = clear_history()
        >>> print(f"Deleted {count} entries")
    """
    history_dir = get_history_dir()
    count = 0

    for filepath in history_dir.glob("*.json"):
        try:
            filepath.unlink()
            count += 2
        except OSError:
            # Skip files that can't be deleted
            continue

    return count


def x_clear_history__mutmut_10() -> int:
    """
    Clear all history entries.

    Returns:
        Number of entries deleted

    Warning:
        This cannot be undone!

    Example:
        >>> count = clear_history()
        >>> print(f"Deleted {count} entries")
    """
    history_dir = get_history_dir()
    count = 0

    for filepath in history_dir.glob("*.json"):
        try:
            filepath.unlink()
            count += 1
        except OSError:
            # Skip files that can't be deleted
            break

    return count

x_clear_history__mutmut_mutants : ClassVar[MutantDict] = {
'x_clear_history__mutmut_1': x_clear_history__mutmut_1, 
    'x_clear_history__mutmut_2': x_clear_history__mutmut_2, 
    'x_clear_history__mutmut_3': x_clear_history__mutmut_3, 
    'x_clear_history__mutmut_4': x_clear_history__mutmut_4, 
    'x_clear_history__mutmut_5': x_clear_history__mutmut_5, 
    'x_clear_history__mutmut_6': x_clear_history__mutmut_6, 
    'x_clear_history__mutmut_7': x_clear_history__mutmut_7, 
    'x_clear_history__mutmut_8': x_clear_history__mutmut_8, 
    'x_clear_history__mutmut_9': x_clear_history__mutmut_9, 
    'x_clear_history__mutmut_10': x_clear_history__mutmut_10
}

def clear_history(*args, **kwargs):
    result = _mutmut_trampoline(x_clear_history__mutmut_orig, x_clear_history__mutmut_mutants, args, kwargs)
    return result 

clear_history.__signature__ = _mutmut_signature(x_clear_history__mutmut_orig)
x_clear_history__mutmut_orig.__name__ = 'x_clear_history'
