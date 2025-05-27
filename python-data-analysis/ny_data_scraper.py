import os
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse
import argparse

DATE = datetime.now().strftime("%Y-%m-%d")
TIME = datetime.now().strftime("%H:%M:%S")

DATA_DIR  = os.path.join(os.path.dirname(__file__), "data")


def is_url(path):
    """Simple check for http(s) URLs."""
    try:
        scheme = urlparse(path).scheme
        return scheme in ('http', 'https')
    except:
        return False


def read_and_select_tab_file(source, value_column_name):
    """
    Reads either:
      • a local TSV with no header (6 cols: agency, site, datetime, tz, value, approved)
      • a USGS RDB URL (skips '#' lines, reads real header, picks the 5th column as value)
    Returns a DF with columns ['datetime', value_column_name], dropping any 'Eqp' readings used for equipment failures.
    """
    if is_url(source):
        df = pd.read_csv(source, sep='\t', comment='#', header=0, dtype=str)
        cols = df.columns.tolist()
        if len(cols) < 5:
            raise ValueError(f"Expected at least 5 columns in RDB source, got {cols!r}")
        val_col = cols[4]
        out = df[['datetime', val_col]].copy()
        out.rename(columns={val_col: value_column_name}, inplace=True)
    else:
        headers = ['agency_cd', 'site_no', 'datetime', 'tz_cd', 'value', 'approved']
        df = pd.read_csv(source, delimiter='\t', header=None, names=headers, dtype=str)
        out = df[['datetime', 'value']].copy()
        out.rename(columns={'value': value_column_name}, inplace=True)

    # Drop equipment-failure markers ('Eqp') entirely
    out = out[out[value_column_name] != 'Eqp']

    return out


def merge_dataframes_by_datetime(dfs):
    """Merges on 'datetime' with an outer join, sorts, resets index."""
    merged = dfs[0]
    for df in dfs[1:]:
        merged = pd.merge(merged, df, on='datetime', how='outer')
    return merged.sort_values('datetime').reset_index(drop=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Format raw USGS data for modeling")
    parser.add_argument('--mode', '-m',
        type=str,
        default='regular',
        choices=['regular', 'refresh'],
        help="Would you like to refresh all data files?"
    )
    parser.add_argument(
        '--river', '-r',
        dest='stream_name',
        default='hammer_creek',
        type=str,
        choices=['mohawk', 'sandy_creek', 'norwalk', 'hammer_creek'],
        help="Stream name to process (mohawk, sandy_creek, norwalk, hammer_creek)"
    )
    args = parser.parse_args()

    sources = {
        'mohawk': [
            (f"https://nwis.waterservices.usgs.gov/nwis/iv/?sites=01355475&agencyCd=USGS&startDT=2024-04-28T19:11:40.120-04:00&endDT={DATE}T{TIME}.120-04:00&parameterCd=63680&format=rdb", 'turbidity_value'),
            (f"https://nwis.waterservices.usgs.gov/nwis/iv/?sites=01355475&agencyCd=USGS&startDT=2024-04-28T19:19:22.139-04:00&endDT={DATE}T{TIME}.139-04:00&parameterCd=00010&format=rdb", 'temp_value'),
            (f"https://nwis.waterservices.usgs.gov/nwis/iv/?sites=01355475&agencyCd=USGS&startDT=2024-04-28T19:19:47.100-04:00&endDT={DATE}T{TIME}.100-04:00&parameterCd=00300&format=rdb", 'dissolved_oxygen_value'),
            (f"https://waterservices.usgs.gov/nwis/iv/?sites=01355475&agencyCd=USGS&startDT=2025-03-29T23:29:19.024-04:00&endDT={DATE}T{TIME}.024-04:00&parameterCd=00400&format=rdb", 'pH_value')
        ],
        'sandy_creek': [
            (f"https://waterservices.usgs.gov/nwis/iv/?sites=04220223&agencyCd=USGS&startDT=2025-03-29T21:38:27.027-04:00&endDT={DATE}T{TIME}.027-04:00&parameterCd=63680&format=rdb", 'turbidity_value'),
            (f"https://waterservices.usgs.gov/nwis/iv/?sites=04220223&agencyCd=USGS&startDT=2025-03-29T21:38:02.604-04:00&endDT={DATE}T{TIME}.604-04:00&parameterCd=00010&format=rdb", 'temp_value'),
            (f"https://waterservices.usgs.gov/nwis/iv/?sites=04220223&agencyCd=USGS&startDT=2025-03-29T21:37:14.410-04:00&endDT={DATE}T{TIME}.410-04:00&parameterCd=00300&format=rdb", 'dissolved_oxygen_value')
        ],
        'norwalk': [
            (f"https://nwis.waterservices.usgs.gov/nwis/iv/?sites=410606073245700&agencyCd=USGS&startDT=2024-04-28T22:59:54.902-04:00&endDT={DATE}T{TIME}.902-04:00&parameterCd=63680&format=rdb", 'turbidity_value'),
            (f"https://nwis.waterservices.usgs.gov/nwis/iv/?sites=410606073245700&agencyCd=USGS&startDT=2024-04-28T23:00:46.571-04:00&endDT={DATE}T{TIME}.571-04:00&parameterCd=00010&format=rdb", 'temp_value'),
            (f"https://nwis.waterservices.usgs.gov/nwis/iv/?sites=410606073245700&agencyCd=USGS&startDT=2024-04-28T23:01:50.407-04:00&endDT={DATE}T{TIME}.407-04:00&parameterCd=00300&format=rdb", 'dissolved_oxygen_value'),
            (f"https://nwis.waterservices.usgs.gov/nwis/iv/?sites=410606073245700&agencyCd=USGS&startDT=2024-04-28T22:59:09.940-04:00&endDT={DATE}T{TIME}.940-04:00&parameterCd=00400&format=rdb", 'pH_value')
        ],
        'hammer_creek': [
            (f"https://nwis.waterservices.usgs.gov/nwis/iv/?sites=01576381&agencyCd=USGS&startDT=2024-04-29T14:09:31.197-04:00&endDT={DATE}T{TIME}.197-04:00&parameterCd=63680&format=rdb", 'turbidity_value'),
            (f"https://nwis.waterservices.usgs.gov/nwis/iv/?sites=01576381&agencyCd=USGS&startDT=2024-04-29T14:10:02.494-04:00&endDT={DATE}T{TIME}.494-04:00&parameterCd=00010&format=rdb", 'temp_value'),
            (f"https://nwis.waterservices.usgs.gov/nwis/iv/?sites=01576381&agencyCd=USGS&startDT=2024-04-29T14:10:28.087-04:00&endDT={DATE}T{TIME}.087-04:00&parameterCd=00300&format=rdb", 'dissolved_oxygen_value'),
            (f"https://nwis.waterservices.usgs.gov/nwis/iv/?sites=01576381&agencyCd=USGS&startDT=2024-04-29T14:10:48.591-04:00&endDT={DATE}T{TIME}.591-04:00&parameterCd=00400&format=rdb", 'pH_value')
        ]
    }

    if args.mode == 'refresh':
        files = ['mohawk', 'sandy_creek', 'norwalk', 'hammer_creek']
    else:
        files = [args.stream_name]

    for stream_name in files:
        dfs = [read_and_select_tab_file(url, col) for url, col in sources[stream_name]]
        merged_df = merge_dataframes_by_datetime(dfs).iloc[:-1]
        merged_df['datetime'] = pd.to_datetime(merged_df['datetime'])
        merged_df = merged_df.sort_values('datetime').reset_index(drop=True)

        os.makedirs(DATA_DIR, exist_ok=True)
        output_file = os.path.join(DATA_DIR, f"{stream_name}_data.csv")
        try:
            os.remove(output_file)
        except OSError:
            pass

        merged_df.to_csv(output_file, index=False)
        print(f"Saved merged data to {output_file} ({len(merged_df)} rows)")
