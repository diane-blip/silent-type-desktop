"""Local video diagnostic. Reads frames only; never opens a microphone or types."""

import argparse
import json

import cv2

from silent_type.recognition import Recognizer
from silent_type.state import format_text, settings

parser = argparse.ArgumentParser()
parser.add_argument("video")
args = parser.parse_args()
cap = cv2.VideoCapture(args.video)
fps = cap.get(cv2.CAP_PROP_FPS) or 25
frames = []
try:
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
        if len(frames) > fps * 20:
            break
finally:
    cap.release()
config = settings()
text, seconds = Recognizer(config).decode(frames, [i / fps for i in range(len(frames))])
print(
    json.dumps(
        {"text": format_text(text, config["names"]), "seconds": round(seconds, 2), "frames": len(frames)}
    )
)
