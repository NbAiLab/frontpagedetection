import sys
import os
#import numpy as np
import glob
import argparse
import requests
import time
from enum import Enum
import io
import json
import random
from random import randint
import shutil
from datetime import date,datetime

from PIL import Image
Image.MAX_IMAGE_PIXELS = None
import requests
from joblib import Parallel, delayed

from scipy import spatial
from transformers import ViTFeatureExtractor, ViTForImageClassification

import torch.nn.functional as nn
import torch
import random

import pickle
import numpy as np
import glob

papers=[]
bundlename=""


savedir="/nfsmounts/datastore/frontpageproductionresults"


logdir="log"
now = datetime.now()

logfile=logdir + "/frontpagelog_"+ now.strftime("%Y%m%d-%H")+ ".log"
logfp=open(logfile, "a+")



feature_extractor = ViTFeatureExtractor.from_pretrained('vit-front-page-384-top-v2/checkpoint-30000')
model = ViTForImageClassification.from_pretrained('vit-front-page-384-top-v2/checkpoint-30000')

#model = model.to(torch.device("cuda"))
model.eval()

firstpagevector=None
pages=[]

def classifyPageImage(image):
    inputs = feature_extractor(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs,output_hidden_states=True)

    v=outputs.hidden_states[-1][0][0].numpy()
    #print(v.shape)
    logits = outputs.logits

    predictions = outputs.logits.softmax(dim=-1)[0].numpy()


    resultstring = f"({predictions[0]:.3f};{predictions[1]:.3f};{predictions[2]:.3f})"

    predicted_class_idx = logits.argmax(-1).item()
    predclass=model.config.id2label[predicted_class_idx]


    return v,resultstring,predclass


def log(message):
    print(message)
    
    now = datetime.now()
    mystrdate=now.strftime("%Y/%m/%d %H:%M:%S")
    ostring=mystrdate + "\t\t" + str(message) + "\n"
    #print(ostring)
    logfp.write(ostring)
    logfp.flush()


class page:
    papername=""
    pageno=0
    tag="U"
    frontprobability=0
    middleprobability = 0
    backprobability = 0
    pagetype=""
    urn=""
    similarity=0.0
    vector=[]

    def __init__(self,papername):
        self.papername=papername
        self.pageno=""
        self.pagetype="U"
        self.tag="U"
        self.frontprobability = 0
        self.middleprobability = 0
        self.backprobability = 0
        self.urn=""
        self.similarityfront = 0.0
        self.similarityback = 0.0
        self.vector=[]

    def print(self):
        print("papername: " + str(self.papername))
        print("pagenumber: " + str(self.pageno))
        print("pagetype: " + str(self.pagetype))
        print("urn: " + str(self.urn))
        print("tag: " + str(self.tag))
        print("frontprobability: " + str(float(self.frontprobability)))
        print("middleprobability: " + str(self.middleprobability))
        print("backprobability: " + str(self.backprobability))
        print("similarityfront: " + str(self.similarityfront))
        print("similarityback: " + str(self.similarityback))
        print("*********************************************")


def fileexists(absfile):
    if os.path.isfile(absfile):
        return True
    else:
        return False

def makedirifnotexist(dir):
    if not os.path.isdir(dir):
        os.makedirs(dir)

def directoryexists(dir):
    if os.path.isdir(dir):
        return True
    else:
        return False

def getcurrentdate():
    today = date.today()
    return today.strftime("%d%m%Y")



def printresults(bundlename):
    currentdate = getcurrentdate()
    actualdir = savedir + "/" + currentdate
    makedirifnotexist(actualdir)
    resultfp = open(actualdir + "/" + str(bundlename) + "_top.list", "w")
    ostring=""
    ostring = bundlename + ":" + bundlename + ":"
    for ind, pg in enumerate(pages):
        ostring += "[" + str(ind + 1) + ",(" + str(pg.frontprobability) + ";" + str(pg.middleprobability) + ";" + str(pg.backprobability) + "),<" + str(pg.similarityfront) + ">," + "<" + str(pg.similarityback) + ">," + str(pg.pagetype) + "," + str(pg.tag) + "]"
        if pg != pages[-1]:
            ostring += ":"
        # print(ostring)
    resultfp.write(ostring)
    resultfp.write("\n")
    resultfp.flush()
    resultfp.close()


if __name__ == '__main__':
        # global firstpagevector

        parser = argparse.ArgumentParser()
        parser.add_argument('--masterpath', help='File with list of newspapers in the form <digavis*>', required=True,
                            type=str)
        args = parser.parse_args()
        bundles= sorted(glob.glob(args.masterpath + "/*/", recursive = True))


        for b in bundles:
            if b[-1] == "/":
                bundlename = b.split("/")[-2]
            else:
                bundlename = b.split("/")[-1]
            print("working with: " + str(bundlename))

            pages = []
            inputlist = glob.glob(args.masterpath + "/" + bundlename + "/**/*.tif", recursive=True)
            filelist=[]
            for f in inputlist:
                filelistelement=[]
                filelistelement.append(f.split("/")[-1])
                filelistelement.append(f)
                filelist.append(filelistelement)

            filelist.sort(key=lambda x: x[0], reverse=False)
            #print(inputlist)
            firstpagevector=None
            lastpagevector = None
            for cnt, pageimage in enumerate(filelist):
                pname = pageimage[0].split(".")[0]
                print("working with page: " + str(pname))
                vector = None
                accuracy = ""
                result = ""
                currentpage = page(pname)
                if "merge" not in pageimage[1]:
                    currentpage.pagetype="F"
                else:
                    currentpage.pagetype="U"

                image = Image.open(pageimage[1]).crop((150,500,4150,2000))
                try:
                    vector, accuracy, result = classifyPageImage(image)
                except:
                    image = image.convert("RGB")
                    vector, accuracy, result = classifyPageImage(image)

                currentpage.frontprobability = float(accuracy.split(";")[0].split("(")[1])
                currentpage.middleprobability = float(accuracy.split(";")[1])
                currentpage.backprobability = float(accuracy.split(";")[2].split(")")[0])

                if (currentpage.frontprobability > currentpage.middleprobability) and ((currentpage.frontprobability > currentpage.backprobability)):
                    currentpage.tag="F"

                if cnt == 0:
                    currentpage.similarityfront = 1.000
                    currentpage.similarityback = 0.000
                    firstpagevector = vector
                else:
                    currentpage.similarityfront = round(1 - spatial.distance.cosine(firstpagevector, vector), 3)

                #currentpage.print()
                currentpage.vector=vector

                lastpagevector = vector
                pages.append(currentpage)

            for cnt,p in enumerate(pages):
                if cnt != 0:
                    p.similarityback = round(1 - spatial.distance.cosine(lastpagevector, p.vector), 3)
            printresults(bundlename)
        now = datetime.now()
        mystrdate = now.strftime("%Y/%m/%d %H:%M:%S")
        ostring = mystrdate + "\n"

        finifp=open(args.masterpath + "/finished_top.status", "w")
        finfp.write(ostring)
        finfp.close()