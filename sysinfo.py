import platform
import socket
import psutil
import os
import subprocess
from datetime import datetime


# -------------------------------------------------
# Basic System Information
# -------------------------------------------------

def get_basic_info():
    return {
        "Hostname": socket.gethostname(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
        "Architecture": platform.architecture()[0],
        "OS": platform.system(),
        "OS Version": platform.version(),
        "Kernel Version": platform.release()
    }


# -------------------------------------------------
# CPU Information (Advanced)
# -------------------------------------------------

def get_cpu_info():
    info = {}
    info["Physical Cores"] = psutil.cpu_count(logical=False)
    info["Logical Threads"] = psutil.cpu_count(logical=True)
    info["CPU Usage (%)"] = psutil.cpu_percent(interval=1)

    system = platform.system()

    try:
        if system == "Linux":
            output = subprocess.check_output("lscpu", shell=True).decode()
            for line in output.split("\n"):
                if "Model name" in line:
                    info["Model"] = line.split(":")[1].strip()
                if "Socket(s)" in line:
                    info["Sockets"] = line.split(":")[1].strip()

        elif system == "Windows":
            output = subprocess.check_output(
                "wmic cpu get Name,NumberOfCores,NumberOfLogicalProcessors /format:list",
                shell=True
            ).decode(errors="ignore")

            for line in output.split("\n"):
                if "Name=" in line:
                    info["Model"] = line.split("=")[1].strip()

    except:
        info["Model"] = "Unable to detect"

    return info


# -------------------------------------------------
# Memory Information
# -------------------------------------------------

def get_memory_info():
    vm = psutil.virtual_memory()

    info = {
        "Total (GB)": round(vm.total / (1024**3), 2),
        "Available (GB)": round(vm.available / (1024**3), 2),
        "Used (GB)": round(vm.used / (1024**3), 2),
        "Usage (%)": vm.percent
    }

    system = platform.system()

    try:
        if system == "Linux":
            output = subprocess.check_output("dmidecode -t memory", shell=True).decode(errors="ignore")
            for line in output.split("\n"):
                if "Part Number:" in line and "Unknown" not in line:
                    info["Part Number"] = line.split(":")[1].strip()
                if "Speed:" in line and "Unknown" not in line:
                    info["Speed"] = line.split(":")[1].strip()

        elif system == "Windows":
            output = subprocess.check_output(
                "wmic memorychip get PartNumber,Capacity,Speed /format:list",
                shell=True
            ).decode(errors="ignore")

            for line in output.split("\n"):
                if "PartNumber=" in line and line.strip():
                    info["Part Number"] = line.split("=")[1].strip()
                if "Speed=" in line and line.strip():
                    info["Speed"] = line.split("=")[1].strip()

    except:
        pass

    return info


# -------------------------------------------------
# Disk Information
# -------------------------------------------------

def get_disk_info():
    disks = []
    system = platform.system()

    try:
        if system == "Linux":
            output = subprocess.check_output(
                "lsblk -d -o NAME,MODEL,SIZE,ROTA", shell=True
            ).decode()

            lines = output.strip().split("\n")[1:]

            for line in lines:
                parts = line.split()
                if len(parts) >= 4:
                    disks.append({
                        "Device": parts[0],
                        "Model": parts[1],
                        "Size": parts[2],
                        "Type": "SSD" if parts[3] == "0" else "HDD"
                    })

        elif system == "Windows":
            output = subprocess.check_output(
                "wmic diskdrive get Model,Size,MediaType /format:list",
                shell=True
            ).decode(errors="ignore")

            disk = {}
            for line in output.split("\n"):
                if "Model=" in line:
                    disk["Model"] = line.split("=")[1].strip()
                if "Size=" in line and line.strip():
                    size = int(line.split("=")[1])
                    disk["Size (GB)"] = round(size / (1024**3), 2)
                if "MediaType=" in line:
                    disk["Type"] = line.split("=")[1].strip()
                    disks.append(disk)
                    disk = {}

    except:
        disks.append({"Error": "Unable to detect disk info"})

    return disks


# -------------------------------------------------
# NUMA Node Information (Linux Only)
# -------------------------------------------------

def get_numa_info():
    system = platform.system()

    if system != "Linux":
        return "NUMA information not supported on this OS."

    base_path = "/sys/devices/system/node/"

    if not os.path.exists(base_path):
        return "NUMA information not available."

    nodes = sorted([d for d in os.listdir(base_path) if d.startswith("node")])

    if not nodes:
        return "No NUMA nodes detected."

    lines = []

    for node in nodes:
        node_path = os.path.join(base_path, node)

        try:
            with open(os.path.join(node_path, "cpulist")) as f:
                cpus = f.read().strip()

            meminfo_path = os.path.join(node_path, "meminfo")
            total_mem = "Unknown"
            free_mem = "Unknown"

            if os.path.exists(meminfo_path):
                with open(meminfo_path) as f:
                    for line in f:
                        if "MemTotal" in line:
                            total_mem = round(int(line.split()[3]) / 1024, 2)
                        if "MemFree" in line:
                            free_mem = round(int(line.split()[3]) / 1024, 2)

            lines.append(f"{node.upper()}")
            lines.append(f"  CPUs        : {cpus}")
            lines.append(f"  Total Memory: {total_mem} MB")
            lines.append(f"  Free Memory : {free_mem} MB")
            lines.append("")

        except:
            lines.append(f"{node.upper()} : Unable to read information")

    return "\n".join(lines)


# -------------------------------------------------
# NUMA Distance Matrix (Linux Only)
# -------------------------------------------------

def get_numa_distance():
    system = platform.system()

    if system != "Linux":
        return "NUMA distance not supported on this OS."

    base_path = "/sys/devices/system/node/"

    if not os.path.exists(base_path):
        return "NUMA information not available."

    nodes = sorted([d for d in os.listdir(base_path) if d.startswith("node")])

    if not nodes:
        return "No NUMA nodes detected."

    lines = []
    lines.append("NUMA DISTANCE MATRIX")
    lines.append("-" * 60)

    header = "       " + "  ".join(n.upper() for n in nodes)
    lines.append(header)

    for node in nodes:
        distance_path = os.path.join(base_path, node, "distance")
        try:
            with open(distance_path) as f:
                distances = f.read().strip().split()
            row = f"{node.upper():6}  " + "  ".join(distances)
            lines.append(row)
        except:
            lines.append(f"{node.upper():6}  Unable to read")

    return "\n".join(lines)


# -------------------------------------------------
# Report Builder
# -------------------------------------------------

def build_report():
    lines = []
    lines.append("=" * 90)
    lines.append("SYSTEM INFORMATION REPORT")
    lines.append("=" * 90)
    lines.append(f"Generated: {datetime.now()}")
    lines.append("")

    # Basic
    basic = get_basic_info()
    for k, v in basic.items():
        lines.append(f"{k:20}: {v}")
    lines.append("")

    # CPU
    lines.append("-" * 90)
    lines.append("CPU INFORMATION")
    lines.append("-" * 90)
    for k, v in get_cpu_info().items():
        lines.append(f"{k:20}: {v}")
    lines.append("")

    # Memory
    lines.append("-" * 90)
    lines.append("MEMORY INFORMATION")
    lines.append("-" * 90)
    for k, v in get_memory_info().items():
        lines.append(f"{k:20}: {v}")
    lines.append("")

    # Disk
    lines.append("-" * 90)
    lines.append("DISK INFORMATION")
    lines.append("-" * 90)
    for disk in get_disk_info():
        for k, v in disk.items():
            lines.append(f"{k:20}: {v}")
        lines.append("")

    # NUMA Nodes
    lines.append("-" * 90)
    lines.append("NUMA NODE INFORMATION")
    lines.append("-" * 90)
    lines.append(get_numa_info())
    lines.append("")

    # NUMA Distance
    lines.append("-" * 90)
    lines.append("NUMA DISTANCE INFORMATION")
    lines.append("-" * 90)
    lines.append(get_numa_distance())
    lines.append("")

    return "\n".join(lines)


# -------------------------------------------------
# Main
# -------------------------------------------------

if __name__ == "__main__":
    report = build_report()

    print(report)

    with open("sysinfolog.txt", "w") as f:
        f.write(report)

    print("\nSaved to sysinfolog.txt")


