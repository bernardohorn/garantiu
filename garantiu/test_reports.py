from junitparser import JUnitXml, Skipped


def parse_junit_report(xml_path: str) -> list[dict]:
    """
    Parses a JUnit XML report into a list of
    {"name": str, "classname": str, "status": "passed"|"failed"|"skipped", "time": float}.
    """
    xml = JUnitXml.fromfile(xml_path)
    results = []
    for suite in xml:
        for case in suite:
            result = case.result
            if result and isinstance(result[0], Skipped):
                status = "skipped"
            elif result:
                status = "failed"
            else:
                status = "passed"
            results.append({
                "name": case.name,
                "classname": case.classname,
                "status": status,
                "time": case.time or 0.0,
            })
    return results


def test_health_by_module(test_results: list) -> dict:
    """
    Groups results by module (first segment of classname, split on '.') and
    returns {module: health_score} where health_score = 100 * passed / total,
    rounded to 1 decimal place.
    """
    by_module: dict = {}
    for r in test_results:
        module = r["classname"].split(".")[0]
        by_module.setdefault(module, []).append(r)

    health = {}
    for module, cases in by_module.items():
        passed = sum(1 for c in cases if c["status"] == "passed")
        health[module] = round(100 * passed / len(cases), 1)
    return health
