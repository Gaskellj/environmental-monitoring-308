import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

# Modeling
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error


def load_data(csv_path: Path) -> pd.DataFrame:
    """Load the stored CSV into a pandas DataFrame."""
    return pd.read_csv(csv_path, index_col="datetime", parse_dates=True)


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """Log-transform turbidity, forward-fill missing values, then drop any remaining NaNs."""
    df = df.copy()
    df['turbidity_value'] = np.log1p(df['turbidity_value'])
    df = df.ffill().dropna()
    return df


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


def plot_variables_and_predictions(df: pd.DataFrame, preds: np.ndarray, title: str):
    """Plot turbidity, temperature, pH, and predicted DO in subplots."""
    times = df.index
    fig, axes = plt.subplots(4, 1, figsize=(12, 16), sharex=True)

    # Log-Transformed Turbidity
    axes[0].plot(times, df['turbidity_value'])
    axes[0].set_ylabel('Log Turbidity')
    axes[0].set_title('Log-Transformed Turbidity over Time')
    axes[0].grid(True)

    # Temperature
    axes[1].plot(times, df['temp_value'])
    axes[1].set_ylabel('Temperature')
    axes[1].set_title('Temperature over Time')
    axes[1].grid(True)

    # pH
    axes[2].plot(times, df['pH_value'])
    axes[2].set_ylabel('pH')
    axes[2].set_title('pH over Time')
    axes[2].grid(True)

    # Predicted DO
    axes[3].plot(times, preds, linestyle='--', marker='o', label='Predicted DO')
    axes[3].set_ylabel('Dissolved Oxygen')
    axes[3].set_title(title)
    axes[3].legend()
    axes[3].grid(True)

    plt.tight_layout()
    plt.show()


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

    # Predict
    preds = model.predict(X_test)

    # Plot all variables and predictions
    plot_variables_and_predictions(df_test, preds, 'Predicted Dissolved Oxygen over Time')

    # Save predictions
    out_df = df_test.copy()
    out_df['predicted_dissolved_oxygen_value'] = preds
    out_df.to_csv(data_dir / "arduino_predictions.csv")
    print(f"Saved predictions to {data_dir / 'arduino_predictions.csv'}")

if __name__ == "__main__":
    main()
