# 🔊 SoundKeeper - Bluetooth Audio Device Keep-Alive

<div align="center">

![GitHub release](https://img.shields.io/github/v/release/Deimz/SoundKeeper)
![License](https://img.shields.io/github/license/Deimz/SoundKeeper)
![Platform](https://img.shields.io/badge/platform-Windows-blue)

**Keep your Bluetooth audio devices connected and active**

[Download Latest Release](https://github.com/Deimz/SoundKeeper/releases/latest) | [Report Bug](https://github.com/Deimz/SoundKeeper/issues) | [Request Feature](https://github.com/Deimz/SoundKeeper/issues)

</div>

---

## 📖 About

**SoundKeeper** is a lightweight Windows application that prevents Bluetooth audio devices from automatically entering standby mode due to inactivity. 

Many Bluetooth audio devices (soundbars, speakers, headphones) automatically disconnect or enter standby mode after ~60 seconds of silence. This is especially common with devices originally designed for TVs or with aggressive power-saving features. SoundKeeper solves this problem by playing imperceptible audio signals at regular intervals, keeping your device active and connected without any audible sound.

## ✨ Features

- 🔇 **Imperceptible Audio** - Plays white noise at extremely low volume (completely inaudible)
- ⏱️ **Configurable Timing** - Choose the wait duration and sound duration from the tray menu
- 🎯 **System Tray Integration** - Minimalist interface accessible from the taskbar
- ✅ **Easy Toggle** - Enable/disable with a single click
- 🚀 **Startup Option** - Configure to launch automatically with Windows
- 🌍 **Languages** - Follow the Windows UI language or choose English, Chinese, French, Russian, Spanish, or Arabic
- 💾 **Saved Preferences** - Keep your timing and language preferences across restarts
- 🛡️ **Single Instance** - Prevents multiple instances from running simultaneously
- 🪶 **Lightweight** - Tray settings use the existing dependencies, without an additional GUI framework

## 📥 Download & Installation

### 💻 For Regular Users (Recommended)

**No Python or programming knowledge required!**

1. Go to the [**Releases page**](https://github.com/Deimz/SoundKeeper/releases/latest)
2. Download `SoundKeeper.exe` from the latest release
3. Double-click the executable - no installation needed!
4. A green Bluetooth icon will appear in your system tray
5. *Optional:* Right-click the icon and enable "Launch at Startup" to run automatically

That's it! Your Bluetooth device will now stay connected.

---

### 👨‍💻 For Developers (Run from Source)

If you want to modify the code or contribute to the project:

**Requirements:**
- Python 3.9 or higher (dependency versions must support the chosen Python version)
- Windows OS

**Installation Steps:**

```powershell
# Clone the repository
git clone https://github.com/Deimz/SoundKeeper.git
cd SoundKeeper

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the application
python soundkeeper.py
```

## 🎮 Usage

### Quick Start

1. **Launch SoundKeeper** - Double-click `SoundKeeper.exe`
2. **Look for the icon** - A green Bluetooth icon appears in your system tray
3. **It's working!** - Your audio device will now stay connected

### System Tray Menu

Right-click the icon to access:

- **✅ Active (Keep-Alive)** - Toggle the keep-alive feature on/off
  - 🟢 Green icon = Active
  - ⚫ Grey icon = Paused
- **🚀 Launch at Startup** - Register/unregister from Windows startup
- **❌ Quit** - Exit the application
- **⚙️ Settings** - Choose the wait duration and sound duration, or restore their defaults
- **🌍 Language** - Follow the system or select one of the six supported languages

An orange icon and an audio status message indicate a playback failure. SoundKeeper
rechecks the output format and retries every five seconds until playback succeeds.

### Compatible Devices

SoundKeeper works with any Bluetooth audio device that has auto-standby/timeout features:

- ✅ **Soundbars** (Samsung, LG, Sony, etc.) - Especially TV soundbars used with PCs
- ✅ **Bluetooth Speakers** - Portable or desktop speakers with power-saving modes
- ✅ **Wireless Headphones** - Any brand with aggressive auto-sleep features
- ✅ **Home Theater Systems** - Bluetooth-enabled receivers and amplifiers
- ✅ **Smart Speakers** - When used in Bluetooth mode

## ⚙️ Configuration

Use the tray menu to change preferences without editing source code or rebuilding:

| Setting | Options | Default |
| --- | --- | --- |
| Wait duration | 30 s, 55 s, 4 min 55 s, 9 min 55 s, 14 min 55 s | 55 s |
| Sound duration | 0.01 s, 0.1 s, 1 s | 1 s |
| Language | Follow system, English, Simplified Chinese, French, Russian, Spanish, Arabic | Follow system |

The wait starts **after playback finishes**. With the defaults, playback starts
approximately every 56 seconds. Changing an audio preference during a wait starts
a new wait using the selected duration; an in-progress sound finishes normally.
Resuming from pause plays immediately. Longer waits must remain shorter than your
device's standby timeout. Very short sounds may not keep every device awake.

Preferences are stored per Windows user in `%APPDATA%\SoundKeeper\config.json`:

```json
{
  "version": 1,
  "wait_seconds": 55,
  "duration_seconds": 1.0,
  "language": "auto"
}
```

Language codes are `auto`, `en`, `zh-Hans`, `fr`, `ru`, `es`, and `ar`.
Follow system checks the Windows preferred UI languages in order and uses the first
supported language family. Unsupported lists fall back to English; all Chinese
variants currently use the Simplified Chinese translation. Language changes update
the menu immediately. Language names are displayed in their own languages.

Missing or invalid preferences use defaults. Settings are saved by atomic file
replacement; a write failure is reported and changes remain usable for the current
session. Restore defaults resets only the two timing preferences, preserving the
language and Windows startup registration. Each launch starts with keep-alive enabled.

The sample rate is selected automatically: validate the current output device's
default rate for stereo `float32` audio, then try 44100 and 48000 Hz if necessary,
skipping duplicate candidates. The selected rate is used both to generate the
samples and to play them. It is cached until the reported device changes or playback
fails, and is not saved in the config file. Detection does not change Windows audio
settings or verify a device's standby behavior. Some drivers require an application
restart after devices are connected or disconnected to refresh their device list.

Noise amplitude remains fixed at `0.0001` in `soundkeeper.py`. There is no manual
input window or additional GUI dependency. Autostart remains managed by the Windows
Run registry key rather than the JSON file.

## 🔧 Building from Source

To create your own executable:

```powershell
# Install PyInstaller
pip install pyinstaller

# Build the executable
pyinstaller --onefile --windowed --icon=icon.ico --name SoundKeeper soundkeeper.py

# Alternatively, use the checked-in portable build specification
pyinstaller SoundKeeper.spec

# Find your .exe in the dist/ folder
```

## 🐛 Troubleshooting

### The audio device still disconnects

- Make sure SoundKeeper is running (check system tray)
- Verify the feature is enabled (icon should be green)
- Select a shorter wait duration in the tray settings
- If using a very short sound, try restoring the default 1-second duration
- If the icon is orange, check that an output device is available; restart the app after reconnecting if necessary

### "SoundKeeper is already running" error

- Only one instance can run at a time
- Check the system tray for an existing icon
- Close it before launching again

### Icon doesn't appear in system tray

- Check Windows notification area settings
- Make sure the application hasn't crashed (check Task Manager)

## Development checks

Run regression tests from the repository root after installing `requirements.txt`:

```powershell
python -m unittest discover -s tests -v
```

Tests use temporary configuration files and mocked audio/registry operations. They
do not play sound or change your Windows startup registration. Actual Bluetooth
standby behavior and Arabic menu rendering should also be checked on Windows before
publishing a release. Build size and memory use depend on dependency and driver versions.

## 📋 System Requirements

- **OS:** Windows 10/11 (64-bit)
- **RAM:** Depends on the Python, dependency, and audio-driver versions
- **Storage:** ~30MB
- **Audio:** Any audio output device

## 🤝 Contributing

Contributions are welcome! Feel free to:

- 🐛 Report bugs
- 💡 Suggest new features
- 🔧 Submit pull requests
- 📖 Improve documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [pystray](https://github.com/moses-palmer/pystray) for system tray integration
- Audio handling powered by [sounddevice](https://python-sounddevice.readthedocs.io/)
- AI generated icon ( Gemini )

## 💬 Support

- **Issues:** [GitHub Issues](https://github.com/Deimz/SoundKeeper/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Deimz/SoundKeeper/discussions)

---

<div align="center">

**If SoundKeeper helped you, please consider giving it a ⭐ on GitHub!**

Made with ❤️ for frustrated Bluetooth users everywhere

</div>
