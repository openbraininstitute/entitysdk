# entitysdk

entitysdk is a Python library for interacting with the [entitycore service][entitycore], providing a type-safe and intuitive interface for managing scientific entities, and their associated assets.

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

### Authentication
- Valid Keycloak access token
- Project context with:
  - Valid project ID (UUID)
  - Valid virtual lab ID (UUID)

Example configuration:
```python
from uuid import UUID
from entitysdk.common import ProjectContext

project_context = ProjectContext(
    project_id=UUID("12345678-1234-1234-1234-123456789012"),
    virtual_lab_id=UUID("87654321-4321-4321-4321-210987654321")
)
```

## Development

### Requirements
- tox/tox-uv

### Clone and run tests

```bash
# Clone the repository
git clone https://github.com/your-org/entitysdk.git

# Run linting, tests, and check-packaging
tox
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

Copyright (c) 2025 Open Brain Institute

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


[entitycore]: https://github.com/openbraininstitute/entitycore
