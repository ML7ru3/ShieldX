import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import lightgbm as lgb
import joblib

# Load data
DF_PATH = "../../datasets/L2-BenignDoH-MaliciousDoH.parquet"
df = pd.read_parquet(DF_PATH)

# Features and label
X = df.drop('Label', axis=1)
y = df['Label']

# Encode label if needed
if y.dtype == 'O' or y.dtype.name == 'category':
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    y = le.fit_transform(y)
    joblib.dump(le, "lightgbm_labelencoder.joblib")

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Train LightGBM classifier
clf = lgb.LGBMClassifier(n_estimators=100, random_state=42, n_jobs=-1)
clf.fit(X_train, y_train, eval_set=[(X_test, y_test)], eval_metric='logloss', early_stopping_rounds=10, verbose=True)

# Evaluate
y_pred = clf.predict(X_test)
print("LightGBM Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

# Save model
clf.booster_.save_model("lightgbm_model.txt")
