#!/usr/bin/env python3
"""
build_oap_json.py
=================
Reads OAP CSV exports produced by the systasks VHC On-A-Page pipeline
and assembles them into a single structured JSON file suitable for
consumption by an agentic workflow (e.g. Claude).

Usage (called from systasks YAML as a script task):
    python scripts/build_oap_json.py  \
        schema:json_schema/oap_schema.yaml  \
        output:Vantage_Health_Check_OAP.json  \
        siteid:MY_SITE  \
        startdate:2025-03-01  \
        enddate:2025-04-11  \
        version:4.5

The script follows the same param style as existing systasks chart/script
tasks: positional args of the form "key:value".
"""

import csv
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Argument parsing (matches systasks chart param convention: "key:value")
# ---------------------------------------------------------------------------

def parse_args(argv):
    """Parse 'key:value' style params into a dict."""
    args = {}
    for arg in argv:
        if ":" in arg:
            key, value = arg.split(":", 1)
            args[key.strip()] = value.strip()
    return args

# ---------------------------------------------------------------------------
# YAML-lite parser (avoids external dependency on PyYAML)
#   Only needs to handle the simple structure of oap_schema.yaml
# ---------------------------------------------------------------------------

def parse_schema_yaml(filepath):
    """
    Minimal YAML parser sufficient for the oap_schema.yaml structure.
    Returns a dict with 'version', 'description', and 'sections'.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    schema = {"version": "", "description": "", "sections": {}}
    current_section = None
    current_source = None
    sources_list = None
    in_sources = False

    for raw_line in lines:
        line = raw_line.rstrip("\n\r")
        stripped = line.strip()

        # skip comments and blanks
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        # top-level keys
        if indent == 0:
            in_sources = False
            current_section = None
            current_source = None
            if stripped.startswith("version:"):
                schema["version"] = stripped.split(":", 1)[1].strip().strip('"').strip("'")
            elif stripped.startswith("description:"):
                schema["description"] = stripped.split(":", 1)[1].strip().strip('"').strip("'")
            elif stripped == "sections:":
                pass
            continue

        # section name (indent == 2)
        if indent == 2 and stripped.endswith(":"):
            section_name = stripped[:-1]
            schema["sections"][section_name] = {
                "description": "",
                "sources": [],
                "visualization_hint": None,
            }
            current_section = schema["sections"][section_name]
            current_source = None
            in_sources = False
            continue

        # section-level attributes (indent == 4)
        if indent == 4 and current_section is not None:
            if stripped.startswith("description:"):
                current_section["description"] = stripped.split(":", 1)[1].strip().strip('"').strip("'")
            elif stripped.startswith("visualization_hint:"):
                current_section["visualization_hint"] = stripped.split(":", 1)[1].strip()
            elif stripped == "sources:":
                in_sources = True
            continue

        # source list items (indent == 6, starts with "- file:")
        if indent == 6 and in_sources and current_section is not None:
            if stripped.startswith("- file:"):
                current_source = {
                    "file": stripped.split(":", 1)[1].strip(),
                    "key": None,
                    "format": "summary",
                    "description": "",
                    "optional": False,
                }
                current_section["sources"].append(current_source)
            continue

        # source attributes (indent == 8)
        if indent == 8 and current_source is not None:
            if stripped.startswith("key:"):
                current_source["key"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("format:"):
                current_source["format"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("description:"):
                current_source["description"] = stripped.split(":", 1)[1].strip().strip('"').strip("'")
            elif stripped.startswith("optional:"):
                current_source["optional"] = stripped.split(":", 1)[1].strip().lower() == "true"
            elif stripped.startswith("visualization_hint:"):
                current_source["visualization_hint"] = stripped.split(":", 1)[1].strip()
            continue

    return schema

# ---------------------------------------------------------------------------
# CSV readers — one per format type
# ---------------------------------------------------------------------------

def _clean_value(val):
    """Strip whitespace and try to coerce to number."""
    val = val.strip()
    if not val or val == "":
        return None
    # try int
    try:
        return int(val.replace(",", ""))
    except (ValueError, AttributeError):
        pass
    # try float
    try:
        return float(val.replace(",", ""))
    except (ValueError, AttributeError):
        pass
    # percentage like "42.5"
    return val


def read_csv_file(filepath):
    """Read a CSV and return (headers, rows) with basic encoding handling."""
    encodings = ["utf-8-sig", "utf-8", "latin-1"]
    for enc in encodings:
        try:
            with open(filepath, "r", encoding=enc, newline="") as f:
                reader = csv.reader(f)
                rows = [row for row in reader if row]  # skip empty rows
            if rows:
                return rows[0], rows[1:]
            return [], []
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise IOError(f"Could not decode CSV file: {filepath}")


def parse_key_value(filepath):
    """
    Two-column CSV (key, value) → flat dict.
    Used for: oap--dbcinfo.csv, oap--COD.csv
    """
    headers, rows = read_csv_file(filepath)
    result = {}
    for row in rows:
        if len(row) >= 2:
            key = row[0].strip().strip("'\"")
            val = _clean_value(row[1])
            result[key] = val
    return result


def parse_summary(filepath):
    """
    Single-row (or few-row) CSV with named columns → flat dict.
    Used for: oap--user_counts.csv, oap--query_counts.csv, etc.
    """
    headers, rows = read_csv_file(filepath)
    if not headers:
        return {}
    # If single row, return flat dict. If multiple, return list of dicts.
    if len(rows) == 1:
        return {h.strip(): _clean_value(v) for h, v in zip(headers, rows[0])}
    else:
        return [
            {h.strip(): _clean_value(v) for h, v in zip(headers, row)}
            for row in rows
        ]


def parse_timeseries(filepath):
    """
    Multi-row CSV where first column is a date → array of objects.
    Used for: oap--OutcomeCPUConsumption.csv
    """
    headers, rows = read_csv_file(filepath)
    if not headers:
        return []
    clean_headers = [h.strip() for h in headers]
    return [
        {h: _clean_value(v) for h, v in zip(clean_headers, row)}
        for row in rows
    ]


def parse_categorical(filepath):
    """
    Multi-row CSV where first column is a label/name → array of objects.
    Column names may contain chart hints like '--#27C1BD'; we strip those.
    Used for: oap--top_users.csv
    """
    headers, rows = read_csv_file(filepath)
    if not headers:
        return []
    clean_headers = []
    for h in headers:
        # strip chart color hints:  "Qry_Cnt--#27C1BD" → "Qry_Cnt"
        name = h.split("--")[0].strip()
        clean_headers.append(name)
    return [
        {h: _clean_value(v) for h, v in zip(clean_headers, row)}
        for row in rows
    ]


def parse_matrix(filepath):
    """
    True wide-format grid CSV (rows already represent one dimension, columns
    the other) → compact 2D structure.  Used when the CSV itself is already
    pivoted, e.g. a 7-row × 24-column table where each row is a day and each
    column is an hour.

        {
            "_format": "matrix",
            "row_label_column": "DayOfWeek",
            "row_labels": ["Sun", "Mon", ...],
            "col_labels": ["00", "01", ..., "23"],
            "values": [
                [1.59, 1.02, ...],   ← one array per day
                ...
            ]
        }
    """
    headers, rows = read_csv_file(filepath)
    if not headers:
        return {"_format": "matrix", "row_label_column": None,
                "row_labels": [], "col_labels": [], "values": []}

    clean_headers = [h.strip() for h in headers]
    row_label_column = clean_headers[0]
    col_labels = clean_headers[1:]

    row_labels = []
    values = []
    for row in rows:
        if not row:
            continue
        row_labels.append(row[0].strip())
        values.append([_clean_value(v) for v in row[1:]])

    return {
        "_format": "matrix",
        "row_label_column": row_label_column,
        "row_labels": row_labels,
        "col_labels": col_labels,
        "values": values,
    }



def parse_heatmap_pivot(filepath):
    """
    Long-format CSV with columns (SiteID, Day_of_Week, Log_Hour, Avg_CPU, Med_CPU)
    -> pivoted 2D structure ready for heatmap rendering.
    Used for: oap--SPMADetailData.csv

    The CSV has one row per (day, hour) combination -- 168 rows for a full week
    (7 days x 24 hours).  We pivot on Day_of_Week (rows) x Log_Hour (columns)
    and produce two value grids: one for Avg_CPU and one for Med_CPU.

    Output structure:
        {
            "_format": "heatmap_pivot",
            "row_labels": ["Sunday", "Monday", ...],   <- 7 days, display names
            "col_labels": [0, 1, 2, ..., 23],          <- 24 hours
            "avg_cpu": [                               <- 7 x 24 grid
                [1.59, 1.02, ...],                     <- Sunday hourly avg
                ...
            ],
            "med_cpu": [                               <- 7 x 24 grid
                [0.195, 0.165, ...],
                ...
            ]
        }
    """
    headers, rows = read_csv_file(filepath)
    if not headers:
        return {"_format": "heatmap_pivot", "row_labels": [],
                "col_labels": [], "avg_cpu": [], "med_cpu": []}

    clean_headers = [h.strip() for h in headers]

    # Locate columns by name (case-insensitive) so column order shifts do not break us
    def _col(names):
        for name in names:
            for i, h in enumerate(clean_headers):
                if h.lower() == name.lower():
                    return i
        return None

    idx_day  = _col(["Day of the Week", "Day_of_Week", "DayOfWeek"])
    idx_hour = _col(["Log_Hour", "LogHour", "Hour"])
    idx_avg  = _col(["Avg_CPU", "AvgCPU", "Avg CPU"])
    idx_med  = _col(["Med_CPU", "MedCPU", "Med CPU", "Median_CPU"])

    if any(i is None for i in [idx_day, idx_hour, idx_avg, idx_med]):
        print(f"  WARNING: heatmap_pivot could not locate required columns in {filepath}")
        print(f"           Found headers: {clean_headers}")
        return {"_format": "heatmap_pivot", "_error": "required columns not found",
                "headers": clean_headers}

    # Collect all (day_raw, hour) -> (avg, med) values
    # day_raw looks like "1Sunday", "2Monday" -- sort key is the leading digit
    data = {}
    for row in rows:
        if len(row) <= max(idx_day, idx_hour, idx_avg, idx_med):
            continue
        day_raw = row[idx_day].strip()
        hour    = _clean_value(row[idx_hour])
        avg     = _clean_value(row[idx_avg])
        med     = _clean_value(row[idx_med])
        if day_raw not in data:
            data[day_raw] = {}
        data[day_raw][hour] = (avg, med)

    # Sort days by the leading sort-digit ("1Sunday" < "2Monday" ...)
    sorted_days = sorted(data.keys())

    # Strip leading sort digit for display: "1Sunday" -> "Sunday"
    display_days = [d.lstrip("0123456789") for d in sorted_days]

    # Hours 0-23 (use whatever hours actually appear, sorted)
    all_hours = sorted({h for day_data in data.values() for h in day_data})

    avg_grid = []
    med_grid = []
    for day in sorted_days:
        avg_row = [data[day].get(h, (None, None))[0] for h in all_hours]
        med_row = [data[day].get(h, (None, None))[1] for h in all_hours]
        avg_grid.append(avg_row)
        med_grid.append(med_row)

    return {
        "_format": "heatmap_pivot",
        "row_labels": display_days,
        "col_labels": all_hours,
        "avg_cpu": avg_grid,
        "med_cpu": med_grid,
    }

FORMAT_PARSERS = {
    "key_value": parse_key_value,
    "summary": parse_summary,
    "timeseries": parse_timeseries,
    "categorical": parse_categorical,
    "matrix": parse_matrix,
    "heatmap_pivot": parse_heatmap_pivot,
}

# ---------------------------------------------------------------------------
# Main assembly
# ---------------------------------------------------------------------------

def build_json(schema, working_dir, metadata):
    """
    Walk the schema, read each CSV, and assemble the final JSON structure.
    """
    output = {
        "_metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "schema_version": schema.get("version", "unknown"),
            "solution": schema.get("description", "Vantage Health Check"),
            **metadata,
        },
        "_section_index": [],  # ordered list of section keys for agent navigation
    }

    for section_name, section_def in schema.get("sections", {}).items():
        section_data = {
            "_description": section_def.get("description", ""),
        }
        if section_def.get("visualization_hint"):
            section_data["_visualization_hint"] = section_def["visualization_hint"]

        for source in section_def.get("sources", []):
            csv_file = source["file"]
            csv_path = os.path.join(working_dir, csv_file)
            key = source.get("key", csv_file.replace(".csv", "").replace("--", "_"))
            fmt = source.get("format", "summary")
            optional = source.get("optional", False)

            if not os.path.exists(csv_path):
                if optional:
                    section_data[key] = None
                    continue
                else:
                    print(f"  WARNING: Required file not found: {csv_path}")
                    section_data[key] = {"_error": f"File not found: {csv_file}"}
                    continue

            try:
                parser = FORMAT_PARSERS.get(fmt, parse_summary)
                parsed = parser(csv_path)
                section_data[key] = parsed

                # Propagate per-source visualization hint if present.
                # - dict (summary, key_value, matrix, heatmap_pivot): attach key directly
                # - list (timeseries, categorical): wrap as {"_visualization_hint": ..., "data": [...]}
                #   so the hint is not silently dropped
                if source.get("visualization_hint"):
                    hint = source["visualization_hint"]
                    if isinstance(parsed, dict):
                        section_data[key]["_visualization_hint"] = hint
                    elif isinstance(parsed, list):
                        section_data[key] = {"_visualization_hint": hint, "data": parsed}

                # Row count reporting — matrices expose their own row count
                if isinstance(parsed, list):
                    row_count = len(parsed)
                elif fmt == "matrix":
                    row_count = len(parsed.get("row_labels", []))
                else:
                    row_count = 1 if parsed else 0

                print(f"  OK: {csv_file} → {key} ({fmt}, {row_count} records)")
            except Exception as e:
                print(f"  ERROR reading {csv_file}: {e}")
                section_data[key] = {"_error": str(e)}

        output[section_name] = section_data
        output["_section_index"].append(section_name)

    return output


def main():
    args = parse_args(sys.argv[1:])

    schema_path = args.get("schema", "json_schema/oap_schema.yaml")
    output_file = args.get("output", "Vantage_Health_Check_OAP.json")
    siteid = args.get("siteid", "unknown")
    startdate = args.get("startdate", "unknown")
    enddate = args.get("enddate", "unknown")
    version = args.get("version", "4.5")

    # Working directory is wherever the CSVs have been exported (cwd in systasks)
    working_dir = os.getcwd()

    # Schema file is relative to the solution directory
    # In systasks, scripts are run from the output dir, but schema lives in the solution dir
    # Try multiple locations
    schema_candidates = [
        schema_path,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", schema_path),
    ]
    resolved_schema = None
    for candidate in schema_candidates:
        if os.path.exists(candidate):
            resolved_schema = candidate
            break

    if not resolved_schema:
        print(f"ERROR: Schema file not found. Tried: {schema_candidates}")
        sys.exit(1)

    print(f"=== Building VHC On-A-Page JSON ===")
    print(f"  Schema:    {resolved_schema}")
    print(f"  Output:    {output_file}")
    print(f"  WorkDir:   {working_dir}")
    print(f"  Site:      {siteid}")
    print(f"  Range:     {startdate} to {enddate}")
    print()

    try:
        schema = parse_schema_yaml(resolved_schema)
    except Exception as e:
        print(f"ERROR parsing schema: {e}")
        traceback.print_exc()
        sys.exit(1)

    metadata = {
        "site_id": siteid,
        "date_range": {"start": startdate, "end": enddate},
        "vhc_version": version,
    }

    result = build_json(schema, working_dir, metadata)

    output_path = os.path.join(working_dir, output_file)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n=== JSON written to: {output_path} ===")
    print(f"  Sections: {len(result.get('_section_index', []))}")
    size_kb = os.path.getsize(output_path) / 1024
    print(f"  File size: {size_kb:.1f} KB")


if __name__ == "__main__":
    main()