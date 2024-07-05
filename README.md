sherpa-onnx-asr
----

模型使用的是小米的 [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx), 这里做了一个http 服务，加上一些文件转换，方便对接一些服务使用。

### 使用


部署完成之后，可以访问 ip:5001, 有一个测试界面可以使用。 

关于 paraformer 和 zipformer 的区别可以查看这里 https://github.com/yaming116/sherpa-onnx-asr/issues/1

```bash
# 完整版， 目前完整版占用 1g 内存
docker pull yaming116/sherpa-onnx-asr:latest
# 目前zipformer 和 latest 模型版本一致，sherpa-onnx 推荐实用 paraformer 模型，目前为了保持稳定暂时latest不修改
docker pull yaming116/sherpa-onnx-asr:zipformer-2024-7-5
# paraformer 非流式识别模式，效果更好
docker pull yaming116/sherpa-onnx-asr:paraformer-2024-7-5

# 低内存版本
docker pull yaming116/sherpa-onnx-asr-tiny:latest

docker run -d \
--restart=always -it \
--name sherpa-onnx-asr \
-p 5001:5001 \
yaming116/sherpa-onnx-asr:latest
```

### 版本更新记录
* 2024-7-5
  * 增加中文数字、百分比转数字支持
  
* 2024-6-30
  * 增加 paraformer 模型支持     



华为测试音频链接： 
https://sis-sample-audio.obs.cn-north-1.myhuaweicloud.com/16k16bit.mp3

### 接口

```
#:5001/api
#入参
file： 音频文件

#返回参数
{
    "code": 0,
    "data": [
        {
            "key": "rand_key_1qeoePtwBldGD",
            "text": "华为致力于把数字世界带入每个人、每个家庭、每个组织，构建万物互联的智能世界。",
    ],
    "filename": "/funAsr/static/tmp/16k16bit.mp3",
    "msg": "ok"
}
```

### 公众号
可以关注我的公众号，一起交流 HomeAssistant 相关技术。
![](./IMG_8406.JPG)
