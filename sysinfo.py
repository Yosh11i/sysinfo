import psutil
import platform
import socket
from datetime import datetime


def bytes_to_gb(bytes_value):
    return bytes_value / (1024 ** 3)


def get_system_info():
    info_lines = []

    # ヘッダー
    info_lines.append("=" * 60)
    info_lines.append("SYSTEM INFORMATION REPORT")
    info_lines.append("=" * 60)
    info_lines.append(f"Timestamp      : {datetime.now()}")
    info_lines.append(f"OS             : {platform.system()} {platform.release()}")
    info_lines.append(f"Hostname       : {socket.gethostname()}")
    info_lines.append(f"Machine        : {platform.machine()}")
    info_lines.append(f"Processor      : {platform.processor()}")
    info_lines.append("")

    # CPU情報
    info_lines.append("-" * 60)
    info_lines.append("CPU INFORMATION")
    info_lines.append("-" * 60)
    info_lines.append(f"Physical cores : {psutil.cpu_count(logical=False)}")
    info_lines.append(f"Total cores    : {psutil.cpu_count(logical=True)}")
    info_lines.append(f"CPU Usage      : {psutil.cpu_percent(interval=1)} %")
    info_lines.append("")

    # メモリ情報
    mem = psutil.virtual_memory()
    info_lines.append("-" * 60)
    info_lines.append("MEMORY INFORMATION")
    info_lines.append("-" * 60)
    info_lines.append(f"Total     : {bytes_to_gb(mem.total):.2f} GB")
    info_lines.append(f"Available : {bytes_to_gb(mem.available):.2f} GB")
    info_lines.append(f"Used      : {bytes_to_gb(mem.used):.2f} GB")
    info_lines.append(f"Usage     : {mem.percent} %")
    info_lines.append("")

    # ディスク情報
    info_lines.append("-" * 60)
    info_lines.append("DISK INFORMATION")
    info_lines.append("-" * 60)

    partitions = psutil.disk_partitions()
    for partition in partitions:
        info_lines.append(f"Device     : {partition.device}")
        info_lines.append(f"Mountpoint : {partition.mountpoint}")
        info_lines.append(f"File system: {partition.fstype}")

        try:
            usage = psutil.disk_usage(partition.mountpoint)
            info_lines.append(f"  Total  : {bytes_to_gb(usage.total):.2f} GB")
            info_lines.append(f"  Used   : {bytes_to_gb(usage.used):.2f} GB")
            info_lines.append(f"  Free   : {bytes_to_gb(usage.free):.2f} GB")
            info_lines.append(f"  Usage  : {usage.percent} %")
        except PermissionError:
            info_lines.append("  Permission denied")

        info_lines.append("")

    return "\n".join(info_lines)


def save_to_file(content, filename="sysinfolog.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    report = get_system_info()

    print(report)              # 画面表示
    save_to_file(report)       # ファイル保存

    print("\nReport saved to sysinfolog.txt")


