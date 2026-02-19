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
from codeocean.capsule import CapsuleSearchParams


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
    
    results = {
        "user_ids": user_ids,
        "capsules": []
    }
    
    print(f"Searching for resources owned by {len(user_ids)} user(s)...", file=sys.stderr)
    
    # Search all capsules using SDK method
    print("Searching capsules...", file=sys.stderr)
    offset = 0
    limit = 100
    
    while True:
        try:
            # Use SDK search_capsules method with proper parameter object
            capsule_search_params = CapsuleSearchParams(
                limit=limit,
                offset=offset
            )
            response = client.capsules.search_capsules(capsule_search_params)
            
            # SDK returns CapsuleSearchResults object
            items = response.results if hasattr(response, 'results') else []
            print(f"Fetched {len(items)} capsules at offset {offset}", file=sys.stderr)
            
            if not items:
                break
                
            for capsule in items:
                # SDK returns Capsule objects - convert to dict or access attributes
                capsule_dict = capsule.to_dict() if hasattr(capsule, 'to_dict') else capsule
                
                # Check if owner is in the target user list
                owner_id = capsule_dict.get("owner") or capsule_dict.get("owner_id")
                if owner_id in user_ids:
                    created_timestamp = capsule_dict.get("created")
                    # Get tags as comma-separated string for CSV compatibility
                    tags = capsule_dict.get("tags", [])
                    tags_str = ", ".join(tags) if tags else ""
                    
                    # Generate capsule URL with full domain
                    slug = capsule_dict.get("slug")
                    capsule_url = f"{base_url_clean}/capsule/{slug}" if slug else ""
                    
                    # Get owner email from search response (may be None on some deployments)
                    owner_email = capsule_dict.get("owner_email")
                    
                    # Build capsule record
                    capsule_record = {
                        "id": capsule_dict.get("id"),
                        "name": capsule_dict.get("name"),
                        "slug": slug,
                        "url": capsule_url,
                        "owner_id": owner_id,
                        "status": capsule_dict.get("status"),
                        "description": capsule_dict.get("description"),
                        "tags": tags_str,
                        "created": created_timestamp,
                        "created_date": format_timestamp(created_timestamp),
                        "type": "capsule"
                    }
                    
                    # Only include email if it's available
                    if owner_email:
                        capsule_record["owner_email"] = owner_email
                    
                    results["capsules"].append(capsule_record)
                    print(f"  Found capsule: {capsule_dict.get('name')} (owner: {owner_id})", file=sys.stderr)
            
            # Check if there are more results
            has_more = response.has_more if hasattr(response, 'has_more') else False
            if not has_more:
                break
            offset += limit
            
        except Exception as e:
            print(f"Error searching capsules: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            break
    
    print(f"\nFound {len(results['capsules'])} capsule(s)", file=sys.stderr)
    
    return results


def save_results(results: Dict, output_format: str, output_dir: Path) -> None:
    """Save results to output files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if output_format == "json":
        # Save as JSON
        output_file = output_dir / "user_capsules.json"
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
