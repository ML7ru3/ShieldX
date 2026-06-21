import subprocess
import sys

# Paths to model training scripts
scripts = [
    # "src/models/random_forest.py",
    # "src/models/lightgbm_model.py",
    "src/models/xgboost_model.py",
    # "src/models/svm_model.py",
]

for script in scripts:
    print(f"== Training with: {script} ==")
    ret = subprocess.call([sys.executable, script])
    if ret != 0:
        print(f"FAILED: {script}")
    else:
        print(f"SUCCESS: {script}\n")
