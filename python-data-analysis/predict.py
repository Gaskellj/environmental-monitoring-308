import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

# Modeling
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error


def load_data(csv_path: Path) -> pd.DataFrame:
    """Load the stored CSV into a pandas DataFrame."""
    return pd.read_csv(csv_path, index_col="datetime", parse_dates=True)


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """Basic cleaning: forward-fill missing values then drop any remaining NaNs."""
    return df.ffill().dropna()


def train_model(X, y):
    """Train a GradientBoosting regressor and return the fitted model."""
    model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
    model.fit(X, y)
    return model


def evaluate_train(model, X_train, y_train):
    """Evaluate on training set and print MAE/MSE."""
    preds = model.predict(X_train)
    mae = mean_absolute_error(y_train, preds)
    mse = mean_squared_error(y_train, preds)
    print(f"Train set — MAE: {mae:.4f}, MSE: {mse:.4f}")


def predict_and_plot(model, X, index, output_path=None):
    """Predict DO and plot predicted values over time."""
    preds = model.predict(X)
    plt.figure(figsize=(12, 6))
    plt.plot(index, preds, marker='o', linestyle='--', label='Predicted DO')
    plt.xlabel('Timestamp')
    plt.ylabel('Predicted Dissolved Oxygen')
    plt.title('Predicted Dissolved Oxygen over Time')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    if output_path:
        out_df = pd.DataFrame({'predicted_dissolved_oxygen': preds}, index=index)
        out_df.to_csv(output_path)
        print(f"Saved predictions to {output_path}")


def main():
    data_dir = Path(__file__).parent / "data"
    train_csv = data_dir / "hammer_creek_data.csv"
    test_csv  = data_dir / "arduino_data.csv"

    # Load and preprocess training data
    df_train = load_data(train_csv)
    df_train = preprocess(df_train)

    # Features and target for training
    target_col = 'dissolved_oxygen_value'
    feature_cols = [c for c in df_train.columns if c != target_col]
    X_train = df_train[feature_cols]
    y_train = df_train[target_col]

    # Train with Gradient Boosting
    model = train_model(X_train, y_train)
    evaluate_train(model, X_train, y_train)

    # Load and preprocess test data (no DO column present)
    df_test = load_data(test_csv)
    df_test = preprocess(df_test)
    X_test = df_test[feature_cols]

    # Predict and plot
    predict_and_plot(
        model,
        X_test,
        df_test.index,
        output_path=data_dir / "arduino_predictions.csv"
    )

if __name__ == "__main__":
    main()