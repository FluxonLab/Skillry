#!/usr/bin/env python3
"""Optional Jev CLI; the portable skill installer remains independent."""
import sys

if len(sys.argv) > 1 and sys.argv[1] == "install":
    from jev.install import main
    del sys.argv[1]
else:
    from jev.cli import main

if __name__ == "__main__":
    main()
