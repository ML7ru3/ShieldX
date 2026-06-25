from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib

from l1_preprocess import load_l1_data

X, y = load_l1_data()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

clf = SVC(kernel="rbf", C=1, random_state=42, max_iter=1000, verbose=True)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
print("L1 SVM Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

joblib.dump(clf, "l1_svm_model.joblib")
print("L1 SVM model saved to l1_svm_model.joblib")
