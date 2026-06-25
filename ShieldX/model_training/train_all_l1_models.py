"""
Train all L1 models and generate a comparison report.
"""
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'models'))

import joblib
import lightgbm as lgb
import xgboost as xgb
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score

from l1_preprocess import load_l1_data

REPORT_FILE = "l1_model_comparison_report.md"

X, y = load_l1_data()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

results = []

def evaluate(name, y_true, y_pred, train_time):
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    results.append((name, acc, prec, rec, f1, train_time))
    print(f"\n=== {name} ===")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"Train time: {train_time:.2f}s")
    print(classification_report(y_true, y_pred))


# 1. XGBoost (already exists)
start = time.time()
clf_xgb = xgb.XGBClassifier(n_estimators=200, max_depth=6, random_state=42)
clf_xgb.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
y_pred_xgb = clf_xgb.predict(X_test)
evaluate("XGBoost", y_test, y_pred_xgb, time.time() - start)
clf_xgb.save_model("l1_xgboost_model.json")
print("Saved l1_xgboost_model.json")


# 2. Random Forest
start = time.time()
clf_rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=2)
clf_rf.fit(X_train, y_train)
y_pred_rf = clf_rf.predict(X_test)
evaluate("Random Forest", y_test, y_pred_rf, time.time() - start)
joblib.dump(clf_rf, "l1_random_forest_model.joblib")
print("Saved l1_random_forest_model.joblib")


# 3. LightGBM
start = time.time()
clf_lgb = lgb.LGBMClassifier(n_estimators=100, random_state=42, n_jobs=-1, verbose=-1)
clf_lgb.fit(X_train, y_train, eval_set=[(X_test, y_test)], eval_metric='logloss')
y_pred_lgb = clf_lgb.predict(X_test)
evaluate("LightGBM", y_test, y_pred_lgb, time.time() - start)
clf_lgb.booster_.save_model("l1_lightgbm_model.txt")
print("Saved l1_lightgbm_model.txt")


# 4. SVM
start = time.time()
clf_svm = SVC(kernel="rbf", C=1, random_state=42, max_iter=500, verbose=False)
clf_svm.fit(X_train, y_train)
y_pred_svm = clf_svm.predict(X_test)
evaluate("SVM", y_test, y_pred_svm, time.time() - start)
joblib.dump(clf_svm, "l1_svm_model.joblib")
print("Saved l1_svm_model.joblib")


# --- Generate comparison report ---
df_report = pd.DataFrame(results, columns=["Model", "Accuracy", "Precision", "Recall", "F1 Score", "Train Time (s)"])
df_report = df_report.sort_values("F1 Score", ascending=False).reset_index(drop=True)

with open(REPORT_FILE, "w") as f:
    f.write("# L1 Model Comparison Report\n\n")
    f.write(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write("Dataset: L1 DoH (l1-doh.csv) vs Non-DoH (l1-nondoh.csv)\n\n")
    f.write("| Model | Accuracy | Precision | Recall | F1 Score | Train Time (s) |\n")
    f.write("|-------|----------|-----------|--------|----------|----------------|\n")
    for _, row in df_report.iterrows():
        f.write(f"| {row['Model']} | {row['Accuracy']:.4f} | {row['Precision']:.4f} | {row['Recall']:.4f} | {row['F1 Score']:.4f} | {row['Train Time (s)']:.2f} |\n")
    f.write("\n")
    f.write("## Classification Details\n\n")

    for name, y_pred in [
        ("XGBoost", y_pred_xgb),
        ("Random Forest", y_pred_rf),
        ("LightGBM", y_pred_lgb),
        ("SVM", y_pred_svm),
    ]:
        f.write(f"### {name}\n\n")
        f.write("```\n")
        f.write(classification_report(y_test, y_pred, digits=4))
        f.write("```\n\n")

print(f"\n\nComparison report saved to {REPORT_FILE}")
print("\n=== SUMMARY ===")
print(df_report.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
