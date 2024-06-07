#FROM yaming116/touch-base:latest
FROM registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-cpu-0.4.4

ARG DELETE_NAMES='*int8.onnx'
ARG BUILD_INT8

ENV USE_INT8=${BUILD_INT8:+1}
ENV USE_INT8=${USE_INT8:-2}

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        tar \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /models && chmod -R 777 /models

# sherpa-onnx-zipformer-multi-zh-hans-2023-9-2.tar.bz2
RUN curl -SL -O https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-zipformer-multi-zh-hans-2023-9-2.tar.bz2
    && tar xvf sherpa-onnx-zipformer-multi-zh-hans-2023-9-2.tar.bz2 -C /models \
    && rm sherpa-onnx-zipformer-multi-zh-hans-2023-9-2.tar.bz2 \
    && find /models  -name ${DELETE_NAMES} -exec rm {} \;

EXPOSE 5001

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python" , "app.py"]