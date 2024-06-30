FROM python:3.11.9-slim-bullseye

#RUN mv /etc/apt/sources.list /etc/apt/sources.list.bak
#RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bullseye main contrib non-free" >> /etc/apt/sources.list
#RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bullseye-updates main contrib non-free" >> /etc/apt/sources.list
#RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bullseye-backports main contrib non-free" >> /etc/apt/sources.list
#RUN echo "deb https://security.debian.org/debian-security bullseye-security main contrib non-free" >> /etc/apt/sources.list

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        tar \
        curl \
        bzip2 \
    && rm -rf /var/lib/apt/lists/*

ARG DELETE_NAMES='*int8.onnx'
ARG MODEL='zipformer'
ARG MODEL_FILE_NAME='sherpa-onnx-zipformer-multi-zh-hans-2023-9-2.tar.bz2'

ENV MODEL=$MODEL
# --build-arg MODEL=paraformer --build-arg DELETE_NAMES='model.onnx' --build-arg MODEL_FILE_NAME=sherpa-onnx-paraformer-zh-2023-03-28.tar.bz2

RUN mkdir -p /models && chmod -R 777 /models

# sherpa-onnx-zipformer-multi-zh-hans-2023-9-2.tar.bz2
# http://192.168.3.107:3000/
# https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models
# sherpa-onnx-paraformer-zh-2023-03-28.tar.bz2


RUN  curl -SL -O https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/${MODEL_FILE_NAME} \
        && ls -all \
        && tar xvf ${MODEL_FILE_NAME} --strip-components 1 -C /models \
        && rm ${MODEL_FILE_NAME} \
        && find /models  -name ${DELETE_NAMES} -exec rm {} \; \
        && ls -all /models

EXPOSE 5001

# RUN pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python" , "app.py"]
