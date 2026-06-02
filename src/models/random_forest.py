import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib

# Load data
DF_PATH = "../../datasets/L2-BenignDoH-MaliciousDoH.parquet"
df = pd.read_parquet(DF_PATH)

# Get features and label
X = df.drop('Label', axis=1)
y = df['Label']

# Encode target if needed
if y.dtype == 'O' or y.dtype.name == 'category':
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    y = le.fit_transform(y)
    joblib.dump(le, "random_forest_labelencoder.joblib")

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Train model
clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
clf.fit(X_train, y_train)

# Evaluate
y_pred = clf.predict(X_test)
print("RandomForest Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

# Save the model
joblib.dump(clf, "random_forest_model.joblib")
