import os
import cv2
import sys
import time
import tempfile
from pytz import timezone
from datetime import datetime
import streamlit as st

import uuid
from pathlib import Path
import av
import cv2
import streamlit as st
from aiortc.contrib.media import MediaRecorder
from streamlit_webrtc import WebRtcMode, webrtc_streamer
from datetime import datetime

# st.session_state.start_recording = False
# st.session_state.end_recording = False

# print(st.session_state)

# Basic App Scaffolding
st.title("HEY-I")
st.subheader("면접 영상을 녹화하세요")
st.markdown("##### 선택한 시간이 지나거나 End Recording 버튼을 누르면 녹화가 종료됩니다.")

# Create Sidebar
st.sidebar.title("Settings")

## Get Video
temp_file = tempfile.NamedTemporaryFile(delete=False)

number = st.sidebar.number_input("분 입력", 1, 10)
start_recording = st.sidebar.button("Start Recording")

RECORD_DIR = Path("./records")
RECORD_DIR.mkdir(exist_ok=True)


def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
    img = frame.to_ndarray(format="bgr24")
    return av.VideoFrame.from_ndarray(img, format="bgr24")


now_time = datetime.now(timezone("Asia/Seoul")).strftime("%y%m%d_%H%M%S")
if "prefix" not in st.session_state:
    st.session_state["prefix"] = now_time
    # st.session_state["prefix"] = str(uuid.uuid4())
prefix = st.session_state["prefix"]
in_file = RECORD_DIR / f"{prefix}_recording.flv"


def in_recorder_factory() -> MediaRecorder:
    return MediaRecorder(
        str(in_file), format="flv"
    )  # HLS does not work. See https://github.com/aiortc/aiortc/issues/331


webrtc_streamer(
    key="record",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={
        "video": True,
        "audio": False,
    },
    video_frame_callback=video_frame_callback,
    in_recorder_factory=in_recorder_factory,
)

if in_file.exists():
    pathToStr = in_file.__str__().split("\\")
    in_file_str = f"./{pathToStr[0]}/{pathToStr[1]}"
    # st.session_state.video_dir = in_file_str
    cap = cv2.VideoCapture(in_file_str)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*"vp80")
    out = cv2.VideoWriter(f"./records/{now_time}.webm", fourcc, fps, (width, height))
    while True:
        ret, frame = cap.read()  # 두 개의 값을 반환하므로 두 변수 지정
        if not ret:  # 새로운 프레임을 못받아 왔을 때 braek
            break
        out.write(frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    st.session_state.video_dir = f"{now_time}.webm"

if "video_dir" in st.session_state.keys():
    if os.path.exists(st.session_state.video_dir):
        # print(st.session_state.video_dir)
        video_file = open(st.session_state.video_dir, "rb")
        video_bytes = video_file.read()
        st.write("가장 최근 녹화된 영상을 확인하시겠습니까?")
        check = st.checkbox("Check Video")
        if check:
            with st.expander("가장 최근 녹화된 영상입니다. 이 영상으로 업로드 할 것인지 결정해주세요"):
                st.video(video_bytes)

                # 분석할 영상 결정
                st.write("이 영상으로 분석을 진행할까요?")
                confirm = st.button("Comfirm")
                if confirm:
                    st.write("분석할 영상이 확인 되었습니다. Result 에서 결과를 확인하세요.")
                    st.session_state.confirm_video = st.session_state.video_dir
