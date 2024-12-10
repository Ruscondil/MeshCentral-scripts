import os
import re
from collections import defaultdict
import glob
import numpy as np 
import matplotlib.pyplot as plt
import pandas as pd

def parse_fio_results(file_path):
    # Regular expressions
    bandwidth_regex = re.compile(r'WRITE: bw=(\d+(?:\.\d+)?)([MK]iB/s)')
    bandwidth_read_regex = re.compile(r'READ: bw=(\d+(?:\.\d+)?)([MK]iB/s)')
    iops_regex = re.compile(r'write: IOPS=(\d+)')
    iops_read_regex = re.compile(r'read: IOPS=(\d+)')
    latency_regex = re.compile(r'lat \([mu]sec\): min=\d+\.?\d*[km]?, max=\d+\.?\d*[km]?, avg=(\d+\.\d+[km]?), stdev=\d+\.?\d*')



    # Function to convert bandwidth to MiB/s
    def convert_bandwidth(value, unit):
        value = float(value)
        if unit == "KiB/s":
            return value / 1024  # Convert KiB/s to MiB/s
        return value  # Already in MiB/s

    results = {}

    with open(file_path, 'r') as file:
        last = 'read'
        for line in file:
            # Match write bandwidth
            if 'write' in line:
                last = 'write'
            elif 'read' in line:
                last = 'read'
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
                if last == 'read':
                    results['Latency READ (ms)'] = float(lat_match.group(1))
                else:
                    results['Latency WRITE (ms)'] = float(lat_match.group(1))


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
                key: {'min': round(min(values),3), 'max':round(max(values),3), 'avg':round(sum(values) / len(values), 2)} if values else '-'
                for key, values in metrics.items()
            }
        resultsdict[filesystem][storage] = ranges
    return resultsdict




file_names = [
    'fio_database_test_output.txt',
    'fio_multimedia_test_output.txt',
    'fio_webserver_test_output.txt',
    'fio_archive_test_output.txt',
]

resultsdict = extract_values('./wyniki/', file_names)


# Function to generate all possible columns
def generate_columns(metrics):
    storage_types = ["HDD", "NVME", "SSD"]
    stats = ["MIN", "MAX", "AVG"]
    columns = ["File System"]
    for storage in storage_types:
        for metric in metrics:
            for stat in stats:
                columns.append(f"{storage} {metric} {stat}")
    return columns


def extract_row_data(data, workload, columns):
    rows = []
    for fs, devices in data.items():
        row = [fs]
        for col in columns[1:]:  # Skip File System 
            if len(col.split()) > 3:
                col = col.split()
                storage, metric, stat = col[0],col[1]+' '+col[2],col[3]
            else:
                storage, metric, stat = col.split(" ", 2)
            if workload == 'database':
                if "Latency" in metric:
                    metric_key = f"{metric} (ms)"
                else:
                    metric_key = f"{metric} (MiB/s)" if "Bandwidth" in metric else metric
            elif workload == 'archive':
                if metric == "Latency":
                    metric_key = "Latency WRITE (ms)"
                else:
                    metric_key = f"{metric} WRITE (MiB/s)" if metric == "Bandwidth" else f"{metric} WRITE"
            else:
                if metric == "Latency":
                    metric_key = "Latency READ (ms)"
                else:
                    metric_key = f"{metric} READ (MiB/s)" if metric == "Bandwidth" else f"{metric} READ"
            # Extract value
            value = "N/A"
            for device_type, workloads in devices.items():
                if device_type.lower() == storage.lower() and workload in workloads:
                    value = workloads[workload].get(metric_key, {}).get(stat.lower(), "N/A")
                    break
            row.append(value)
        rows.append(row)
    return rows



# Workloads to process
workloads = ["database", "multimedia", "webserver", "archive"]

# Generate and display tables for each workload
for workload in workloads:
    if workload == "database":
        columns = generate_columns(["Bandwidth WRITE", "Bandwidth READ", "IOPS WRITE", "IOPS READ","Latency WRITE","Latency READ"])
    else:
        columns = generate_columns(["Bandwidth", "IOPS", "Latency"])
    rows = extract_row_data(resultsdict, workload, columns)
    df = pd.DataFrame(rows, columns=columns)
    display(df.style.set_caption(f"Performance Metrics: {workload.capitalize()}").format(precision=3))