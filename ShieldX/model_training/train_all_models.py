import subprocess
import sys

# Paths to model training scripts
scripts = [
    "src/models/random_forest.py",
    "src/models/lightgbm_model.py",
    "src/models/xgboost_model.py",  # Layer 2: Malicious vs Benign
    "src/models/l1_xgboost.py",     # Layer 1: DoH vs Non-DoH
    "src/models/svm_model.py",
]

for script in scripts:
    print(f"== Training with: {script} ==")
    ret = subprocess.call([sys.executable, script])
    if ret != 0:
        print(f"FAILED: {script}")
    else:
        print(f"SUCCESS: {script}\n")
