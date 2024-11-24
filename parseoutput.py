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
    latency_regex = re.compile(r'avg=(\d+\.\d+), stdev=.*')

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


def calculate_averages(resultsfolder, file_names):
    resultsdict = {'ext4': {}, 'zfs': {}, 'xfs': {}, 'btrfs': {}}
    cumulative_data = {file_name.split('_')[1]: defaultdict(list) for file_name in file_names}
    prepaths = [folder for folder in glob.glob(resultsfolder + '*/')]
    for prepath in prepaths:
        filesystem = prepath.split('/')[-2].split('_')[2]
        storage = prepath.split('/')[-2].split('_')[3]
        folders = [folder for folder in glob.glob(prepath + '*/')]
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

        averages = {}
        for file_name, metrics in cumulative_data.items():
            averages[file_name] = {
                key: round(sum(values) / len(values),2) if values else 0
                for key, values in metrics.items()
            }
        resultsdict[filesystem][storage] = averages
    return resultsdict


file_names = [
    'fio_database_test_output.txt',
    'fio_multimedia_test_output.txt',
    'fio_webserver_test_output.txt',
    'fio_archive_test_output.txt',
]

resultsdict = calculate_averages('./wyniki/', file_names)
print(resultsdict)
for filesystem, storage in resultsdict.items():
    print('\n------------------------------------------------------\n')
    print(filesystem.upper(), end='\n******\n')
    for storage, averages in storage.items():
        print()
        print('>>>>>>',storage.upper(), end=' <<<<<<<\n\n')
        for file_name, metrics in averages.items():
            print(file_name+':')
            for metric, avg_value in metrics.items():
                unit = "MiB/s" if "Bandwidth" in metric else "ms" if metric == "Latency" else ""
                print(f"  {metric}: {avg_value:.2f} {unit}")

# Flatten the nested dictionary into a DataFrame
rows = []
for fs, devices in resultsdict.items():
    for device, workloads in devices.items():
        for workload, metrics in workloads.items():
            row = {'FileSystem': fs, 'Device': device, 'Workload': workload}
            row.update(metrics)  # Add the metric values
            rows.append(row)

# Create a pandas DataFrame
df = pd.DataFrame(rows)

# Save to Excel
df.to_excel('output.xlsx', index=False)