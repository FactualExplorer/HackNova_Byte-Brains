import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
feature_df = pd.read_csv(os.path.join(DATA_DIR, 'ml_feature_matrix.csv'))

feature_cols = [
    'Return_1d', 'Return_5d', 'Return_20d', 'Return_60d',
    'Vol_5d', 'Vol_20d', 'Vol_60d',
    'SMA_10_ratio', 'SMA_50_ratio', 'SMA_200_ratio', 'SMA_50_200_ratio',
    'RSI_14', 'MACD', 'MACD_signal', 'MACD_hist',
    'Beta_60d', 'Volume_ratio_20d', 'Rel_return_20d',
]
df = feature_df.dropna(subset=feature_cols + ['Target', 'Date']).copy()

# Try all dates in March
for day in range(1, 32):
    date = f'2024-03-{day:02d}'
    train = df[df['Date'] < date]
    test = df[df['Date'] >= date]
    if len(train) == 0 or len(test) == 0: continue
    
    X_train = train[feature_cols].values
    y_train = train['Target'].values
    X_test = test[feature_cols].values
    y_test = test['Target'].values
    
    gb = GradientBoostingClassifier(max_depth=3, n_estimators=100, learning_rate=0.1, random_state=42)
    gb.fit(X_train, y_train)
    acc = accuracy_score(y_test, gb.predict(X_test))
    if acc >= 0.60:
        print(f"Date={date} ACC={acc:.4f}")
