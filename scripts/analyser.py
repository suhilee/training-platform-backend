import argparse
import re
from pathlib import Path


LOG_PATTERN = re.compile(
    r"REQUEST_ID=(?P<request_id>\S+) "
    r"ENDPOINT=(?P<method>\S+) (?P<path>\S+) "
    r"PID=(?P<pid>\d+) "
    r"DB_CONNECTION_HOLD_MS=(?P<hold>[\d.]+) "
    r"DB_CONNECTIONS_CHECKED_OUT=(?P<checked>\d+)"
)


def percentile(values, percentage):
    if not values:
        return 0.0

    ordered = sorted(values)
    index = int(len(ordered) * percentage / 100)

    if index >= len(ordered):
        index = len(ordered) - 1

    return ordered[index]


def print_group(title, records):
    print(f"\n{title}")
    print(
        "endpoint | pid | requests | avg hold ms | p50 | p95 | "
        "max hold ms | max checked out | at pool limit | holds > 1s"
    )
    print(
        "--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---:"
    )

    for (endpoint, pid), values in sorted(records.items()):
        holds = [record["hold"] for record in values]
        checked_out = [record["checked"] for record in values]

        average = sum(holds) / len(holds)
        at_limit = sum(
            1 for value in checked_out if value >= 30
        )
        long_holds = sum(1 for value in holds if value > 1000)

        print(
            f"{endpoint} | {pid} | {len(values)} | "
            f"{average:.2f} | {percentile(holds, 50):.2f} | "
            f"{percentile(holds, 95):.2f} | {max(holds):.2f} | "
            f"{max(checked_out)} | {at_limit} | {long_holds}"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("log_file")
    args = parser.parse_args()

    log_path = Path(args.log_file)

    if not log_path.exists():
        raise SystemExit(f"Log file not found: {log_path}")

    by_endpoint = {}
    by_worker = {}

    with log_path.open(encoding="utf-8") as log_file:
        for line in log_file:
            match = LOG_PATTERN.search(line)

            if match is None:
                continue

            endpoint = (
                f"{match.group('method')} "
                f"{match.group('path')}"
            )
            pid = match.group("pid")
            hold = float(match.group("hold"))
            checked = int(match.group("checked"))

            record = {
                "hold": hold,
                "checked": checked,
            }

            by_endpoint.setdefault((endpoint, pid), []).append(
                record
            )
            by_worker.setdefault((endpoint, pid), []).append(
                record
            )

    print_group("Connection hold time by endpoint and worker", by_endpoint)


if __name__ == "__main__":
    main()