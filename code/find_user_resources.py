#!/usr/bin/env python3
"""Find capsules and data assets owned by specific users."""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from codeocean import CodeOcean


def format_timestamp(timestamp: int) -> str:
    """Convert Unix timestamp to human-readable format."""
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError, OSError):
        return str(timestamp)





def find_user_resources(
    api_token: str,
    base_url: Optional[str],
    user_ids: List[str],
    output_format: str = "json"
) -> Dict:
    """
    Find all capsules and data assets owned by specified users.
    
    Args:
        api_token: Code Ocean API token
        base_url: Code Ocean base URL (required)
        user_ids: List of user IDs to search for
        output_format: Output format (json or csv)
    
    Returns:
        Dict with capsules and data_assets lists
    """
    client = CodeOcean(domain=base_url, token=api_token)
    
    # Ensure base_url doesn't have trailing slash for URL construction
    base_url_clean = base_url.rstrip("/") if base_url else ""
    
    # Helper function to search using SDK session
    def search_resource(endpoint: str, limit: int, offset: int) -> Dict:
        """Generic search helper using SDK's session."""
        response = client.session.post(
            f"{base_url_clean}/api/v1/{endpoint}/search",
            json={"limit": limit, "offset": offset}
        )
        response.raise_for_status()
        return response.json()
    
    results = {
        "user_ids": user_ids,
        "capsules": [],
        "data_assets": []
    }
    
    print(f"Searching for resources owned by {len(user_ids)} user(s)...", file=sys.stderr)
    
    # Search all capsules
    print("Searching capsules...", file=sys.stderr)
    offset = 0
    limit = 100
    
    while True:
        try:
            # Use SDK's session for search endpoint
            data = search_resource("capsules", limit, offset)
            
            items = data.get("results", [])
            print(f"Fetched {len(items)} capsules at offset {offset}", file=sys.stderr)
            
            if not items:
                break
                
            for capsule in items:
                # Check if owner is in the target user list
                # The search API returns 'owner' field, not 'owner_id'
                owner_id = capsule.get("owner") or capsule.get("owner_id")
                if owner_id in user_ids:
                    created_timestamp = capsule.get("created")
                    # Get tags as comma-separated string for CSV compatibility
                    tags = capsule.get("tags", [])
                    tags_str = ", ".join(tags) if tags else ""
                    
                    # Generate capsule URL with full domain
                    slug = capsule.get("slug")
                    capsule_url = f"{base_url_clean}/capsule/{slug}" if slug else ""
                    
                    # Get owner email from search response (may be None on some deployments)
                    owner_email = capsule.get("owner_email")
                    
                    # Build capsule record
                    capsule_record = {
                        "id": capsule.get("id"),
                        "name": capsule.get("name"),
                        "slug": slug,
                        "url": capsule_url,
                        "owner_id": owner_id,
                        "status": capsule.get("status"),
                        "description": capsule.get("description"),
                        "tags": tags_str,
                        "created": created_timestamp,
                        "created_date": format_timestamp(created_timestamp),
                        "type": "capsule"
                    }
                    
                    # Only include email if it's available
                    if owner_email:
                        capsule_record["owner_email"] = owner_email
                    
                    results["capsules"].append(capsule_record)
                    print(f"  Found capsule: {capsule.get('name')} (owner: {owner_id})", file=sys.stderr)
            
            # Check if there are more results
            if not data.get("has_more", False):
                break
            offset += limit
            
        except Exception as e:
            print(f"Error searching capsules: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            break
    
    # Search all data assets
    print("Searching data assets...", file=sys.stderr)
    offset = 0
    
    while True:
        try:
            # Use SDK's session for search endpoint
            data = search_resource("data_assets", limit, offset)
            
            items = data.get("results", [])
            print(f"Fetched {len(items)} data assets at offset {offset}", file=sys.stderr)
            
            # Debug: Show sample owner IDs from first batch
            if offset == 0 and items:
                sample_owners = [item.get("owner") or item.get("owner_id") for item in items[:3]]
                print(f"  Sample owner IDs from data assets: {sample_owners}", file=sys.stderr)
                print(f"  Looking for user IDs: {user_ids}", file=sys.stderr)
            
            if not items:
                break
                
            for asset in items:
                # Check if owner is in the target user list
                # The search API returns 'owner' field, not 'owner_id'
                owner_id = asset.get("owner") or asset.get("owner_id")
                if owner_id in user_ids:
                    created_timestamp = asset.get("created")
                    
                    # Generate data asset URL with full domain
                    asset_id = asset.get("id")
                    asset_url = f"{base_url_clean}/data-assets/{asset_id}" if asset_id else ""
                    
                    # Get owner email from search response (may be None on some deployments)
                    owner_email = asset.get("owner_email")
                    
                    # Build data asset record
                    asset_record = {
                        "id": asset_id,
                        "name": asset.get("name"),
                        "url": asset_url,
                        "owner_id": owner_id,
                        "created": created_timestamp,
                        "created_date": format_timestamp(created_timestamp),
                        "type": asset.get("type"),
                        "size": asset.get("size")
                    }
                    
                    # Only include email if it's available
                    if owner_email:
                        asset_record["owner_email"] = owner_email
                    
                    results["data_assets"].append(asset_record)
                    print(f"  Found data asset: {asset.get('name')} (owner: {owner_id})", file=sys.stderr)
            
            # Check if there are more results
            if not data.get("has_more", False):
                break
            offset += limit
            
        except Exception as e:
            print(f"Error searching data assets: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            break
    
    print(f"\nFound {len(results['capsules'])} capsule(s) and "
          f"{len(results['data_assets'])} data asset(s)", file=sys.stderr)
    
    return results


def save_results(results: Dict, output_format: str, output_dir: Path) -> None:
    """Save results to output files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if output_format == "json":
        # Save as JSON
        output_file = output_dir / "user_resources.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {output_file}")
    
    elif output_format == "csv":
        # Save capsules CSV
        if results["capsules"]:
            capsules_file = output_dir / "user_capsules.csv"
            
            # Determine fields dynamically - check if any capsule has email
            has_email = any("owner_email" in c for c in results["capsules"])
            base_fields = ["id", "name", "slug", "url", "owner_id"]
            if has_email:
                base_fields.append("owner_email")
            base_fields.extend(["status", "description", "tags", "created", "created_date", "type"])
            
            with open(capsules_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=base_fields)
                writer.writeheader()
                writer.writerows(results["capsules"])
            print(f"Capsules saved to {capsules_file}")
        
        # Save data assets CSV
        if results["data_assets"]:
            assets_file = output_dir / "user_data_assets.csv"
            
            # Determine fields dynamically - check if any asset has email
            has_email = any("owner_email" in a for a in results["data_assets"])
            base_fields = ["id", "name", "url", "owner_id"]
            if has_email:
                base_fields.append("owner_email")
            base_fields.extend(["created", "created_date", "type", "size"])
            
            with open(assets_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=base_fields)
                writer.writeheader()
                writer.writerows(results["data_assets"])
            print(f"Data assets saved to {assets_file}")


def get_api_token() -> Optional[str]:
    """
    Get API token from environment variables.
    Checks multiple common variable names for flexibility.
    """
    # Check common environment variable names in order of preference
    token_var_names = [
        "CUSTOM_KEY",  # Capsule-specific secret
        "CODE_OCEAN_API_TOKEN",
        "API_TOKEN",
        "CO_API_TOKEN",
        "CODEOCEAN_API_TOKEN"
    ]
    
    for var_name in token_var_names:
        token = os.environ.get(var_name)
        if token:
            print(f"Using API token from environment variable: {var_name}", 
                  file=sys.stderr)
            return token
    
    return None


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Find all capsules and data assets owned by specific users"
    )
    parser.add_argument(
        "--user-ids",
        required=True,
        help="Comma-separated list of user IDs to search for"
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "csv"],
        default="json",
        help="Output format (default: json)"
    )
    parser.add_argument(
        "--api-token",
        default=None,
        help="Code Ocean API token (or set CODE_OCEAN_API_TOKEN/API_TOKEN env var)"
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Code Ocean base URL (or set CODE_OCEAN_URL env var)"
    )
    
    args = parser.parse_args()
    
    # Get API token from CLI arg or environment variable
    api_token = args.api_token or get_api_token()
    
    if not api_token:
        print("Error: API token required", file=sys.stderr)
        print("Provide via --api-token flag or set one of these environment variables:", 
              file=sys.stderr)
        print("  CODE_OCEAN_API_TOKEN, API_TOKEN, CO_API_TOKEN, or CODEOCEAN_API_TOKEN", 
              file=sys.stderr)
        sys.exit(1)
    
    # Get base URL from CLI arg or environment variable
    base_url = args.base_url or os.environ.get("CODE_OCEAN_URL")
    
    # If base_url is still None, try to get from CO_API_DOMAIN or other common names
    if not base_url:
        base_url = os.environ.get("CO_API_DOMAIN") or os.environ.get("CODE_OCEAN_DOMAIN")
    
    # If still not found, use default domain (you may need to customize this)
    if not base_url:
        # Default to the edge domain - adjust if your instance has a different domain
        base_url = "https://acmecorp-edge.codeocean.com"
        print(f"No domain specified, using default: {base_url}", file=sys.stderr)
    else:
        print(f"Using Code Ocean domain: {base_url}", file=sys.stderr)
    
    # Parse user IDs
    user_ids = [uid.strip() for uid in args.user_ids.split(",")]
    
    # Find resources
    results = find_user_resources(
        api_token=api_token,
        base_url=base_url,
        user_ids=user_ids,
        output_format=args.output_format
    )
    
    # Save results
    output_dir = Path("/results")
    save_results(results, args.output_format, output_dir)


if __name__ == "__main__":
    main()
