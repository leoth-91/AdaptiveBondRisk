import os
import sys
from pathlib import Path


sys.path.insert(0, os.environ["ADAPTIVE_BOND_RISK_CLIENT_MODULE_DIR"])
sys.path.insert(0, os.environ["ADAPTIVE_BOND_RISK_GENERATED_PYTHON_DIR"])
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "client"))
