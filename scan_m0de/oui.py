"""Offline MAC OUI Vendor lookup table for local device identification."""

# Comprehensive database of common MAC OUI prefixes (first 3 bytes: XX:XX:XX)
OUI_DB = {
    # Apple
    "00:03:93": "Apple", "00:05:02": "Apple", "00:0A:27": "Apple", "00:0D:93": "Apple",
    "00:10:FA": "Apple", "00:11:24": "Apple", "00:14:51": "Apple", "00:16:CB": "Apple",
    "00:17:F2": "Apple", "00:19:E3": "Apple", "00:1B:63": "Apple", "00:1C:B3": "Apple",
    "00:1D:4F": "Apple", "00:1E:52": "Apple", "00:1F:5B": "Apple", "00:1F:F3": "Apple",
    "00:21:E9": "Apple", "00:22:41": "Apple", "00:23:12": "Apple", "00:23:32": "Apple",
    "00:23:6C": "Apple", "00:24:36": "Apple", "00:25:00": "Apple", "00:25:4B": "Apple",
    "00:26:08": "Apple", "00:26:4A": "Apple", "00:26:B0": "Apple", "00:26:BB": "Apple",
    "00:88:65": "Apple", "04:0C:CE": "Apple", "04:15:52": "Apple", "04:26:65": "Apple",
    "04:48:9A": "Apple", "04:54:53": "Apple", "04:DB:56": "Apple", "04:E5:36": "Apple",
    "04:F1:5E": "Apple", "08:00:07": "Apple", "08:66:98": "Apple", "08:70:45": "Apple",
    "08:E6:89": "Apple", "08:F4:AB": "Apple", "0C:15:C4": "Apple", "0C:30:21": "Apple",
    "0C:4D:E9": "Apple", "0C:51:01": "Apple", "0C:74:C2": "Apple", "0C:BC:9F": "Apple",
    "10:1C:0C": "Apple", "10:40:F3": "Apple", "10:93:E9": "Apple", "10:94:BB": "Apple",
    "10:DD:B1": "Apple", "14:10:9F": "Apple", "14:20:5B": "Apple", "14:7D:C5": "Apple",
    "14:99:E2": "Apple", "14:C0:3D": "Apple", "18:20:32": "Apple", "18:34:51": "Apple",
    "18:3B:D2": "Apple", "18:65:90": "Apple", "18:81:0E": "Apple", "18:AF:61": "Apple",
    "18:E7:28": "Apple", "1C:1A:C0": "Apple", "1C:5C:F2": "Apple", "1C:99:4C": "Apple",
    "1C:AB:A7": "Apple", "1C:E8:5D": "Apple", "20:3C:AE": "Apple", "20:7D:74": "Apple",
    "20:78:F0": "Apple", "20:9B:CD": "Apple", "20:A2:E4": "Apple", "20:C9:D0": "Apple",
    "AC:3C:8E": "Apple", "4C:50:DD": "Apple", "1C:30:08": "Apple", "1C:53:F9": "Apple",
    "A0:9F:10": "Apple", "60:A4:4C": "Apple", "9C:BC:F0": "Apple", "74:40:BB": "Apple",
    "DC:36:98": "Apple", "80:EE:73": "Apple", "58:D8:12": "TP-Link",

    # Raspberry Pi Foundation
    "B8:27:EB": "Raspberry Pi", "DC:A6:32": "Raspberry Pi", "E4:5F:01": "Raspberry Pi",
    "28:CD:C1": "Raspberry Pi", "D8:3A:DD": "Raspberry Pi",

    # Espressif Systems (ESP8266 / ESP32 Smart Home Devices)
    "18:FE:34": "Espressif (ESP32/ESP8266)", "24:0A:C4": "Espressif (ESP32/ESP8266)",
    "24:62:AB": "Espressif (ESP32/ESP8266)", "24:B2:DE": "Espressif (ESP32/ESP8266)",
    "30:AE:A4": "Espressif (ESP32/ESP8266)", "3C:71:BF": "Espressif (ESP32/ESP8266)",
    "40:22:D8": "Espressif (ESP32/ESP8266)", "48:3F:DA": "Espressif (ESP32/ESP8266)",
    "4C:11:AE": "Espressif (ESP32/ESP8266)", "54:5A:A6": "Espressif (ESP32/ESP8266)",
    "5C:CF:7F": "Espressif (ESP32/ESP8266)", "60:01:94": "Espressif (ESP32/ESP8266)",
    "68:C6:3A": "Espressif (ESP32/ESP8266)", "70:03:9F": "Espressif (ESP32/ESP8266)",
    "7C:DF:A1": "Espressif (ESP32/ESP8266)", "80:7D:3A": "Espressif (ESP32/ESP8266)",
    "84:0D:8E": "Espressif (ESP32/ESP8266)", "84:CC:A8": "Espressif (ESP32/ESP8266)",
    "8C:AA:B5": "Espressif (ESP32/ESP8266)", "90:97:D5": "Espressif (ESP32/ESP8266)",
    "94:B5:55": "Espressif (ESP32/ESP8266)", "A0:20:A6": "Espressif (ESP32/ESP8266)",
    "A4:7B:9D": "Espressif (ESP32/ESP8266)", "A4:CF:12": "Espressif (ESP32/ESP8266)",
    "AC:67:B2": "Espressif (ESP32/ESP8266)", "B4:E6:2D": "Espressif (ESP32/ESP8266)",
    "BC:DD:C2": "Espressif (ESP32/ESP8266)", "C4:4F:33": "Espressif (ESP32/ESP8266)",
    "CC:50:E3": "Espressif (ESP32/ESP8266)", "D8:A0:1D": "Espressif (ESP32/ESP8266)",
    "DC:4F:22": "Espressif (ESP32/ESP8266)", "E0:5A:1B": "Espressif (ESP32/ESP8266)",
    "E8:68:E7": "Espressif (ESP32/ESP8266)", "EC:FA:BC": "Espressif (ESP32/ESP8266)",

    # Google
    "00:1A:11": "Google", "3C:5A:B4": "Google", "48:D6:D5": "Google", "54:60:09": "Google",
    "66:55:70": "Google", "70:EE:50": "Google", "94:EB:CD": "Google", "A4:77:33": "Google",
    "B4:F6:1C": "Google", "D8:6C:63": "Google", "E4:F0:42": "Google", "F8:8F:CA": "Google",

    # Amazon / Ring
    "00:FC:8B": "Amazon", "0C:47:C9": "Amazon", "18:74:2E": "Amazon", "34:D2:70": "Amazon",
    "38:F9:D3": "Amazon", "40:B4:CD": "Amazon", "44:65:0D": "Amazon", "50:DC:E7": "Amazon",
    "5C:49:7D": "Amazon", "68:54:5A": "Amazon", "68:9A:87": "Amazon", "74:C2:46": "Amazon",
    "78:E1:03": "Amazon", "84:D6:70": "Amazon", "8C:45:00": "Amazon", "A0:02:DC": "Amazon",
    "AC:63:BE": "Amazon", "B4:7C:9C": "Amazon", "CC:6E:A4": "Amazon", "F0:D2:F1": "Amazon",
    "FC:A1:83": "Amazon", "FC:A6:67": "Amazon",

    # Ubiquiti Networks / UniFi
    "00:15:6D": "Ubiquiti", "00:27:22": "Ubiquiti", "04:18:D6": "Ubiquiti", "18:E8:29": "Ubiquiti",
    "24:A4:3C": "Ubiquiti", "68:72:51": "Ubiquiti", "74:83:C2": "Ubiquiti", "78:8A:20": "Ubiquiti",
    "80:2A:A8": "Ubiquiti", "B4:FB:E4": "Ubiquiti", "D8:B0:4C": "Ubiquiti", "DC:9F:DB": "Ubiquiti",
    "F0:9F:C2": "Ubiquiti", "FC:EC:DA": "Ubiquiti",

    # Synology
    "00:11:32": "Synology", "00:90:A9": "Synology", "D4:C9:EF": "Synology",

    # Sonos
    "00:0E:58": "Sonos", "34:7E:5C": "Sonos", "48:A6:B8": "Sonos", "5C:AA:FD": "Sonos",
    "78:28:CA": "Sonos", "94:9F:3E": "Sonos", "B8:E9:37": "Sonos", "C4:38:75": "Sonos",

    # Samsung
    "00:07:AB": "Samsung", "00:12:FB": "Samsung", "00:15:99": "Samsung", "00:1D:25": "Samsung",
    "00:21:19": "Samsung", "00:23:D7": "Samsung", "00:24:E2": "Samsung", "00:26:5D": "Samsung",
    "08:37:3D": "Samsung", "08:D4:6A": "Samsung", "10:1D:C1": "Samsung", "14:1F:78": "Samsung",
    "18:1E:B0": "Samsung", "1C:5A:3E": "Samsung", "24:4B:03": "Samsung", "28:CC:01": "Samsung",
    "30:CD:A7": "Samsung", "34:BE:00": "Samsung", "38:0B:40": "Samsung", "40:0E:85": "Samsung",
    "48:44:F7": "Samsung", "50:B7:C3": "Samsung", "54:99:63": "Samsung", "5C:A3:9D": "Samsung",
    "64:1C:AE": "Samsung", "64:B5:C6": "Samsung", "6C:83:36": "Samsung", "78:47:1D": "Samsung",
    "84:25:DB": "Samsung", "8C:77:12": "Samsung", "94:35:0A": "Samsung", "A0:0B:BA": "Samsung",
    "AC:5F:3E": "Samsung", "B4:79:A7": "Samsung", "BC:8C:CD": "Samsung", "C4:73:1E": "Samsung",

    # LG Electronics
    "00:1C:62": "LG", "00:1E:B6": "LG", "00:22:A9": "LG", "00:E0:91": "LG",
    "08:00:28": "LG", "10:68:3F": "LG", "14:C9:12": "LG", "20:3D:B9": "LG",
    "34:4D:F7": "LG", "40:B0:34": "LG", "48:59:A4": "LG", "58:A2:B5": "LG",
    "64:99:5D": "LG", "78:5D:C8": "LG", "88:C9:D0": "LG", "98:D6:F7": "LG",
    "A8:23:FE": "LG", "B8:6C:E8": "LG", "CC:2D:8C": "LG", "E8:5B:5B": "LG",

    # TP-Link
    "00:1D:0F": "TP-Link", "00:27:19": "TP-Link", "14:CC:20": "TP-Link", "18:A6:F7": "TP-Link",
    "1B:28:5A": "TP-Link", "30:B5:C2": "TP-Link", "50:C7:BF": "TP-Link", "54:C8:0F": "TP-Link",
    "5C:A6:E6": "TP-Link", "60:E3:27": "TP-Link", "74:DA:38": "TP-Link", "78:8C:54": "TP-Link",
    "84:16:F9": "TP-Link", "90:F6:52": "TP-Link", "98:DA:C4": "TP-Link", "A0:F3:C1": "TP-Link",
    "B0:48:7A": "TP-Link", "C0:25:E9": "TP-Link", "C4:6E:1F": "TP-Link", "CC:32:E5": "TP-Link",
    "D8:07:B6": "TP-Link", "E8:48:B8": "TP-Link", "EC:08:6B": "TP-Link", "F4:F2:6D": "TP-Link",

    # Asus
    "00:0E:A6": "Asus", "00:11:D8": "Asus", "00:13:D4": "Asus", "00:15:F2": "Asus",
    "00:18:F3": "Asus", "00:1A:92": "Asus", "00:1B:FC": "Asus", "00:1D:60": "Asus",
    "00:1E:8C": "Asus", "00:1F:C6": "Asus", "00:22:15": "Asus", "00:23:54": "Asus",
    "00:24:8C": "Asus", "00:26:18": "Asus", "04:D4:C4": "Asus", "08:60:6E": "Asus",
    "10:BF:48": "Asus", "14:DA:E9": "Asus", "1C:87:2C": "Asus", "20:CF:30": "Asus",
    "30:5A:3A": "Asus", "38:D5:47": "Asus", "40:16:9F": "Asus", "40:B0:76": "Asus",
    "50:46:5D": "Asus", "54:04:A6": "Asus", "60:45:CB": "Asus", "70:4D:7B": "Asus",
    "AC:22:0B": "Asus", "B0:6E:BF": "Asus", "BC:EE:7B": "Asus", "C8:60:00": "Asus",

    # Netgear
    "00:09:5B": "Netgear", "00:0F:B5": "Netgear", "00:14:6C": "Netgear", "00:18:4D": "Netgear",
    "00:1B:2F": "Netgear", "00:1E:2A": "Netgear", "00:1F:33": "Netgear", "00:22:3F": "Netgear",
    "00:24:B2": "Netgear", "00:26:F2": "Netgear", "04:A1:51": "Netgear", "08:02:8E": "Netgear",
    "10:0C:6B": "Netgear", "14:59:C0": "Netgear", "1C:7E:E5": "Netgear", "20:4E:7F": "Netgear",
    "28:80:88": "Netgear", "2C:30:33": "Netgear", "30:46:9A": "Netgear", "44:94:FC": "Netgear",
    "A0:04:60": "Netgear", "B0:39:56": "Netgear", "C0:3F:0E": "Netgear", "E0:46:EE": "Netgear",

    # Intel
    "00:02:B3": "Intel", "00:03:47": "Intel", "00:04:23": "Intel", "00:0E:0C": "Intel",
    "00:13:02": "Intel", "00:13:CE": "Intel", "00:15:00": "Intel", "00:16:EA": "Intel",
    "00:18:DE": "Intel", "00:19:D2": "Intel", "00:1B:21": "Intel", "00:1C:C0": "Intel",
    "00:1D:E0": "Intel", "00:1E:64": "Intel", "00:1F:3C": "Intel", "00:21:6A": "Intel",
    "00:22:FB": "Intel", "00:23:14": "Intel", "00:24:D7": "Intel", "00:27:0E": "Intel",
    "08:00:27": "VirtualBox / Intel", "34:60:F9": "Intel", "3C:A8:2A": "Intel", "48:51:B7": "Intel",
    "48:F1:7F": "Intel", "50:7B:9D": "Intel", "54:8C:A0": "Intel", "58:91:CF": "Intel",
    "60:57:18": "Intel", "64:4B:F0": "Intel", "68:05:CA": "Intel", "6C:88:14": "Intel",
    "70:1C:E7": "Intel", "74:E5:F9": "Intel", "78:2B:46": "Intel", "7C:5C:F8": "Intel",
    "80:86:F2": "Intel", "84:7B:EB": "Intel", "88:78:73": "Intel", "8C:85:90": "Intel",
    "94:65:9C": "Intel", "98:2C:BC": "Intel", "A0:36:9F": "Intel", "A4:4E:31": "Intel",
    "AC:D1:B8": "Intel", "B4:2E:99": "Intel", "B8:6B:23": "Intel", "C8:5B:76": "Intel",

    # Gaming & Entertainment
    "00:04:13": "SNOM", "00:0D:0D": "Microsoft", "00:12:5A": "Microsoft", "00:17:FA": "Microsoft",
    "00:1D:D8": "Microsoft", "00:22:48": "Microsoft", "00:25:AE": "Microsoft", "28:18:78": "Microsoft",
    "58:82:A8": "Microsoft (Xbox)", "60:45:BD": "Microsoft (Xbox)", "7C:ED:8D": "Microsoft (Xbox)",
    "00:01:4A": "Sony", "00:04:1F": "Sony", "00:13:15": "Sony", "00:15:C1": "Sony",
    "00:19:C5": "Sony", "00:1D:0D": "Sony", "00:24:8D": "Sony", "00:D0:09": "Sony",
    "00:E0:4C": "Realtek", "54:53:ED": "Sony (PlayStation)", "70:9E:29": "Sony (PlayStation)",
    "F8:46:1C": "Sony (PlayStation)", "00:09:BF": "Nintendo", "00:17:AB": "Nintendo",
    "00:19:FD": "Nintendo", "00:1B:EA": "Nintendo", "00:1D:2C": "Nintendo", "00:1E:A9": "Nintendo",
    "00:1F:C5": "Nintendo", "00:21:47": "Nintendo", "00:22:AA": "Nintendo", "00:23:CC": "Nintendo",
    "00:24:44": "Nintendo", "00:25:A0": "Nintendo", "78:A2:A0": "Nintendo (Switch)",
    "98:B6:E9": "Nintendo (Switch)", "B8:AE:6E": "Nintendo (Switch)", "E0:0C:7F": "Nintendo (Switch)",
    "00:25:90": "Super Micro", "00:30:48": "Super Micro", "00:E0:81": "Super Micro",
    "00:0C:29": "VMware", "00:50:56": "VMware", "00:1C:14": "VMware", "00:05:69": "VMware",
    "50:6B:8D": "Valve Corporation (Steam Deck)", "7C:25:DA": "Valve Corporation",
}


def lookup_oui(mac: str) -> str:
    """Look up vendor name from MAC address string (formats like XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX)."""
    if not mac or mac.strip() in ("", "00:00:00:00:00:00", "FF:FF:FF:FF:FF:FF"):
        return "Unknown"

    cleaned = mac.upper().replace("-", ":").replace(".", "")
    parts = cleaned.split(":")
    if len(parts) >= 3:
        prefix = ":".join(parts[:3])
        if prefix in OUI_DB:
            return OUI_DB[prefix]

    # Check for randomized / private MAC addresses (bit 1 of 1st byte is set)
    try:
        first_byte = int(parts[0], 16)
        if (first_byte & 2) != 0:
            return "Private/Randomized MAC"
    except (ValueError, IndexError):
        pass

    return "Unknown Vendor"
