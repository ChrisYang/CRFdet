#some additional functions

import numpy
import pyrHOG2

def getfeat(a,y1,y2,x1,x2,trunc=0):
    """
        returns the hog features at the given position and 
        zeros in case the coordiantes are outside the borders
        """
    dimy=a.shape[0]
    dimx=a.shape[1]
    py1=y1;py2=y2;px1=x1;px2=x2
    dy1=0;dy2=0;dx1=0;dx2=0
    #if trunc>0:
    b=numpy.zeros((abs(y2-y1),abs(x2-x1),a.shape[2]+trunc),dtype=a.dtype)
    if trunc>0:
        b[:,:,-trunc]=1
    #else:
    #    b=numpy.zeros((abs(y2-y1),abs(x2-x1),a.shape[2]))
    if py1<0:
        py1=0
        dy1=py1-y1
    if py2>=dimy:
        py2=dimy
        dy2=y2-py2
    if px1<0:
        px1=0
        dx1=px1-x1
    if px2>=dimx:
        px2=dimx
        dx2=x2-px2
    if numpy.array(a[py1:py2,px1:px2].shape).min()==0 or numpy.array(b[dy1:y2-y1-dy2,dx1:x2-x1-dx2].shape).min()==0:
        pass
    else:
        if trunc==1:
            b[dy1:y2-y1-dy2,dx1:x2-x1-dx2,:-1]=a[py1:py2,px1:px2]
            #b[:,:,-1]=1
            b[dy1:y2-y1-dy2,dx1:x2-x1-dx2,-1]=0
        else:
            b[dy1:y2-y1-dy2,dx1:x2-x1-dx2]=a[py1:py2,px1:px2]
    return b

def myzoom(img,factor,order):
    auxf=numpy.array(factor)
    order=1 #force order to be 1 otherwise I do not know if it is still correct
    from scipy.ndimage import zoom
    aux=img.copy()
    while (auxf[0]<0.5 and auxf[1]<0.5):
        aux=zoom(aux,(0.5,0.5,1),order=order)
        auxf[0]=auxf[0]*2
        auxf[1]=auxf[1]*2
    aux=zoom(aux,auxf,order=order)
    return aux

def flip(m):
    """
    flip of the object model
    """  
    ww1=[]
    df1=[]
    for l in m["ww"]:
        ww1.append(numpy.ascontiguousarray(pyrHOG2.hogflip(l)))
    m1={"ww":ww1,"rho":m["rho"],"fy":ww1[0].shape[0],"fx":ww1[0].shape[1]}
    if m.has_key("id"):
        m1["id"]=m["id"]
    if m.has_key("cost"):
        m1["cost"]=pyrHOG2.crfflip(m["cost"])
    if m.has_key("big"):
        m1["big"]=m["big"]
    if m.has_key("norm"):
        m1["norm"]=m["norm"]
    if m.has_key("N"):
        m1["N"]=m["N"]
    if m.has_key("E"):
        m1["E"]=m["E"]
    if m.has_key("facial"):
        m1["facial"]=m["facial"].copy()
        m1["facial"][1::2]=(m1["ww"][0].shape[1]*(m["N"]/float(m["N"]+2*m["E"])))-m["facial"][1::2]
        #m1["facial"][1::2]=(m1["ww"][0].shape[1])-m["facial"][1::2]
    return m1    

def locatePoints(det,N,points,sbin=8):
    """visualize a detection and the corresponding featues"""
    fp=[]
    for l in range(len(det)):#lsort[:100]:
        fp.append([])
        res=det[l]["def"]
        for pp in range(len(points)/2):
            py=points[pp*2]/N
            px=points[pp*2+1]/N
            ppy=float(points[pp*2])/N
            ppx=float(points[pp*2+1])/N
            scl=det[l]["scl"]
            sf=float(sbin*N/scl)
            impy=int((ppy)*sf+(res[0,py,px]+1)*sf/N)
            impx=int((ppx)*sf+(res[1,py,px]+1)*sf/N)
            fp[-1]+=[impy,impx]
    return fp

def locatePointsInter(det,N,points):
    """visualize a detection and the corresponding featues"""
    fp=[]
    for l in range(len(det)):#lsort[:100]:
        fp.append([])
        res=det[l]["def"]
        for pp in range(len(points)/2):
            py=float(points[pp*2])/N
            px=float(points[pp*2+1])/N
            #ppy=float(py)
            #ppx=float(px)
            ipy=int(float(points[pp*2])/N-N/2)#this is wrong, should be 0.5 and not N/2
            ipx=int(float(points[pp*2+1])/N-N/2)
            dy=float((points[pp*2]-N/2)%N)/N
            dx=float((points[pp*2+1]-N/2)%N)/N
            scl=det[l]["scl"]
            sf=float(8*N/scl)
            impy0=int((py)*sf+(res[0,ipy,ipx]+1)*sf/N)
            impx0=int((px)*sf+(res[1,ipy,ipx]+1)*sf/N)
            impy1=int((py)*sf+(res[0,ipy,ipx+1]+1)*sf/N)
            impx1=int((px)*sf+(res[1,ipy,ipx+1]+1)*sf/N)
            impy2=int((py)*sf+(res[0,ipy+1,ipx]+1)*sf/N)
            impx2=int((px)*sf+(res[1,ipy+1,ipx]+1)*sf/N)
            impy3=int((py)*sf+(res[0,ipy+1,ipx+1]+1)*sf/N)
            impx3=int((px)*sf+(res[1,ipy+1,ipx+1]+1)*sf/N)           
            #impy=(impy0+impy1+impy2+impy3)/4.0
            impx=(impx0+impx1+impx2+impx3)/4.0
            impy=(impy0*dy+impy1*dy+impy2*(1-dy)+impy3*(1-dy))/2.0
            impx=(impx0*dx+impx1*(1-dx)+impx2*dx+impx3*(1-dx))/2.0
            if pp==1:
                print dy,dx
            fp[-1]+=[impy,impx]
    return fp



import pylab

def showDef(cost):
    vmin=cost.min()
    vmax=cost.max()
    pl=pylab
    pl.subplot(2,2,1)
    pl.imshow(cost[0][:-1],interpolation="nearest",vmin=vmin,vmax=vmax)
    #pl.title("Vertical Edge Y")
    pl.xlabel("V Edge Y (%.5f,%.5f)"%(cost[0].min(),cost[0].max()))
    pl.subplot(2,2,2)
    pl.imshow(cost[1][:-1],interpolation="nearest",vmin=vmin,vmax=vmax)
    #pl.title("Vertical Edge X")
    pl.xlabel("V Edge X (%.5f,%.5f)"%(cost[1].min(),cost[1].max()))
    pl.subplot(2,2,3)
    pl.imshow(cost[2][:,:-1],interpolation="nearest",vmin=vmin,vmax=vmax)
    #pl.title("Horizontal Edge Y")
    pl.xlabel("H Edge Y (%.5f,%.5f)"%(cost[2].min(),cost[2].max()))
    pl.subplot(2,2,4)
    pl.imshow(cost[3][:,:-1],interpolation="nearest",vmin=vmin,vmax=vmax)
    #pl.title("Horizontal Edge X")
    pl.xlabel("H Edge X (%.5f,%.5f)"%(cost[3].min(),cost[3].max()))


def showDefNodes(cost):
    from scipy.ndimage.filters import uniform_filter
    #vmin=cost.min()
    #vmax=cost.max()
    pl=pylab
    if cost[0].shape[0]>cost[0].shape[1]:
        ny=3;nx=2
        pl.figure(figsize=(5,10))
    else:
        ny=2;nx=3
        pl.figure(figsize=(10,5))
    #pl.figure(figsize=(4,12))
    vy=(cost[0])
    vx=(cost[1])
    hy=(cost[2])
    hx=(cost[3])
    vyn=uniform_filter(vy,[2,1],mode="constant")
    vxn=uniform_filter(vx,[2,1],mode="constant")
    hyn=uniform_filter(hy,[1,2],mode="constant")
    hxn=uniform_filter(hx,[1,2],mode="constant")
    vmin=(vyn+hyn+vxn+hxn).min()/2.0
    vmax=(vyn+hyn+vxn+hxn).max()/2.0
    pl.subplot(ny,nx,1)
    pl.imshow(vyn+hyn,interpolation="nearest")#,vmin=vmin,vmax=vmax)
    pl.xlabel("lin Y (%.5f,%.5f)"%((vyn+hyn).min(),(vyn+hyn).max()))
    pl.subplot(ny,nx,2)
    pl.imshow(vxn+hxn,interpolation="nearest")#,vmin=vmin,vmax=vmax)
    pl.xlabel("lin X (%.5f,%.5f)"%((vxn+hxn).min(),(vxn+hxn).max()))
    pl.subplot(ny,nx,3)
    pl.imshow(vyn+hyn+vxn+hxn,interpolation="nearest")#,vmin=vmin*2,vmax=vmax*2)
    pl.xlabel("lin All (%.5f,%.5f)"%((vxn+hxn+vyn+hyn).min(),(vxn+hxn+vyn+hyn).max()))

    vy=(cost[4])
    vx=(cost[5])
    hy=(cost[6])
    hx=(cost[7])
    vyn=uniform_filter(vy,[2,1],mode="constant")
    vxn=uniform_filter(vx,[2,1],mode="constant")
    hyn=uniform_filter(hy,[1,2],mode="constant")
    hxn=uniform_filter(hx,[1,2],mode="constant")
    vmin=(vyn+hyn+vxn+hxn).min()
    vmax=(vyn+hyn+vxn+hxn).max()    
    pl.subplot(ny,nx,4)
    pl.imshow(vyn+hyn,interpolation="nearest")#,vmin=vmin,vmax=vmax)
    pl.xlabel("quad Y (%.5f,%.5f)"%((vyn+hyn).min(),(vyn+hyn).max()))
    pl.subplot(ny,nx,5)
    pl.imshow(vxn+hxn,interpolation="nearest")#,vmin=vmin,vmax=vmax)
    pl.xlabel("quad X (%.5f,%.5f)"%((vxn+hxn).min(),(vxn+hxn).max()))
    pl.subplot(ny,nx,6)
    pl.imshow(vyn+hyn+vxn+hxn,interpolation="nearest")#,vmin=vmin,vmax=vmax)
    pl.xlabel("quad All (%.5f,%.5f)"%((vxn+hxn+vyn+hyn).min(),(vxn+hxn+vyn+hyn).max()))

def showDef2(cost):
    from scipy.ndimage.filters import uniform_filter
    #vmin=cost.min()
    #vmax=cost.max()
    pl=pylab
    vy=(cost[0])
    vx=(cost[1])
    hy=(cost[2])
    hx=(cost[3])
    vyn=uniform_filter(vy,[2,1],mode="constant")
    vxn=uniform_filter(vx,[2,1],mode="constant")
    hyn=uniform_filter(hy,[1,2],mode="constant")
    hxn=uniform_filter(hx,[1,2],mode="constant")
    qvy=(cost[4])
    qvx=(cost[5])
    qhy=(cost[6])
    qhx=(cost[7])
    qvyn=uniform_filter(qvy,[2,1],mode="constant")
    qvxn=uniform_filter(qvx,[2,1],mode="constant")
    qhyn=uniform_filter(qhy,[1,2],mode="constant")
    qhxn=uniform_filter(qhx,[1,2],mode="constant")
    vmin=(vyn+hyn+vxn+hxn+qvyn+qhyn+qvxn+qhxn).min()
    vmax=(vyn+hyn+vxn+hxn+qvyn+qhyn+qvxn+qhxn).max()    
    pl.imshow(vyn+hyn+vxn+hxn,interpolation="nearest")#,vmin=vmin,vmax=vmax)
    pl.xlabel("Def (min %.5f,max %.5f)"%(vmin,vmax))
    return vyn+hyn+vxn+hxn+qvyn+qhyn+qvxn+qhxn


def showDefNodes2(cost):
    from scipy.ndimage.filters import uniform_filter
    #vmin=cost.min()
    #vmax=cost.max()
    pl=pylab
    if cost[0].shape[0]>cost[0].shape[1]:
        ny=3;nx=1
        pl.figure(figsize=(5,10))
    else:
        ny=1;nx=3
        pl.figure(figsize=(10,5))
    #pl.figure(figsize=(4,12))

    vy=(cost[0])
    vx=(cost[1])
    hy=(cost[2])
    hx=(cost[3])
    vyn=uniform_filter(vy,[2,1],mode="constant")
    vxn=uniform_filter(vx,[2,1],mode="constant")
    hyn=uniform_filter(hy,[1,2],mode="constant")
    hxn=uniform_filter(hx,[1,2],mode="constant")
    qvy=(cost[4])
    qvx=(cost[5])
    qhy=(cost[6])
    qhx=(cost[7])
    qvyn=uniform_filter(qvy,[2,1],mode="constant")
    qvxn=uniform_filter(qvx,[2,1],mode="constant")
    qhyn=uniform_filter(qhy,[1,2],mode="constant")
    qhxn=uniform_filter(qhx,[1,2],mode="constant")
    pl.subplot(ny,nx,1)
    pl.imshow(vyn+hyn+qvyn+qhyn,interpolation="nearest")#,vmin=vmin,vmax=vmax)
    pl.xlabel("Y (%.5f,%.5f)"%((vyn+hyn+qvyn+qhyn).min(),(vyn+hyn+qvyn+qhyn).max()))
    pl.subplot(ny,nx,2)
    pl.imshow(vxn+hxn+qvxn+qhxn,interpolation="nearest")#,vmin=vmin,vmax=vmax)
    pl.xlabel("X (%.5f,%.5f)"%((vxn+hxn+qvxn+qhxn).min(),(vxn+hxn+qvxn+qhxn).max()))
    pl.subplot(ny,nx,3)
    pl.imshow(vyn+hyn+vxn+hxn+qvyn+qhyn+qvxn+qhxn,interpolation="nearest")#,vmin=vmin*2,vmax=vmax*2)
    pl.xlabel("All (%.5f,%.5f)"%((vxn+hxn+vyn+hyn+qvyn+qhyn+qvxn+qhxn).min(),(vxn+hxn+vyn+hyn+qvyn+qhyn+qvxn+qhxn).max()))

def defontop(cost,pix=15,N=2):
    from scipy.ndimage.filters import uniform_filter
    #vmin=cost.min()
    #vmax=cost.max()
    pl=pylab
    #pl.figure(figsize=(4,12))
    vy=(cost[0])
    vx=(cost[1])
    hy=(cost[2])
    hx=(cost[3])
    vyn=uniform_filter(vy,[2,1],mode="constant")
    vxn=uniform_filter(vx,[2,1],mode="constant")
    hyn=uniform_filter(hy,[1,2],mode="constant")
    hxn=uniform_filter(hx,[1,2],mode="constant")
    qvy=(cost[4])
    qvx=(cost[5])
    qhy=(cost[6])
    qhx=(cost[7])
    qvyn=uniform_filter(qvy,[2,1],mode="constant")
    qvxn=uniform_filter(qvx,[2,1],mode="constant")
    qhyn=uniform_filter(qhy,[1,2],mode="constant")
    qhxn=uniform_filter(qhx,[1,2],mode="constant")
    vedges=vyn+hyn+qvyn+qhyn
    hedges=vxn+hxn+qvxn+qhxn
    #pl.subplot(ny,nx,1)
    #pl.imshow(vyn+hyn+qvyn+qhyn,interpolation="nearest")#,vmin=vmin,vmax=vmax)
    #pl.xlabel("Y (%.5f,%.5f)"%((vyn+hyn+qvyn+qhyn).min(),(vyn+hyn+qvyn+qhyn).max()))
    #pl.subplot(ny,nx,2)
    #pl.imshow(vxn+hxn+qvxn+qhxn,interpolation="nearest")#,vmin=vmin,vmax=vmax)
    #pl.xlabel("X (%.5f,%.5f)"%((vxn+hxn+qvxn+qhxn).min(),(vxn+hxn+qvxn+qhxn).max()))
    #pl.subplot(ny,nx,3)
    #pl.imshow(vyn+hyn+vxn+hxn+qvyn+qhyn+qvxn+qhxn,interpolation="nearest")#,vmin=vmin*2,vmax=vmax*2)
    #pl.xlabel("All (%.5f,%.5f)"%((vxn+hxn+vyn+hyn+qvyn+qhyn+qvxn+qhxn).min(),(vxn+hxn+vyn+hyn+qvyn+qhyn+qvxn+qhxn).max()))
    vmin=vedges.min();vmax=vedges.max()-vmin
    hmin=hedges.min();hmax=hedges.max()-hmin
    pix=pix*N
    for py in range(vedges.shape[0]):
        pl.plot([0,pix*vedges.shape[1]],[py*pix,py*pix],"w-.")
    for px in range(vedges.shape[1]):
        pl.plot([px*pix,px*pix],[0,pix*vedges.shape[0]],"w-.")
    for py in range(vedges.shape[0]):
        for px in range(vedges.shape[1]):
            #pl.plot([pix/2+px*pix,pix/2+(px)*pix],[pix/2+py*pix,pix/2+(py+1)*pix],"w-",lw=(vedges[py,px]-vmin)/vmax*10,alpha=0.3)
            if py<vedges.shape[0]-1:
                pl.plot([pix/2+px*pix,pix/2+(px)*pix],[pix/2+py*pix,pix/2+(py+1)*pix],"w.-",alpha=0.5,lw=(vedges[py,px]-vmin)/vmax*10)
            #pl.plot([pix/2+px*pix,pix/2+(px+1)*pix],[pix/2+py*pix,pix/2+(py)*pix],"w-",lw=(hedges[py,px]-hmin)/hmax*10,alpha=0.3)
            if px<vedges.shape[1]-1:
                pl.plot([pix/2+px*pix,pix/2+(px+1)*pix],[pix/2+py*pix,pix/2+(py)*pix],"w.-",alpha=0.5,lw=(hedges[py,px]-hmin)/hmax*10)
                 




