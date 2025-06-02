import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.ndimage import gaussian_filter1d
from matplotlib.colors import LinearSegmentedColormap

df = pd.read_csv(
    os.path.join(os.path.dirname(__file__), 'data', 'arduino_data.csv'),
    parse_dates=['datetime'],   # replace 'datetime' if your column is named otherwise
    index_col='datetime'
)

tds = df['tds_value']   # replace 'turbidity' if needed

sigma = 20  
tds_filtered = gaussian_filter1d(tds.values, sigma=sigma)

vmin = 0
vmax = np.max(tds_filtered) * 1.1   # a bit above your maximum NTU

times = df.index
times_num = mdates.date2num(times)

T = np.linspace(vmin, vmax, 300)
Z = np.tile(T.reshape(-1, 1), (1, len(times)))

XX, YY = np.meshgrid(times_num, T)


fig, ax = plt.subplots(figsize=(12, 6))

ax.minorticks_on()

ax.plot(
    times,
    tds_filtered,
    color='black',
    linewidth=2,
    label='Filtered TDS (ppm)'
)

ax.grid(
    which='major',
    linestyle='-',
    linewidth=0.8,
    color="#0F0D0D1F",      # pure white (or swap to '#F8F8F5' if you want a bit of warmth)
    alpha=0.4
)

#    — Minor grid: dashed white, alpha=0.2, linewidth=0.5
ax.grid(
    which='minor',
    linestyle='-',
    linewidth=0.5,
    color="#1D1A1A1F",      # same white, just more transparent
    alpha=0.2
)

ax.axhline(
    y=500,
    color='red',
    linewidth=1.5,
    linestyle='-',
    alpha=0.7,
    label='Drinking Threshold'
)

ax.set_xlim(times[0], times[-1])
ax.set_ylim(vmin, vmax)

ax.set_title('TDS Over Time')
ax.set_xlabel('Date')
ax.set_ylabel('TDS (ppm)')

# Format x-axis as dates
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d-%Y %H:%M'))
plt.xticks(rotation=45)

ax.legend(loc='upper right')

plt.tight_layout()
plt.show()

