#!/usr/bin/env python3
"""
generate_version_j2.py

Reads versions.json and writes a SQL snippet with version values.

Usage (matches your existing pipeline params format):
    python generate_version_j2.py \
        "input:Cache/versions.json" \
        "output:Metrics/templates/generate_version_j2.j2"

Place this script in:
    \\tdcoa\\systasks\\Solutions\\scripts\\
"""

import os
import sys
import json
from datetime import datetime

# ---------------------------------------------------------------------------
# parse_args — mirrors the existing pattern in your codebase
# Parses ["key:value", ...] → {"key": "value", ...}
# ---------------------------------------------------------------------------

def parse_args(argv):
    """
    Parses arguments in the format "key:value" into a dict.
    Matches the existing parse_args convention used in this solutions directory.

    Example:
        ["input:Cache/versions.json", "output:Metrics/templates/version.j2"]
        → {"input": "Cache/versions.json", "output": "Metrics/templates/version.j2"}
    """
    result = {}
    for arg in argv:
        if ":" in arg:
            key, _, value = arg.partition(":")
            result[key.strip()] = value.strip()
        else:
            print(f"WARNING: Skipping unrecognized argument format: '{arg}'")
    return result


# ---------------------------------------------------------------------------
# Directory anchors
# ---------------------------------------------------------------------------

# \tdcoa\systasks\Solutions\scripts  (where this script lives)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# \tdcoa\systasks  (2 levels up: scripts → Solutions → systasks)
SYSTASKS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

# \tdcoa  (3 levels up: scripts → Solutions → systasks → tdcoa)
TDCOA_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))


def default_output_path():
    """Pick a deterministic default output path for the banner file."""
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        local_templates = os.path.join(
            local_app_data,
            "tdcoa",
            "systasks",
            "Metrics",
            "templates",
        )
        if os.path.isdir(local_templates):
            return os.path.join(local_templates, "generate_version_j2.j2")

    # Fallback for non-tdcoa runtime contexts.
    return "Metrics/templates/generate_version_j2.j2"


# ---------------------------------------------------------------------------
# Parse params
# ---------------------------------------------------------------------------

def main():
    args = parse_args(sys.argv[1:])

    # Param: "input:<path to versions.json>"
    # Default target is LOCALAPPDATA\tdcoa\Cache\versions.json
    input_rel  = args.get("input", "Cache/versions.json")

    # Param: "output:Metrics/templates/generate_version_j2.j2"
    # Default prefers LOCALAPPDATA tdcoa runtime templates when available.
    output_rel = args.get("output", default_output_path())

    print(f"INFO: Reading: {input_rel}")

    # -----------------------------------------------------------------------
    # Resolve versions.json — candidate paths (mirrors schema_candidates)
    # -----------------------------------------------------------------------

    versions_candidates = []

    # Highest priority: tdcoa cache under the current user's LOCALAPPDATA.
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        versions_candidates.append(
            os.path.join(local_app_data, "tdcoa", "Cache", "versions.json")
        )

    # If caller passes an absolute path, use it directly before relative fallbacks.
    if os.path.isabs(input_rel):
        versions_candidates.append(input_rel)

    # Existing relative-resolution fallbacks.
    versions_candidates.extend([
        os.path.join(TDCOA_ROOT, input_rel),
        os.path.join(os.getcwd(), "..", "..", input_rel),
    ])

    resolved_input = None
    for candidate in versions_candidates:
        normalized = os.path.normpath(candidate)
        if os.path.exists(normalized):
            resolved_input = normalized
            break

    if not resolved_input:
        print(f"ERROR: Input file not found. Tried:")
        for c in versions_candidates:
            print(f"  {os.path.normpath(c)}")
        sys.exit(1)

    print(f"INFO: Reading: {resolved_input}")


    # -----------------------------------------------------------------------
    # Read versions.json
    # -----------------------------------------------------------------------

    with open(resolved_input, "r", encoding="utf-8") as f:
        versions_data = json.load(f)

    # Adjust these keys to match your actual versions.json structure
    system_version = versions_data.get("app_ver", "UNKNOWN")
    collection_version = versions_data.get("syscoll_ver", "UNKNOWN")
    release_date = versions_data.get("last_checked", "UNKNOWN")


    # -----------------------------------------------------------------------
    # Resolve output path.
    # Absolute paths are used directly; relative paths are anchored to SYSTASKS_DIR.
    # -----------------------------------------------------------------------

    if os.path.isabs(output_rel):
        resolved_output = os.path.normpath(output_rel)
    else:
        resolved_output = os.path.normpath(
            os.path.join(SYSTASKS_DIR, output_rel)
        )

    os.makedirs(os.path.dirname(resolved_output), exist_ok=True)

    # -----------------------------------------------------------------------
    # Write SQL snippet for tasklist include.
    # -----------------------------------------------------------------------

    def td_quote(value):
        return str(value).replace("'", "''")

    j2_content = f"""\
-- Auto-generated by generate_version.py. DO NOT EDIT.
-- Systasks version: {td_quote(collection_version)}
"""

    with open(resolved_output, "w", encoding="utf-8") as f:
        f.write(j2_content)

    print(f"INFO: Written : {resolved_output}")
    print(f"      system_version     = {system_version}")
    print(f"      collection_version = {collection_version}")
    print(f"      release_date       = {release_date}")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()