# entitysdk

entitysdk is a Python library for interacting with the entitycore service, providing a type-safe and intuitive interface for managing scientific entities, and their associated assets.

## Requirements

- Python3.11 or higher
- Network access to entitycore service endpoints

## Installation

```bash
pip install entitysdk
```

## Quick Start

```python
from uuid import UUID
from entitysdk.client import Client
from entitysdk.common import ProjectContext
from entitysdk.models.morphology import ReconstructionMorphology

# Initialize client
client = Client(
    api_url="http://api.example.com",
    project_context=ProjectContext(
        project_id=UUID("your-project-id"),
        virtual_lab_id=UUID("your-lab-id")
    )
)

# Search for morphologies
iterator = client.search(
    entity_type=ReconstructionMorphology,
    query={"mtype__pref_label": "L5_TPC:A"},
    token=token,
    limit=1,
)
morphology = next(iterator)

# Upload an asset
client.upload_file(
    entity_id=morphology.id,
    entity_type=ReconstructionMorphology,
    file_path="path/to/file.swc",
    file_content_type="application/swc",
    token="your-token"
)
```

## Development

### Requirements
- tox/tox-uv

### Clone and run tests

```bash
# Clone the repository
git clone https://github.com/your-org/entitysdk.git

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run type checks
mypy src/entitysdk
```

```bash
tox
```

## Development



Copyright (c) 2025 Open Brain Institute
