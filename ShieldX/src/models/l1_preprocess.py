import pandas as pd

L1_DOH_PATH = "./datasets/l1-doh.csv"
L1_NONDOH_PATH = "./datasets/l1-nondoh.csv"
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
