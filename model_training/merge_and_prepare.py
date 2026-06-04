import pandas as pd

# Paths
BENIGN = "./datasets/l2-benign.csv"
MALICIOUS = "./datasets/l2-malicious.csv"
OUTPUT = "./datasets/l2.csv"

# Load CSVs
benign = pd.read_csv(BENIGN)
malicious = pd.read_csv(MALICIOUS)

# Normalize labels to Benign in l2-benign and l1-doh
benign['Label'] = 'Benign'
malicious['Label'] = 'Malicious'

# Merge l1_doh + l2_benign, update benign file
total_benign = pd.concat([benign], ignore_index=True)
total_benign.to_csv(BENIGN, index=False)

# Merge all for final dataset
merged = pd.concat([total_benign, malicious], ignore_index=True)
merged.to_csv(OUTPUT, index=False)
print(f"Final merged dataset shape: {merged.shape}, written to {OUTPUT}")

