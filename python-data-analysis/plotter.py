#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
import threading
import time
import data_scraper
from datetime import timedelta

# Path to the CSV data file
os_dir = os.path.dirname(__file__)
data_file_dir = os.path.join(os_dir, "data")
DATA_FILE = os.path.join(data_file_dir, "arduino_data.csv")

# Update intervals
UPDATE_INTERVAL_MS = 5000  # plot refresh (ms)
SCRAPE_INTERVAL_SEC = UPDATE_INTERVAL_MS / 1000  # scraper sleep (s)

# Default time window (1 day)
time_window = timedelta(days=1)


def read_data():
    """
    Load the Arduino sensor data CSV into a DataFrame,
    parsing the index as datetime.
    """
    df = pd.read_csv(DATA_FILE, index_col="timestamp", parse_dates=True)
    return df


def animate(frame, sensors, axes):
    """
    Animation function: update subplots with current time window,
    and break lines at missing data (NaNs).
    """
    df = read_data()
    if not df.empty:
        now = df.index.max()
        df = df[df.index >= now - time_window]

    for ax, sensor in zip(axes, sensors):
        ax.clear()
        ax.set_title(sensor)
        series = df[sensor]
        # direct plot including NaNs to break at missing points
        ax.plot(series.index, series)
        ax.set_ylabel(sensor)
    axes[-1].set_xlabel("Time")


def scraper_loop():
    """
    Background thread: periodically fetch new data and save to CSV.
    """
    while True:
        df = data_scraper.get_arduino_data()
        data_scraper.save_data(df)
        time.sleep(SCRAPE_INTERVAL_SEC)


def main():
    global time_window
    # Ensure data folder exists
    os.makedirs(data_file_dir, exist_ok=True)

    # Start background scraper thread
    thread = threading.Thread(target=scraper_loop, daemon=True)
    thread.start()

    # Wait until data is available
    print("Waiting for initial data...")
    while True:
        try:
            df = read_data()
            if not df.empty:
                break
        except (FileNotFoundError, pd.errors.EmptyDataError):
            pass
        time.sleep(1)
    print(f"Loaded initial data with {len(df)} records")

    sensors = df.columns.tolist()

    # Create figure and subplots stacked vertically
    fig, axes = plt.subplots(len(sensors), 1, sharex=True, figsize=(10, 8))
    fig.subplots_adjust(top=0.85)
    fig.autofmt_xdate()

    # Add buttons for time window selection
    btn_axes = [fig.add_axes(pos) for pos in ([0.1, 0.92, 0.1, 0.05],
                                              [0.21, 0.92, 0.1, 0.05],
                                              [0.32, 0.92, 0.1, 0.05])]
    btn_1h = Button(btn_axes[0], '1 Hour')
    btn_1d = Button(btn_axes[1], '1 Day')
    btn_1w = Button(btn_axes[2], '1 Week')

    def set_1h(event):
        global time_window
        time_window = timedelta(hours=1)
        animate(None, sensors, axes)
        fig.canvas.draw_idle()

    def set_1d(event):
        global time_window
        time_window = timedelta(days=1)
        animate(None, sensors, axes)
        fig.canvas.draw_idle()

    def set_1w(event):
        global time_window
        time_window = timedelta(weeks=1)
        animate(None, sensors, axes)
        fig.canvas.draw_idle()

    btn_1h.on_clicked(set_1h)
    btn_1d.on_clicked(set_1d)
    btn_1w.on_clicked(set_1w)

    # Set up the animation
    ani = animation.FuncAnimation(
        fig,
        animate,
        fargs=(sensors, axes),
        interval=UPDATE_INTERVAL_MS
    )

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
