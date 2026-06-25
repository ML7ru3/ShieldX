# L1 Model Comparison Report

Generated at: 2026-06-26 01:35:34

Dataset: L1 DoH (l1-doh.csv) vs Non-DoH (l1-nondoh.csv)

| Model | Accuracy | Precision | Recall | F1 Score | Train Time (s) |
|-------|----------|-----------|--------|----------|----------------|
| XGBoost | 0.9982 | 0.9983 | 0.9940 | 0.9961 | 34.20 |
| Random Forest | 0.9979 | 0.9983 | 0.9927 | 0.9955 | 320.70 |
| LightGBM | 0.9974 | 0.9970 | 0.9917 | 0.9944 | 21.87 |
| SVM | 0.3877 | 0.2679 | 0.9525 | 0.4182 | 57.91 |

## Classification Details

### XGBoost

```
              precision    recall  f1-score   support

           0     0.9982    0.9995    0.9988    179499
           1     0.9983    0.9940    0.9961     53929

    accuracy                         0.9982    233428
   macro avg     0.9982    0.9968    0.9975    233428
weighted avg     0.9982    0.9982    0.9982    233428
```

### Random Forest

```
              precision    recall  f1-score   support

           0     0.9978    0.9995    0.9987    179499
           1     0.9983    0.9927    0.9955     53929

    accuracy                         0.9979    233428
   macro avg     0.9981    0.9961    0.9971    233428
weighted avg     0.9979    0.9979    0.9979    233428
```

### LightGBM

```
              precision    recall  f1-score   support

           0     0.9975    0.9991    0.9983    179499
           1     0.9970    0.9917    0.9944     53929

    accuracy                         0.9974    233428
   macro avg     0.9973    0.9954    0.9963    233428
weighted avg     0.9974    0.9974    0.9974    233428
```

### SVM

```
              precision    recall  f1-score   support

           0     0.9386    0.2179    0.3537    179499
           1     0.2679    0.9525    0.4182     53929

    accuracy                         0.3877    233428
   macro avg     0.6033    0.5852    0.3860    233428
weighted avg     0.7836    0.3877    0.3686    233428
```

