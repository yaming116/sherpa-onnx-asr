
import logging
from flask import Flask, request, render_template, jsonify, send_from_directory
import os
from gevent.pywsgi import WSGIServer, WSGIHandler
from logging.handlers import RotatingFileHandler
import warnings
import tools

import numpy as np
import sherpa_onnx
import wave
from typing import  Tuple
import time

warnings.filterwarnings('ignore')

ROOT_DIR = os.getcwd()
STATIC_DIR = os.path.join(ROOT_DIR, 'static')
TMP_DIR = os.path.join(STATIC_DIR, 'tmp')
RULE_DIR = os.path.join(STATIC_DIR, 'rules')

# 本地使用需要下载模型到 ./models
M_DIR = os.path.join(ROOT_DIR, 'models')
ROOT_M_DIR = os.path.join('/', 'models')

if os.path.exists(ROOT_M_DIR):
    M_DIR = ROOT_M_DIR

log = logging.getLogger('werkzeug')
log.handlers[:] = []
log.setLevel(logging.WARNING)

root_log = logging.getLogger()  # Flask的根日志记录器
root_log.handlers = []
root_log.setLevel(logging.WARNING)

recognizer = None
try:
    m = os.getenv('MODEL', 'zipformer')
    r = os.getenv('RULE', 'on')

    rules = ''

    if r == 'on':
        rules = os.path.join(RULE_DIR, 'itn_zh_number.fst')

    if m == 'zipformer':
        recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
            joiner=os.path.join(M_DIR, 'joiner-epoch-20-avg-1.onnx'),
            encoder=os.path.join(M_DIR, 'encoder-epoch-20-avg-1.onnx'),
            decoder=os.path.join(M_DIR, 'decoder-epoch-20-avg-1.onnx'),
            tokens=os.path.join(M_DIR, 'tokens.txt'),
            num_threads=2,
            rule_fsts= rules
        )
    elif m == 'paraformer':
        recognizer = sherpa_onnx.OfflineRecognizer.from_paraformer(
            paraformer=os.path.join(M_DIR, 'model.int8.onnx'),
            tokens=os.path.join(M_DIR, 'tokens.txt'),
            num_threads=2,
            rule_fsts = rules,
        )
except Exception as e:
    print('模型加载异常')
    print(e)


class CustomRequestHandler(WSGIHandler):
    def log_request(self):
        pass


app = Flask(__name__)

# 配置日志
app.logger.setLevel(logging.WARNING)  # 设置日志级别为 INFO
# 创建 RotatingFileHandler 对象，设置写入的文件路径和大小限制
file_handler = RotatingFileHandler(os.path.join(ROOT_DIR, 'sherpa-onnx.log'), maxBytes=1024 * 1024, backupCount=5)
# 创建日志的格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# 设置文件处理器的级别和格式
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(formatter)
# 将文件处理器添加到日志记录器中
app.logger.addHandler(file_handler)


def read_wave(wave_filename: str) -> Tuple[np.ndarray, int]:
    """
    Args:
      wave_filename:
        Path to a wave file. It should be single channel and each sample should
        be 16-bit. Its sample rate does not need to be 16kHz.
    Returns:
      Return a tuple containing:
       - A 1-D array of dtype np.float32 containing the samples, which are
       normalized to the range [-1, 1].
       - sample rate of the wave file
    """

    with wave.open(wave_filename) as f:
        assert f.getnchannels() == 1, f.getnchannels()
        assert f.getsampwidth() == 2, f.getsampwidth()  # it is in bytes
        num_samples = f.getnframes()
        samples = f.readframes(num_samples)
        samples_int16 = np.frombuffer(samples, dtype=np.int16)
        samples_float32 = samples_int16.astype(np.float32)

        samples_float32 = samples_float32 / 32768
        return samples_float32, f.getframerate()


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.config['STATIC_FOLDER'], filename)


@app.route('/')
def index():
    return render_template("index.html", language='zh')


@app.route('/upload', methods=['POST'])
def upload():
    try:
        # 获取上传的文件
        audio_file = request.files['audio']
        # 如果是mp4
        noextname, ext = os.path.splitext(audio_file.filename)
        ext = ext.lower()
        # 如果是视频，先分离
        wav_file = os.path.join(TMP_DIR, f'{noextname}{ext}')
        if os.path.exists(wav_file) and os.path.getsize(wav_file) > 0:
            return jsonify({'code': 0, 'msg': 'zh', "data": os.path.basename(wav_file)})
        msg = ""


        audio_file.save(wav_file)

        # 返回成功的响应
        return jsonify({'code': 0, 'msg': '上传成功' + msg, "data": os.path.basename(wav_file)})
    except Exception as e:
        app.logger.error(f'[upload]error: {e}')
        return jsonify({'code': 2, 'msg': '上传失败'})


@app.route('/api',methods=['GET','POST'])
def api():
    source_file = ''
    wav_file = ''
    is_delete = None
    try:

        is_delete = request.form.get('is_delete', None)

        # 获取上传的文件
        if request.form.get('wav_name') is not None:
            source_file = os.path.join(TMP_DIR, request.form.get('wav_name') )
        else:
            audio_file = request.files.get("file") or request.form.get("file")
            noextname, ext = os.path.splitext(audio_file.filename)
            ext = ext.lower()
            source_file = os.path.join(TMP_DIR, f'{noextname}{ext}')
            if not os.path.exists(source_file) or os.path.getsize(source_file) == 0:
                audio_file.save(source_file)

        noextname, ext = os.path.splitext(source_file)
        wav_file = os.path.join(TMP_DIR, f'{noextname}.wav')
        print(f'{wav_file=}')
        params = [
            "-i",
            source_file,
        ]

        params.append('-acodec')
        params.append('pcm_s16le')
        params.append('-ar')
        params.append('16k')
        params.append('-ac')
        params.append('1')

        if not os.path.exists(wav_file) or os.path.getsize(wav_file) == 0:
            if ext in ['.mp4', '.mov', '.avi', '.mkv', '.mpeg', '.mp3', '.flac']:

                if ext not in ['.mp3', '.flac']:
                    params.append('-vn')
                params.append(wav_file)
                rs = tools.runffmpeg(params)
                if rs != 'ok':
                    return jsonify({"code": 1, "msg": rs})
            elif ext == '.speex':
                params.append(wav_file)
                rs = tools.runffmpeg(params)
                if rs != 'ok':
                    return jsonify({"code": 1, "msg": rs})
            elif ext == '.wav':
                wav_file = source_file
            else:
                return jsonify({"code": 1, "msg": f"格式不支持 {ext}"})
        print(f'{ext=}')
        print(f'{source_file=}')

        start_time = time.time()

        if recognizer is None:
            return jsonify({"code": 1, "msg": "模型初始化异常"})

        total_duration = 0
        samples, sample_rate = read_wave(wav_file)
        duration = len(samples) / sample_rate
        total_duration += duration
        s = recognizer.create_stream()
        s.accept_waveform(sample_rate, samples)

        recognizer.decode_stream(s)
        results = s.result.text
        end_time = time.time()

        return jsonify({"code": 0, "msg": 'ok', "data": [{'text': results }], 'times': (end_time -start_time) ,
                        'total_duration': total_duration, 'filename': f'{noextname}{ext}'})
    except Exception as e:
        print(e)
        app.logger.error(f'[api]error: {e}')
        return jsonify({'code': 2, 'msg': str(e)})
    finally:
        pass
        if is_delete is None:
            if os.path.exists(wav_file):
                os.remove(source_file)
            if os.path.exists(source_file):
                os.remove(source_file)


if __name__ == '__main__':
    http_server = None
    try:
        try:
            web_address = '0.0.0.0:5001'
            host = web_address.split(':')
            http_server = WSGIServer((host[0], int(host[1])), app, handler_class=CustomRequestHandler)

            app.logger.info(f" http://{web_address}")

            http_server.serve_forever(stop_timeout=10)
            print("start server")
        finally:
            if http_server:
                http_server.stop()
    except Exception as e:
        if http_server:
            http_server.stop()
        print("error:" + str(e))
        app.logger.error(f"[app]start error:{str(e)}")
