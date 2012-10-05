# build the condot script to train all classes
cls = ["bicycle"]
#["aeroplane","bicycle","bird","boat","bottle","bus","car","cat","chair","cow","diningtable","dog","horse","motorbike","person","pottedplant","sheep","sofa", "train","tvmonitor"]
#[0"aeroplane",1"bicycle",2"bird",3"boat",4"bottle",5"bus",6"car",7"cat",8"chair",9"cow",10"diningtable",
# 11"dog",12"horse",13"motorbike",14"person",15"pottedplant",16"sheep",17"sofa",18 "train",19"tvmonitor"]


#common part
header="""
Universe = vanilla

#Requirements = ( Cpus >= {cpus} && Memory >= 10000 && konick and donovan have python2.6! 
Requirements =  ( (machine != "horse.esat.kuleuven.be") && (machine != "vicarus.esat.kuleuven.be") && (machine != "vicarus.esat.kuleuven.be") && (machine != "achel.esat.kuleuven.be") && (machine != "donovan.esat.kuleuven.be") && (machine != "koninck.esat.kuleuven.be") )
RequestCpus = {cpus}
RequestMemory = 4000
#Requirements = ARCH == "X86_64" || ARCH == "INTEL"
NiceUser = True
+RequestWalltime = (24 * 3600)
                    #20hours = 72000 
Executable = /usr/bin/python 
getenv = True
"""

conf="pascal"#"condor_rigid"
args="Arguments = -u denseCRF.py %s %s"
exec "from config_%s import *"%conf

streams="""
Output = {path}/{cls}{numcl}_{name}$(Cluster).$(Process).out
Error = {path}/{cls}{numcl}_{name}$(Cluster).$(Process).err
Log = {path}/{cls}{numcl}_{name}$(Cluster).$(Process).log
Notification = Error
Queue
"""

f=open("start.job","w")
f.write(header.format(cpus=cfg.multipr))
for l in cls:
    f.write(args%(l,conf))
    f.write(streams.format(path=cfg.testpath,name=cfg.testspec,cls=l,numcl=cfg.numcl))

f.close()
import os
os.system("condor_submit start.job")



