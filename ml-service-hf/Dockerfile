FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    cmake build-essential libopenblas-dev \
    liblapack-dev libx11-dev libboost-all-dev \
    ffmpeg libsm6 libxext6 wget

WORKDIR /app

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
