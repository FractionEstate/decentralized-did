# USB Fingerprint Sensor Hardware Setup Guide

**Date**: October 12, 2025
**Status**: ✅ **COMPLETE** - Ready for Hardware Purchase
**Target Sensor**: Eikon Touch 700 USB Fingerprint Reader
**Cost**: $25-30 USD

---

## Executive Summary

This guide provides complete instructions for purchasing, installing, and configuring a USB fingerprint sensor for biometric DID generation. The recommended sensor (Eikon Touch 700) is affordable, widely available, and fully supported by open-source libraries (libfprint).

###Purpose**: Enable **real biometric DID generation** with raw minutiae extraction (WebAuthn cannot do this).

---

## Hardware Selection

### Recommended: Eikon Touch 700

**Why This Sensor**:
- ✅ **Affordable**: $25-30 USD on Amazon/eBay
- ✅ **Open-Source Support**: Full libfprint support
- ✅ **No Proprietary Drivers**: Works with standard Linux drivers
- ✅ **USB 2.0**: Universal compatibility
- ✅ **Optical Sensor**: 500 DPI resolution
- ✅ **Proven**: Widely used in biometric projects

**Specifications**:
- **Model**: Eikon Touch 700
- **Connection**: USB 2.0
- **Resolution**: 500 DPI
- **Sensor Type**: Optical
- **Image Size**: 256 x 360 pixels
- **Power**: USB bus-powered (no external power needed)
- **OS Support**: Linux, macOS, Windows (with libfprint)

### Where to Buy

**Amazon**: Search "Eikon Touch 700" or "Eikon USB Fingerprint Reader"
- **Link**: https://www.amazon.com/s?k=eikon+touch+700
- **Price**: $25-35 USD
- **Shipping**: 1-2 days (Prime)

**eBay**: Often cheaper, slower shipping
- **Link**: https://www.ebay.com/sch/i.html?_nkw=eikon+touch+700
- **Price**: $15-25 USD
- **Shipping**: 3-7 days

**AliExpress**: Cheapest, slowest shipping
- **Link**: Search "Eikon fingerprint scanner"
- **Price**: $12-20 USD
- **Shipping**: 2-4 weeks

### Alternative Options

| Sensor | Price | libfprint Support | Resolution | Notes |
|--------|-------|-------------------|------------|-------|
| **Eikon Touch 700** | $25 | ✅ Excellent | 500 DPI | **Recommended** |
| ZhongZhi ZK4500 | $18 | ✅ Good | 500 DPI | Cheaper alternative |
| Suprema BioMini Plus 2 | $60 | ✅ Good | 500 DPI | Higher quality |
| Digital Persona U.are.U 4500 | $50 | ✅ Excellent | 512 DPI | Enterprise grade |
| Futronic FS88 | $30 | ✅ Good | 500 DPI | Solid mid-range |

**Recommendation**: Start with Eikon Touch 700 for development. Upgrade to Suprema or Digital Persona for production if needed.

---

## Software Requirements

### Development Container (Current)

Your dev container already has most dependencies. You'll need to add:

```bash
# Install libfprint and Python bindings
sudo apt-get update
sudo apt-get install -y \
    libfprint-2-2 \
    libfprint-2-dev \
    python3-gi \
    python3-dev \
    libgirepository1.0-dev \
    pkg-config

# Verify installation
python3 -c "import gi; gi.require_version('FPrint', '2.0'); from gi.repository import FPrint; print('libfprint version:', FPrint.Device)"
```

### System Requirements

- **OS**: Linux (Ubuntu 22.04+, Debian 12+)
- **Python**: 3.10+ (already installed)
- **USB Port**: USB 2.0 or 3.0
- **Permissions**: Will need udev rules for non-root access

---

## Installation Steps

### Step 1: Physical Installation

1. **Unbox Sensor**:
   - Remove from packaging
   - Inspect for damage
   - Do NOT touch sensor surface (oils reduce quality)

2. **Connect to USB Port**:
   - Plug into any available USB 2.0/3.0 port
   - Sensor LED should light up (usually blue or green)
   - No external power needed

3. **Verify Detection**:
   ```bash
   lsusb | grep -i "eikon\|fingerprint"
   # Should see: Bus 001 Device 003: ID 1491:0020 Eikon Digital ART Development fingerprint sensor
   ```

### Step 2: Install libfprint

```bash
# Update package lists
sudo apt-get update

# Install libfprint and dependencies
sudo apt-get install -y \
    libfprint-2-2 \
    libfprint-2-dev \
    python3-gi \
    python3-dev \
    libgirepository1.0-dev \
    pkg-config \
    gir1.2-fprint-2.0

# Verify installation
dpkg -l | grep libfprint
# Should show libfprint-2-2 and libfprint-2-dev installed
```

### Step 3: Configure USB Permissions

Create udev rules so non-root users can access the sensor:

```bash
# Create udev rules file
sudo nano /etc/udev/rules.d/60-fingerprint.rules
```

Add this content:
```
# Eikon Touch 700
SUBSYSTEM=="usb", ATTRS{idVendor}=="1491", ATTRS{idProduct}=="0020", MODE="0666", GROUP="plugdev"

# ZhongZhi ZK4500
SUBSYSTEM=="usb", ATTRS{idVendor}=="1b55", ATTRS{idProduct}=="0020", MODE="0666", GROUP="plugdev"

# Generic fingerprint devices
SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device", ATTRS{bInterfaceClass}=="ff", ATTRS{bInterfaceSubClass}=="00", MODE="0666", GROUP="plugdev"
```

Save and reload udev rules:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger

# Add your user to plugdev group
sudo usermod -a -G plugdev $USER

# Reconnect sensor or reboot for changes to take effect
```

### Step 4: Test Sensor

Test sensor with fprintd (fingerprint daemon):

```bash
# Install testing tools
sudo apt-get install -y fprintd fprintd-demo

# List available devices
fprintd-list

# Test capture (should prompt to place finger)
fprintd-enroll
```

If enrollment works, sensor is ready!

### Step 5: Python Integration Test

Create test script:

```python
#!/usr/bin/env python3
"""Test libfprint sensor detection"""

import gi
gi.require_version('FPrint', '2.0')
from gi.repository import FPrint

def test_sensor():
    ctx = FPrint.Context()
    devices = ctx.get_devices()

    if not devices:
        print("❌ No fingerprint devices found")
        return False

    print(f"✅ Found {len(devices)} fingerprint device(s):")
    for i, device in enumerate(devices):
        print(f"  Device {i+1}:")
        print(f"    Name: {device.get_name()}")
        print(f"    Driver: {device.get_driver()}")
        print(f"    Device Type: {device.get_device_type()}")
        print(f"    Open: {device.is_open()}")

    return True

if __name__ == "__main__":
    test_sensor()
```

Run test:
```bash
python3 test_sensor.py
# Should show: ✅ Found 1 fingerprint device(s)
```

---

## Troubleshooting

### Issue: Sensor Not Detected

**Symptoms**: `lsusb` doesn't show sensor

**Solutions**:
1. **Check USB Connection**:
   - Try different USB port
   - Ensure cable fully inserted
   - Test with another USB device to verify port works

2. **Check Power**:
   - Sensor LED should be lit
   - If not, USB port may not provide enough power
   - Try powered USB hub

3. **Check USB Mode**:
   - Ensure USB 2.0 mode enabled in BIOS
   - Some systems disable USB devices by default

---

### Issue: Permission Denied

**Symptoms**: `fprintd-enroll` says "Permission denied"

**Solutions**:
1. **Check udev rules**:
   ```bash
   cat /etc/udev/rules.d/60-fingerprint.rules
   # Verify rules exist
   ```

2. **Reload udev**:
   ```bash
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```

3. **Check group membership**:
   ```bash
   groups $USER
   # Should include "plugdev"
   ```

4. **Reconnect sensor**:
   - Unplug and replug USB cable
   - Or reboot system

---

### Issue: libfprint Not Found

**Symptoms**: `ImportError: cannot import name 'FPrint'`

**Solutions**:
1. **Install Python GObject bindings**:
   ```bash
   sudo apt-get install -y python3-gi gir1.2-fprint-2.0
   ```

2. **Verify installation**:
   ```bash
   python3 -c "import gi; print(gi.repository.__path__)"
   # Should show path to gi repository
   ```

3. **Check libfprint version**:
   ```bash
   dpkg -l | grep libfprint
   # Should show version 2.x (not 1.x)
   ```

---

### Issue: Poor Image Quality

**Symptoms**: Fingerprint capture fails, image too dark/light

**Solutions**:
1. **Clean Sensor Surface**:
   - Use microfiber cloth (like for glasses)
   - Gently wipe sensor surface
   - Do NOT use water or chemicals

2. **Clean Finger**:
   - Wash and dry hands thoroughly
   - Remove oils/lotions
   - Avoid very dry skin (use light lotion if needed)

3. **Adjust Pressure**:
   - Press firmly but not too hard
   - Ensure full finger contact with sensor
   - Hold steady for 2-3 seconds

4. **Try Different Fingers**:
   - Some fingers have better ridge clarity
   - Index finger usually best
   - Avoid thumbs (often worn down)

---

### Issue: Slow Capture

**Symptoms**: Takes >10 seconds to capture fingerprint

**Solutions**:
1. **Check USB Speed**:
   ```bash
   lsusb -t
   # Ensure sensor on USB 2.0 or 3.0 (not 1.1)
   ```

2. **Close Other USB Devices**:
   - USB bandwidth shared across all devices
   - Unplug webcams, external drives during capture

3. **Optimize libfprint Settings**:
   - Reduce image quality (faster capture)
   - Adjust timeout values in code

---

## Maintenance

### Daily Use

- **Clean sensor weekly**: Use microfiber cloth
- **Avoid touching sensor surface**: Hold by edges
- **Unplug when not in use**: Extends sensor life
- **Store in dust-free location**: Prevents surface scratches

### Quality Checks

Run quality test monthly:

```bash
# Enroll 5 fingerprints
for i in {1..5}; do
  echo "Capture $i/5"
  fprintd-enroll
done

# Test verification
fprintd-verify
```

If verification fails >10%, sensor may need replacement.

---

## Integration with Demo-Wallet

Once sensor is working, you'll integrate it with the backend API:

### Updated Architecture

```
Demo-Wallet (Browser)
    ↓ HTTP POST /enroll
Backend API (FastAPI)
    ↓ Python subprocess
Python CLI (decentralized-did)
    ↓ libfprint wrapper
USB Sensor (Eikon Touch 700)
    ↓ Raw fingerprint image
Minutiae Extraction (NBIS)
    ↓ Minutiae points
Fuzzy Extractor
    ↓ Helper Data + ID Hash
Return to Demo-Wallet
```

### Code Changes Required

1. **Create libfprint wrapper** (`src/decentralized_did/capture/libfprint_capture.py`)
2. **Update CLI** (`src/decentralized_did/cli.py`) to use real capture
3. **Update Backend API** (`api_server_mock.py` → `api_server.py`)
4. **Test end-to-end** with real fingerprints

See `docs/hardware/libfprint-integration.md` for detailed implementation guide.

---

## Cost Breakdown

| Item | Cost | Notes |
|------|------|-------|
| Eikon Touch 700 | $25-30 | One-time purchase |
| USB Cable (if needed) | $5 | Usually included |
| Microfiber Cloth | $2 | For cleaning |
| **Total** | **$27-37** | **One-time hardware cost** |

**Ongoing Costs**: $0 (no subscriptions, no licenses)

---

## Alternatives to USB Sensor

If you can't purchase hardware right now:

### Option 1: WebAuthn (Already Implemented) ✅
- **Cost**: $0
- **Capability**: Verification only (no DID generation)
- **Use Cases**: Unlock wallet, sign transactions
- **Status**: Production-ready

### Option 2: Webcam + OpenCV (Future)
- **Cost**: $0 (uses existing webcam)
- **Capability**: Full DID generation
- **Use Cases**: All biometric operations
- **Quality**: Medium (worse than USB sensor)
- **Status**: Not implemented yet

### Option 3: Mock Mode (Current) ✅
- **Cost**: $0
- **Capability**: Full DID generation (fake data)
- **Use Cases**: Development and demo only
- **Status**: Already working

**Recommendation**: Keep using WebAuthn + Mock mode until sensor arrives.

---

## Timeline

### Day 1: Order Hardware
- [ ] Purchase Eikon Touch 700 from Amazon ($25-30)
- [ ] Select Prime shipping (1-2 days) or standard (3-5 days)
- [ ] Total time: 5 minutes

### Day 2-3: Await Delivery
- [ ] Continue development with WebAuthn + Mock mode
- [ ] Prepare libfprint integration code (see next task)

### Day 4: Install and Test
- [ ] Follow installation steps above (~30 minutes)
- [ ] Test sensor with fprintd (~10 minutes)
- [ ] Run Python integration test (~5 minutes)
- [ ] Total time: 45 minutes

### Day 5: Integration
- [ ] Integrate libfprint wrapper (~2 hours)
- [ ] Update Backend API (~1 hour)
- [ ] Test end-to-end (~1 hour)
- [ ] Total time: 4 hours

**Total Timeline**: 4-6 days (including shipping)

---

## Next Steps

After hardware setup complete:

1. **✅ Task 3**: Implement libfprint wrapper (`docs/hardware/libfprint-integration.md`)
2. **✅ Task 4**: Upgrade Backend API to production mode
3. **✅ Test**: Enroll with real fingerprints (10 fingers)
4. **✅ Test**: Verify with real fingerprints
5. **✅ Test**: Generate real biometric DID

---

## Success Criteria

Hardware setup is complete when:

- ✅ Sensor detected by `lsusb`
- ✅ Sensor detected by libfprint
- ✅ Can capture fingerprint with `fprintd-enroll`
- ✅ Python can import libfprint
- ✅ Test script detects sensor
- ✅ Non-root user has permissions

---

## Support

**libfprint Documentation**: https://fprint.freedesktop.org/
**Eikon Support**: support@eikondevices.com
**Project Issues**: https://github.com/FractionEstate/decentralized-did/issues

---

**Prepared by**: GitHub Copilot
**Date**: October 12, 2025
**Status**: ✅ **COMPLETE** - Ready for Hardware Purchase
**Estimated Setup Time**: 45 minutes (after hardware arrives)
