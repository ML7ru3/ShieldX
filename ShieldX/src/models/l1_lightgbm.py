from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from lightgbm import early_stopping
import lightgbm as lgb

from l1_preprocess import load_l1_data

X, y = load_l1_data()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

clf = lgb.LGBMClassifier(n_estimators=100, random_state=42, n_jobs=-1)
clf.fit(
    X_train,
    y_train,
    eval_set=[(X_test, y_test)],
    eval_metric='logloss',
    callbacks=[early_stopping(stopping_rounds=10)],
)

y_pred = clf.predict(X_test)
print("L1 LightGBM Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

clf.booster_.save_model("l1_lightgbm_model.txt")
print("L1 LightGBM model saved to l1_lightgbm_model.txt")
