FROM python:3.11.9-slim-bullseye

ARG DELETE_NAMES='*int8.onnx'
ARG BUILD_INT8

# --build-arg BUILD_INT8=1 --build-arg DELETE_NAMES='*avg-1.onnx'

ENV USE_INT8=${BUILD_INT8:+1}
ENV USE_INT8=${USE_INT8:-2}

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        tar \
        curl \
        bzip2 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /models && chmod -R 777 /models

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bzip2

# sherpa-onnx-zipformer-multi-zh-hans-2023-9-2.tar.bz2
# http://192.168.3.107:3000/
# https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models
RUN curl -SL -O https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-zipformer-multi-zh-hans-2023-9-2.tar.bz2 \
    && ls -all \
    && tar xvf sherpa-onnx-zipformer-multi-zh-hans-2023-9-2.tar.bz2 --strip-components 1 -C /models \
    && rm sherpa-onnx-zipformer-multi-zh-hans-2023-9-2.tar.bz2 \
    && find /models  -name ${DELETE_NAMES} -exec rm {} \; \
    && ls -all /models

EXPOSE 5001
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple flask
WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python" , "app.py"]
