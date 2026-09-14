import cv2
import numpy as np
import zxingcpp


def paintQR(frame, code) -> np.ndarray:
    pos = code.position
    tl = np.array([pos.top_left.x, pos.top_left.y], dtype=np.float32)
    tr = np.array([pos.top_right.x, pos.top_right.y], dtype=np.float32)
    bl = np.array([pos.bottom_left.x, pos.bottom_left.y], dtype=np.float32)
    br = np.array([pos.bottom_right.x, pos.bottom_right.y], dtype=np.float32)

    quad = np.array([tl, tr, br, bl], dtype=np.int32)

    width = max(int(np.linalg.norm(tr - tl)), 1)
    height = max(int(np.linalg.norm(bl - tl)), 1)

    # --- blurred background instead of white box ---
    blurred = cv2.GaussianBlur(frame, (0, 0), sigmaX=25)
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [quad], 255)
    frame[mask > 0] = blurred[mask > 0]

    # --- draw text as large as possible to fill the QR area ---
    canvas = np.zeros((height, width, 3), dtype=np.uint8)  # black bg for mask purposes
    text = code.text
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = max(width // 80, 1)

    scale = 1.0
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    # grow or shrink until it nearly fills the box
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

    # warp canvas (text mask) so its top edge lands on the QR's top edge
    src_pts = np.float32([[0, 0], [width, 0], [0, height]])
    dst_pts = np.float32([tl, tr, bl])
    M = cv2.getAffineTransform(src_pts, dst_pts)
    warped_text = cv2.warpAffine(
        canvas, M, (frame.shape[1], frame.shape[0]), borderValue=(0, 0, 0)
    )

    text_mask = cv2.cvtColor(warped_text, cv2.COLOR_BGR2GRAY) > 30
    frame[text_mask] = (255, 255, 255)  # black text over the blurred background

    return frame


def read(cap: cv2.VideoCapture) -> bool:
    fps = cap.get(cv2.CAP_PROP_FPS)
    while cap.isOpened():
        ret, frame = cap.read()

        if not ret:
            return False

        data = zxingcpp.read_barcodes(frame)

        for code in data:
            frame = paintQR(frame, code)

        cv2.imshow("This thing", frame)

        # WTF is this slop i need to change this
        if cv2.waitKey(round(1 / fps * 1000)) & 0xFF == ord("q"):
            break


def main() -> None:
    start = 112
    cap = cv2.VideoCapture("vidbest.mp4")
    cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)

    if not cap.isOpened():
        print("no video")
        exit()

    res = read(cap)
    if not res:
        print("it's joever")
