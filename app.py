#-*- coding:utf-8 -*-
from flask import Flask, request, jsonify, render_template
from routes import init_route
# import cv2
import numpy as np
from PIL import Image, ImageSequence
import os
import sys
import requests
from StringIO import StringIO
import datetime

reload(sys)
print sys.getdefaultencoding()
sys.setdefaultencoding('utf8')


app = Flask(__name__)
init_route(app)


if __name__ == "__main__":
    # app.run(debug=True)
    app.run(host='0.0.0.0', debug=True)
    # app.run(host='0.0.0.0', port=5555)

