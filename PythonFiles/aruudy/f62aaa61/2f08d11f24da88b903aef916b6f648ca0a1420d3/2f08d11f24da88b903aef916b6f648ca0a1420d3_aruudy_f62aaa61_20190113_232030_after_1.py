#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  Copyright 2019 Abdelkrime Aries <kariminfo0@gmail.com>
#
#  ---- AUTHORS ----
# 2019	Abdelkrime Aries <kariminfo0@gmail.com>
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

import re, copy

SALIM = 0
# zuhaf 2nd
IDHMAR = 1
WAQS = 2
KHABN = 3
# zuhaf 4th
TAI = 4
# zuhaf 5th
ASAB = 5
AQL = 6
QABDH = 7
# zuhaf 7th
KAFF = 8
# zuhaf 2nd + 4th
KHABL = 9
# zuhaf 2nd + 4th
KHAZL = 10
# zuhaf 2nd + 7th
SHAKL = 11
# zuhaf 5th + 7th
NAQS = 12
#illa
TARFIIL = 13
IDALA = TADIIL = 14
ISBAGH = 15
HADF = 16
QATE = 17
BATR = 18
QASR = 19
QATF = 20
HADAD = 21
SALAM = 22
KASHF = 23

zuhaf_illa_names = {
SALIM: u"",
IDHMAR: u"",
WAQS: u"",
KHABN: u"",
TAI: u"",
ASAB: u"",
AQL: u"",
QABDH: u"",
KAFF: u"",
KHABL: u"",
KHAZL: u"",
SHAKL: u"",
NAQS: u"",
TARFIIL: u"",
IDALA: u"",
ISBAGH: u"",
HADF: u"",
QATE: u"",
BATR: u"",
QASR: u"",
QATF: u"",
HADAD: u"",
SALAM: u"",
KASHF: u""
}


class Tafiila(object):

    def init(self, var):
        self.afeet = [] # allowed feet
        for foot in self.feet:
            if foot["var"] in var:
                self.afeet.append(foot)

    def process(self, text_emeter):
        for foot in self.afeet:
            if text_emeter.startswith(foot["emeter"]):
                text_foot = copy.deepcopy(foot)
                return text_foot, text_emeter[len(foot["emeter"]):]
        return None, None

# https://sites.google.com/site/mihfadha/aroudh/14

# فَاعِلُنْ
class CVCCV(Tafiila):
    #varation
    def __init__(self, var=[SALIM]):
        self.feet = [
        {
            "var": SALIM,
            "mnemonic": u"فَاعِلُنْ",
            "emeter": "-u-"
        },
        {
            "var": KHABN,
            "mnemonic": u"فَعِلُنْ",
            "emeter": "uu-"
        },
        {
            "var": TARFIIL,
            "mnemonic": u"فَاعِلَاتُنْ",
            "emeter": "-u--"
        },
        {
            "var": IDALA,
            "mnemonic": u"فَاعِلَانْ",
            "emeter": "-u-:"
        },
        {
            "var": QATE,
            "mnemonic": u"فِعْلُنْ",
            "emeter": "--"
        }
        ]
        self.init(var)

# فَعُولُنْ
class CCVCV(Tafiila):
    #varation
    def __init__(self, var=[SALIM]):
        self.feet = [
        {
            "var": SALIM,
            "mnemonic": u"فَعُولُنْ",
            "emeter": "u--"
        },
        {
            "var": QABDH,
            "mnemonic": u"فَعُولُ",
            "emeter": "u-u"
        },
        {
            "var": HADF,
            "mnemonic": u"فِعَلْ",
            "emeter": "u-"
        },
        {
            "var": BATR,
            "mnemonic": u"فِعْ",
            "emeter": "-"
        },
        {
            "var": QASR,
            "mnemonic": u"فَعُولْ",
            "emeter": "u-:"
        }
        ]
        self.init(var)

# مَفَاعِيلُنْ
class CCVCVCV(Tafiila):
    #varation
    def __init__(self, var=[SALIM]):
        self.feet = [
        {
            "var": SALIM,
            "mnemonic": u"مَفَاعِيلُنْ",
            "emeter": "u---"
        },
        {
            "var": QABDH,
            "mnemonic": u"مَفَاعِلُنْ",
            "emeter": "u-u-"
        },
        {
            "var": KAFF,
            "mnemonic": u"مَفَاعِيلُ",
            "emeter": "u--u"
        },
        {
            "var": HADF,
            "mnemonic": u"فَعُولُنْ",
            "emeter": "u--"
        }
        ]
        self.init(var)

# مُسْتَفْعِلُنْ
class CVCVCCV(Tafiila):
    #varation
    def __init__(self, var=[SALIM]):
        self.feet = [
        {
            "var": SALIM,
            "mnemonic": u"مُسْتَفْعِلُنْ",
            "emeter": "--u-"
        },
        {
            "var": KHABN,
            "mnemonic": u"مُتَفْعِلُنْ",
            "emeter": "u-u-"
        },
        {
            "var": TAI,
            "mnemonic": u"مُسْتَعِلُنْ",
            "emeter": "-uu-"
        },
        {
            "var": KHABL,
            "mnemonic": u"مُتَعِلُنْ",
            "emeter": "uuu-"
        },
        {
            "var": IDALA,
            "mnemonic": u"مُسْتَفْعِلَانْ",
            "emeter": "--u-:"
        },
        {
            "var": QATE,
            "mnemonic": u"مَفْعُولُنْ",
            "emeter": "---"
        }
        ]
        self.init(var)

# مُتَفَاعِلُنْ
class CCCVCCV(Tafiila):
    #varation
    def __init__(self, var=[SALIM]):
        self.feet = [
        {
            "var": SALIM,
            "mnemonic": u"مُتَفَاعِلُنْ",
            "emeter": "uu-u-"
        },
        {
            "var": IDHMAR,
            "mnemonic": u"مُتْفَاعِلُنْ",
            "emeter": "--u-"
        },
        {
            "var": WAQS,
            "mnemonic": u"مُفَاعِلُنْ",
            "emeter": "u-u-"
        },
        {
            "var": KHAZL,
            "mnemonic": u"مُتْفَعِلُنْ",
            "emeter": "u--"
        },
        {
            "var": TARFIIL,
            "mnemonic": u"مُتَفَاعِلَاتُنْ",
            "emeter": "uu-u--"
        },
        {
            "var": TADIIL,
            "mnemonic": u"مُتَفَاعِلَانْ",
            "emeter": "uu-u-:"
        },
        {
            "var": QATE,
            "mnemonic": u"مُتَفَاعِلْ",
            "emeter": "uu--:"
        },
        {
            "var": HADAD,
            "mnemonic": u"فِعْلُنْ",
            "emeter": "--"
        }
        ]
        self.init(var)

# مُفَاعَلَتُنْ
class CCVCCCV(Tafiila):
    #varation
    def __init__(self, var=[SALIM]):
        self.feet = [
        {
            "var": SALIM,
            "mnemonic": u"مُفَاعَلَتُنْ",
            "emeter": "u-uu-"
        },
        {
            "var": ASAB,
            "mnemonic": u"مُفَاعَلْتُنْ",
            "emeter": "u---"
        },
        {
            "var": AQL,
            "mnemonic": u"مُفَاعَتُنْ",
            "emeter": "u-u-"
        },
        {
            "var": NAQS,
            "mnemonic": u"مُفَاعَلْتُ",
            "emeter": "u--u"
        },
        {
            "var": QATF,
            "mnemonic": u"فَعُولُنْ",
            "emeter": "u--"
        }
        ]
        self.init(var)

# فَاعِلَاتُنْ
class CVCCVCV(Tafiila):
    #varation
    def __init__(self, var=[SALIM]):
        self.feet = [
        {
            "var": SALIM,
            "mnemonic": u"فَاعِلَاتُنْ",
            "emeter": "-u--"
        },
        {
            "var": KHABN,
            "mnemonic": u"فَعِلَاتُنْ",
            "emeter": "uu--"
        },
        {
            "var": KAFF,
            "mnemonic": u"فَاعِلَاتُ",
            "emeter": "-u-u"
        },
        {
            "var": ISBAGH,
            "mnemonic": u"فَاعِلَاتَانْ",
            "emeter": "-u--:"
        },
        {
            "var": HADF,
            "mnemonic": u"فَاعِلُنْ",
            "emeter": "-u-"
        },
        {
            "var": SHAKL,
            "mnemonic": u"فَعِلَاتُ",
            "emeter": "uu-u"
        },
        {
            "var": BATR,
            "mnemonic": u"فِعْلُنْ",
            "emeter": "--"
        },
        {
            "var": QASR,
            "mnemonic": u"فَاعِلَانْ",
            "emeter": "-u-:"
        }
        ]
        self.init(var)

# مَفْعُولَاتْ
# normaly, it is used in sarii, but it is used as fa3ilun

if __name__ == '__main__':
    c = CVCCV([SALIM, KHABN, QATE])
    print c.process("--u--u--u")