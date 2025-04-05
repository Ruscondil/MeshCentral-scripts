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

    with pd.ExcelWriter(output_file) as writer:
        for test, details in test_details.items():
            rows = []
            for fs, devices in resultsdict.items():
                for device, workloads in devices.items():
                    workload_metrics = workloads.get(test.split()[0].lower(), {})
                    row = {
                        "FileSystem": fs.upper(),
                        "Device": device.upper()
                    }
                    # Fill metrics if available
                    row.update({
                        metric: workload_metrics.get(metric, None) for metric in details["metrics"]
                    })
                    rows.append(row)

            # Convert to DataFrame
            df = pd.DataFrame(rows)
            print(df)
            # Pivot the data to create device-specific columns
            metrics = details["metrics"]
            pivoted_data = df.pivot(index="FileSystem", columns="Device", values=metrics)
            pivoted_data.columns = [f"{col[1]} {col[0]}" for col in pivoted_data.columns]  # Flatten MultiIndex
            
            # Reorganize columns to group by device
            devices = df['Device'].unique()  # List of devices (e.g., NVME, SDA)
            devices = sorted([device for device in devices if device in ['HDD', 'SSD', 'NVME']], key=lambda x: ['HDD', 'SSD', 'NVME'].index(x))
            ordered_columns = []
            for device in devices:
                for metric in metrics:
                    ordered_columns.append(f"{device} {metric}")
            
            pivoted_data = pivoted_data[ordered_columns]  # Reorder columns

            # Add test details as a header
            details_df = pd.DataFrame.from_dict(details, orient='index', columns=['Details']).reset_index()
            details_df.rename(columns={"index": "Parameter"}, inplace=True)

            # Write details and results to Excel
            details_df.to_excel(writer, sheet_name=test, index=False, startrow=0)
            pivoted_data.reset_index().to_excel(writer, sheet_name=test, index=False, startrow=len(details_df) + 2)

    print(f"Data saved to {output_file}")



# Main logic
file_names = [
    'fio_database_test_output.txt',
    'fio_multimedia_test_output.txt',
    'fio_webserver_test_output.txt',
    'fio_archive_test_output.txt',
]

resultsdict = extract_values('./wyniki/', file_names)
print(resultsdict['btrfs']['ssd'])
#exit(0)
# Save results to Excel with formatting
#format_and_save_as_excel(resultsdict)
format_and_save_custom_excel(resultsdict)
