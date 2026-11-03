#!/usr/bin/env python3
"""Generate portable project assets from the one canonical template source."""
import sys
sys.dont_write_bytecode = True
from template_release import main

if __name__ == "__main__":
    raise SystemExit(main())
