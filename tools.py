import subprocess
import sys


def runffmpeg(arg):
    cmd = ["ffmpeg","-hide_banner","-y"]
    # if cfg.devtype =='cuda':
    #     cmd.extend(["-hwaccel", "cuda","-hwaccel_output_format","cuda"])
    cmd = cmd + arg
    p = subprocess.Popen(cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=0 if sys.platform != 'win32' else subprocess.CREATE_NO_WINDOW)
    while True:
        try:
            #等待0.1未结束则异常
            outs, errs = p.communicate(timeout=0.5)
            errs=str(errs)
            if errs:
                errs = errs.replace('\\\\','\\').replace('\r',' ').replace('\n',' ')
                errs=errs[errs.find("Error"):]
            # 成功
            if p.returncode==0:
                return "ok"
            # 失败
            # if cfg.devtype=='cuda':
            #     errs+="[error] Please try upgrading the graphics card driver and reconfigure CUDA"
            return errs
        except subprocess.TimeoutExpired as e:
            # 如果前台要求停止
            pass
        except Exception as e:
            #出错异常
            errs=f"[error]ffmpeg:error {cmd=},\n{str(e)}"
            return errs
