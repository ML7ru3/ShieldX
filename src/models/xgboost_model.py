from preprocess import load_X_y
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import xgboost as xgb

# Load data
DF_PATH = "./datasets/L2-BenignDoH-MaliciousDoH.parquet"
X, y = load_X_y(DF_PATH)
# Map string labels to integers for XGBoost compatibility
y = y.map({'Benign': 0, 'Malicious': 1})


# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Train XGBoost classifier
clf = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=6,
    random_state=42
)

# Remove early_stopping_rounds from fit()
clf.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=True)

# Evaluate
y_pred = clf.predict(X_test)
print("XGBoost Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

# Save model
clf.save_model("xgboost_model.json")
