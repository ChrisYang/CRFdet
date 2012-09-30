#function to detect using the CRF approach

import util
import numpy
import pylab
import pyrHOG2
import crf3
import drawHOG
import time
import copy
#from scipy.ndimage import zoom
from extra import myzoom as zoom

def refinePos(el):
    t=time.time()
    rescale=1.0
    #[f,det]=detectCRF.detectCrop(el)
    print "----Image-%s-(%d)-----------"%(el["file"].split("/")[-1],el["idim"])
    imname=el["file"]
    bbox=el["bbox"]
    models=el["models"]
    cfg=el["cfg"]
    imageflip=el["flip"]
    dratios=[]
    fy=[]
    fx=[]
    for m in models:
        fy.append(m["ww"][0].shape[0])
        fx.append(m["ww"][0].shape[1])
        dratios.append(fy[-1]/float(fx[-1]))
    fy=numpy.array(fy)
    fx=numpy.array(fx)
    dratios=numpy.array(dratios)
    #dratios=numpy.array(cfg.fy)/numpy.array(cfg.fx)
    img=util.myimread(imname,resize=cfg.resize)
    if imageflip:
        img=util.myimread(imname,True,resize=cfg.resize)
        if bbox!=None:
             bbox = util.flipBBox(img,[bbox])[0]
    maxy=numpy.max([x["ww"][0].shape[0] for x in models])    
    maxx=numpy.max([x["ww"][0].shape[1] for x in models])    
    if (bbox!=[]):
        marginy=(bbox[2]-bbox[0])*0.5 #safe margin to be sure the border is not used
        marginx=(bbox[3]-bbox[1])*0.5
        y1=max(0,bbox[0]-marginy);x1=max(0,bbox[1]-marginx)
        y2=min(bbox[2]+marginy,img.shape[0]);x2=min(bbox[3]+marginx,img.shape[1])
        img=img[y1:y2,x1:x2]
        newbbox=(bbox[0]-y1,bbox[1]-x1,bbox[2]-y1,bbox[3]-x1)
        cropratio= marginy/float(marginx)
        dist=abs(numpy.log(dratios)-numpy.log(cropratio))
        idm=numpy.where(dist<0.4)[0] #
        if cfg.rescale and len(idm)>0:
            tiley=(marginy*2)/numpy.max(fy[idm])
            tilex=(marginx*2)/numpy.max(fx[idm])
            if tiley>16 and tilex>16:
                rescale=16/float(min(tiley,tilex))
                img=zoom(img,(rescale,rescale,1),order=1)
                newbbox=numpy.array(newbbox)*rescale
        if cfg.useclip:
            if bbox[4]==1:# use all models for truncated
                #print "TRUNCATED!!!"
                idm=range(len(models)) 
        selmodels=[models[x] for x in idm] 
        if cfg.usebbPOS:
            [f,det]=rundetbb(img,cfg,selmodels,numdet=cfg.numhypPOS, interv=cfg.intervPOS,aiter=cfg.aiterPOS,restart=cfg.restartPOS)
        else:         
            [f,det]=rundet(img,cfg,selmodels,numhyp=cfg.numhypPOS,interv=cfg.intervPOS,aiter=cfg.
aiterPOS,restart=cfg.restartPOS)
    #else: #for negatives
    #    [f,det]=rundet(img,cfg,models)
    print "Detection time:",time.time()-t
    #detectCRF.check(det[:10],f,models)
    boundingbox(det)
    if cfg.useclip:
        clip(det,img.shape)
    #detectCRF.visualize(det[:10],f,img,cfgpos)
    bestscr=-100
    best=-1
    for idl,l in enumerate(det):
        ovr=util.overlap(newbbox,l["bbox"])
        if ovr>cfg.posovr and l["scr"]>cfg.posthr:#valid detection
            if l["scr"]>bestscr:
                best=idl
                bestscr=l["scr"]
    if len(det)>0 and best!=-1:
        if cfg.show:
            visualize([det[best]],f,img)
        feat,edge=getfeature([det[best]],f,models,cfg.bias)
        #add image name and bbx so that each annotation is unique
        if imageflip:
            det[best]["idim"]=el["file"].split("/")[-1]+".flip"
        else:
            det[best]["idim"]=el["file"].split("/")[-1]
        det[best]["idbb"]=el["idbb"]
        #add bias
        #det[best]["scr"]-=models[det[best]["id"]]["rho"]/float(cfg.bias)
        return det[best],feat[0],edge[0],[rescale,y1,x1,y2,x2]#last just for drawing
    return [],[],[],[rescale,y1,x1,y2,x2]

def hardNeg(el):
    t=time.time()
    #[f,det]=detectCRF.detectCrop(el)
    print "----Image-%s-(%d)-----------"%(el["file"].split("/")[-1],el["idim"])
    imname=el["file"]
    bbox=el["bbox"]
    models=el["models"]
    cfg=el["cfg"]
    #cfg.numhyp=1 #make the search for negatives 5 times faster
    #                #but you should check if generates problems
    imageflip=el["flip"]
    if imageflip:
        img=util.myimread(imname,True,resize=cfg.resize)
    else:
        img=util.myimread(imname,resize=cfg.resize)
    #imageflip=el["flip"]
    if cfg.usebbNEG:
        [f,det]=rundetbb(img,cfg,models,numdet=cfg.numhypNEG,interv=cfg.intervNEG,aiter=cfg.aiterNEG,restart=cfg.restartNEG)
    else:
        [f,det]=rundet(img,cfg,models,numhyp=cfg.numhypNEG,interv=cfg.intervNEG,aiter=cfg.aiterNEG,restart=cfg.restartNEG)
    ldet=[]
    lfeat=[]
    ledge=[]
    for idl,l in enumerate(det[:cfg.numneg]):
        #add bias
        #det[idl]["scr"]-=models[det[idl]["id"]]["rho"]/float(cfg.bias)
        if det[idl]["scr"]>-1:
            det[idl]["idim"]=el["file"].split("/")[-1]
            ldet.append(det[idl])
            feat,edge=getfeature([det[idl]],f,models,cfg.bias)
            lfeat+=feat
            ledge+=edge
    if cfg.show:
        visualize(ldet,f,img)
    print "Detection time:",time.time()-t
    print "Found %d hard negatives"%len(ldet)
    return ldet,lfeat,ledge

def hardNegPos(el):
    t=time.time()
    #[f,det]=detectCRF.detectCrop(el)
    print "----Image-%s-(%d)-----------"%(el["file"].split("/")[-1],el["idim"])
    imname=el["file"]
    bbox=el["bbox"]
    models=el["models"]
    cfg=el["cfg"]
    #cfg.numhyp=1 #make the search for negatives 5 times faster
    #                #but you should check if generates problems
    imageflip=el["flip"]
    if imageflip:
        img=util.myimread(imname,True,resize=cfg.resize)
    else:
        img=util.myimread(imname,resize=cfg.resize)
    #imageflip=el["flip"]
    if cfg.usebbNEG:
        [f,det]=rundetbb(img,cfg,models,numdet=cfg.numhypNEG,interv=cfg.intervNEG,aiter=cfg.aiterNEG,restart=cfg.restartNEG)
    else:
        [f,det]=rundet(img,cfg,models,numhyp=cfg.numhypNEG,interv=cfg.intervNEG,aiter=cfg.aiterNEG,restart=cfg.restartNEG)
    ldet=[]
    lfeat=[]
    ledge=[]
    boundingbox(det)
    if cfg.useclip:
        clip(det,img.shape)
    for idl,l in enumerate(det):#(det[:cfg.numneg]):
        #add bias
        #det[idl]["scr"]-=models[det[idl]["id"]]["rho"]/float(cfg.bias)
        skip=False
        if det[idl]["scr"]>-1:
            for gt in bbox:
                ovr=util.overlap(det[idl]["bbox"],gt)
                if ovr>0.3 and (cfg.db!="inria" or ovr<0):#is not a false positive 
                    skip=True
                    break
            if not(skip):
                det[idl]["idim"]=el["file"].split("/")[-1]
                ldet.append(det[idl])
                feat,edge=getfeature([det[idl]],f,models,cfg.bias)
                lfeat+=feat
                ledge+=edge
        if len(ldet)==cfg.numneg:
            break
    if cfg.show:
        visualize(ldet,f,img)
    print "Detection time:",time.time()-t
    print "Found %d hard negatives"%len(ldet)
    return ldet,lfeat,ledge


def test(el,docluster=True,show=False,inclusion=False,onlybest=False):
    t=time.time()
    #[f,det]=detectCRF.detectCrop(el)
    print "----Image-%s-(%d)-----------"%(el["file"].split("/")[-1],el["idim"])
    imname=el["file"]
    bbox=el["bbox"]
    models=el["models"]
    cfg=el["cfg"]
    imageflip=el["flip"]
    if imageflip:
        img=util.myimread(imname,True,resize=cfg.resize)
    else:
        img=util.myimread(imname,resize=cfg.resize)
    #imageflip=el["flip"]
    if cfg.usebbTEST:
        [f,det]=rundetbb(img,cfg,models,numdet=cfg.numhypTEST,interv=cfg.intervTEST,aiter=cfg.aiterTEST,restart=cfg.restartTEST)
    else:
        [f,det]=rundet(img,cfg,models,numhyp=cfg.numhypTEST,interv=cfg.intervTEST,aiter=cfg.aiterTEST,restart=cfg.restartTEST)
    boundingbox(det)
    if cfg.useclip:
        clip(det,img.shape)
    if docluster:
        #det=cluster(det,maxcl=100,inclusion=False)
        det=cluster(det,maxcl=100,inclusion=inclusion,onlybest=onlybest)
    for idl,l in enumerate(det):
        det[idl]["idim"]=el["file"].split("/")[-1]
    if show:
        visualize(det[:5],f,img)
    print "Detection time:",time.time()-t
    return det


def cluster(det,ovr=0.5,maxcl=20,inclusion=False,onlybest=False):
    """
    cluster detection with a minimum area k of overlapping
    """
    cllist=[]
    for ls in det:
        found=False
        for cl in cllist:
            for cle in cl:
                if not(inclusion):
                    myovr=util.overlap(ls["bbox"],cle["bbox"])
                else:   
                    myovr=util.inclusion(ls["bbox"],cle["bbox"])
                if myovr>ovr:
                    if not(onlybest):
                        cl.append(ls)
                    found=True
                    break
        if not(found):
            if len(cllist)<maxcl:
                cllist.append([ls])
            else:
                break
    return [el[0] for el in cllist]


def check(det,f,models,bias):
    """ check if score of detections and score from features are correct"""
    for l in range(len(det)):#lsort[:100]:
        scr=det[l]["scr"]
        idm=det[l]["id"]
        r=det[l]["hog"]    
        m1=models[idm]["ww"][0]
        m2=f.hog[r]
        res=det[l]["def"]
        mcost=models[idm]["cost"].astype(numpy.float32)
        dfeat,edge=crf3.getfeat_full(m2,0,res)
        print "Scr",numpy.sum(m1*dfeat)+numpy.sum(edge*mcost)-models[idm]["rho"],"Error",numpy.sum(m1*dfeat)+numpy.sum(edge*mcost)-scr-models[idm]["rho"]
        if numpy.sum(m1*dfeat)+numpy.sum(edge*mcost)-scr-models[idm]["rho"]>0.0001:
            printf("Error %f too big, there is something wrong!!!"%(numpy.sum(m1*dfeat)+numpy.sum(edge*mcost)-scr-models[idm]["rho"]))
            raw_input()

def getfeature(det,f,models,bias):
    """ check if score of detections and score from features are correct"""
    lfeat=[];ledge=[]
    for l in range(len(det)):#lsort[:100]:
        scr=det[l]["scr"]
        idm=det[l]["id"]
        r=det[l]["hog"]    
        m1=models[idm]["ww"][0]
        m2=f.hog[r]
        res=det[l]["def"]
        mcost=models[idm]["cost"].astype(numpy.float32)
        dfeat,edge=crf3.getfeat_full(m2,0,res)
        lfeat.append(dfeat)
        ledge.append(edge)
        #print "Scr",numpy.sum(m1*dfeat)+numpy.sum(edge*mcost)-models[idm]["rho"],"Error",numpy.sum(m1*dfeat)+numpy.sum(edge*mcost)-scr-models[idm]["rho"]
        if numpy.sum(m1*dfeat)+numpy.sum(edge*mcost)-scr-models[idm]["rho"]>0.0001:
            print("Error %f too big, there is something wrong!!!"%(numpy.sum(m1*dfeat)+numpy.sum(edge*mcost)-scr-models[idm]["rho"]))
            raw_input()
    return lfeat,ledge


def boundingbox(det):
    """extract the detection boundig box"""
    for l in range(len(det)):
        scl=det[l]["scl"]
        scr=det[l]["scr"]
        idm=det[l]["id"]
        r=det[l]["hog"]    
        #m2=f.hog[r]
        res=det[l]["def"]
        pos=numpy.zeros(res.shape)
        sf=int(8*2/scl)
        for px in range(res.shape[2]):
            for py in range(res.shape[1]):
                #util.box(py*2*hogpix+res[0,py,px]*hogpix,px*2*hogpix+res[1,py,px]*hogpix,py*2*hogpix+res[0,py,px]*hogpix+2*hogpix,px*2*hogpix+res[1,py,px]*hogpix+2*hogpix, col=col[fres.shape[0]-hy-1], lw=2)  
                pos[0,py,px]=(py)*sf+(res[0,py,px]+1)*sf/2
                pos[1,py,px]=(px)*sf+(res[1,py,px]+1)*sf/2
        det[l]["bbox"]=(numpy.min(pos[0]),numpy.min(pos[1]),numpy.max(pos[0])+sf,numpy.max(pos[1])+sf)

def clip(det,imsize):#imsize(y,x)
    """clip the deteciton bboxes to be inside the image"""
    for idl,l in enumerate(det):
        #print l["bbox"],
        y1=max(0,l["bbox"][0])
        x1=max(0,l["bbox"][1])
        y2=min(imsize[0],l["bbox"][2])
        x2=min(imsize[1],l["bbox"][3])
        det[idl]["bbox"]=(y1,x1,y2,x2)
        #print det[idl]["bbox"]

def visualize(det,f,img):
    """visualize a detection and the corresponding featues"""
    pl=pylab
    col=['w','r','g','b','y','c','k','y','c','k']
    pl.figure(300,figsize=(15,5))
    pl.clf()
    pl.subplot(1,3,1)
    pl.imshow(img)
    im=img
    pad=0
    cc=0
    #rcim=numpy.array([])
    for l in range(len(det)):#lsort[:100]:
        scl=det[l]["scl"]
        idm=det[l]["id"]
        r=det[l]["hog"]
        res=det[l]["def"]
        scr=det[l]["scr"]
        numy=det[l]["def"].shape[1]#cfg.fy[idm]
        numx=det[l]["def"].shape[2]#cfg.fx[idm]
        sf=int(8*2/scl)
        #m1=models[idm]["ww"][0]
        m2=f.hog[r]
        #mcost=models[idm]["cost"].astype(numpy.float32)
        if l==0:
           im2=numpy.zeros((im.shape[0]+sf*numy*2,im.shape[1]+sf*numx*2,im.shape[2]),dtype=im.dtype)
           im2[sf*numy:sf*numy+im.shape[0],sf*numx:sf*numx+im.shape[1]]=im
           rcim=numpy.zeros((sf*numy,sf*numx,3),dtype=im.dtype)
        dfeat,edge=crf3.getfeat_full(m2,pad,res)
        #print "Scr",numpy.sum(m1*dfeat)+numpy.sum(edge*mcost),"Error",numpy.sum(m1*dfeat)+numpy.sum(edge*mcost)-scr
        pl.subplot(1,3,1)
        for px in range(res.shape[2]):
            for py in range(res.shape[1]):
                #util.box(py*2*hogpix+res[0,py,px]*hogpix,px*2*hogpix+res[1,py,px]*hogpix,py*2*hogpix+res[0,py,px]*hogpix+2*hogpix,px*2*hogpix+res[1,py,px]*hogpix+2*hogpix, col=col[fres.shape[0]-hy-1], lw=2)  
                impy=(py)*sf+(res[0,py,px]+1)*sf/2
                impx=(px)*sf+(res[1,py,px]+1)*sf/2
                util.box(impy,impx,impy+sf,impx+sf, col=col[cc%10], lw=1.5)  
                if det[l].has_key("bbox"):
                    util.box(det[l]["bbox"][0],det[l]["bbox"][1],det[l]["bbox"][2],det[l]["bbox"][3],col=col[cc%10],lw=2)
                #rcim[sf*py:sf*(py+1),sf*px:sf*(px+1)]=im2[sf*numy+impy:sf*numy+impy+sf,sf*numx+impx:sf*
                #util.box(py*2*hogpix+res[0,py,px]*hogpix,px*2*hogpix+res[1,py,px]*hogpix,py*2*hogpix+res[0,py,px]*hogpix+2*hogpix,px*2*hogpix+res[1,py,px]*hogpix+2*hogpix, col=col[fres.shape[0]-hy-1], lw=2)  
                if l==0:
                    rcim[sf*py:sf*(py+1),sf*px:sf*(px+1)]=im2[sf*numy+impy:sf*numy+impy+sf,sf*numx+impx:sf*numx+impx+sf] 
        cc+=1
        if l==0:
            pl.subplot(1,3,2)
            hdet=drawHOG.drawHOG(dfeat)
            pl.imshow(hdet)
            pl.subplot(1,3,3)
            pl.title("%f"%scr)
            pl.imshow(rcim)    
    pl.subplot(1,3,1)    
    #pl.axis([0,img.shape[1],0,img.shape[0]])
    pl.axis("image")
    pl.draw()
    pl.show()
    #raw_input()

def visualize2(det,img,bb=[],text=""):
    """visualize a detection and the corresponding featues"""
    pl=pylab
    col=['w','r','g','b','y','c','k','y','c','k']
    pl.figure(300,figsize=(8,4))
    pl.clf()
    pl.subplot(1,2,1)
    pl.title(text)
    pl.imshow(img)
    im=img
    pad=0
    cc=0
    if bb!=[]:
        util.box(bb[0],bb[1],bb[2],bb[3], col="b--", lw=2)  
    for l in range(len(det)):#lsort[:100]:
        scl=det[l]["scl"]
        idm=det[l]["id"]
        r=det[l]["hog"]
        res=det[l]["def"]
        scr=det[l]["scr"]
        numy=det[l]["def"].shape[1]#cfg.fy[idm]
        numx=det[l]["def"].shape[2]#cfg.fx[idm]
        sf=int(8*2/scl)
        #m2=f.hog[r]
        if l==0:
           im2=numpy.zeros((im.shape[0]+sf*numy*2,im.shape[1]+sf*numx*2,im.shape[2]),dtype=im.dtype)
           im2[sf*numy:sf*numy+im.shape[0],sf*numx:sf*numx+im.shape[1]]=im
           rcim=numpy.zeros((sf*numy,sf*numx,3),dtype=im.dtype)
        #dfeat,edge=crf3.getfeat_full(m2,pad,res)
        pl.subplot(1,2,1)
        for px in range(res.shape[2]):
            for py in range(res.shape[1]):
                impy=(py)*sf+(res[0,py,px]+1)*sf/2
                impx=(px)*sf+(res[1,py,px]+1)*sf/2
                util.box(impy,impx,impy+sf,impx+sf, col=col[cc%10], lw=1.5)  
                if det[l].has_key("bbox"):
                    util.box(det[l]["bbox"][0],det[l]["bbox"][1],det[l]["bbox"][2],det[l]["bbox"][3],col=col[cc%10],lw=2)
                if l==0:
                    rcim[sf*py:sf*(py+1),sf*px:sf*(px+1)]=im2[sf*numy+impy:sf*numy+impy+sf,sf*numx+impx:sf*numx+impx+sf] 
        cc+=1
        if l==0:
            pl.subplot(1,2,2)
            pl.title("scr:%.3f id:%d"%(scr,idm))
            pl.imshow(rcim)    
    pl.subplot(1,2,1)    
    pl.axis("image")
    pl.draw()
    pl.show()


def rundet(img,cfg,models,numhyp=5,interv=10,aiter=3,restart=0):
    notsave=False
    #print "Normal"
    f=pyrHOG2.pyrHOG(img,interv=interv,savedir=cfg.auxdir+"/hog/",notsave=not(cfg.savefeat),notload=not(cfg.loadfeat),hallucinate=True,cformat=True)#,flip=imageflip,resize=cfg.resize)
    det=[]
    for idm,m in enumerate(models):
        mcost=m["cost"].astype(numpy.float32)
        m1=m["ww"][0]
        numy=m["ww"][0].shape[0]#models[idm]["ww"][0].shape[0]#cfg.fy[idm]
        numx=m["ww"][0].shape[1]#models[idm]["ww"][0].shape[1]#cfg.fx[idm]
        for r in range(len(f.hog)):#otherwise crashes should be checked!!!!
            #if numpy.min(f.hog[r].shape[:-1])<max(numy,numx):
            #    break
            m2=f.hog[r]
            #print numy,numx
            lscr,fres=crf3.match_full2(m1,m2,mcost,show=False,feat=False,rot=False,numhyp=numhyp,aiter=aiter,restart=restart)
            #print "Total time",time.time()-t
            #print "Score",lscr
            idraw=False
            if idraw:
                import drawHOG
                #rec=drawHOG.drawHOG(dfeat)
                pylab.figure(figsize=(15,5))
                #subplot(1,2,1)
                #imshow(rec)
                pylab.title("Reconstructed HOG Image (Learned Costs)")
                pylab.subplot(1,2,2)
                img=drawHOG.drawHOG(m2)
            for idt in range(len(lscr)):
                det.append({"id":m["id"],"hog":r,"scl":f.scale[r],"def":fres[idt],"scr":lscr[idt]-models[idm]["rho"]})
    det.sort(key=lambda by: -by["scr"])
    if cfg.show:
        pylab.draw()
        pylab.show()
    return [f,det]

def rundetbb(img,cfg,models,numdet=50,interv=10,aiter=3,restart=0):
    #notsave=False
    #print "Branc and bound"
    f=pyrHOG2.pyrHOG(img,interv=interv,savedir=cfg.auxdir+"/hog/",notsave=not(cfg.savefeat),notload=not(cfg.loadfeat),hallucinate=True,cformat=True)
    ldet2=[]
    for idm,m in enumerate(models):
        mcost=m["cost"].astype(numpy.float32)
        m1=m["ww"][0]
        numy=m["ww"][0].shape[0]#models[idm]["ww"][0].shape[0]#cfg.fy[idm]
        numx=m["ww"][0].shape[1]#models[idm]["ww"][0].shape[1]#cfg.fx
        ldet=crf3.match_bb(m1,f.hog,mcost,show=False,rot=False,numhyp=numdet,aiter=aiter,restart=restart)
        for l in ldet:
            r=l["scl"]
            ldet2.append({"id":m["id"],"hog":r,"scl":f.scale[r],"def":l["def"][0],"scr":l["scr"]-models[idm]["rho"]})            
    ldet2.sort(key=lambda by: -by["scr"])
    return [f,ldet2]


def detectCrop(a):
    """
        substitutes the entire image with the corresponding bounding box if there
    """
    i=a["idim"]
    imname=a["file"]
    bbox=a["bbox"]
    models=a["models"]
    cfg=a["cfg"]
    imageflip=a["flip"]
    #if len(a)<=5:
    #    imageflip=False
    #else:
    #    imageflip=a[5]
    img=util.myimread(imname,resize=cfg.resize)
    if imageflip:
        img=util.myimread(imname,True,resize=cfg.resize)
        if bbox!=None:
             bbox = util.flipBBox(img,bbox)
    #maxy=numpy.min([x["ww"][0].shape[0] for x in models])    
    #maxx=numpy.min([x["ww"][0].shape[1] for x in models])    
    if (bbox!=[]):
        marginy=(bbox[2]-bbox[0])*0.5 #safe margin to be sure the border is not used
        marginx=(bbox[3]-bbox[1])*0.5
        y1=max(0,bbox[0]-marginy);x1=max(0,bbox[1]-marginx)
        y2=min(bbox[2]+marginy,img.shape[0]);x2=min(bbox[3]+marginx,img.shape[1])
        img=img[y1:y2,x1:x2]
    res=rundet(img,cfg,models)
    return res



