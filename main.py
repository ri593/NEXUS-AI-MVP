import os
import sys
from pathlib import Path


if __name__ == "__main__":
    target = Path(__file__).with_name("main (1).py")
    os.execv(sys.executable, [sys.executable, str(target)])
