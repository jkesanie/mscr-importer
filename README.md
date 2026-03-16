# MSCR Importer

CLI for harvesting YAML data and ingesting to MSCR API.

## Features

- **Harvest** YAML documents from URLs or local files
- **Validate** against the `fair_mappings_schema.MappingSpecification` Pydantic schema
- **Transform** validated data to MSCR API's `CrosswalkInfoDTO` metadata format
- **Ingest** via the MSCR `/v2/crosswalkFull` API endpoint with JWT authentication

## Installation

### Using Poetry (Recommended)

```bash
# Install dependencies
poetry install

# Install with dev dependencies
poetry install --with dev
```

### Using pip

```bash
pip install -r requirements.txt
```

## Usage

### Environment Variables

Create a `.env` file:

```bash
MSCR_API_KEY=your_jwt_token_here
MSCR_API_URL=https://mscr-release.2.rahtiapp.fi/datamodel-api
MSCR_TIMEOUT=120
```

### Commands

#### Validate YAML

```bash
# Using Poetry
poetry run python mscr_importer.py validate <file_or_url>

# Using Make
make validate PATH_OR_URL=<file_or_url>

# Direct (if installed)
python mscr_importer.py validate <file_or_url>
```

#### Harvest from URL

```bash
# Dry-run (validate and transform only)
poetry run python mscr_importer.py harvest <url> --dry-run

# Live ingestion
poetry run python mscr_importer.py harvest <url> --key <jwt_token>

# With custom options
poetry run python mscr_importer.py harvest <url> \
  --key <jwt_token> \
  --action create \
  --visibility PUBLIC \
  --state DRAFT
```

#### Ingest Local File

```bash
# Basic ingest
poetry run python mscr_importer.py ingest <file.yaml> --key <jwt_token>

# With verbose output
poetry run python mscr_importer.py ingest <file.yaml> --key <jwt_token> --verbose
```

### Make Commands

```bash
make install          # Install dependencies with Poetry
make install-dev      # Install with dev dependencies
make run              # Run the CLI
make harvest          # Harvest from URL (set URL env var)
make ingest           # Ingest file (set FILE env var)
make validate         # Validate file/URL (set PATH_OR_URL env var)
make dev-format       # Format code with Black
make dev-lint         # Lint code with Ruff
make dev-test         # Run tests with pytest
make dev-test-cov     # Run tests with coverage
```

## Content URL Handling

- **HTTP URLs** (`http://`, `https://`): Sent as `contentURL` form field
- **File URLs** (`file://`): File uploaded directly via multipart form-data

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--key, -k` | JWT API token | `MSCR_API_KEY` env var |
| `--api, -a` | API base URL | `https://mscr-release.2.rahtiapp.fi/datamodel-api` |
| `--action` | Action type (create, update, etc.) | `create` |
| `--visibility` | Visibility (PUBLIC, PRIVATE) | `PUBLIC` |
| `--state` | State (DRAFT, PUBLISHED, etc.) | `DRAFT` |
| `--target` | Target identifier | None |
| `--dry-run` | Skip ingestion | `false` |
| `--verbose, -v` | Enable verbose output | `false` |
| `--timeout` | Request timeout in seconds | `120` |

## Testing

```bash
# Run test suite
./test_cli.sh

# Or using Poetry
poetry run pytest
```

## Development

```bash
# Install dev dependencies
poetry install --with dev

# Format code
make dev-format

# Lint code
make dev-lint

# Run tests
make dev-test
```

## License

MIT