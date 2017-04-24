#-*- coding:utf-8 -*-
from flask import jsonify
from flask import render_template
from flask import flash
from flask import current_app
from flask import abort
import datetime
import time
import os
import hashlib
import requests
import json
from StringIO import StringIO
import tensorflow as tf
from PIL import Image, ImageSequence
from io import BytesIO

basedir = os.path.abspath(os.path.dirname(__file__))

# Loads label file, strips off carriage return
# 加载标签数据
label_lines = [line.rstrip() for line 
                   in tf.gfile.GFile(basedir + '/retrained_labels.txt')]

# Unpersists graph from file
with tf.gfile.FastGFile(basedir + '/retrained_graph.pb', 'rb') as f:
    print("加载模型")
    graph_def = tf.GraphDef()
    graph_def.ParseFromString(f.read())
    _ = tf.import_graph_def(graph_def, name='')

sess = tf.Session()
softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')

def init_route(app):
    app.add_url_rule('/', 'home', home, methods=['GET'])
    app.add_url_rule('/search/<string:key>/page/<string:page>', 'search', search, methods=['GET'])

def home():
    return render_template('home.html')
    pass

def search(key, page):
    overStart = time.time()
    apiUrl = "http://open-api.biaoqingmm.com/open-api/gifs/search"

    params = {}
    params['app_id'] = "b05b585673334bc081493f069510d6ad"
    print int(1000 * time.time())
    params['size'] = 20
    params['timestamp'] = str(int(1000 * time.time()))
    params['q'] = key
    params['p'] = page

    paramsString = apiUrl + "app_id=" + params['app_id'] + "&p=" + params['p'] + "&q=" + params['q'] + "&size=" + str(params['size']) + "&timestamp=" + params['timestamp']
    print paramsString
    sig = hashlib.md5(paramsString).hexdigest().upper()
    params['signature'] = sig
    print params
    response = requests.get(apiUrl, params)
    print("搜索接口耗时：%.3fs" % (time.time() - overStart))
    print response
    gifs = json.load(StringIO(response.content))['gifs']

    imageUrls = []
    for gif in gifs:
        imageUrls.append(gif["main"])
        print (gif["main"])

    results = []
    datas = {}
    downloadStart = time.time()
    for url in imageUrls:
        da = {}
        image_data = read_image2RGBbytes(url)
        if image_data is None:
            continue
        da['data'] = image_data
        da['url'] = url
        datas.append(da)

    print("下载用时：%.3fs", %(time.time() - downloadStart))

    predictStart = time.time()
    for (url, image_data) in datas:
        re = {}
        re['url'] = url
        predictions = sess.run(softmax_tensor, \
                 {'DecodeJpeg/contents:0': image_data})
        
        # Sort to show labels of first prediction in order of confidence
        top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
        predict = {}
        for node_id in top_k:
            human_string = label_lines[node_id]
            score = predictions[0][node_id]
            re[human_string] = '%.5f' % score
        print re
        results.append(re)
    print("预测用时：%.3fs" % (time.time() - predictStart))

    overEnd = time.time()
    print("总共用时：%.3fs" % (overEnd - overStart))
    return render_template('result.html', results=results)

def read_image2RGBbytes(imgurl):
    try:
        with BytesIO() as output:
            response = requests.get(imgurl)
            with Image.open(StringIO(response.content)) as img:
                  frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
                  frameCount = len(frames)
                  if frameCount < 5 :
                      temImg = frames[frameCount // 2]
                      temImg.convert('RGB').save(output, 'JPEG')
                  else:
                      temImg = frames[frameCount - 4]
                      temImg.convert('RGB').save(output, 'JPEG')
                  image_data = output.getvalue()
    except:
        print ("读取图片失败")
        return None

    return image_data


def list_routes(app):
    result = []
    for rt in app.url_map.iter_rules():
        result.append({
            'methods': list(rt.methods),
            'route': str(rt)
        })
    return jsonify({'routes': result, 'total': len(result)})




