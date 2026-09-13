"""
MCAP Bridge — ingestion and extraction of MCAP files in Mosaico.

This module provides bridge functionality for working with MCAP data format,
enabling both ingestion (reading MCAP files into Mosaico) and extraction
(writing Mosaico sequences back to MCAP files).

Main components:
- :class:`McapSequenceExtractor`: Extract Mosaico sequences to MCAP files
- :class:`McapExtractorConfig`: Configuration for extraction
"""

from .extractor import (
    McapExtractorConfig as McapExtractorConfig,
    McapSequenceExtractor as McapSequenceExtractor,
)

__all__ = [
    "McapExtractorConfig",
    "McapSequenceExtractor",
]
