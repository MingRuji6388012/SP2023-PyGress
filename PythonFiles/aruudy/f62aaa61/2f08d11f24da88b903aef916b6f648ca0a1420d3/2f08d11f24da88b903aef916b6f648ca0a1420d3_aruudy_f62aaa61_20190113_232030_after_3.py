#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  Copyright 2019 Abdelkrime Aries <kariminfo0@gmail.com>
#
#  ---- AUTHORS ----
#  2019    Abdelkrime Aries <kariminfo0@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from aruudy.poetry import prosody, meter

app = Flask(__name__)
CORS(app)
app.config["JSON_AS_ASCII"] = False
#headers = {
#    "Content-Type": "application/json",0
#    "charset": "utf-8"
#}

@app.route("/info/<name>", methods=["GET", "POST"])
def info(name):
    b = meter.get_bahr(name)
    if b == None:
        return "Bahr not found", 404
    return jsonify(b), 200

@app.route("/ls", methods=["GET", "POST"])
def bahrs_list():
    res = {
    "arabic": meter.arabic_names(),
    "english": meter.english_names(),
    "trans": meter.trans_names()
    }
    return jsonify(res), 200

@app.route("/shatr/<text>", methods=["GET", "POST"])
def process_shatr(text):
    s = prosody.process_shatr(text).to_dict(bahr=True)
    res = 200
    if not s["bahr"] == "None":
        res = 404
    return jsonify(s), res


@app.route("/", methods=["GET", "POST"])
def route():
    #res = '<a href="./ls">list meters</a>'
    return render_template("index.htm", host = request.host_url)

if __name__ == "__main__":
    app.run(debug=True)