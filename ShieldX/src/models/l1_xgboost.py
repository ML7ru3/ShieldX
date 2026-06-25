import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import xgboost as xgb

L1_DOH_PATH = "./datasets/l1-doh.csv"
L1_NONDOH_PATH = "./datasets/l1-nondoh.csv"
OUTPUT_MODEL = "l1_xgboost_model.json"

L1_DROP_FIELDS = ['SourceIP', 'SourcePort', 'DestinationIP', 'DestinationPort', 'TimeStamp', 'Duration']


def load_l1_data():
    doh = pd.read_csv(L1_DOH_PATH)
    nondoh = pd.read_csv(L1_NONDOH_PATH)
    df = pd.concat([doh, nondoh], ignore_index=True)

    X = df.drop(columns=L1_DROP_FIELDS + ['Label'], errors='ignore')
    y = df['Label'].map({'DoH': 1, 'NonDoH': 0})

    numeric_cols = X.select_dtypes(include=['number']).columns
    X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].median())

    print('L1 training features:', list(X.columns))
    print(f'Class distribution:\n{y.value_counts()}')

    return X, y


X, y = load_l1_data()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

clf = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=6,
    random_state=42
)

clf.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=True)

y_pred = clf.predict(X_test)
print("Layer 1 XGBoost Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

clf.save_model(OUTPUT_MODEL)
print(f"Layer 1 model saved to {OUTPUT_MODEL}")
