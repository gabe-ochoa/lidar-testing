"""Quick test: connect to lidar, print 5 scans, exit."""

import sys

from lidar_testing.drivers.rplidar_a2 import RPLidarA2Driver


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/tty.usbserial-0001"
    driver = RPLidarA2Driver(port=port)
    driver.connect()
    print(f"Connected: {driver.get_info()}")
    try:
        for i, scan in enumerate(driver.iter_scans()):
            valid = [p for p in scan if p.distance > 0]
            if valid:
                print(
                    f"Scan {i}: {len(valid)} points, "
                    f"min={min(p.distance for p in valid):.0f}mm, "
                    f"max={max(p.distance for p in valid):.0f}mm"
                )
            else:
                print(f"Scan {i}: no valid points")
            if i >= 4:
                break
    finally:
        driver.disconnect()
        print("Disconnected.")


if __name__ == "__main__":
    main()
