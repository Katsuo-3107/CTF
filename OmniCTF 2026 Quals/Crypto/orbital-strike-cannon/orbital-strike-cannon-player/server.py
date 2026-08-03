#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from cannon import instance_from_env, make_instance, public_json


BANNER = r"""
      ____       __    _ __        __   _____ __        _ __
     / __ \_____/ /_  (_) /_____ _/ /  / ___// /________(_) /_____  _____
    / / / / ___/ __ \/ / __/ __ `/ /   \__ \/ __/ ___/ / / //_/ _ \/ ___/
   / /_/ / /  / /_/ / / /_/ /_/ / /   ___/ / /_/ /  / / / ,< /  __/ /
   \____/_/  /_.___/_/\__/\__,_/_/   /____/\__/_/  /_/_/_/|_|\___/_/

                         C A N N O N
""".strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Orbital-Strike-Cannon service")
    parser.add_argument("--json", action="store_true", help="print only the public JSON transcript")
    parser.add_argument("--seed", help="local deterministic seed for testing")
    parser.add_argument("--show-answer", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    inst = make_instance(args.seed) if args.seed is not None else instance_from_env()

    if args.json:
        print(public_json(inst))
        return 0

    print(BANNER)
    print()
    print("Telemetry follows. Survive the non-associative recoil.")
    print(public_json(inst))
    print()
    print("Submit firing code:")
    sys.stdout.flush()

    attempt = sys.stdin.readline().strip()
    if args.show_answer:
        print(f"[debug] firing_code={inst.firing_code}")

    if attempt == inst.firing_code:
        print("LOCK CONFIRMED. CANNON FIRED.")
        print(inst.flag.decode())
        return 0

    print("KABOOM: unstable kernel collapse detected.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

