import argparse
import subprocess
import cv2
import numpy as np
import zxingcpp


# This function is pure slop
# Idk what's it doing but it doing it great
# And painfully slow
def paintQR(frame, code) -> np.ndarray:
    pos = code.position
    tl = np.array([pos.top_left.x, pos.top_left.y], dtype=np.float32)
    tr = np.array([pos.top_right.x, pos.top_right.y], dtype=np.float32)
    bl = np.array([pos.bottom_left.x, pos.bottom_left.y], dtype=np.float32)
    br = np.array([pos.bottom_right.x, pos.bottom_right.y], dtype=np.float32)

    quad = np.array([tl, tr, br, bl], dtype=np.int32)

    width = max(int(np.linalg.norm(tr - tl)), 1)
    height = max(int(np.linalg.norm(bl - tl)), 1)

    blurred = cv2.GaussianBlur(frame, (0, 0), sigmaX=25)
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [quad], 255)
    frame[mask > 0] = blurred[mask > 0]

    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    text = code.text
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = max(width // 80, 1)

    scale = 1.0
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    while tw < width * 0.95 and th < height * 0.85:
        scale += 0.05
        thickness = max(int(width // 80 * scale), 1)
        (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    while (tw > width * 0.95 or th > height * 0.85) and scale > 0.05:
        scale -= 0.05
        thickness = max(int(width // 80 * scale), 1)
        (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)

    tx = (width - tw) // 2
    ty = (height + th) // 2
    cv2.putText(
        canvas, text, (tx, ty), font, scale, (255, 255, 255), thickness, cv2.LINE_AA
    )

    src_pts = np.float32([[0, 0], [width, 0], [0, height]])
    dst_pts = np.float32([tl, tr, bl])
    M = cv2.getAffineTransform(src_pts, dst_pts)
    warped_text = cv2.warpAffine(
        canvas, M, (frame.shape[1], frame.shape[0]), borderValue=(0, 0, 0)
    )

    text_mask = cv2.cvtColor(warped_text, cv2.COLOR_BGR2GRAY) > 30
    frame[text_mask] = (255, 255, 255)

    return frame


def process(input_path: str, temp_path: str, start_sec: float) -> None:
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print("no video")
        exit()

    cap.set(cv2.CAP_PROP_POS_MSEC, start_sec * 1000)

    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(temp_path, fourcc, fps, (w, h))

    frame_num = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        data = zxingcpp.read_barcodes(frame)
        for code in data:
            frame = paintQR(frame, code)

        writer.write(frame)

        frame_num += 1
        if frame_num % 30 == 0:
            print(f"processed {frame_num} frames")

    cap.release()
    writer.release()


def mux_audio(
    input_path: str, temp_video_path: str, output_path: str, start_sec: float
) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        temp_video_path,
        "-ss",
        str(start_sec),
        "-i",
        input_path,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-shortest",
        output_path,
    ]
    subprocess.run(cmd, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", default="silly_qr_test.mp4")
    parser.add_argument("-o", "--output", default="out.mp4")
    parser.add_argument("-t", "--temp", default="temp_noaudio.mp4")
    parser.add_argument("-s", "--start", type=float, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    process(args.input, args.temp, args.start)
    mux_audio(args.input, args.temp, args.output, args.start)

    print(f"done -> {args.output}")


if __name__ == "__main__":
    main()
