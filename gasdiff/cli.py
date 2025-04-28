import json
import sys
import os
from collections import defaultdict

def load_json(path):
    with open(path, 'r') as f:
        return {item['contract']: item for item in json.load(f)}

def simplify_contract_name(contract):
    return contract.split(":")[-1].split("/")[-1]

def compute_diff(after, before):
    if after != before:
        diff = after - before
        rel_diff = (diff / before * 100) if before != 0 else float('inf')
        return diff, rel_diff
    return None, None

def format_diff(diff, rel_diff):
    if diff is None:
        return ""
    return f"{diff:+} ({rel_diff:.1f}%)"

def print_markdown_table(contract_name, deployment_diff, function_diffs):
    print(f"\n### {contract_name}\n")

    headers = ["Metric", "Before", "After", "Difference"]
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join(["-" for _ in headers]) + " |")

    for metric, values in deployment_diff.items():
        before, after, diff, rel_diff = values
        print(f"| Deployment {metric} | {before} | {after} | {format_diff(diff, rel_diff)} |")

    for fn_name, metrics in function_diffs.items():
        for metric, values in metrics.items():
            before, after, diff, rel_diff = values
            print(f"| {fn_name} {metric} | {before} | {after} | {format_diff(diff, rel_diff)} |")

def main(before_path, after_path):
    before = load_json(before_path)
    after = load_json(after_path)

    all_contracts = set(before.keys()) | set(after.keys())

    for contract in sorted(all_contracts):
        before_entry = before.get(contract, {})
        after_entry = after.get(contract, {})

        deployment_diff = {}
        function_diffs = defaultdict(dict)

        if 'deployment' in after_entry and 'deployment' in before_entry:
            for key in ['gas', 'size']:
                b = before_entry['deployment'].get(key, 0)
                a = after_entry['deployment'].get(key, 0)
                diff, rel_diff = compute_diff(a, b)
                if diff is not None:
                    deployment_diff[key] = (b, a, diff, rel_diff)

        before_funcs = before_entry.get('functions', {})
        after_funcs = after_entry.get('functions', {})
        all_functions = set(before_funcs.keys()) | set(after_funcs.keys())

        for fn in all_functions:
            before_fn = before_funcs.get(fn, {})
            after_fn = after_funcs.get(fn, {})
            for key in ['min', 'mean', 'median', 'max']:
                b = before_fn.get(key, 0)
                a = after_fn.get(key, 0)
                diff, rel_diff = compute_diff(a, b)
                if diff is not None:
                    function_diffs[fn][key] = (b, a, diff, rel_diff)

        if deployment_diff or function_diffs:
            simplified_name = simplify_contract_name(contract)
            print_markdown_table(simplified_name, deployment_diff, function_diffs)

def cli():
    if len(sys.argv) != 3:
        print("Usage: python -m gasdiff before.json after.json")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
