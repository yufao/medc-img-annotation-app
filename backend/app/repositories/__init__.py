"""Repository layer package (Phase 3).

Currently only implements DatasetRepository as a pattern example.
Other collections can follow the same shape incrementally to reduce refactor risk.
"""
from .dataset_repository import dataset_repository, DatasetRepository  # noqa: F401

__all__ = [
    'dataset_repository',
    'DatasetRepository'
]
