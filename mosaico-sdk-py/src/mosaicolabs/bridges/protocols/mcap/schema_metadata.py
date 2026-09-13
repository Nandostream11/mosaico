"""
McapSchemaMetadata — encapsulates MCAP-specific topic metadata.

Mirrors the ROS Bridge's `RosSchemaMetadata` pattern for byte-exact round-tripping
of MCAP schemas during extraction.

The `_mcap_` namespace stores:
- `encoding` (e.g. "protobuf", "jsonschema", "ros2msg")
- `schema_name` (e.g. "sensor_msgs/msg/Imu" or "foxglove.PointCloud")
- `schema_data_b64` (raw schema bytes, base64-encoded)

This ensures extractors can reconstruct MCAP files with bit-identical schemas.
"""

from __future__ import annotations

import base64
from typing import Any, ClassVar, Optional


class McapSchemaMetadata:
    """
    Encapsulates Mosaico's reserved ``_mcap_`` topic-metadata namespace.

    Every topic ingested from MCAP carries encoding-specific bookkeeping (original
    ``encoding``, raw``schema_name``, raw ``schema_data_b64``) under one reserved
    key, so that:

    * The literal string ``"_mcap_"`` exists in exactly one place (:attr:`KEY`), instead of
      being duplicated across adapters, loaders, and the injector.
    * Callers build up this namespace incrementally via :meth:`update` without ever touching
      the wrapping dict shape by hand.
    * Extractors can byte-exactly reconstruct the original MCAP schema on write-back.

    Example:
        ```python
        meta = McapSchemaMetadata(
            encoding="protobuf",
            schema_name="sensor_msgs/msg/Imu",
            schema_data_b64=base64.b64encode(raw_schema_bytes).decode()
        )
        topic_metadata = meta.merge_into(user_supplied_metadata)
        # topic_metadata == {..., "_mcap_": {"encoding": "protobuf", ...}}
        ```
    """

    KEY: ClassVar[str] = "_mcap_"
    """The reserved metadata key. Loaders/extractors should reference this
    constant rather than the literal string, so the namespace can be renamed in one place."""

    def __init__(self, **fields: Any):
        """Initialize with keyword arguments for MCAP metadata fields.

        Args:
            **fields: MCAP-specific metadata fields (encoding, schema_name, schema_data_b64, etc.)
        """
        self.fields: dict = dict(fields)

    def update(self, **fields: Any) -> "McapSchemaMetadata":
        """
        Merge additional fields into this block, in place. Returns `self` for chaining.

        Args:
            **fields (Any): Additional fields to merge.

        Returns:
            McapSchemaMetadata: The updated metadata instance.
        """
        self.fields.update(fields)
        return self

    def to_dict(self) -> dict:
        """
        Wrap the current fields under the reserved key, e.g. `{"_mcap_": {...}}`.

        Returns:
            dict: A dictionary containing the `_mcap_` block with the current fields.
        """
        return {self.KEY: dict(self.fields)}

    def merge_into(self, metadata: dict) -> dict:
        """
        Merge this block into an existing metadata dict's `_mcap_` namespace, creating it
        if absent. Mutates and returns `metadata`.

        Args:
            metadata (dict): The existing metadata dict to merge into.

        Returns:
            dict: The updated metadata dict with the `_mcap_` block merged in.
        """
        metadata.setdefault(self.KEY, {}).update(self.fields)
        return metadata

    @classmethod
    def extract(cls, metadata: Optional[dict]) -> dict:
        """
        Read the `_mcap_` block out of a metadata dict, or `{}` if absent.

        Args:
            metadata (Optional[dict]): A metadata dict, typically `{"_mcap_": {...}}` or `None`.

        Returns:
            dict: The extracted `_mcap_` block, or an empty dict if not present.
        """
        return dict((metadata or {}).get(cls.KEY) or {})

    @classmethod
    def from_dict(cls, metadata: Optional[dict]) -> "McapSchemaMetadata":
        """
        Create a `McapSchemaMetadata` from a plain metadata dict.

        Args:
            metadata (Optional[dict]): A metadata dict, typically `{"_mcap_": {...}}` or `None`.

        Returns:
            McapSchemaMetadata: A new instance seeded with the extracted `_mcap_` fields
                (empty if `metadata` is `None` or carries no `_mcap_` block).
        """
        return cls(**cls.extract(metadata))

    def get_schema_data_bytes(self) -> Optional[bytes]:
        """
        Extract and decode the schema data from base64.

        Returns:
            Optional[bytes]: The decoded schema bytes, or None if `schema_data_b64` is not set.

        Raises:
            ValueError: If `schema_data_b64` is invalid base64.
        """
        schema_b64 = self.fields.get("schema_data_b64")
        if schema_b64 is None:
            return None
        try:
            return base64.b64decode(schema_b64)
        except Exception as e:
            raise ValueError(f"Invalid base64 in schema_data_b64: {e}")

    @classmethod
    def set_schema_data_bytes(cls, schema_bytes: bytes) -> str:
        """
        Encode schema bytes to base64 for storage.

        Args:
            schema_bytes: Raw schema data bytes.

        Returns:
            str: Base64-encoded schema string ready for storage in metadata.
        """
        return base64.b64encode(schema_bytes).decode("utf-8")

    def __repr__(self) -> str:
        return f"McapSchemaMetadata({self.fields})"

    def __str__(self) -> str:
        return f"McapSchemaMetadata({self.fields})"
