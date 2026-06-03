import pandas as pd

# Paths
BENIGN = "./datasets/l2-benign.csv"
L1_DOH = "./datasets/l1-doh.csv"
MALICIOUS = "./datasets/l2-malicious.csv"
OUTPUT = "./datasets/L2-BenignDoH-MaliciousDoH.parquet"

# Load CSVs
benign = pd.read_csv(BENIGN)
l1_doh = pd.read_csv(L1_DOH)
malicious = pd.read_csv(MALICIOUS)

# Normalize labels to Benign in l2-benign and l1-doh
benign['Label'] = 'Benign'
l1_doh['Label'] = 'Benign'
malicious['Label'] = 'Malicious'

# Merge l1_doh + l2_benign, update benign file
total_benign = pd.concat([benign, l1_doh], ignore_index=True)
total_benign.to_csv(BENIGN, index=False)

# Merge all for final dataset
merged = pd.concat([total_benign, malicious], ignore_index=True)
merged.to_parquet(OUTPUT)
print(f"Final merged dataset shape: {merged.shape}, written to {OUTPUT}")

