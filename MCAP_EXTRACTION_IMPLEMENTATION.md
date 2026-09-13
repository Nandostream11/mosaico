# Issue #738: MCAP Extraction - Implementation Guide

## 🎯 Objective
Add `_mcap_` metadata to Mosaico topics and implement extraction of Mosaico sequences back to MCAP files with byte-exact schema round-tripping.

**Related**: RFC #717 - MCAP Bridge design document

## ✅ Completed Work

### 1. **McapSchemaMetadata Class** ✓
- **Location**: `src/mosaicolabs/bridges/protocols/mcap/schema_metadata.py`
- **Features**:
  - Mirrors `RosSchemaMetadata` pattern for consistency
  - Stores `encoding` (protobuf, jsonschema, ros2msg, etc.)
  - Stores `schema_name` (e.g., "sensor_msgs/msg/Imu")
  - Stores `schema_data_b64` (base64-encoded raw schema bytes for exact reconstruction)
  - Methods: `to_dict()`, `merge_into()`, `extract()`, `from_dict()`, `get_schema_data_bytes()`, `set_schema_data_bytes()`
  - Reserved metadata key: `_mcap_` (follows ROS Bridge pattern)

### 2. **McapSequenceExtractor Skeleton** ✓
- **Location**: `src/mosaicolabs/bridges/mcap/extractor.py`
- **Components**:
  - `McapExtractorConfig`: Configuration dataclass with all necessary parameters
    - `mcap_path`: Output file location
    - `sequence_name`: Source sequence on Mosaico server
    - `host`, `port`: Server connection details
    - `topics`: Topic filtering (glob patterns with ! exclusion support)
    - `timestamp ranges`: Time-window filtering
    - `overwrite`, `dry_run`: Execution modes
    - `log_level`: Logging configuration
  - `McapSequenceExtractor`: Main orchestrator class with `run()` method
  - `mcap_sequence_extractor()`: Console script entry point

### 3. **Module Exports** ✓
- Updated `src/mosaicolabs/bridges/protocols/mcap/__init__.py` to export `McapSchemaMetadata`
- Created `src/mosaicolabs/bridges/mcap/__init__.py` to export extractor classes

## 🔲 Remaining Work

### Phase 1: Schema Metadata Tracking During Loading

**Goal**: Store `_mcap_` metadata during MCAP file ingestion so extraction can reconstruct byte-exact schemas.

#### 1.1 MCAP Loader Integration
- [ ] Create/update MCAP loader to capture schema metadata
- [ ] Store schema information in topic metadata during ingestion:
  - `encoding`: The MCAP encoding (e.g., "protobuf", "jsonschema")
  - `schema_name`: The MCAP schema name
  - `schema_data_b64`: Raw schema bytes, base64-encoded
- [ ] Ensure metadata round-trips through Mosaico platform unchanged

**Files to create/modify**:
- `src/mosaicolabs/bridges/mcap/loader.py` - MCAP loader with metadata tracking
- `src/mosaicolabs/bridges/mcap/injector.py` - Optional: MCAP injection config (mirrors ROS)

**Implementation considerations**:
- Use `McapSchemaMetadata` class to build metadata consistently
- Call `schema_metadata.merge_into(user_topics_metadata)` before pushing messages
- Validate that `schema_data_b64` is correctly base64-encoded/decodable

#### 1.2 Tests for Metadata Storage
- [ ] Unit test: Verify `McapSchemaMetadata` correctly encodes/decodes schemas
- [ ] Integration test: MCAP ingestion → Mosaico → verify metadata preserved
- [ ] Codec: Test metadata round-trip for all encodings (protobuf, jsonschema, ros2msg, etc.)

---

### Phase 2: Extraction Implementation

**Goal**: Implement the core extraction logic to read from Mosaico and write MCAP files.

#### 2.1 Message Streaming from Mosaico
- [ ] Implement sequence/topic retrieval from Mosaico server
- [ ] Stream messages from each topic
- [ ] Apply topic and timestamp filtering

**In `McapSequenceExtractor.run()`**:
```python
# Pseudo-code
with MosaicoClient.connect(...) as client:
    seq_handler = client.sequence_handler(self.cfg.sequence_name)
    for topic_name in seq_handler.topics:
        topic_handler = client.topic_handler(self.cfg.sequence_name, topic_name)
        for message in topic_handler.messages():
            # 2.2: Convert and write message
```

#### 2.2 Adapter-Based Message Conversion
- [ ] Resolve adapter for each topic based on `_mcap_` metadata
  - Read `encoding` and `schema_name` from topic metadata
  - Look up registered adapter using `(encoding, schema_name)` key
  - Fall back to unmodeled adapter if no registered adapter exists
- [ ] Call adapter's `to_mcap()` method to convert Mosaico ontology → native MCAP type
- [ ] Handle encoding-specific conversion requirements

**Adapter pattern** (to be implemented on top of existing `BridgeAdapterBase`):
```python
class McapAdapterBase(BridgeAdapterBase[T, bytes]):
    encoding: ClassVar[str]  # "protobuf", "jsonschema", etc.
    schema_name: ClassVar[str]  # e.g., "sensor_msgs/msg/Imu"
    
    @classmethod
    def to_mcap(cls, mosaico_data, **kwargs) -> bytes:
        """Convert Mosaico ontology to native MCAP encoding."""
        ...
```

#### 2.3 MCAP File Writing
- [ ] Open MCAP writer
- [ ] Register schemas from `_mcap_` metadata (byte-exact reconstruction):
  - Decode `schema_data_b64` to get original bytes
  - Re-register schema with `mcap.writer.Writer.register_schema()`
  - Preserve exact encoding and schema_name
- [ ] Register channels for each topic
- [ ] Write messages with proper timestamps
- [ ] Handle encoding-specific writers (e.g., `mcap_protobuf.writer.Writer` for protobuf)

**Implementation considerations**:
- Different encodings require different writer classes:
  - `protobuf`: `from mcap_protobuf.writer import Writer`
  - `jsonschema`, `ros2msg`, etc.: `from mcap.writer import Writer`
- Schema bytes must be byte-identical for downstream MCAP consumers (Foxglove, etc.)
- Use `McapSchemaMetadata.get_schema_data_bytes()` to retrieve and decode stored schema

#### 2.4 Encoding-Specific Extraction Logic
- [ ] **Protobuf**: Reconstruct `.proto` message from stored schema, use `mcap_protobuf.writer.Writer`
- [ ] **JSONSchema**: Use stored schema JSON, use standard `mcap.writer.Writer`
- [ ] **ROS 2 Message (ros2msg)**: Leverage existing ROS Bridge adapter infrastructure
- [ ] **ROS 1 Message (ros1msg)**: Similar to ros2msg, coordinate with ROS Bridge
- [ ] **ROS 2 IDL (ros2idl)**: Similar to ros2msg, coordinate with ROS Bridge

**Reference behavior from RFC #717**:
- Protobuf extraction requires: `.proto` file from `schema_data` (FileDescriptorSet)
- JSONSchema extraction requires: schema JSON from `schema_data`
- ROS msg extraction requires: `msgdef` from `_ros_` metadata (coordinate with ROS Bridge)

---

### Phase 3: Testing & Validation

#### 3.1 Unit Tests
- [ ] Test `McapSchemaMetadata` encoding/decoding for each schema encoding
- [ ] Test adapter resolution with mock topic metadata
- [ ] Test message conversion (Mosaico → native type) for each encoding

#### 3.2 Integration Tests
- [ ] Create test MCAP file with mixed encodings (protobuf + jsonschema)
- [ ] Ingest into Mosaico, verify metadata stored in `_mcap_` namespace
- [ ] Extract back to MCAP file
- [ ] Verify extracted MCAP is byte-identical or semantically equivalent to original
  - Schema names match
  - Encodings match
  - Message payloads are correct
  - Timestamps preserved

#### 3.3 Round-Trip Tests
- [ ] MCAP (protobuf encoding) → Mosaico → MCAP (protobuf)
- [ ] MCAP (jsonschema encoding) → Mosaico → MCAP (jsonschema)
- [ ] MCAP (mixed encodings) → Mosaico → MCAP (mixed)

---

### Phase 4: Console Entry Point & Documentation

#### 4.1 Console Script Setup
- [ ] Add entry point to `pyproject.toml`:
  ```toml
  [project.scripts]
  mosaicolabs.mcap_extractor = "mosaicolabs.bridges.mcap.extractor:mcap_sequence_extractor"
  ```
- [ ] Test CLI invocation:
  ```bash
  mosaicolabs.mcap_extractor output.mcap --name "my_sequence" --host localhost --port 6726
  ```

#### 4.2 User Documentation
- [ ] Update SDK docs with MCAP extraction example
- [ ] Document `_mcap_` metadata namespace
- [ ] Document usage of `McapSequenceExtractor` as library API
- [ ] Document CLI options and examples

---

## 📋 Implementation Checklist

### Must-Have (Minimum Viable)
- [x] `McapSchemaMetadata` class
- [ ] MCAP metadata storage during ingestion
- [ ] Adapter-based message conversion
- [ ] Basic MCAP file writing
- [ ] Console entry point
- [ ] Basic round-trip testing

### Nice-to-Have (Next Iteration)
- [ ] Support for all encodings (currently: protobuf, jsonschema sufficient)
- [ ] Dry-run reporting
- [ ] Topic filtering validation
- [ ] Comprehensive error handling
- [ ] Performance optimization

---

## 🔗 Related Components

### Dependency Chain
```
McapSchemaMetadata (DONE)
    ↓
MCAP Loader (TODO: 2.1)
    ↓
Topic Metadata Storage (TODO: 1.1)
    ↓
McapSequenceExtractor + Adapters (TODO: 2.2, 2.3, 2.4)
    ↓
Console Entry Point (TODO: 4.1)
    ↓
Tests (TODO: 3.x)
```

### Referencing Existing Code
- **ROS Extractor**: `src/mosaicolabs/bridges/ros/sequence_extractor.py` (2
62-line pattern to follow)
- **ROS Adapter Pattern**: `src/mosaicolabs/bridges/ros/adapter_base.py`
- **ROS Schema Metadata**: `src/mosaicolabs/bridges/ros/adapter_base.py#RosSchemaMetadata`
- **MCAP Test Files**: `src/testing/conftest.py` (fixtures for MCAP files)
- **MCAP Converters**: `src/mosaicolabs/bridges/protocols/mcap/converters/` (existing schema conversion code)

---

## 💡 Key Design Decisions

1. **Metadata Storage Pattern**: Follow `RosSchemaMetadata` for consistency
   - Reserved key: `_mcap_`
   - Fields: `encoding`, `schema_name`, `schema_data_b64`
   - Byte-exact schema preservation via base64 encoding

2. **Adapter Architecture**: Extend `BridgeAdapterBase` (from RFC #717)
   - Tuples `(encoding, schema_name)` as adapter keys (not strings)
   - Encoding-specific adapter implementations
   - Lazy adapter resolution per topic

3. **Error Handling**: Silent skip with warning (mirrors ROS Bridge behavior)
   - Skip topics with no adapter
   - Log warnings but continue extraction
   - Dry-run mode for validation

4. **Encoding Handling**: Accept current iteration (2-3 encodings), design for extensibility
   - Different writers per encoding (protobuf needs special writer)
   - Schema reconstruction from metadata

---

## 🚀 Getting Started

To work on any remaining items:

1. **Phase 1 (Metadata Storage)**:
   ```python
   # In MCAP loader:
   meta = McapSchemaMetadata(
       encoding=schema.encoding,
       schema_name=schema.name,
       schema_data_b64=McapSchemaMetadata.set_schema_data_bytes(schema.data)
   )
   topic_metadata = meta.merge_into(user_metadata)
   ```

2. **Phase 2 (Extraction)**:
   ```python
   # In McapSequenceExtractor.run():
   class BasicMcapWriter:
       def write_schema_and_message(self, mcap_meta, message_bytes):
           # Reconstruct schema from _mcap_ metadata
           # Write to MCAP file with correct encoding/schema_name
           pass
   ```

3. **Testing**:
   Create integration test in `src/testing/integration/bridges/mcap/test_extractor.py`

---

## 📚 References

- RFC #717: https://github.com/mosaico-labs/mosaico/discussions/717
- Issue #738: https://github.com/mosaico-labs/mosaico/issues/738
- MCAP Spec: https://mcap.dev/
- McapPython Lib Docs: https://github.com/foxglove/mcap
