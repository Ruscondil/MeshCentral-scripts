import os
import re
from collections import defaultdict

def parse_fio_results(file_path):
    # TODO fix, float numbers
    bandwidth_regex = re.compile(r'WRITE: bw=(\d+MiB/s)')
    bandwidth_read_regex = re.compile(r'READ: bw=(\d+MiB/s)')
    iops_regex = re.compile(r'write: IOPS=(\d+)')
    iops_read_regex = re.compile(r'read: IOPS=(\d+)')
    latency_regex = re.compile(r'avg=(\d+\.\d+), stdev=.*')


    results = {}

    with open(file_path, 'r') as file:
        if 'archive' in file_path:
            for line in file:
                bw_match = bandwidth_regex.search(line)
                iops_match = iops_regex.search(line)
                lat_match = latency_regex.search(line)
            
                if bw_match:
                    results['Bandwidth'] = int(bw_match.group(1).replace('MiB/s', ''))
                if iops_match:
                    results['IOPS'] = int(iops_match.group(1))
                if lat_match:
                    results['Latency'] = float(lat_match.group(1))
        elif 'database' in file_path:
                for line in file:
                    bw_write_match = bandwidth_regex.search(line)
                    bw_read_match = bandwidth_read_regex.search(line)
                    iops_write_match = iops_regex.search(line)
                    iops_read_match = iops_read_regex.search(line)
                    lat_match = latency_regex.search(line)
                    if bw_write_match:
                        results['Bandwidth'] = int(bw_write_match.group(1).replace('MiB/s', ''))
                    if bw_read_match:
                        results['BandwidthR'] = int(bw_read_match.group(1).replace('MiB/s', ''))
                        print(results['BandwidthR'])
                    if iops_write_match:
                        results['IOPS'] = int(iops_write_match.group(1))
                    if iops_read_match:
                        results['IOPSR'] = int(iops_read_match.group(1))
                    if lat_match:
                        results['Latency'] = float(lat_match.group(1))
        elif 'webserver' in file_path:
                for line in file:
                    bw_write_match = bandwidth_regex.search(line)
                    bw_read_match = bandwidth_read_regex.search(line)
                    iops_write_match = iops_regex.search(line)
                    iops_read_match = iops_read_regex.search(line)
                    lat_match = latency_regex.search(line)
                    
                    if bw_write_match:
                        results['Bandwidth'] = int(bw_write_match.group(1).replace('MiB/s', ''))
                    if bw_read_match:
                        results['BandwidthR'] = int(bw_read_match.group(1).replace('MiB/s', ''))
                    if iops_write_match:
                        results['IOPS'] = int(iops_write_match.group(1))
                    if iops_read_match:
                        results['IOPSR'] = int(iops_read_match.group(1))
                    if lat_match:
                        results['Latency'] = float(lat_match.group(1))
        elif 'multimedia' in file_path:
                for line in file:
                    bw_read_match = bandwidth_read_regex.search(line)
                    iops_read_match = iops_read_regex.search(line)
                    lat_match = latency_regex.search(line)
                    
                    if bw_read_match:
                        results['BandwidthR'] = int(bw_read_match.group(1).replace('MiB/s', ''))
                    if iops_read_match:
                        results['IOPSR'] = int(iops_read_match.group(1))
                    if lat_match:
                        results['Latency'] = float(lat_match.group(1))
        else:
            print("FDGDF")
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


prepath = './wyniki/fio_results_zfs_nvme/'
folders = [prepath+'lab-sec-5', prepath+'lab-sec-6', prepath+'lab-sec-7']  
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
