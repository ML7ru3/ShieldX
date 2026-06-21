import pandas as pd

# Central columns to drop for network feature ML
DROP_FEATS = ['Label']

# Returns (X, y) from a Parquet dataframe, with imputation
# Usage: X, y = load_X_y(parquet_path)
def load_X_y(df_path):
    df = pd.read_csv(df_path)
    X = df.drop(DROP_FEATS, axis=1)
    y = df['Label']

    print('Training features:', list(X.columns))
    missing_before = X.isnull().sum().sum()
    if missing_before:
        print(f"Imputing {missing_before} missing values in features with median.")
        numeric_cols = X.select_dtypes(include=['number']).columns
        X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].median())
    print('Features NaN after impute:', X.isnull().sum().sum())
    return X, y
