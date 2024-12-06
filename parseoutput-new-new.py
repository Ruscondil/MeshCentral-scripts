import os
import re
from collections import defaultdict
import glob
import pandas as pd

def parse_fio_results(file_path):
    # Regular expressions
    bandwidth_regex = re.compile(r'WRITE: bw=(\d+(?:\.\d+)?)([MK]iB/s)')
    bandwidth_read_regex = re.compile(r'READ: bw=(\d+(?:\.\d+)?)([MK]iB/s)')
    iops_regex = re.compile(r'write: IOPS=(\d+)')
    iops_read_regex = re.compile(r'read: IOPS=(\d+)')
    latency_regex = re.compile(r'lat \(msec\): min=\d+, max=\d+, avg=(\d+\.\d+), stdev=\d+\.\d+')


    # Function to convert bandwidth to MiB/s
    def convert_bandwidth(value, unit):
        value = float(value)
        if unit == "KiB/s":
            return value / 1024  # Convert KiB/s to MiB/s
        return value  # Already in MiB/s

    results = {}

    with open(file_path, 'r') as file:
        for line in file:
            # Match write bandwidth
            bw_match = bandwidth_regex.search(line)
            if bw_match:
                value, unit = bw_match.groups()
                results['Bandwidth WRITE (MiB/s)'] = convert_bandwidth(value, unit)

            # Match read bandwidth
            bw_read_match = bandwidth_read_regex.search(line)
            if bw_read_match:
                value, unit = bw_read_match.groups()
                results['Bandwidth READ (MiB/s)'] = convert_bandwidth(value, unit)

            # Match write IOPS
            iops_match = iops_regex.search(line)
            if iops_match:
                results['IOPS WRITE'] = float(iops_match.group(1))

            # Match read IOPS
            iops_read_match = iops_read_regex.search(line)
            if iops_read_match:
                results['IOPS READ'] = float(iops_read_match.group(1))

            # Match latency
            lat_match = latency_regex.search(line)
            if lat_match:
                results['Latency (ms)'] = float(lat_match.group(1))

    return results


def extract_values(resultsfolder, file_names):
    resultsdict = {'ext4': {}, 'zfs': {}, 'xfs': {}, 'btrfs': {}, 'f2fs': {}}
    cumulative_data = {file_name.split('_')[1]: defaultdict(list) for file_name in file_names}
    prepaths = [folder for folder in glob.glob(resultsfolder + '*/')]
    for prepath in prepaths:
        filesystem = prepath.split('/')[-2].split('_')[2]
        storage = prepath.split('/')[-2].split('_')[3]
        folders = [folder for folder in glob.glob(prepath + '*/')]
        cumulative_data = {file_name.split('_')[1]: defaultdict(list) for file_name in file_names}
        for folder in folders:
            for file_name in file_names:
                file_path = os.path.join(folder, file_name)
                if os.path.exists(file_path):
                    try:
                        results = parse_fio_results(file_path)
                        for key, value in results.items():
                            cumulative_data[file_name.split('_')[1]][key].append(value)
                    except Exception as e:
                        print(f"Error parsing {file_path}: {e}")
                else:
                    print(f"File not found: {file_path}")

        ranges = {}
        for file_name, metrics in cumulative_data.items():
            ranges[file_name] = {
                key: {'min': str(min(values)), 'max':str(max(values)), 'avg':round(sum(values) / len(values), 2)} if values else '-'
                for key, values in metrics.items()
            }
        resultsdict[filesystem][storage] = ranges
    return resultsdict


def format_and_save_as_excel(resultsdict, output_file='output.xlsx'):
    # Prepare rows for formatting
    rows = []
    for fs, devices in resultsdict.items():
        for device, workloads in devices.items():
            for workload, metrics in workloads.items():
                row = {
                    'FileSystem': fs.upper(),
                    'Device': device.upper(),
                    'Workload': workload.capitalize(),
                }
                row.update(metrics)
                rows.append(row)

    # Convert to DataFrame
    df = pd.DataFrame(rows)

    # Pivot to match the table layout example
    formatted_table = df.pivot_table(
        index=['FileSystem', 'Device', 'Workload'],
        values=[
            'Bandwidth READ (MiB/s)', 'Bandwidth WRITE (MiB/s)',
            'IOPS READ', 'IOPS WRITE', 'Latency (ms)'
        ],
        aggfunc='mean'
    )

    # Save to Excel
    with pd.ExcelWriter(output_file) as writer:
        formatted_table.to_excel(writer, sheet_name='Summary')

    print(f"Data saved to {output_file}")


import pandas as pd

import pandas as pd

import pandas as pd

def format_and_save_custom_excel(resultsdict, output_file='formatted_output.xlsx'):
    # Test details
    test_details = {
        "DATABASE TEST": {
            "rw type": "random read write",
            "reads percentage": "70%",
            "numjobs": 8,
            "runtime": "60s",
            "io queue size": 16,
            "blocksize": "80% - 4k\n20% - 8k",
            "metrics": ["Bandwidth READ (MiB/s)", "Bandwidth WRITE (MiB/s)", "IOPS READ", "IOPS WRITE", "Latency (ms)"]
        },
        "MULTIMEDIA TEST": {
            "rw type": "sequential read",
            "numjobs": 4,
            "runtime": "120s",
            "io queue size": 64,
            "blocksize": "128k",
            "metrics": ["Bandwidth READ (MiB/s)", "IOPS READ", "Latency (ms)"]
        },
        "WEBSERVER TEST": {
            "rw type": "random read",
            "numjobs": 16,
            "runtime": "120s",
            "io queue size": 32,
            "blocksize": "90% - 4k\n10% - 8k",
            "metrics": ["Bandwidth READ (MiB/s)", "IOPS READ", "Latency (ms)"]
        },
        "ARCHIVE TEST": {
            "rw type": "sequential write",
            "numjobs": 2,
            "runtime": "180s",
            "io queue size": 128,
            "blocksize": "70% - 64k\n30% - 128k",
            "metrics": ["Bandwidth WRITE (MiB/s)", "IOPS WRITE", "Latency (ms)"]
        },
    }

    rows = []

    # Process results
    for fs, devices in resultsdict.items():
        for device, workloads in devices.items():
            # Iterate over test types to capture the relevant metrics for each
            for test_type, test_config in test_details.items():
                # Access the metrics for the current test
                metrics = test_config.get("metrics", [])
                # Process each metric for the current test
                for metric in metrics:
                    # Check if the metric exists within the current test's workloads
                    test_key = test_type.split()[0].lower()
                    if metric in workloads.get(test_key, {}):
                        # Extract the metric data (min, max, avg)
                        workload = workloads[test_key][metric]
                        row = {
                            "FileSystem": fs,
                            "Device": device,
                            "Test Type": test_type,
                            f"{device} AVG {metric}": workload.get('avg', None),
                            f"{device} MIN {metric}": workload.get('min', None),
                            f"{device} MAX {metric}": workload.get('max', None)
                        }
                        rows.append(row)

    # Check if rows are correctly populated
    if not rows:
        print("No data to save. The rows list is empty.")
        return

    # Create a DataFrame from the rows
    df = pd.DataFrame(rows)

    # Ensure 'FileSystem' is in the DataFrame
    if 'FileSystem' not in df.columns:
        print("Error: 'FileSystem' column is missing in the DataFrame.")
        print("Columns available: ", df.columns)
        return

    # Pivot the DataFrame so that FileSystem and Test Type are the index and columns are properly named
    df_pivoted = df.pivot_table(index=["FileSystem", "Test Type"], columns=["Device"], aggfunc="first")

    # Flatten the column multi-index
    df_pivoted.columns = [f"{device} {metric}" for metric, device in df_pivoted.columns]

    # Write to Excel
    with pd.ExcelWriter(output_file) as writer:
        df_pivoted.to_excel(writer, sheet_name="Results")

    print(f"Data saved to {output_file}")




# Main logic
file_names = [
    'fio_database_test_output.txt',
    'fio_multimedia_test_output.txt',
    'fio_webserver_test_output.txt',
    'fio_archive_test_output.txt',
]

resultsdict = extract_values('./wyniki/', file_names)

# Save results to Excel with formatting
#format_and_save_as_excel(resultsdict)
format_and_save_custom_excel(resultsdict)
