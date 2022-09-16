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
import requests
from joblib import Parallel, delayed

papers_full=[]
bundles_full=[]

papers_top=[]
bundles_top=[]

frontthreshold=0.61
middlethreshold=0.0
backthreshold=0.0
combinedthreshold=0.0

highestresult=float(0)

logdir="log"
now = datetime.now()

logfile=logdir + "/frontpagelog_"+ now.strftime("%Y%m%d-%H")+ ".log"
logfp=open(logfile, "a+")
currentbundlesize=0


globalind=0
def log(message):
    #print(message)
    if message.startswith("#####"):
        now = datetime.now()
        mystrdate=now.strftime("%Y/%m/%d %H:%M:%S")
        ostring=mystrdate + "\t\t" + str(message) + "\n"
        #print(ostring)
        logfp.write(ostring)
        logfp.flush()


class page:
    bundlename=""
    papername=""
    pageno=0
    classifiedtag=""
    frontprobability=0
    middleprobability = 0
    backprobability = 0
    pagetype ="U"
    similarityfront=0
    similarityback = 0
    tupleform=""
    alg1 = "U"
    alg2 = "U"
    alg3 = "U"
    alg1_value = 0.0
    alg2_value = 0.0
    alg3_value = 0.0

    def __init__(self,bundlename,papername,pagespesification):
        self.bundlename=bundlename
        self.papername=papername
        #print(papername+"---->"+pagespesification)
        self.pageno=int(pagespesification.split("[")[1].split(",")[0])
        self.classifiedtag=pagespesification.split(",")[5].split("]")[0]
        self.frontprobability = float(pagespesification.split("[")[1].split(",")[1].split(";")[0].split("(")[1])
        self.middleprobability = float(pagespesification.split("[")[1].split(",")[1].split(";")[1])
        self.backprobability = float(pagespesification.split("[")[1].split(",")[1].split(";")[2].split(")")[0])
        self.pagetype = pagespesification.split(",")[4]
        self.similarityfront = pagespesification.split(",")[2].split("<")[1].split(">")[0]
        self.similarityback = pagespesification.split(",")[3].split("<")[1].split(">")[0]

        self.tupleform=pagespesification
        self.alg1 = "U"
        self.alg2 = "U"
        self.alg3 = "U"
        self.alg1_value = 0.0
        self.alg2_value = 0.0
        self.alg3_value = 0.0

    def print(self):
        print("bundlename: " + str(self.bundlename))
        print("papername: " + str(self.papername))
        print("pagenumber: " + str(self.pageno))
        print("pagetype: " + str(self.pagetype))
        print("classifiedtag: " + str(self.classifiedtag))
        print("frontprobability: " + str(float(self.frontprobability)))
        print("middleprobability: " + str(self.middleprobability))
        print("backprobability: " + str(self.backprobability))
        print("Similarityfront: " + str(self.similarityfront))
        print("Similarityback: " + str(self.similarityback))
        print("Alg 1: " + str(self.alg1) + " value: " + str(self.alg1_value))
        print("Alg 2: " + str(self.alg2) + " value: " + str(self.alg2_value))
        print("Alg 3: " + str(self.alg3) + " value: " + str(self.alg3_value))
        #print("Tupleform: " + str(self.tupleform))
        print("*********************************************")


class paper:
    bundlename="blabla bundle"
    papername="blabla"
    pages=[]
    pagecounter=0
    def __init__(self, bundlename,papername):
        self.bundlename=bundlename
        self.papername=papername
        self.pages=[]
        self.pagecounter = 0

    def __del__(self):
        del self.pages


    def appendpage(self,currentpage):
        self.pages.append(currentpage)
        self.pagecounter+=1
       # print("----> appending page")

    def print(self):
        print("*************** Start paper ****************************")
        print("bundlename: " + self.bundlename)
        print("papername: " + self.papername)
        print("pagecount: " + str(self.pagecounter))
        print("***************** Pages **************************")
        for p in self.pages:
            p.print()

class bundle():
    bundlename = "blabla bundle"
    papers=[]
    papercount=0
    pagecount=0

    def __init__(self, bundlename):
        self.bundlename=bundlename
        self.papers=[]
        self.papercount=0
        self.pagecount=0

    def __del__(self):
        del self.papers

    def appendpaper(self,pap):
        self.papers.append(pap)
        self.papercount+=1
        self.pagecount+=pap.pagecounter
        #print("----------->"+ str(pap.pagecounter))

    def print(self):
        print("Paper count: " + str(self.papercount))
        print("Bundle name: " + str(self.bundlename))
        for p in self.papers:
            p.print()

def makepaper_full(currentspesification):
    #print(currentspesification)
    paperspec=currentspesification.split(":")
    if (len(paperspec) <= 3):
        return
    bundlename=currentspesification.split(":")[0].split(".")[0]
    papername = currentspesification.split(":")[1]
    mycurrentpaper = paper(bundlename,papername)
    #print("Processing : " + bundlename + " " +papername)
    for ind,i in enumerate(paperspec):
        if ind > 1:
            mycurrentpage = page(bundlename,papername,i)
            mycurrentpaper.appendpage(mycurrentpage)


    papers_full.append(mycurrentpaper)

def makepaper_top(currentspesification):

    paperspec=currentspesification.split(":")
    if (len(paperspec) <= 3):
        return
    bundlename=currentspesification.split(":")[0].split(".")[0]
    papername = currentspesification.split(":")[1]
    mycurrentpaper = paper(bundlename,papername)

    for ind,i in enumerate(paperspec):
        if ind > 1:
            mycurrentpage = page(bundlename,papername,i)
            mycurrentpaper.appendpage(mycurrentpage)

    papers_top.append(mycurrentpaper)




def printfalsepositives():
    lines=0
    fp=0
    for p in papers_full:
        for pa in p.pages:
            lines+=1
            if pa.pagetype != "F" and pa.classifiedtag == "F" and float(pa.similarityfront) > 0.7:
                #pa.print()
                fp+=1

    print(str(fp)+ " false positives of "+ str(lines) + " pages")

def printfalsenegatives():
    lines=0
    fn=0
    for p in papers_full:
        for pa in p.pages:
            lines+=1
            if pa.pagetype == "F" and pa.classifiedtag != "F":
                #pa.print()
                fn+=1

    print(str(fn)+ " false negatives of "+ str(lines) + " pages")

def bundlesorganization():
    global bundles_full
    global bundles_top
    bname=papers_full[0].bundlename
    currentbundle=bundle(bname)

    for pa in papers_full:
        if (pa.bundlename == bname):
            #print("Appending paper:" + str(pa.papername) + " to bundle: " + pa.bundlename)
            currentbundle.appendpaper(pa)
        else:
            #print(currentbundle.bundlename + str(currentbundle.papercount))
            bundles_full.append(currentbundle)
            bname = pa.bundlename
            currentbundle = bundle(bname)
            currentbundle.appendpaper(pa)

    bundles_full.append(currentbundle)

    bname = papers_top[0].bundlename
    currentbundle = bundle(bname)
    for pa in papers_top:
        if (pa.bundlename == bname):
            currentbundle.appendpaper(pa)
        else:
            bundles_top.append(currentbundle)
            bname = pa.bundlename
            currentbundle = bundle(bname)
            currentbundle.appendpaper(pa)

    bundles_top.append(currentbundle)

def getpapertopindex(papername):
    for i,p in enumerate(papers_top):
        #print(p.papername+ " " + papername)
        if p.papername == papername:
            return i

    #print(str("Newspaper missing length paper_top:") + str(len(papers_top)) + str(" full:") + str(len(papers_full)) + " " + str(papername))
    return -1

def verifypapers():
    print(len(papers_top))
    print(len(papers_full))
    cnt = 0
    while (cnt < len(papers_full)):
        if papers_full[cnt].bundlename == papers_top[cnt].bundlename and papers_full[cnt].papername == papers_top[
            cnt].papername:
            print("ok")
        else:
            print("nok")
            exit(-1)
        cnt += 1


def verifybundles():
    print("papers in bundles")
    print(str(len(papers_full)) + " " + str(len(papers_top)))

    for ind,b in enumerate(papers_full):
        print(papers_full[ind].papername + " " + papers_top[ind].papername)




def evaluation_M3():

    for b in bundles_full:

        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                if float(pg.similarityfront) > 0.5 and (indpages % 2) !=0 :
                    pg.similarityfront=0.000

    for b in bundles_full:
        numberofpapers = len(b.papers)
        resultlist = []
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                element = []
                element.append(indpaper)
                element.append(indpages)
                element.append(pg.frontprobability)
                resultlist.append(element)

        resultlist.sort(key=lambda x: x[2], reverse=True)
        resultlist=resultlist[0:numberofpapers]
        #print(resultlist)

        correct=0
        for r in resultlist:
            if b.papers[r[0]].pages[r[1]].pagetype== "F":
                correct+=1
        #print(correct)

        if (correct == numberofpapers):
            print("M3," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(correct) + "," + str(b.papercount) + ",correct")
        else:
            print("M3," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(correct) + "," + str(b.papercount) + ",incorrect")



def evaluation_M2():
    for b in bundles_full:
        numberofpapers = len(b.papers)
        resultlist = []
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                if (indpages % 2) !=0 :
                    pg.similarityfront=0.000
    for b in bundles_top:
        numberofpapers = len(b.papers)
        resultlist = []
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                if (indpages % 2) !=0 :
                    pg.similarityfront=0.000

    # for b in bundles:
    #     numberofpapers = len(b.papers)
    #     resultlist = []
    #     for indpaper,pap in enumerate(b.papers):
    #         for indpages,pg in enumerate(pap.pages):
    #             if indpages< len(pap.pages)-1 and float(pg.similarityback) >0.6:
    #                 #print("M2:setting")
    #                 pap.pages[indpages+1].similarityfront=1.000
    #
    # for b in bundles:
    #     numberofpapers = len(b.papers)
    #     resultlist = []
    #     for indpaper,pap in enumerate(b.papers):
    #         for indpages,pg in enumerate(pap.pages):
    #             if (indpages % 2) !=0 :
    #                 pg.similarityfront=0.000

    for b in bundles_full:
        numberofpapers = len(b.papers)
        resultlist = []
        for indpaper,pap in enumerate(b.papers):
            toppaperind=getpapertopindex(pap.papername)
            for indpages,pg in enumerate(pap.pages):
                element = []
                element.append(indpaper)
                element.append(indpages)
                xindpaper=indpaper
                #print(indpaper)
                #print(indpages)
                if toppaperind != -1 and papers_top[toppaperind].pages[indpages].similarityfront > pg.similarityfront:
                    element.append((float(papers_top[toppaperind].pages[indpages].similarityfront)))
                else:
                    element.append((float(pg.similarityfront)))
                resultlist.append(element)
        tmplist = resultlist
        resultlist.sort(key=lambda x: x[2], reverse=True)

        resultlist=resultlist[0:numberofpapers]
        #print(resultlist)

        correct=0
        for r in resultlist:
            #print(b.papers[r[0]].pages[r[1]].pagetype)
            if b.papers[r[0]].pages[r[1]].pagetype == "F":
                correct+=1
        #print(correct)


        if (correct == numberofpapers):
            print("M2," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(
                correct) + "," + str(b.papercount) + ",correct")
        else:
            print("M2," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(
                correct) + "," + str(b.papercount) + ",incorrect")


def evaluation_M1():
    for b in bundles_full:
        numberofpapers = len(b.papers)
        resultlist = []
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                if pg.classifiedtag == "F" and (indpages % 2) !=0 :
                    pg.classifiedtag == "M"
    #print("method1")
    countpapers = 0
    for b in bundles_full:
        countpapers = 0
        correct = 0
        for p in b.papers:
            countpapers += 1
            illegalposition = False
            for pa in p.pages:
                if pa.pagetype == "F" and pa.classifiedtag == "F":
                    correct += 1
                elif pa.pagetype != "F" and pa.classifiedtag == "F":
                    correct += 1
                    illegalposition=True
        if (correct == countpapers and  illegalposition==False):
            print("M1,"+ str(b.bundlename) + "," +str(b.papercount) + "," + str(b.pagecount) + "," + str(correct)+","+str(countpapers) + ",correct")
        else:
           print("M1," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(correct) + "," + str(countpapers) + ",incorrect")

def evaluation_M4():
    for b in bundles_full:
        for indpaper, pap in enumerate(b.papers):
            pgcount = 1
            for indpages, pg in enumerate(pap.pages):
                if ((indpages % 2) != 0):
                    pg.similarityfront = 0.00
    countpapers = 0
    allcorrect=True
    for b in bundles_full:
        numberofpapers = len(b.papers)
        countpapers = 0
        correct = 0
        for p in b.papers:
            countpapers += 1
            for pa in p.pages:
                if pa.pagetype == "F" and (pa.classifiedtag == "F" or abs(float(pa.similarityfront)) > 0.7):
                    correct += 1
                elif  pa.pagetype != "F" and (pa.classifiedtag == "F" or abs(float(pa.similarityfront)) > 0.7):
                    allcorrect=False

        #print("M1: " + str(correct) + " real:" + str(countpapers))

        if (correct == numberofpapers and allcorrect== True):
            print("M4," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(correct) + "," + str(b.papercount) + ",correct")
        else:
            print("M4," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(correct) + "," + str(b.papercount) + ",incorrect")


def evaluation_M6():


    for b in bundles_full:
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                if (indpages % 2) !=0 :
                    pg.similarityfront=0.000


    for b in bundles_top:
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                if (indpages % 2) !=0 :
                    pg.similarityfront=0.000


    for b in bundles_full:
        numberofpapers = len(b.papers)
        resultlist = []
        for indpaper,pap in enumerate(b.papers):
            toppaperind=getpapertopindex(pap.papername)
            for indpages,pg in enumerate(pap.pages):
                element = []
                element.append(indpaper)
                element.append(indpages)
                xindpaper=indpaper
                #print(indpaper)
                #print(indpages)
                if pg.classifiedtag == "F":
                    pg.alg2="F"
                if indpaper==0 and indpages==0:
                    pg.alg3="F"
                elif indpages == 0:
                    if float(b.papers[indpaper-1].pages[-1].similarityback) > 0.2:
                        pg.alg3 = "F"
                else:
                    if float(b.papers[indpaper].pages[indpages-1].similarityback) > 0.2:
                        pg.alg3 = "F"
                if toppaperind != -1 and papers_top[toppaperind].pages[indpages].similarityfront > pg.similarityfront:
                    element.append((float(papers_top[toppaperind].pages[indpages].similarityfront)))
                else:
                    element.append((float(pg.similarityfront)))
                resultlist.append(element)

        resultlist.sort(key=lambda x: x[2], reverse=True)

        resultlist=resultlist[0:numberofpapers]



        for r in resultlist:
            b.papers[r[0]].pages[r[1]].alg1="F"

    for b in bundles_full:
        correct = 0
        numberofpapers = len(b.papers)
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                reslist=[]
                reslist.append(pg.alg1)
                reslist.append(pg.alg2)
                reslist.append(pg.alg3)
                if reslist.count("F") >= 2 and pg.pagetype == "F":
                    correct+=1


        if (correct == numberofpapers ):
            print("M6," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(
                correct) + "," + str(b.papercount) + ",correct")
        else:
            print("M6," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(
                correct) + "," + str(b.papercount) + ",incorrect")


def evaluation_M7():


    for b in bundles_full:
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                if (indpages % 2) !=0 :
                    pg.similarityfront=0.000


    for b in bundles_top:
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                if (indpages % 2) !=0 :
                    pg.similarityfront=0.000


    for b in bundles_full:
        numberofpapers = len(b.papers)
        resultlist = []
        resultlist2 = []
        for indpaper,pap in enumerate(b.papers):
            toppaperind=getpapertopindex(pap.papername)
            for indpages,pg in enumerate(pap.pages):
                element = []
                element2 = []
                element.append(indpaper)
                element2.append(indpaper)
                element.append(indpages)
                element2.append(indpages)


                element.append((float(pg.similarityfront)))
                element2.append((float(papers_top[toppaperind].pages[indpages].similarityfront)))

                if pg.classifiedtag == "F":
                    pg.alg2="F"

                resultlist.append(element)
                resultlist2.append(element2)

        resultlist.sort(key=lambda x: x[2], reverse=True)
        resultlist2.sort(key=lambda x: x[2], reverse=True)
        resultlist=resultlist[0:numberofpapers]
        resultlist2 = resultlist2[0:numberofpapers]

        for r in resultlist:
            b.papers[r[0]].pages[r[1]].alg1="F"
        for r in resultlist2:
            b.papers[r[0]].pages[r[1]].alg3="F"

    for b in bundles_full:
        correct = 0
        numberofpapers = len(b.papers)
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                reslist=[]
                reslist.append(pg.alg1)
                reslist.append(pg.alg2)
                reslist.append(pg.alg3)
                if reslist.count("F") >= 2 and pg.pagetype == "F":
                    correct+=1


        if (correct == numberofpapers ):
            print("M7," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(
                correct) + "," + str(b.papercount) + ",correct")
        else:
            print("M7," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(
                correct) + "," + str(b.papercount) + ",incorrect")


def evaluation_M8():


    for b in bundles_full:
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                if (indpages % 2) !=0 :
                    pg.similarityfront=0.000


    for b in bundles_top:
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                if (indpages % 2) !=0 :
                    pg.similarityfront=0.000


    for b in bundles_full:
        numberofpapers = len(b.papers)
        resultlist = []
        resultlist2 = []
        for indpaper,pap in enumerate(b.papers):
            toppaperind=getpapertopindex(pap.papername)
            for indpages,pg in enumerate(pap.pages):
                element = []
                element2 = []
                element.append(indpaper)
                element2.append(indpaper)
                element.append(indpages)
                element2.append(indpages)


                element.append((float(pg.similarityfront)))
                element2.append((float(papers_top[toppaperind].pages[indpages].similarityfront)))

                if papers_top[toppaperind].pages[indpages].classifiedtag == "F":
                    pg.alg2="F"

                resultlist.append(element)
                resultlist2.append(element2)

        resultlist.sort(key=lambda x: x[2], reverse=True)
        resultlist2.sort(key=lambda x: x[2], reverse=True)
        resultlist=resultlist[0:numberofpapers]
        resultlist2 = resultlist2[0:numberofpapers]

        for r in resultlist:
            b.papers[r[0]].pages[r[1]].alg1="F"
        for r in resultlist2:
            b.papers[r[0]].pages[r[1]].alg3="F"

    for b in bundles_full:
        correct = 0
        numberofpapers = len(b.papers)
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                reslist=[]
                reslist.append(pg.alg1)
                reslist.append(pg.alg2)
                reslist.append(pg.alg3)
                if reslist.count("F") >= 2 and pg.pagetype == "F":
                    correct+=1



        if (correct == numberofpapers ):
            print("M8," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(
                correct) + "," + str(b.papercount) + ",correct")
        else:
            print("M8," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(
                correct) + "," + str(b.papercount) + ",incorrect")

def evaluation_M9():


    for b in bundles_full:
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                if (indpages % 2) !=0 :
                    pg.similarityfront=0.000


    for b in bundles_top:
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                if (indpages % 2) !=0 :
                    pg.similarityfront=0.000


    for b in bundles_full:
        numberofpapers = len(b.papers)
        resultlist = []
        resultlist2 = []
        for indpaper,pap in enumerate(b.papers):
            toppaperind=getpapertopindex(pap.papername)
            for indpages,pg in enumerate(pap.pages):
                element = []
                element2 = []
                element.append(indpaper)
                element2.append(indpaper)
                element.append(indpages)
                element2.append(indpages)


                element.append((float(pg.similarityfront)))
                element2.append((float(papers_top[toppaperind].pages[indpages].similarityfront)))

                if pg.classifiedtag == "F":
                    pg.alg2="F"
                    pg.alg2_value=float(pg.frontprobability)

                resultlist.append(element)
                resultlist2.append(element2)

        resultlist.sort(key=lambda x: x[2], reverse=True)
        resultlist2.sort(key=lambda x: x[2], reverse=True)
        resultlist=resultlist[0:numberofpapers]
        resultlist2 = resultlist2[0:numberofpapers]

        for r in resultlist:
            b.papers[r[0]].pages[r[1]].alg1="F"
            b.papers[r[0]].pages[r[1]].alg1_value=float(r[2])
        for r in resultlist2:
            b.papers[r[0]].pages[r[1]].alg3="F"
            b.papers[r[0]].pages[r[1]].alg3_value=float(r[2])

    for b in bundles_full:
        correct = 0
        numberofpapers = len(b.papers)
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):

                max=pg.alg1_value

                result=pg.alg1
                if max < pg.alg2_value:
                    result = pg.alg2
                    max=pg.alg2_value
                if max < pg.alg3_value:
                    result = pg.alg3
                    max=pg.alg3_value

                if result=="F" and pg.pagetype == "F":
                    correct+=1



        if (correct == numberofpapers ):
            print("M9," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(
                correct) + "," + str(b.papercount) + ",correct")
        else:
            print("M9," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(
                correct) + "," + str(b.papercount) + ",incorrect")

def evaluation_M10():


    for b in bundles_full:
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                if (indpages % 2) !=0 :
                    pg.similarityfront=0.000


    for b in bundles_top:
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                if (indpages % 2) !=0 :
                    pg.similarityfront=0.000


    for b in bundles_full:

        numberofpapers = int(b.bundlename.split("_")[3])
        resultlist = []
        resultlist2 = []
        for indpaper,pap in enumerate(b.papers):
            toppaperind=getpapertopindex(pap.papername)
            for indpages,pg in enumerate(pap.pages):
                element = []
                element2 = []
                element.append(indpaper)
                element2.append(indpaper)
                element.append(indpages)
                element2.append(indpages)


                element.append((float(pg.similarityfront)))
                element2.append((float(papers_top[toppaperind].pages[indpages].similarityfront)))

                if pg.classifiedtag == "F":
                    pg.alg2="F"
                    if indpaper == 0 and indpages == 0:
                        pg.alg2_value=float(1.0)
                    elif indpages == 0:
                        # (0.75 * back + front) / (0.75 + 1) > 0.5
                        back=b.papers[indpaper - 1].pages[-1].backprobability
                        sim= (0.75 * back + pg.frontprobability)/1.75
                        pg.alg2_value = sim
                    else:
                        back=b.papers[indpaper].pages[indpages - 1].backprobability
                        sim = (0.75 * back + pg.frontprobability) / 1.75
                        pg.alg2_value = sim


                resultlist.append(element)
                resultlist2.append(element2)

        resultlist.sort(key=lambda x: x[2], reverse=True)
        resultlist2.sort(key=lambda x: x[2], reverse=True)
        resultlist=resultlist[0:numberofpapers]
        resultlist2 = resultlist2[0:numberofpapers]

        for r in resultlist:
            b.papers[r[0]].pages[r[1]].alg1="F"
            b.papers[r[0]].pages[r[1]].alg1_value=float(r[2])
        for r in resultlist2:
            b.papers[r[0]].pages[r[1]].alg3="F"
            b.papers[r[0]].pages[r[1]].alg3_value=float(r[2])

    for b in bundles_full:
        correct = 0
        bildenr=0
        forside=[]
        numberofpapers = int(b.bundlename.split("_")[3])
        for indpaper,pap in enumerate(b.papers):
            for indpages,pg in enumerate(pap.pages):
                bildenr+=1
                max=pg.alg1_value

                result=pg.alg1
                if max <= pg.alg2_value:
                    result = pg.alg2
                    max=pg.alg2_value
                if max <= pg.alg3_value:
                    result = pg.alg3
                    max=pg.alg3_value

                if result=="F" and pg.pagetype == "F":
                    correct+=1
                    forside.append(bildenr)



        if (correct == numberofpapers):
            ostring=""
            for f in forside:
                if f != forside[0] :
                    ostring += "," + str(f)
                else:
                    ostring += str(f)

            print("M10," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(correct) + "," + str(numberofpapers) + ",correct"+ "["+ ostring + "]")
        else:
            ostring = ""
            for f in forside:
                if  f != forside[0]  :
                    ostring += "," + str(f)
                else:
                    ostring += str(f)
            print("M10," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(
                correct) + "," + str(numberofpapers) + ",incorrect"+ "["+ ostring + "]")

            # for indpaper, pap in enumerate(b.papers):
            #     for indpages, pg in enumerate(pap.pages):
            #         if pg.classifiedtag != "F" and pg.pagetype == "F":
            #             pg.print()


def evaluation_M11():
    for b in bundles_full:
        for indpaper, pap in enumerate(b.papers):
            for indpages, pg in enumerate(pap.pages):
                if (indpages % 2) != 0:
                    pg.similarityfront = 0.000

    for b in bundles_top:
        for indpaper, pap in enumerate(b.papers):
            for indpages, pg in enumerate(pap.pages):
                if (indpages % 2) != 0:
                    pg.similarityfront = 0.000

    for b in bundles_full:
        for indpaper, pap in enumerate(b.papers):
            for indpages, pg in enumerate(pap.pages):
                if (indpages % 2) != 1:
                    pg.similarityback = 0.000

    for b in bundles_top:
        for indpaper, pap in enumerate(b.papers):
            for indpages, pg in enumerate(pap.pages):
                if (indpages % 2) != 1:
                    pg.similarityback = 0.000

    for b in bundles_full:
        numberofpapers = int(b.bundlename.split("_")[3])
        resultlist = []
        resultlist2 = []
        for indpaper, pap in enumerate(b.papers):
            toppaperind = getpapertopindex(pap.papername)
            for indpages, pg in enumerate(pap.pages):
                element = []
                element2 = []
                element.append(indpaper)
                element2.append(indpaper)
                element.append(indpages)
                element2.append(indpages)

                element.append((float(pg.similarityfront)))
                element2.append((float(papers_top[toppaperind].pages[indpages].similarityfront)))

                if pg.classifiedtag == "F":
                    pg.alg2 = "F"
                    if indpaper == 0 and indpages == 0:
                        pg.alg2_value = float(1.0)
                    elif indpages == 0:
                        # (0.75 * back + front) / (0.75 + 1) > 0.5
                        back = b.papers[indpaper - 1].pages[-1].backprobability
                        sim = (0.75 * back + pg.frontprobability) / 1.75
                        pg.alg2_value = sim
                    else:
                        back = b.papers[indpaper].pages[indpages - 1].backprobability
                        sim = (0.75 * back + pg.frontprobability) / 1.75
                        pg.alg2_value = sim

                resultlist.append(element)
                resultlist2.append(element2)

        resultlist.sort(key=lambda x: x[2], reverse=True)
        resultlist2.sort(key=lambda x: x[2], reverse=True)
        resultlist = resultlist[0:numberofpapers]
        resultlist2 = resultlist2[0:numberofpapers]

        for r in resultlist:
            b.papers[r[0]].pages[r[1]].alg1 = "F"
            b.papers[r[0]].pages[r[1]].alg1_value = float(r[2])
        for r in resultlist2:
            b.papers[r[0]].pages[r[1]].alg3 = "F"
            b.papers[r[0]].pages[r[1]].alg3_value = float(r[2])

    for b in bundles_full:
        correct = 0
        numberofpapers = int(b.bundlename.split("_")[3])
        fishy = False
        for indpaper, pap in enumerate(b.papers):
            for indpages, pg in enumerate(pap.pages):

                max = pg.alg1_value

                result = pg.alg1
                if max <= pg.alg2_value:
                    result = pg.alg2
                    max = pg.alg2_value
                if max <= pg.alg3_value:
                    result = pg.alg3
                    max = pg.alg3_value

                if result == "F" and pg.pagetype == "F":
                    correct += 1
                    #print("c " + str(max)+ " "+ str(pg.alg1_value))
                if result == "F" and pg.pagetype != "F":
                   fishy=True
                   #print("f " + str(max) + " " + str(pg.alg1_value))
        if (fishy):
            print("fishy")
        if (correct == numberofpapers):
            print("M11," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(correct) + "," + str(b.papercount) + ",correct")
        else:
            print("M11," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(correct) + "," + str(b.papercount) + ",incorrect")

def getnextset():
    global globalind
    sample_full=[]
    sample_top=[]
    #print(globalind)
    #print(len(results_full))
    if globalind >(len(results_full)-1):
        return sample_full, sample_top

    currentbundle=results_full[globalind].split(":")[0]
    firstbundle=currentbundle
    while (currentbundle==firstbundle):
        sample_full.append(results_full[globalind])
        sample_top.append(results_top[globalind])
        globalind+=1
        if globalind > (len(results_full)-1):
            return sample_full, sample_top
        currentbundle = results_full[globalind].split(":")[0]

    if validatesubset(sample_full,sample_top) == False:
        return getnextset()
    return sample_full,sample_top

def validatesubset(full,top):
    if len(full) != len(top):
        print("length mismatch of sets")
        return False
    for i,res in enumerate(full):
        if top[i].split(":")[0] != res.split(":")[0]:
            print ("Bundlename mismatch")
            return False
        if top[i].split(":")[1] != res.split(":")[1]:
            print("papername mismatch")
            return False
        fulllastpage=res.split(":")[-1].split(",")[0].split("[")[1]
        toplastpage=top[i].split(":")[-1].split(",")[0].split("[")[1]


        if int(fulllastpage) != int(toplastpage):
            print("different number of pages in paper")
            return False
        nopagesfull=len(res.split(":"))
        nopagestop = len(top[i].split(":"))
        if nopagesfull < 4 or nopagestop<4:
            return False
    return True


def evaluation_M12():
    for b in bundles_full:
        for indpaper, pap in enumerate(b.papers):
            for indpages, pg in enumerate(pap.pages):
                if (indpages % 2) != 0:
                    pg.similarityfront = 0.000

    for b in bundles_top:
        for indpaper, pap in enumerate(b.papers):
            for indpages, pg in enumerate(pap.pages):
                if (indpages % 2) != 0:
                    pg.similarityfront = 0.000

    for b in bundles_full:
        numberofpapers  = int(b.bundlename.split("_")[3])
        resultlist = []
        resultlist2 = []
        for indpaper, pap in enumerate(b.papers):
            toppaperind = getpapertopindex(pap.papername)
            for indpages, pg in enumerate(pap.pages):
                element = []
                element2 = []
                element.append(indpaper)
                element2.append(indpaper)
                element.append(indpages)
                element2.append(indpages)

                element.append((float(pg.similarityfront)))
                element2.append((float(papers_top[toppaperind].pages[indpages].similarityfront)))

                if pg.classifiedtag == "F":
                    pg.alg2 = "F"
                    if indpaper == 0 and indpages == 0:
                        pg.alg2_value = float(1.0)
                    elif indpages == 0:
                        # (0.75 * back + front) / (0.75 + 1) > 0.5
                        back = b.papers[indpaper - 1].pages[-1].backprobability
                        sim = (0.75 * back + pg.frontprobability) / 1.75
                        pg.alg2_value = sim
                    else:
                        back = b.papers[indpaper].pages[indpages - 1].backprobability
                        sim = (0.75 * back + pg.frontprobability) / 1.75
                        pg.alg2_value = sim

                resultlist.append(element)
                resultlist2.append(element2)

        resultlist.sort(key=lambda x: x[2], reverse=True)
        resultlist2.sort(key=lambda x: x[2], reverse=True)
        resultlist = resultlist[0:numberofpapers]
        resultlist2 = resultlist2[0:numberofpapers]

        for r in resultlist:
            b.papers[r[0]].pages[r[1]].alg1 = "F"
            b.papers[r[0]].pages[r[1]].alg1_value = float(r[2])
        for r in resultlist2:
            b.papers[r[0]].pages[r[1]].alg3 = "F"
            b.papers[r[0]].pages[r[1]].alg3_value = float(r[2])

    for b in bundles_full:
        correct = 0
        resultlist=[]
        numberofpapers  = int(b.bundlename.split("_")[3])
        for indpaper, pap in enumerate(b.papers):
            ostring=str(b.bundlename)+ ":" +str(pap.papername) + ":"
            justupdated = False
            for indpages, pg in enumerate(pap.pages):

                max = pg.alg1_value

                result = pg.alg1
                if max <= pg.alg2_value:
                    result = pg.alg2
                    max = pg.alg2_value
                if max <= pg.alg3_value:
                    result = pg.alg3
                    max = pg.alg3_value


                if result == "F" and pg.pagetype == "F" :
                  correct += 1
                if result == "F":
                    element = []
                    element.append(indpaper)
                    element.append(indpages)
                    element.append(float(max))
                    resultlist.append(element)

        resultlist.sort(key=lambda x: x[2], reverse=True)
        resultlist = resultlist[0:numberofpapers]
        for r in resultlist:
            if b.papers[r[0]].pages[r[1]].pagetype == "F":
                print("r")
            else:
                print("e")
        if (correct == numberofpapers):
            print("M12," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(correct) + "," + str(b.papercount) + ",correct")
        else:
            print("M12," + str(b.bundlename) + "," + str(b.papercount) + "," + str(b.pagecount) + "," + str(correct) + "," + str(b.papercount) + ",incorrect")

            # for indpaper, pap in enumerate(b.papers):
            #     for indpages, pg in enumerate(pap.pages):
            #         if pg.classifiedtag != "F" and pg.pagetype == "F":
            #             pg.print()



def runevaluations():
    # evaluation_M1()
    # evaluation_M2()
    # evaluation_M3()
    # evaluation_M4()
    # evaluation_M6()
    # evaluation_M7()
    # evaluation_M8()
    # evaluation_M9()
    # evaluation_M10()
    evaluation_M10()
    evaluation_M12()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--resultfile_full', help='File with results in the form <bundlename>,<digavis*>:<result>:...', required=True, type=str)
    parser.add_argument('--resultfile_top', help='File with results in the form  <bundlename>,<digavis*>:<result>:...',
                        required=True, type=str)
    args = parser.parse_args()
    results_full=sorted(open(args.resultfile_full,"r").readlines())
    results_top =sorted(open(args.resultfile_top, "r").readlines())

    papernames_full= set()
    papernames_top = set()
    for p in results_full:
        papernames_full.add(p.split(":")[1])
    for p in results_top:
        papernames_top.add(p.split(":")[1])

    allowedpapernames = papernames_top & papernames_full
    cleanresults_full=[]
    cleanresults_top = []
    for res in results_full:
        if res.split(":")[1] in allowedpapernames:
            cleanresults_full.append(res)

    results_full=cleanresults_full

    for res in results_top:
        if res.split(":")[1] in allowedpapernames:
            cleanresults_top.append(res)

    results_top = cleanresults_top
    ind =0
    sample_full, sample_top=getnextset()
    print("out")
    while len(sample_full) > 0:

        if len(sample_full) != len(sample_top):
            print("lengthmismatch full: " + str(len(sample_full))+ " top: " + str(len(sample_top)))
            sample_full, sample_top = getnextset()
            continue

        for cnt,r in enumerate(sample_full):
            if len(r.split(":")) != len(sample_top[cnt].split(":")):
                print("lenght error of tuple")
                print(r)
                print(sample_top[cnt])
        papers_full=[]
        for r in sample_full:
            papername=r.split(":")[1]
            if papername in allowedpapernames:
                makepaper_full(r)

        papers_top=[]
        for s in sample_top:
            papername = s.split(":")[1]
            if papername in allowedpapernames:
                makepaper_top(s)


        results=""
    #bundletest(20# )
    # for p in papers:
    #     p.print()

    #printfalsepositives()
    #printfalsenegatives()
    #print(papers_full[0].papername)
    #print(papers_top[0].papername)
    #exit(-1)
        #verifybundles()
        bundlesorganization()
        runevaluations()
        del papers_full
        del papers_top
        del bundles_full
        del bundles_top
        papers_full=[]
        bundles_full=[]

        papers_top=[]
        bundles_top=[]
        #del papers_top,papers_full,bundles_full,bundles_top
        sample_full, sample_top = getnextset()