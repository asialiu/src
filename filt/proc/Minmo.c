/* Inverse normal moveout.

Takes: < gather.rsf velocity=velocity.rsf [offset=offset.rsf] > nmod.rsf
*/

#include <math.h>

#include <rsf.h>

#include "stretch4.h"

int main (int argc, char* argv[])
{
    map4 nmo;
    bool half;
    int it,ix,ih, nt,nx, nh, nw, CDPtype;
    float dt, t0, h, h0, f, dh, eps, dy;
    float *trace, *vel, *off, *str, *out;
    sf_file cmp, nmod, velocity, offset;

    sf_init (argc,argv);
    cmp = sf_input("in");
    velocity = sf_input("velocity");
    nmod = sf_output("out");

    if (SF_FLOAT != sf_gettype(cmp)) sf_error("Need float input");
    if (!sf_histint(cmp,"n1",&nt)) sf_error("No n1= in input");
    if (!sf_histfloat(cmp,"d1",&dt)) sf_error("No d1= in input");
    if (!sf_histfloat(cmp,"o1",&t0)) sf_error("No o1= in input");

    if (!sf_histint(cmp,"n2",&nh)) sf_error("No n2= in input");

    off = sf_floatalloc(nh);

    CDPtype=1;
    if (NULL != sf_getstring("offset")) {
	offset = sf_input("offset");
	sf_floatread (off,nh,offset);
	sf_fileclose(offset);
    } else {
	if (!sf_histfloat(cmp,"d2",&dh)) sf_error("No d2= in input");
	if (!sf_histfloat(cmp,"o2",&h0)) sf_error("No o2= in input");

	if (!sf_getbool("half",&half)) half=true;
	/* if y, the second axis is half-offset instead of full offset */
	
	if (half) {
	    dh *= 2.;
	    h0 *= 2.;
	}
	
	if (sf_histfloat(cmp,"d3",&dy)) {
	    CDPtype=0.5+0.5*dh/dy;
	    if (1 != CDPtype) sf_histint(cmp,"CDPtype",&CDPtype);
	} 	    
	sf_warning("CDPtype=%d",CDPtype);

	for (ih = 0; ih < nh; ih++) {
	    off[ih] = h0 + ih*dh; 
	}
    }

    nx = sf_leftsize(cmp,2);

    if (!sf_getfloat ("h0",&h0)) h0=0.;
    /* reference offset */
    if (!sf_getfloat("eps",&eps)) eps=0.01;
    /* stretch regularization */

    trace = sf_floatalloc(nt);
    vel = sf_floatalloc(nt);
    str = sf_floatalloc(nt);
    out = sf_floatalloc(nt);

    if (!sf_getint("extend",&nw)) nw=8;
    /* trace extension */

    nmo = stretch4_init (nt, t0, dt, nt, eps);
    
    for (ix = 0; ix < nx; ix++) {
	sf_floatread (vel,nt,velocity);	

	for (ih = 0; ih < nh; ih++) {
	    sf_floatread (trace,nt,cmp);
	    
	    h = off[ih] + (dh/CDPtype)*(ix%CDPtype); 
	    h = h*h - h0*h0;
	    
	    for (it=0; it < nt; it++) {
		f = t0 + it*dt;
		f = f*f + h/(vel[it]*vel[it]);
		if (f < 0.) {
		    str[it]=t0-10.*dt;
		} else {
		    str[it] = sqrtf(f);
		}
	    }

	    stretch4_define (nmo,str);
	    stretch4_apply (nmo,trace,out);
	    
	    sf_floatwrite (out,nt,nmod);
	}
    }
	
    sf_close();
    exit (0);
}

/* 	$Id: Minmo.c,v 1.7 2004/06/03 05:35:51 fomels Exp $	 */
