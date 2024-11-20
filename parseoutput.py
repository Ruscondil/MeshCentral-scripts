import os
import re
from collections import defaultdict

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
                results['Bandwidth'] = convert_bandwidth(value, unit)

            # Match read bandwidth
            bw_read_match = bandwidth_read_regex.search(line)
            if bw_read_match:
                value, unit = bw_read_match.groups()
                results['BandwidthR'] = convert_bandwidth(value, unit)

            # Match write IOPS
            iops_match = iops_regex.search(line)
            if iops_match:
                results['IOPS'] = float(iops_match.group(1))

            # Match read IOPS
            iops_read_match = iops_read_regex.search(line)
            if iops_read_match:
                results['IOPSR'] = float(iops_read_match.group(1))

            # Match latency
            lat_match = latency_regex.search(line)
            if lat_match:
                results['Latency'] = float(lat_match.group(1))

    return results

def calculate_averages(folders, file_names):
    cumulative_data = {file_name: defaultdict(list) for file_name in file_names}

    for folder in folders:
        for file_name in file_names:
            file_path = os.path.join(folder, file_name)
            if os.path.exists(file_path):
                try:
                    results = parse_fio_results(file_path)
                    for key, value in results.items():
                        cumulative_data[file_name][key].append(value)
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")
            else:
                print(f"File not found: {file_path}")

    averages = {}
    for file_name, metrics in cumulative_data.items():
        averages[file_name] = {
            key: sum(values) / len(values) if values else 0
            for key, values in metrics.items()
        }

    return averages

prepath = './wyniki/fio_results_xfs_nvme/'
folders = [prepath + 'lab-sec-13', prepath + 'lab-sec-14', prepath + 'lab-sec-15', prepath + 'lab-sec-16']
file_names = [
    'fio_archive_test_output.txt',
    'fio_database_test_output.txt',
    'fio_multimedia_test_output.txt',
    'fio_webserver_test_output.txt',
]

averages = calculate_averages(folders, file_names)

# Print averages
for file_name, metrics in averages.items():
    print(f"\nAverages for {file_name}:")
    for metric, avg_value in metrics.items():
        unit = "MiB/s" if "Bandwidth" in metric else "ms" if metric == "Latency" else ""
        print(f"  {metric}: {avg_value:.2f} {unit}")
