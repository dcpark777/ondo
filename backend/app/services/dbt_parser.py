"""
Parser for dbt manifest.json and catalog.json files.

Extracts models, columns, and metadata from dbt artifacts.
"""

from typing import Any, Dict, List, Optional


class DbtParseError(Exception):
    """Error parsing dbt files."""

    pass


def parse_manifest(manifest_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse dbt manifest.json to extract models.

    Args:
        manifest_data: Parsed JSON from manifest.json

    Returns:
        Dict mapping model unique_id to model metadata

    Raises:
        DbtParseError: If manifest is invalid
    """
    if not isinstance(manifest_data, dict):
        raise DbtParseError("Manifest must be a JSON object")

    if "nodes" not in manifest_data:
        raise DbtParseError("Manifest missing 'nodes' key")

    models = {}
    nodes = manifest_data.get("nodes", {})

    for unique_id, node in nodes.items():
        # Only process model nodes
        if node.get("resource_type") != "model":
            continue

        # Extract model metadata
        model_info = {
            "unique_id": unique_id,
            "name": node.get("name", ""),
            "schema": node.get("schema", ""),
            "database": node.get("database", ""),
            "alias": node.get("alias"),
            "description": node.get("description"),
            "meta": node.get("meta", {}),
            "columns": node.get("columns", {}),  # Column definitions from manifest
            "config": node.get("config", {}),
            "tags": node.get("tags", []),
            "tests": _extract_tests(node),
        }

        # Build full_name: database.schema.name or schema.name
        if model_info["database"]:
            full_name = f"{model_info['database']}.{model_info['schema']}.{model_info['name']}"
        else:
            full_name = f"{model_info['schema']}.{model_info['name']}"

        model_info["full_name"] = full_name
        models[unique_id] = model_info

    return models


def parse_catalog(catalog_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Parse dbt catalog.json to extract column information.

    Args:
        catalog_data: Parsed JSON from catalog.json

    Returns:
        Dict mapping model unique_id to column metadata

    Raises:
        DbtParseError: If catalog is invalid
    """
    if not isinstance(catalog_data, dict):
        raise DbtParseError("Catalog must be a JSON object")

    if "nodes" not in catalog_data:
        raise DbtParseError("Catalog missing 'nodes' key")

    model_columns = {}
    nodes = catalog_data.get("nodes", {})

    for unique_id, node in nodes.items():
        # Only process model nodes
        if node.get("metadata", {}).get("type") != "table":
            continue

        columns = {}
        column_data = node.get("columns", {})

        for col_name, col_info in column_data.items():
            columns[col_name] = {
                "name": col_name,
                "type": col_info.get("type", ""),
                "description": col_info.get("comment") or col_info.get("description"),
                "nullable": _parse_nullable(col_info.get("type", "")),
            }

        if columns:
            model_columns[unique_id] = columns

    return model_columns


def _extract_tests(node: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract test information from model node.

    Args:
        node: Model node from manifest

    Returns:
        Dict with test counts and types
    """
    # Count tests that reference this model
    # In manifest, tests are in "sources" or we can count test nodes
    # For MVP, we'll look for test configurations in meta or config
    test_count = 0
    has_freshness = False
    has_volume = False

    # Check meta for test indicators
    meta = node.get("meta", {})
    if "tests" in meta:
        test_count = len(meta.get("tests", []))
    if "freshness_check" in meta:
        has_freshness = meta.get("freshness_check", False)
    if "volume_check" in meta:
        has_volume = meta.get("volume_check", False)

    # Check config for test-related settings
    config = node.get("config", {})
    if "tests" in config:
        test_list = config.get("tests", [])
        test_count = len(test_list)
        has_freshness = any("freshness" in str(t).lower() for t in test_list)
        has_volume = any("volume" in str(t).lower() or "row_count" in str(t).lower() for t in test_list)

    return {
        "count": test_count,
        "has_freshness": has_freshness,
        "has_volume": has_volume,
    }


def _parse_nullable(type_str: str) -> Optional[bool]:
    """
    Parse nullable from type string.

    Args:
        type_str: Column type string (e.g., "VARCHAR(255)", "INTEGER NOT NULL")

    Returns:
        True if nullable, False if not null, None if unknown
    """
    if not type_str:
        return None

    type_upper = type_str.upper()
    if "NOT NULL" in type_upper:
        return False
    if "NULL" in type_upper and "NOT NULL" not in type_upper:
        return True

    # Default: assume nullable unless explicitly marked
    return None


def merge_model_data(
    manifest_models: Dict[str, Any],
    catalog_columns: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Merge manifest and catalog data into dataset metadata.

    Args:
        manifest_models: Models from manifest.json
        catalog_columns: Columns from catalog.json

    Returns:
        List of dataset metadata dicts ready for ingestion
    """
    datasets = []

    for unique_id, model in manifest_models.items():
        # Get columns from catalog if available, otherwise from manifest
        columns = catalog_columns.get(unique_id, {})
        if not columns:
            # Fallback to manifest columns
            manifest_cols = model.get("columns", {})
            columns = {
                col_name: {
                    "name": col_name,
                    "description": col_info.get("description"),
                    "nullable": None,
                }
                for col_name, col_info in manifest_cols.items()
            }

        # Convert columns dict to list
        columns_list = list(columns.values())

        # Extract metadata
        meta = model.get("meta", {})
        tests = model.get("tests", {})

        # Build dataset metadata
        dataset_metadata = {
            "full_name": model["full_name"],
            "display_name": model.get("alias") or model["name"],
            "owner_name": meta.get("owner"),
            "owner_contact": meta.get("owner_contact"),
            "description": model.get("description"),
            "intended_use": meta.get("intended_use"),
            "limitations": meta.get("limitations"),
            "columns": columns_list,
            "has_freshness_checks": tests.get("has_freshness", False),
            "has_volume_checks": tests.get("has_volume", False),
            "dbt_test_count": tests.get("count", 0),
            "has_sla": meta.get("has_sla", False),
            "breaking_changes_30d": meta.get("breaking_changes_30d"),
            "has_release_notes": meta.get("has_release_notes", False),
            "has_versioning": meta.get("has_versioning", False),
            "backward_compatible": meta.get("backward_compatible"),
        }

        datasets.append(dataset_metadata)

    return datasets

