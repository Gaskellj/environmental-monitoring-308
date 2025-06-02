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

turbidity = df['turbidity_value']   # replace 'turbidity' if needed


sigma = 20  
turbidity_filtered = gaussian_filter1d(turbidity.values, sigma=sigma)


vmin = 0
vmax = np.max(turbidity_filtered) * 1.1   # a bit above your maximum NTU

cmap = LinearSegmentedColormap.from_list(
    'water_turbidity',
    [
        (0.00, '#F8F8F5'),  # 0 NTU: pure white (very clear)
        (0.1, '#F2EFE6'),  # low turbidity: very pale tan/cream
        (0.18, '#C3C090'),  # mid turbidity: light olive‐tan
        (0.4, "#62523E"),  # higher turbidity: medium brown
        (0.8, "#42301A"),
        (1.00, "#36261F"),  # very high turbidity: deep, rich brown
    ]
)


times = df.index
times_num = mdates.date2num(times)

T = np.linspace(vmin, vmax, 300)
Z = np.tile(T.reshape(-1, 1), (1, len(times)))

XX, YY = np.meshgrid(times_num, T)


fig, ax = plt.subplots(figsize=(12, 6))

pcm = ax.pcolormesh(
    XX,
    YY,
    Z,
    shading='auto',
    cmap=cmap,
    norm=plt.Normalize(vmin=vmin, vmax=vmax)
)

ax.minorticks_on()

ax.plot(
    times,
    turbidity_filtered,
    color='black',
    linewidth=2,
    label='Filtered Turbidity (NTU)'
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
    y=5,
    color='red',
    linewidth=1.5,
    linestyle='-',
    alpha=0.7,
    label='Drinking Threshold'
)

ax.axhline(
    y=100,
    color='blue',
    linewidth=1.5,
    linestyle='-',
    alpha=0.7,
    label='Aquatic Life Threshold'
)

# e) Formatting axes, labels, and title
ax.set_xlim(times[0], times[-1])
ax.set_ylim(vmin, vmax)

ax.set_title('Turbidity Over Time')
ax.set_xlabel('Date')
ax.set_ylabel('Turbidity (NTU)')

# Format x-axis as dates
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d-%Y %H:%M'))
plt.xticks(rotation=45)

ax.legend(loc='upper right')

plt.tight_layout()
plt.show()