#!/usr/bin/env python3
# log_decoder.py - Decode binary battlebot logs to human-readable format

import struct
import sys
from datetime import datetime
import csv

class LogDecoder:
    """
    Decodes binary log files from the battlebot.
    """

    ENTRY_SIZE = 24
    ENTRY_FORMAT = '<IhhhHHhhhBBH'

    FLAG_NAMES = {
        0x01: 'ARMED',
        0x02: 'FAILSAFE',
        0x04: 'LOW_BATTERY',
        0x08: 'OVERTEMP',
        0x10: 'IMU_VALID',
        0x20: 'WIFI_CONNECTED',
    }

    def __init__(self, filename):
        self.filename = filename
        self.entries = []
        self.header = None

    def read_header(self, f):
        """Read and parse log file header"""
        header_data = f.read(12)
        if len(header_data) < 12:
            raise ValueError("Invalid log file - header too short")

        magic, version, entry_size, start_time = struct.unpack('<4sHHI', header_data)

        if magic != b'BTBL':
            raise ValueError(f"Invalid magic number: {magic}")

        self.header = {
            'version': version,
            'entry_size': entry_size,
            'start_time_ms': start_time,
        }

        print(f"Log version: {version}")
        print(f"Entry size: {entry_size} bytes")
        print(f"Recording started: {start_time}ms since boot")
        print()

    def decode(self):
        """Decode entire log file"""
        with open(self.filename, 'rb') as f:
            # Read header
            self.read_header(f)

            # Read entries
            entry_num = 0
            while True:
                data = f.read(self.ENTRY_SIZE)
                if len(data) < self.ENTRY_SIZE:
                    break

                entry = self.decode_entry(data, entry_num)
                if entry:
                    self.entries.append(entry)

                entry_num += 1

        print(f"Decoded {len(self.entries)} entries")
        return self.entries

    def decode_entry(self, data, entry_num):
        """Decode a single log entry"""
        try:
            (timestamp, motor_left, motor_right, weapon_speed,
             battery_mv, current_ma, accel_x, accel_y, accel_z,
             status_flags, error_code, checksum) = struct.unpack(self.ENTRY_FORMAT, data)

            # Verify checksum
            calc_checksum = (timestamp + motor_left + motor_right + weapon_speed +
                           battery_mv + current_ma + accel_x + accel_y + accel_z +
                           status_flags + error_code) & 0xFFFF

            if calc_checksum != checksum:
                print(f"Warning: Checksum mismatch at entry {entry_num}")

            # Convert values
            battery_v = battery_mv / 100.0
            current_a = current_ma / 1000.0
            accel = (accel_x / 100.0, accel_y / 100.0, accel_z / 100.0)

            # Parse flags
            flags = []
            for bit, name in self.FLAG_NAMES.items():
                if status_flags & bit:
                    flags.append(name)

            return {
                'entry': entry_num,
                'timestamp_ms': timestamp,
                'time_s': timestamp / 1000.0,
                'motor_left': motor_left,
                'motor_right': motor_right,
                'weapon_speed': weapon_speed,
                'battery_v': battery_v,
                'current_a': current_a,
                'accel_x': accel[0],
                'accel_y': accel[1],
                'accel_z': accel[2],
                'flags': flags,
                'error_code': error_code,
            }

        except Exception as e:
            print(f"Error decoding entry {entry_num}: {e}")
            return None

    def print_summary(self):
        """Print summary statistics"""
        if not self.entries:
            print("No entries to summarize")
            return

        print("\n" + "="*60)
        print("LOG SUMMARY")
        print("="*60)

        # Time range
        start_time = self.entries[0]['time_s']
        end_time = self.entries[-1]['time_s']
        duration = end_time - start_time

        print(f"Duration: {duration:.2f} seconds")
        print(f"Total entries: {len(self.entries)}")
        print(f"Average rate: {len(self.entries) / duration:.1f} Hz")

        # Battery stats
        voltages = [e['battery_v'] for e in self.entries]
        print(f"\nBattery: {min(voltages):.2f}V - {max(voltages):.2f}V")

        # Motor stats
        print(f"\nMotor Left: {min(e['motor_left'] for e in self.entries)} to {max(e['motor_left'] for e in self.entries)}")
        print(f"Motor Right: {min(e['motor_right'] for e in self.entries)} to {max(e['motor_right'] for e in self.entries)}")
        print(f"Weapon: {min(e['weapon_speed'] for e in self.entries)} to {max(e['weapon_speed'] for e in self.entries)}")

        # Flag occurrences
        all_flags = {}
        for entry in self.entries:
            for flag in entry['flags']:
                all_flags[flag] = all_flags.get(flag, 0) + 1

        if all_flags:
            print("\nFlag occurrences:")
            for flag, count in sorted(all_flags.items()):
                percentage = (count / len(self.entries)) * 100
                print(f"  {flag}: {count} ({percentage:.1f}%)")

        # Errors
        errors = [e for e in self.entries if e['error_code'] != 0]
        if errors:
            print(f"\nErrors detected: {len(errors)}")
            for entry in errors[:10]:  # Show first 10
                print(f"  t={entry['time_s']:.2f}s: Error code {entry['error_code']}")

    def export_csv(self, output_filename):
        """Export decoded data to CSV"""
        if not self.entries:
            print("No entries to export")
            return

        with open(output_filename, 'w', newline='') as csvfile:
            fieldnames = ['entry', 'timestamp_ms', 'time_s', 'motor_left', 'motor_right',
                         'weapon_speed', 'battery_v', 'current_a', 'accel_x', 'accel_y',
                         'accel_z', 'flags', 'error_code']

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for entry in self.entries:
                # Convert flags list to string
                row = entry.copy()
                row['flags'] = '|'.join(row['flags']) if row['flags'] else ''
                writer.writerow(row)

        print(f"\nExported to {output_filename}")

    def plot_data(self):
        """Create plots of the log data (requires matplotlib)"""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("matplotlib not installed - skipping plots")
            return

        if not self.entries:
            print("No entries to plot")
            return

        times = [e['time_s'] for e in self.entries]

        # Create subplots
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        fig.suptitle(f'BattleBot Log Analysis: {self.filename}')

        # Motor speeds
        axes[0].plot(times, [e['motor_left'] for e in self.entries], label='Left Motor', alpha=0.7)
        axes[0].plot(times, [e['motor_right'] for e in self.entries], label='Right Motor', alpha=0.7)
        axes[0].plot(times, [e['weapon_speed'] for e in self.entries], label='Weapon', alpha=0.7)
        axes[0].set_ylabel('Motor Speed (%)')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Battery voltage
        axes[1].plot(times, [e['battery_v'] for e in self.entries], color='red', linewidth=2)
        axes[1].set_ylabel('Battery Voltage (V)')
        axes[1].grid(True, alpha=0.3)
        axes[1].axhline(y=10.0, color='r', linestyle='--', label='Low Battery')
        axes[1].legend()

        # Acceleration
        axes[2].plot(times, [e['accel_x'] for e in self.entries], label='Accel X', alpha=0.7)
        axes[2].plot(times, [e['accel_y'] for e in self.entries], label='Accel Y', alpha=0.7)
        axes[2].plot(times, [e['accel_z'] for e in self.entries], label='Accel Z', alpha=0.7)
        axes[2].set_xlabel('Time (seconds)')
        axes[2].set_ylabel('Acceleration (g)')
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)

        plt.tight_layout()

        # Save plot
        plot_filename = self.filename.replace('.bin', '_plot.png')
        plt.savefig(plot_filename, dpi=150)
        print(f"\nPlot saved to {plot_filename}")

        plt.show()


def main():
    if len(sys.argv) < 2:
        print("Usage: python log_decoder.py <logfile.bin> [--csv output.csv] [--plot]")
        sys.exit(1)

    filename = sys.argv[1]

    print(f"Decoding: {filename}")
    print("-" * 60)

    decoder = LogDecoder(filename)
    decoder.decode()
    decoder.print_summary()

    # Check for CSV export
    if '--csv' in sys.argv:
        csv_idx = sys.argv.index('--csv')
        if csv_idx + 1 < len(sys.argv):
            csv_filename = sys.argv[csv_idx + 1]
            decoder.export_csv(csv_filename)
        else:
            # Default CSV name
            csv_filename = filename.replace('.bin', '.csv')
            decoder.export_csv(csv_filename)

    # Check for plotting
    if '--plot' in sys.argv:
        decoder.plot_data()


if __name__ == '__main__':
    main()