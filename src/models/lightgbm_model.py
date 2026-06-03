from preprocess import load_X_y
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from lightgbm import early_stopping
import lightgbm as lgb

# Load data
DF_PATH = "../../datasets/L2-BenignDoH-MaliciousDoH.parquet"
X, y = load_X_y(DF_PATH)


# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Train LightGBM classifier
clf = lgb.LGBMClassifier(n_estimators=100, random_state=42, n_jobs=-1)
# Pass early_stopping as a list to the 'callbacks' argument
clf.fit(
    X_train, 
    y_train, 
    eval_set=[(X_test, y_test)], 
    eval_metric='logloss', 
    callbacks=[early_stopping(stopping_rounds=10)], 
    verbose=True
)

# Evaluate
y_pred = clf.predict(X_test)
print("LightGBM Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

# Save model
clf.booster_.save_model("lightgbm_model.txt")
