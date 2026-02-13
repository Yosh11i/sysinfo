import psutil
import platform
import socket
import subprocess
import os
from datetime import datetime


# -------------------------------------------------
# Utility Functions
# -------------------------------------------------

def bytes_to_gb(value):
    return value / (1024 ** 3)


def run_command(command):
    """Run system command safely and return output."""
    try:
        result = subprocess.check_output(
            command,
            shell=True,
            stderr=subprocess.DEVNULL
        )
        return result.decode(errors="ignore").strip()
    except Exception:
        return None


# -------------------------------------------------
# OS Info
# -------------------------------------------------

def get_linux_pretty_name():
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME"):
                    return line.split("=")[1].strip().strip('"')
    except:
        return None


def get_os_info():
    system = platform.system()
    info = {
        "os_name": system,
        "release": platform.release(),
        "version": platform.version(),
        "kernel": platform.uname().release
    }

    if system == "Linux":
        pretty = get_linux_pretty_name()
        if pretty:
            info["pretty_name"] = pretty

    return info


# -------------------------------------------------
# H/W Info
# -------------------------------------------------

def get_cpu_model():
    system = platform.system()

    if system == "Linux":
        output = run_command("grep 'model name' /proc/cpuinfo | head -1")
        if output:
            return output.split(":")[1].strip()

    elif system == "Windows":
        output = run_command("wmic cpu get Name")
        if output:
            lines = output.splitlines()
            if len(lines) > 1:
                return lines[1].strip()

    return "Unknown"


def get_disk_info_extended():
    system = platform.system()
    lines = []

    if system == "Linux":
        output = run_command("lsblk -o NAME,MODEL,SIZE,TYPE -d")
        if output:
            lines.append("Device   Model                 Size    Type")
            lines.append("-" * 70)
            for line in output.splitlines()[1:]:
                lines.append(line.strip())

    elif system == "Windows":
        output = run_command("wmic diskdrive get Model,SerialNumber,Size")
        if output:
            lines.append("Model                        SerialNumber        Size")
            lines.append("-" * 80)
            for line in output.splitlines()[1:]:
                if line.strip():
                    lines.append(line.strip())

    if not lines:
        lines.append("Extended disk info not available.")

    return "\n".join(lines)


def get_memory_modules():
    system = platform.system()
    lines = []

    if system == "Linux":
        output = run_command("dmidecode -t memory")
        if output:
            lines.append("Memory module information detected (sudo may be required).")
        else:
            lines.append("Memory module info requires sudo privileges.")

    elif system == "Windows":
        output = run_command("wmic memorychip get Manufacturer,PartNumber,Capacity,Speed")
        if output:
            lines.append("Manufacturer  PartNumber  Capacity  Speed")
            lines.append("-" * 70)
            for line in output.splitlines()[1:]:
                if line.strip():
                    lines.append(line.strip())

    if not lines:
        lines.append("Memory module info not available.")

    return "\n".join(lines)


# -------------------------------------------------
# NUMA Info (Linux Only)
# -------------------------------------------------

def get_numa_info():
    system = platform.system()

    if system != "Linux":
        return "NUMA information not supported on this OS."

    base_path = "/sys/devices/system/node/"

    if not os.path.exists(base_path):
        return "NUMA information not available."

    nodes = [d for d in os.listdir(base_path) if d.startswith("node")]

    if not nodes:
        return "No NUMA nodes detected."

    lines = []

    for node in sorted(nodes):
        meminfo_path = os.path.join(base_path, node, "meminfo")
        cpulist_path = os.path.join(base_path, node, "cpulist")

        lines.append(node.upper())

        # CPU list
        try:
            with open(cpulist_path) as f:
                cpus = f.read().strip()
            lines.append(f"  CPUs        : {cpus}")
        except:
            lines.append("  CPUs        : Unknown")

        # Memory info
        try:
            with open(meminfo_path) as f:
                for line in f:
                    if "MemTotal" in line:
                        total_kb = int(line.split()[3])
                        total_gb = total_kb / (1024 * 1024)
                        lines.append(f"  Total Memory: {total_gb:.2f} GB")
                    if "MemFree" in line:
                        free_kb = int(line.split()[3])
                        free_gb = free_kb / (1024 * 1024)
                        lines.append(f"  Free Memory : {free_gb:.2f} GB")
        except:
            lines.append("  Memory info : Unknown")

        lines.append("")

    return "\n".join(lines)


# -------------------------------------------------
# Main Report Builder
# -------------------------------------------------

def build_report():
    lines = []
    os_info = get_os_info()

    lines.append("=" * 90)
    lines.append("ADVANCED SYSTEM INFORMATION REPORT")
    lines.append("=" * 90)
    lines.append(f"Timestamp      : {datetime.now()}")
    lines.append(f"Hostname       : {socket.gethostname()}")
    lines.append(f"Machine        : {platform.machine()}")

    if "pretty_name" in os_info:
        lines.append(f"OS Pretty Name : {os_info['pretty_name']}")

    lines.append(f"OS Name        : {os_info['os_name']}")
    lines.append(f"OS Release     : {os_info['release']}")
    lines.append(f"OS Version     : {os_info['version']}")
    lines.append(f"Kernel Version : {os_info['kernel']}")
    lines.append(f"CPU Model      : {get_cpu_model()}")
    lines.append("")

    # CPU usage
    lines.append("-" * 90)
    lines.append("CPU STATUS")
    lines.append("-" * 90)
    lines.append(f"Physical cores : {psutil.cpu_count(logical=False)}")
    lines.append(f"Total cores    : {psutil.cpu_count(logical=True)}")
    lines.append(f"CPU usage      : {psutil.cpu_percent(interval=1)} %")
    lines.append("")

    # Memory usage
    mem = psutil.virtual_memory()
    lines.append("-" * 90)
    lines.append("MEMORY STATUS")
    lines.append("-" * 90)
    lines.append(f"Total     : {bytes_to_gb(mem.total):.2f} GB")
    lines.append(f"Available : {bytes_to_gb(mem.available):.2f} GB")
    lines.append(f"Used      : {bytes_to_gb(mem.used):.2f} GB")
    lines.append(f"Usage     : {mem.percent} %")
    lines.append("")

    # Disk usage
    lines.append("-" * 90)
    lines.append("DISK USAGE")
    lines.append("-" * 90)
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            lines.append(f"{part.device} ({part.mountpoint})")
            lines.append(
                f"  Total: {bytes_to_gb(usage.total):.2f} GB | "
                f"Used: {bytes_to_gb(usage.used):.2f} GB | "
                f"Free: {bytes_to_gb(usage.free):.2f} GB | "
                f"Usage: {usage.percent} %"
            )
        except PermissionError:
            continue
    lines.append("")

    # Extended h/w
    lines.append("-" * 90)
    lines.append("EXTENDED DISK HARDWARE INFO")
    lines.append("-" * 90)
    lines.append(get_disk_info_extended())
    lines.append("")

    lines.append("-" * 90)
    lines.append("MEMORY MODULE INFO")
    lines.append("-" * 90)
    lines.append(get_memory_modules())
    lines.append("")

    # NUMA info
    lines.append("-" * 90)
    lines.append("NUMA NODE INFORMATION")
    lines.append("-" * 90)
    lines.append(get_numa_info())
    lines.append("")

    return "\n".join(lines)


def save_report(content, filename="sysinfo.log"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print("Failed to save file:", e)


# -------------------------------------------------
# Entry Point
# -------------------------------------------------

if __name__ == "__main__":
    report = build_report()
    print(report)
    save_report(report)
    print("\nReport saved to sysinfo.log")


