from rsf.proj import * 
import sys  

# --------------------------------------------------------------------------
# Example of parameters for sglfdrtm
rtmpar = {
    'lnx':  5395,
    'lnz':  956,
    'nx' :  3201,
    'nz' :  956,
    'nt' :  7500,
    'dx' :  12.5,
    'dz' :  12.5,
    'dt' :  0.002,
    'labelx': "Distance",
    'labelz': "Depth",
    'unitx' : "Km",
    'unitz' : "Km",
    'shtbgn':  2001,
    'shtend':  3595,
    'sintv' : 4,
    'spz'   : 10,
    'gp'    : 0,
    'size'   : 8,
    'frqcut' : 1.0,
    'pml'    : 30,
    #source
    'srcbgn'  : 100,
    'frq'     : 20

    }

# --------------------------------------------------------------------------

def igrey(custom):
    return '''
    grey color=j labelsz=5 titlesz=6 %s
    ''' %(custom)

def grey(custom):
    return '''
    grey labelsz=5 titlesz=6 %s
    ''' %(custom)

def getpar(ipar, idn):
    opar = ipar
    opar['shtnum']   = int((ipar['shtend']-ipar['shtbgn'])/ipar['sintv'])+1
    opar['curid']    = idn
    opar['cursht']   = ipar['shtbgn']  + ipar['sintv']*idn
    opar['curxbgn']  = opar['cursht']  - int(ipar['nx']*0.5)
    opar['curxend']  = opar['curxbgn'] + ipar['nx'] - 1
    opar['spx']      = int(ipar['nx']*0.5)
    opar['bd']       = int(opar['size']*0.5+0.5) + opar['pml']
    checkpar(opar)
    return opar


def checkpar(par):
    if par['cursht'] > par['shtend'] or par['cursht'] < par['shtbgn'] :
        print " >>>> current source error cursht=%d " %(par['cursht']) 
        sys.exit()
    
    if par['curxbgn'] < 0 or par['curxend'] > par['lnx'] :
        print " >>>> curxbgn error: curxbgn=%d, curxend=%d" %(par['curxbgn'],  par['curxend']) 
        sys.exit()
    
def printpar(par):
    keylist = par.keys()
    keylist.sort()
    print "{"
    for key in keylist:
        print '  {0:<10}'.format(key)+":  %s" %par[key];
    print "}"
           
# --------------------------------------------------------------------------     
def splitmodel(Fout, Fin, par):
    Flow(Fout,Fin,
         '''
         window n1=%(nz)d n2=%(nx)d f2=%(curxbgn)d |
         put label1=%(labelz)s unit1=%(unitz)s
             label2=%(labelx)s unit2=%(unitz)s 
         '''%par)
    
def sglfdrtm(Fimg1, Fimg2, Fsrc, Ffvel, Ffden, Fbvel, Fbden, par, surfix):
    
    Gx = 'Gx%s'    %surfix
    Gz = 'Gz%s'    %surfix
    sxx ='sxx%s'   %surfix 
    sxz ='sxz%s'   %surfix
    szx = 'szx%s'  %surfix
    szz = 'szz%s'  %surfix
    Frcd = 'record%s' %surfix 
    
    Ftmpwf =  'tmpwf%s'  %surfix
    Ftmpbwf = 'tmpbwf%s' %surfix

    for m in [Ffden, Ffvel, Fbden, Fbvel]:
        pml  = m+'_pml'
        Flow(pml,m,
             '''
             expand left=%(bd)d right=%(bd)d 
                    top=%(bd)d  bottom=%(bd)d
             '''%par)
    Ffdenpml = Ffden+'_pml'
    Ffvelpml = Ffvel+'_pml'
    Fbdenpml = Fbden+'_pml'
    Fbvelpml = Fbvel+'_pml'
    
    Flow([Gx,sxx,sxz],Ffvelpml,
         '''
         sfsglfdcx2_7 dt=%(dt)g eps=0.00001 npk=50 
                      size=%(size)d sx=${TARGETS[1]} sz=${TARGETS[2]}
                      wavnumcut=%(frqcut)g
         '''%par)
    
    Flow([Gz,szx,szz],Ffvelpml,
         '''
         sfsglfdcz2_7 dt=%(dt)g eps=0.00001 npk=50 
                      size=%(size)d sx=${TARGETS[1]} sz=${TARGETS[2]}
                      wavnumcut=%(frqcut)g
         '''%par)
        
    Flow([Fimg1, Fimg2, Frcd],[Fsrc,Ffvelpml,Ffdenpml,Fbvelpml,Fbdenpml,Gx,sxx,sxz,Gz,szx,szz],
     '''
     sfsglfdrtm2 img2=${TARGETS[1]} rec=${TARGETS[2]}
                 fvel=${SOURCES[1]} fden=${SOURCES[2]}
                 bvel=${SOURCES[3]} bden=${SOURCES[4]}
                 Gx=${SOURCES[5]} sxx=${SOURCES[6]} sxz=${SOURCES[7]}
                 Gz=${SOURCES[8]} szx=${SOURCES[9]} szz=${SOURCES[10]}
                 freesurface=n  verb=y decay=n 
                 spx=%(spx)g spz=%(spz)g pmlsize=%(pml)d snapinter=10 
                 srcdecay=y  gp=%(gp)g srctrunc=0.2 pmld0=200
     '''%par)



def sgrtm(Fimg1, Fimg2, Fsrc, Flvel, Flden, Par):
    par = getpar(Par, 0)
    
    img1list = []
    img2list = []
    srclist = ''

    for ii in range(0,par['shtnum']):
        par = getpar(par, ii)
        vel  = '%s-%d'  %(Flvel, ii)
        den  = '%s-%d'  %(Flden, ii)
        img1 = '%s-%d'  %(Fimg1, ii)
        img2 = '%s-%d'  %(Fimg2, ii)
        _sfix = str(ii)

        splitmodel(vel, Flvel, par)
        splitmodel(den, Flden, par)
        sglfdrtm(img1, img2, Fsrc, vel, den, par, _sfix)
        img1list = img1list + [img1]
        img2list = img2list + [img2]
    
        srclist = srclist + ' ${SOURCES[%d]}' %(ii+1)
    Flow(Fimg1, [Flvel]+img1list, 'sfstackimg %s' %srclist)
    Flow(Fimg2, [Flvel]+img2list, 'sfstackimg %s' %srclist)



    

        



