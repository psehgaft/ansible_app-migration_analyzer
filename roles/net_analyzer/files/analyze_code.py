#!/usr/bin/env python3
import os
import re
import json
import sys

def analyze_project(source_path):
    metrics = {
        "total_files_cs": 0,
        "total_files_vb": 0,
        "total_classes": 0,
        "total_loc": 0,
        "wsdl_files": [],
        "findings": {
            "system_web_usages": 0,      # ASP.NET Web
            "wcf_usages": 0,             # WCF / SOAP
            "aspx_files": 0,             # WebForms
            "win_api_usages": 0,         # Windows specific
            "dataset_usages": 0          # Legacy Data access
        }
    }

    # Regular expressions for class and pattern counting.
    cs_class_regex = re.compile(r'\b(public|internal|private|protected)?\s*(abstract|sealed|static)?\s*class\s+([A-Za-z0-9_]+)')
    vb_class_regex = re.compile(r'\b(Public|Friend|Private)?\s*(MustInherit|NotInheritable)?\s*Class\s+([A-Za-z0-9_]+)', re.IGNORECASE)

    for root, _, files in os.walk(source_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            full_path = os.path.join(root, file)

            # Detect WSDL files.
            if ext == '.wsdl':
                metrics["wsdl_files"].append(full_path)
                continue

            if ext == '.aspx':
                metrics["findings"]["aspx_files"] += 1

            if ext in ['.cs', '.vb']:
                if ext == '.cs':
                    metrics["total_files_cs"] += 1
                else:
                    metrics["total_files_vb"] += 1

                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        metrics["total_loc"] += len(lines)
                        content = "".join(lines)

                        # Count classes.
                        if ext == '.cs':
                            metrics["total_classes"] += len(cs_class_regex.findall(content))
                        else:
                            metrics["total_classes"] += len(vb_class_regex.findall(content))

                        # Detect complexity patterns.
                        if "System.Web" in content:
                            metrics["findings"]["system_web_usages"] += 1
                        if "System.ServiceModel" in content:
                            metrics["findings"]["wcf_usages"] += 1
                        if "DllImport" in content or "Microsoft.Win32" in content:
                            metrics["findings"]["win_api_usages"] += 1
                        if "DataSet" in content or "DataTable" in content:
                            metrics["findings"]["dataset_usages"] += 1

                except Exception:
                    pass

    # Complexity scoring.
    metrics["score_net_core"] = "Low"
    metrics["score_quarkus"] = "Medium"

    if metrics["findings"]["wcf_usages"] > 0 or metrics["findings"]["system_web_usages"] > 5:
        metrics["score_net_core"] = "Medium"
        metrics["score_quarkus"] = "High"

    if metrics["findings"]["aspx_files"] > 0 or metrics["findings"]["win_api_usages"] > 0:
        metrics["score_net_core"] = "High"
        metrics["score_quarkus"] = "Very High (Rewrite Required)"

    return metrics

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    results = analyze_project(path)
    print(json.dumps(results))
