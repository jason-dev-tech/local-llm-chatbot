import sys

from operational.runtime_checks import run_backend_smoke_checks


def main() -> None:
    result = run_backend_smoke_checks()

    print("Backend self-check")
    print()
    print(f"Status: {'PASS' if result['ok'] else 'FAIL'}")

    if result["config_errors"]:
        print("Configuration issues:")
        for error in result["config_errors"]:
            print(f"- {error}")

    print("Checks:")
    for name, ok in result["checks"].items():
        print(f"- {name}: {'PASS' if ok else 'FAIL'}")

    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
