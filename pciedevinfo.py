import subprocess
import re
import json
from datetime import datetime

def run_command(cmd):
    try:
        return subprocess.check_output(["sudo"] + cmd, text=True).strip()
    except Exception as e:
        return f"ERROR: {e}"

# Parse lspci -vvv
def parse_lspci_vvv():
    output = run_command(["lspci", "-vvv"])
    devices = []
    current = None
    for line in output.splitlines():
        if re.match(r'^\S.*: ', line):
            if current:
                devices.append(current)
            current = {
                "pci_address": line.split()[0],
                "device_name": line.strip(),
                "bars": []
            }
        elif "Region" in line and current:
            match = re.search(r"(Region \d+: .*?\[size=.*?\])", line)
            if match:
                current["bars"].append(match.group(1))
    if current:
        devices.append(current)
    return devices

# Parse nvme list
def parse_nvme():
    output = run_command(["nvme", "list"])
    devices = []
    for line in output.splitlines()[2:]:
        parts = line.split()
        if len(parts) >= 6:
            devices.append({
                "nvme_device": parts[0],
                "nvme_model": parts[1],
                "nvme_serial": parts[2],
                "nvme_size": parts[4]
            })
    return devices

# Parse lsblk
def parse_lsblk():
    output = run_command(["lsblk", "-o", "NAME,MODEL,SERIAL,SIZE,MOUNTPOINT"])
    devices = []
    for line in output.splitlines()[1:]:
        parts = line.split(None, 4)
        if len(parts) >= 5:
            devices.append({
                "lsblk_name": parts[0],
                "lsblk_model": parts[1],
                "lsblk_serial": parts[2],
                "lsblk_size": parts[3],
                "lsblk_mount": parts[4]
            })
    return devices

# Parse full nvidia-smi GPU info
def parse_nvidia_smi_full():
    fields = [
        "index", "name", "serial", "uuid", "pci.bus_id",
        "memory.total", "driver_version", "vbios_version",
        "compute_capability"
    ]
    cmd = ["nvidia-smi", "--query-gpu=" + ",".join(fields), "--format=csv,noheader,nounits"]
    output = run_command(cmd)
    devices = []
    for line in output.splitlines():
        values = [x.strip() for x in line.split(',')]
        devices.append(dict(zip(fields, values)))
    return devices

# Check IOMMU kernel params and dmesg
def check_iommu_status():
    iommu_info = {"kernel_cmdline": "", "iommu_in_dmesg": ""}
    try:
        with open("/proc/cmdline", "r") as f:
            iommu_info["kernel_cmdline"] = f.read().strip()
    except Exception as e:
        iommu_info["kernel_cmdline"] = f"ERROR: {e}"

    try:
        dmesg_output = run_command(["dmesg"])
        lines = [line for line in dmesg_output.splitlines() if "IOMMU" in line or "iommu" in line]
        iommu_info["iommu_in_dmesg"] = "\n".join(lines)
    except Exception as e:
        iommu_info["iommu_in_dmesg"] = f"ERROR: {e}"

    return iommu_info

# Group data by device type and iommu status
def group_by_type(pci_devices, nvme_devices, blk_devices, gpu_devices, iommu_info):
    return {
        "PCI Devices": pci_devices,
        "NVMe Devices": nvme_devices,
        "Block Devices": blk_devices,
        "GPU Devices": gpu_devices,
        "IOMMU Status": iommu_info
    }

if __name__ == "__main__":
    print("Collecting PCI devices...")
    pci_devices = parse_lspci_vvv()

    print("Collecting NVMe devices...")
    nvme_devices = parse_nvme()

    print("Collecting block devices...")
    blk_devices = parse_lsblk()

    print("Collecting GPU devices...")
    gpu_devices = parse_nvidia_smi_full()

    print("Checking IOMMU status...")
    iommu_info = check_iommu_status()

    print("Grouping all data by device type...")
    grouped_data = group_by_type(pci_devices, nvme_devices, blk_devices, gpu_devices, iommu_info)

    timestamp = datetime.now().strftime("%m%d%H%M%S")
    json_file = f"devinfo_{timestamp}.json"
    with open(json_file, "w") as jf:
        json.dump(grouped_data, jf, indent=4)

    print(f"✅ Device info collection complete. Data saved to: {json_file}")
