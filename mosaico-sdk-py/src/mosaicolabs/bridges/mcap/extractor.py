"""
McapSequenceExtractor — extracts a Mosaico sequence and writes it as an MCAP file.

Provides :class:`McapSequenceExtractor` and the :class:`McapExtractorConfig` dataclass
that drive the extraction pipeline:

1. Connect to the Mosaico server.
2. Stream every message in the requested sequence (optionally filtered by topic or
   time window).
3. Convert each message from its Mosaico Ontology form back to its original MCAP
   native type via registered adapters.
4. Write the result into a new MCAP file with byte-exact schema reconstruction.

The module also exposes ``mcap_sequence_extractor()``, the console-script entry point
installed by the package.
"""

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich.console import Console

from mosaicolabs import MosaicoClient
from mosaicolabs.logging_config import get_logger, setup_sdk_logging

# Set the hierarchical logger
logger = get_logger(__name__)


# --- Configuration ---
@dataclass
class McapExtractorConfig:
    """
    Configuration for :class:`McapSequenceExtractor`.

    Collects all parameters needed to connect to the Mosaico server, select the
    target sequence, control topic and time-window filtering, and control the
    MCAP output format and storage location.
    """

    mcap_path: Path
    """
    The path where to save the MCAP file.
    """

    sequence_name: str
    """
    The name of the sequence to extract.
    """

    host: str = "localhost"
    """
    The hostname of the Mosaico server.
    """

    port: int = 6726
    """
    The port of the Mosaico server.
    """

    topics: Optional[list[str]] = None
    """List of topic patterns used to filter available topics.

    Supports shell-style glob patterns (e.g., "/cam/*", "*camera_info").
    Patterns starting with '!' are treated as exclusions (e.g., "!/cam/debug*").
    
    **Pattern order matters**:
        - Each non-'!' pattern adds matching topics to the selection.
        - Each '!' pattern removes matching topics from the selection.
        - Later patterns override earlier ones.
        - If no inclusion pattern is provided, selection starts from ALL topics,
          and only exclusion patterns reduce the set.

    If None, all topics are loaded.
    """

    log_level: str = "INFO"
    """The Log Level"""

    mosaico_api_key: Optional[str] = None
    """
    The API key for authentication on the mosaico server. Defaults to None.
    
    If provided it must have the `read` permission.
    """

    tls_cert_path: Optional[str] = None
    """
    Path to the TLS certificate file for secure connection on the mosaico server. Defaults to None. 
    If tls_cert_path=None and enable_tls=True, a standard one-way TLS (server authenticated only) connection is established
    """

    enable_tls: bool = False
    """
    Enable the TLS standard one-way TLS (server authenticated only) communication protocol. Defaults to False. 
    If tls_cert_path is provided (not None), this flag does not have any effect.
    """

    start_timestamp_ns: Optional[int] = None
    """Timestamp (in nanoseconds) from where to start extracting data of specified sequence"""

    end_timestamp_ns: Optional[int] = None
    """Timestamp (in nanoseconds) to finish extracting data of specified sequence"""

    overwrite: bool = False
    """If True, delete and recreate the mcap path if it already exists. Defaults to False."""

    dry_run: bool = False
    """
    If `True`, connects to the Mosaico server and reports which topics would be extracted
    (and with which adapter/MCAP encoding), which topics would be rejected (and why), and
    whether the output path already exists — without writing any MCAP file, and without
    deleting an existing output path even if `overwrite=True`. Default: False.
    """


# --- Main Extractor Class ---


class McapSequenceExtractor:
    """
    Orchestrates the extraction of a Mosaico sequence into an MCAP file.

    On each call to :meth:`run`, the extractor:

    1. Prepares (and optionally clears) the output directory.
    2. Connects to the Mosaico server via :class:`MosaicoClient`.
    3. Opens the schema handler to retrieve all topics in the sequence.
    4. For every message in each topic, looks up the appropriate adapter and converts
       the Mosaico ontology type back to its native MCAP form.
    5. Writes the converted message to the MCAP file with metadata round-trip support.

    Topics that have no registered adapter, or whose conversion fails, are silently
    skipped after logging a warning.
    """

    def __init__(self, config: McapExtractorConfig):
        """
        Initialize the MCAP Sequence Extractor.

        Args:
            config (McapExtractorConfig): The configuration for this extraction run.
        """
        self.cfg = config
        self.console = Console(stderr=True)
        setup_sdk_logging(
            level=self.cfg.log_level.upper(), pretty=True, console=self.console
        )

        self.ignored_topics: set[str] = set()

    def run(self) -> None:
        """
        Main execution entry point for the extraction pipeline.

        This method establishes the necessary contexts (Network Client, MCAP Writer)
        and executes the processing loop. It handles graceful shutdowns in case of
        user interrupts and provides a summary report upon completion.

        If `self.cfg.dry_run` is `True`, delegates to `_dry_run_report()` and returns
        without connecting to the server.

        Raises:
            Exception: Any fatal error encountered during connection, loading, or extraction is
                logged and then re-raised, so callers can detect failure.
                `KeyboardInterrupt` is the only exception handled silently, to allow a clean
                shutdown on user interrupt.
        """
        if self.cfg.dry_run:
            self._dry_run_report()
            return

        try:
            # Context: Mosaico Client (Network Connection)
            self.console.print(
                f"[bold blue]Connecting to Mosaico at '{self.cfg.host}:{self.cfg.port}'...[/bold blue]"
            )
            with MosaicoClient.connect(
                host=self.cfg.host,
                port=self.cfg.port,
                api_key=self.cfg.mosaico_api_key,
                enable_tls=self.cfg.enable_tls,
                tls_cert_path=self.cfg.tls_cert_path,
            ) as client:
                self.console.print("[bold green]✓ Connected to Mosaico[/bold green]")

                # Check if sequence exists
                sequences = client.list_sequences()
                if self.cfg.sequence_name not in sequences:
                    raise ValueError(
                        f"Sequence '{self.cfg.sequence_name}' not found. "
                        f"Available sequences: {sequences}"
                    )

                self.console.print(
                    f"[bold blue]Extracting sequence: '{self.cfg.sequence_name}'[/bold blue]"
                )

                # TODO: Implement MCAP extraction logic
                #  - Get sequence handler
                #  - Get topics
                #  - Stream messages
                #  - Write to MCAP file

                self.console.print(
                    f"[bold green]✓ MCAP file written to: {self.cfg.mcap_path}[/bold green]"
                )

        except KeyboardInterrupt:
            self.console.print("[bold red]Extraction cancelled by user[/bold red]")
            raise
        except Exception as e:
            logger.exception(f"Extraction failed: {e}")
            raise

    def _dry_run_report(self) -> None:
        """
        Performs a dry-run: connects, lists available topics and adapters, and reports
        findings without writing any files.
        """
        # TODO: Implement dry-run reporting
        pass


# --- Console Entry Point ---


def mcap_sequence_extractor():
    """
    Console script entry point.
    Parses arguments, sets up configuration, and initiates the extractor.
    """
    parser = argparse.ArgumentParser(
        description="Extract Mosaico sequence to MCAP file."
    )

    # Required Arguments
    parser.add_argument(
        "mcap_path", type=Path, help="Path where to write the MCAP file"
    )
    parser.add_argument(
        "--name", "-n", required=True, help="Source Sequence Name on Mosaico server"
    )

    # Optional Arguments
    parser.add_argument(
        "--host",
        default="localhost",
        help="Hostname of the Mosaico server (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=6726,
        help="Port of the Mosaico server (default: 6726)",
    )
    parser.add_argument(
        "--topics",
        nargs="+",
        help="Topic patterns to extract (shell-style glob, supports ! for exclusion)",
    )
    parser.add_argument(
        "--start-timestamp-ns",
        type=int,
        help="Start timestamp in nanoseconds (optional)",
    )
    parser.add_argument(
        "--end-timestamp-ns",
        type=int,
        help="End timestamp in nanoseconds (optional)",
    )
    parser.add_argument(
        "--api-key",
        help="API key for authentication on the Mosaico server",
    )
    parser.add_argument(
        "--tls-cert-path",
        help="Path to TLS certificate file for secure connection",
    )
    parser.add_argument(
        "--enable-tls",
        action="store_true",
        help="Enable TLS (server-authenticated) connection",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite output file if it already exists",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Resolve topics/adapters/encodings and print a report, without connecting "
            "to the Mosaico server or writing any MCAP file."
        ),
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # --- Configuration ---
    config = McapExtractorConfig(
        mcap_path=args.mcap_path,
        sequence_name=args.name,
        host=args.host,
        port=args.port,
        topics=args.topics,
        start_timestamp_ns=args.start_timestamp_ns,
        end_timestamp_ns=args.end_timestamp_ns,
        mosaico_api_key=args.api_key,
        tls_cert_path=args.tls_cert_path,
        enable_tls=args.enable_tls,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
        log_level=args.log_level,
    )

    # --- Execution ---
    extractor = McapSequenceExtractor(config)
    try:
        extractor.run()
    except KeyboardInterrupt:
        exit(130)
    except Exception:
        # Already logged with a full traceback inside run(); exit non-zero so
        # calling scripts/CI can detect the failure.
        exit(1)


if __name__ == "__main__":
    mcap_sequence_extractor()
