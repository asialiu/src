from rsf.proj import *

def param(par):
    p  = ' '
    p = p + ' --readwrite=y'
    if(par.has_key('verb')):
        p = p + ' verb='  +     par['verb']
    if(par.has_key('nrmax')):
        p = p + ' nrmax=' + str(par['nrmax'])
    if(par.has_key('dtmax')):
        p = p + ' dtmax=' + str(par['dtmax'])
    if(par.has_key('eps')):
        p = p + ' eps='   + str(par['eps'])
    if(par.has_key('tmx')):
        p = p + ' tmx='   + str(par['tmx'])
    if(par.has_key('tmy')):
        p = p + ' tmy='   + str(par['tmy'])
    if(par.has_key('pmx')):
        p = p + ' pmx='   + str(par['pmx'])
    if(par.has_key('pmy')):
        p = p + ' pmy='   + str(par['pmy'])
    if(par.has_key('misc')):
        p = p + ' '       +     par['misc']
    p = p + ' '
    return p

# ------------------------------------------------------------
def wempar(par):
    if(not par.has_key('verb')):    par['verb']='y'
    if(not par.has_key('eps')):     par['eps']=0.1

    if(not par.has_key('nrmax')):   par['nrmax']=1
    if(not par.has_key('dtmax')):   par['dtmax']=0.00005

    if(not par.has_key('tmx')):     par['tmx']=16
    if(not par.has_key('tmy')):     par['tmy']=16

    if(not par.has_key('incore')):  par['incore']='y'

def eicpar(par):
    p = ' '
    if(par.has_key('nhx')):
        p = p + ' nhx='   + str(par['nhx'])
    if(par.has_key('nhy')):
        p = p + ' nhy='   + str(par['nhy'])
    if(par.has_key('nhz')):
        p = p + ' nhz='   + str(par['nhz'])
    if(par.has_key('nht')):
        p = p + ' nht='   + str(par['nht'])
    if(par.has_key('oht')):
        p = p + ' oht='   + str(par['oht'])
    if(par.has_key('dht')):
        p = p + ' dht='   + str(par['dht'])
    p = p + ' '
    return(p)


# ------------------------------------------------------------
# prepare slowness
def slowness(slow,velo,par):
    Flow(slow,velo,
         '''
         math "output=1/input" |
         transp plane=12 | 	
	 transp plane=23
         ''')

# ------------------------------------------------------------
# Wavefield Reconstruction
def wfl(wfld,data,slow,custom,par):
    Flow(wfld,[data,slow],
         '''
         wex verb=y irun=wfl causal=n
         slo=${SOURCES[1]}
         %s
         ''' % (param(par)+custom))

# ------------------------------------------------------------
# Wavefield Datuming
def dtm(ddat,data,slow,custom,par):
    Flow(ddat,[data,slow],
         '''
         wex verb=y irun=dtm causal=n
         slo=${SOURCES[1]}
         %s
         ''' % (param(par)+custom))

# ------------------------------------------------------------
# migration with Conventional Imaging Condition
def cic(icic,sdat,rdat,slow,custom,par):
    Flow(icic,[sdat,rdat,slow],
         '''
         wex verb=y irun=cic
         dat=${SOURCES[1]}
         slo=${SOURCES[2]}
         %s
         ''' % (param(par)+custom))
    
# ------------------------------------------------------------
# 3D imaging condition
def cic3d(imag,swfl,rwfl,par):
    Flow(imag,[swfl,rwfl],
         '''
         cic uu=${SOURCES[1]} axis=3 verb=y ompnth=%(ompnth)d
         ''' % par)
    
def eic3d(cip,swfl,rwfl,cc,custom,par):
    par['eiccustom'] = custom
   
    Flow(cip,[swfl,rwfl,cc],
         '''
         eic verb=y
         nhx=%(nhx)d nhy=%(nhy)d nhz=%(nhz)d nht=%(nht)d dht=%(dht)g
         ur=${SOURCES[1]}
         cc=${SOURCES[2]}
         %(eiccustom)s
         ''' %par)
