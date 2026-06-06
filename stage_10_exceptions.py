# Stage 10 - Exception Reporting


def build_report(exceptions):
    report = {
        "total": len(exceptions),
        "critical": [],
        "warnings": [],
    }

    for ex in exceptions:
        if ex["type"] in ("MISSING_DOCUMENT", "MISSING_SIGNATURE"):
            ex["severity"] = "CRITICAL"
            report["critical"].append(ex)
        else:
            ex["severity"] = "WARNING"
            report["warnings"].append(ex)

    return report
