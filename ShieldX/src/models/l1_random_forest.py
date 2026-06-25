from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib

from l1_preprocess import load_l1_data

X, y = load_l1_data()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=2)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
print("L1 RandomForest Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

joblib.dump(clf, "l1_random_forest_model.joblib")
print("L1 Random Forest model saved to l1_random_forest_model.joblib")
