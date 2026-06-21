from preprocess import load_X_y
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib

# Load data
DF_PATH = "./datasets/BCCC-CIRA-CIC-DoHBrw-2020.csv"
X, y = load_X_y(DF_PATH)


# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Train model
clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=2)
clf.fit(X_train, y_train)

# Evaluate
y_pred = clf.predict(X_test)
print("RandomForest Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

# Save the model
joblib.dump(clf, "random_forest_model.joblib")
