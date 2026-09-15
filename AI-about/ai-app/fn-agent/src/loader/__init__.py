"""Schema loader package.

Loads JSON schema files from the top-level `schema/` directory and
builds an in-memory index for runtime use.
"""

from .loader import load_all, SchemaBundle
from .index import SchemaIndex, build_index

__all__ = ["load_all", "SchemaBundle", "SchemaIndex", "build_index"]