# Admin Tool - User Resource Finder

This capsule enables admins to find all capsules and data assets owned by specific users using the Code Ocean API.

## Features

- Search all capsules by user ownership
- Search all data assets by user ownership
- Export results in JSON or CSV format
- Admin tool for resource discovery and auditing

## Usage

### Parameters

- **user-ids** (required): Comma-separated list of user IDs to search for
- **output-format** (optional): Output format - `json` or `csv` (default: json)
- **api-token** (optional): Code Ocean API token (can be set via environment variable)
- **base-url** (optional): Code Ocean base URL (can be set via environment variable)

### Example

```bash
python find_user_resources.py \
  --user-ids "user-id-1,user-id-2" \
  --output-format csv \
  --api-token YOUR_API_TOKEN
```

### Environment Variables

The tool automatically detects API credentials from environment variables (secrets):

**API Token** (checked in order):
- `CUSTOM_KEY` (capsule-specific, recommended)
- `CODE_OCEAN_API_TOKEN`
- `API_TOKEN`
- `CO_API_TOKEN`
- `CODEOCEAN_API_TOKEN`

**Base URL:**
- `CODE_OCEAN_URL` (optional, auto-detected if not set)

**Note:** If `CUSTOM_KEY` is already set in your capsule environment, no additional configuration is needed. The script will automatically use it for authentication.

## Output

The tool generates:
- **JSON format**: Single `user_resources.json` file with all results
- **CSV format**: Two files - `user_capsules.csv` and `user_data_assets.csv`

All output files are saved to `/results/`.

## Requirements

- Python 3.11+
- codeocean SDK package
- Valid API token with admin privileges
