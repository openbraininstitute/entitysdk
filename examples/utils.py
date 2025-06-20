"""Helpers."""

from pathlib import Path


def create_mock_circuit_dir(output_dir: Path):
    """Create a mock hierarchy that looks like a circuit."""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    (output_dir / "circuit_config.json").touch()
    (output_dir / "sonata").mkdir()
    (output_dir / "sonata" / "nodes.h5").touch()
    (output_dir / "sonata" / "edges.h5").touch()
