FROM python:3.10-bullseye

RUN apt-get update && apt-get install -y \
    wget bzip2 ffmpeg libsm6 libxext6

WORKDIR /app

# Install binary dlib build to avoid compiling from source on HF
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir dlib-bin==19.24.6

# Download dlib model files during build
RUN mkdir models && \
    wget -q http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2 && \
    bzip2 -d shape_predictor_68_face_landmarks.dat.bz2 && \
    mv shape_predictor_68_face_landmarks.dat models/ && \
    wget -q http://dlib.net/files/dlib_face_recognition_resnet_model_v1.dat.bz2 && \
    bzip2 -d dlib_face_recognition_resnet_model_v1.dat.bz2 && \
    mv dlib_face_recognition_resnet_model_v1.dat models/

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
