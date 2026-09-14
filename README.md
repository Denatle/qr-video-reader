# qr-video-reader

Finds QR codes in a video and replaces each one with its decoded text,
painted over a blurred patch, aligned to the code's orientation.

<img width="1921" height="1078" alt="Screenshot 2026-09-15 at 00 54 16" src="https://github.com/user-attachments/assets/40dc285d-c18d-4626-bd49-f662d5475f60" />

## Install

Requires Python 3.11+ and `ffmpeg` on your PATH.

```bash
# macOS
brew install ffmpeg

# Debian/Ubuntu
sudo apt install ffmpeg
```

Then set up the Python side:

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install opencv-python numpy zxing-cpp qrcode
```

Check ffmpeg is visible:

```bash
ffmpeg -version
```

## Run

Process a video:

```bash
python qr_video_processor.py input.mp4
```

Writes `out.mp4` with the original audio muxed back in.

### Options

| Flag | Default | What it does |
|---|---|---|
| `input` (positional) | `silly_qr_test.mp4` | Source video |
| `-o`, `--output` | `out.mp4` | Where the final video goes |
| `-t`, `--temp` | `temp_noaudio.mp4` | Intermediate silent render |
| `-s`, `--start` | `0` | Skip to this many seconds into the source |

Example — start 112 seconds in, write to `result.mp4`:

```bash
python qr_video_processor.py vidbest.mp4 -o result.mp4 -s 112
```
## Notes

- OpenCV can't write audio, so the pipeline renders a silent video first, 
then calls ffmpeg to attach the original audio track. It crashes if video has no audio but it's okay cause there's a temporary file lol.

