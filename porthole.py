import sys
import subprocess
import re
import socket


def ip_to_int(ip):
    return sum(int(part) << (8 * (3 - i)) for i, part in enumerate(ip.split(".")))


def int_to_ip(ip_int):
    return ".".join(str((ip_int >> (8 * (3 - i))) & 255) for i in range(4))


def parse_cidr(cidr):
    try:
        ip_part, prefix = cidr.split("/")
        prefix = int(prefix)
        if not (0 <= prefix <= 32):
            raise ValueError
    except:
        raise ValueError("Invalid CIDR format")

    base_ip = ip_to_int(ip_part)
    total_ips = 2 ** (32 - prefix)

    return base_ip, total_ips


def parse_ports(port_string):
    ports = set()

    if "-" in port_string:
        start, end = port_string.split("-")
        for p in range(int(start), int(end) + 1):
            ports.add(p)

    elif "," in port_string:
        for p in port_string.split(","):
            ports.add(int(p.strip()))

    else:
        ports.add(int(port_string))

    return sorted(ports)


def ping_host(ip):
    command = ["ping", "-c", "1", "-W", "1", ip]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode == 0:
            time_match = re.search(r'time[=<]\s?(\d+\.?\d*)', result.stdout)
            if time_match:
                return "UP", f"{time_match.group(1)} ms", None
            return "UP", "Unknown", None
        else:
            return "DOWN", None, result.stderr.strip()

    except Exception as e:
        return "ERROR", None, str(e)


def scan_ports(ip, ports):
    open_ports = []

    for port in ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((ip, port))
                if result == 0:
                    open_ports.append(port)
        except:
            continue

    return open_ports


def main():
    if len(sys.argv) != 4 or sys.argv[1] != "-p":
        print("Error: Too many or too few arguments")
        print("Usage: python3 porthole.py -p <ports> <CIDR>")
        print("Example:")
        print("python3 porthole.py -p 80 192.168.1.0/24")
        print("python3 porthole.py -p 1-100 192.168.1.0/24")
        print("python3 porthole.py -p 80,443,3306 192.168.1.0/24")
        sys.exit(1)

    port_argument = sys.argv[2]
    cidr_argument = sys.argv[3]

    try:
        ports = parse_ports(port_argument)
    except:
        print("Invalid port format")
        sys.exit(1)

    try:
        base_ip, total_ips = parse_cidr(cidr_argument)
    except ValueError as e:
        print(e)
        sys.exit(1)

    print("\nStarting scan...\n")

    for i in range(1, total_ips - 1):
        ip = int_to_ip(base_ip + i)
        print(f"Scanning {ip}...")

        status, response_time, error = ping_host(ip)

        if status == "UP":
            print(f"[+] {ip} is UP | Response Time: {response_time}")

            open_ports = scan_ports(ip, ports)

            if open_ports:
                print(f"    Open Ports: {', '.join(map(str, open_ports))}")
            else:
                print("    No specified ports open.")

        elif status == "DOWN":
            print(f"[-] {ip} is DOWN")
        else:
            print(f"[!] {ip} ERROR | {error}")

    print("\nScan complete.")


if __name__ == "__main__":
    main()