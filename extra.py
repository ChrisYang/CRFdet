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
    if m.has_key("cost"):
        m1["cost"]=pyrHOG2.crfflip(m["cost"])
    return m1    


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




