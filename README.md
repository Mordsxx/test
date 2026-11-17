# Mords Studio

**Made by Mords**  
**TikTok: @Mords_69**

A Windows desktop video utility with two independent workspaces:

1. **AI Frame Interpolation** — uses an external `rife-ncnn-vulkan` executable and FFmpeg.
2. **TikTok 60FPS Patch** — an experimental MP4 timing patcher that edits timing tables without re-encoding media samples.

## Important status

This is a development starter, not a verified production release. The GUI and module separation are implemented. The MP4 patcher supports common, non-fragmented MP4 layouts but must be tested against representative source files before relying on it. Some MP4 files contain timing/edit-list combinations that need additional handling. Always keep backups.

The RIFE workflow expects an external RIFE NCNN Vulkan build. CLI arguments and output naming can vary by release; verify your binary's help output and adapt `core/process_manager.py` if necessary.

## Requirements

- Windows 10/11, 64-bit
- Python 3.10+
- FFmpeg + FFprobe added to PATH
- For interpolation: a compatible `rife-ncnn-vulkan.exe` build and its model files
- NVIDIA GPU / Vulkan-capable GPU recommended for RIFE

## Run from source

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

If Tkinter is missing, install a Python distribution that includes Tcl/Tk.

## FFmpeg setup

Install an FFmpeg Windows build and add its `bin` folder to PATH. Confirm:

```powershell
ffmpeg -version
ffprobe -version
```

## RIFE setup

Download/build a compatible RIFE NCNN Vulkan package from its official project distribution. Keep the executable and model directory together. In Mords Studio, choose the executable in the AI Interpolation workspace.

The current adapter invokes:

```text
rife-ncnn-vulkan -i INPUT_FOLDER -o OUTPUT_FOLDER -n MULTIPLIER
```

Check your specific build's `-h` output. If the syntax differs, update the invocation in `core/process_manager.py`.

## Build a Windows executable

```powershell
pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --name "MordsStudio" main.py
```

The executable will be in `dist\MordsStudio\MordsStudio.exe` (or `dist\MordsStudio.exe`, depending on PyInstaller mode). Test on a clean Windows account before distribution.

## MP4 patch algorithm

The patcher parses MP4 box boundaries, locates movie/track/media headers and sample timing tables, and scales relevant duration and per-sample timing values by an integer slowdown factor. It does not decode or re-encode video/audio samples and does not change `mdat` payload bytes.

**Caution:** MP4 timing is complex. Audio decoder configuration, edit lists, composition offsets, unusual brands, fragmented MP4, and variable-frame-rate streams can require specialized handling. This initial version rejects fragmented MP4 and should be validated using FFprobe and actual playback in multiple players. It is not yet certified to preserve A/V sync for every MP4 variant.

## Project layout

```text
MordsStudio/
  main.py
  gui/
  core/
  engines/mp4_patch/
  requirements.txt
  README.md
```

## Branding

The UI includes:
- Made by Mords
- TikTok: @Mords_69
