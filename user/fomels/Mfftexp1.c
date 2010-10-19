/* 2-D FFT-based prestack exploding reflector modeling/migration  */
/*
  Copyright (C) 2010 University of Texas at Austin
  
  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.
  
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
  
  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software
  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
*/
#include <rsf.h>

#include "fft3.h"

int main(int argc, char* argv[])
{
    bool mig, cmplx;
    int it, nt, ix, nx, iz, nz, nx2, nz2, nzx, nzx2, ih, nh, nh2;
    int im, i, j, m1, m2, it1, it2, its, ik, n2, nk;
    float dt, dx, dz, c, old, dh;
    float *curr, *prev, **img, **dat, **lft, **mid, **rht, **wave;
    sf_complex *cwave, *cwavem;
    sf_file data, image, left, middle, right;

    sf_init(argc,argv);

    if (!sf_getbool("mig",&mig)) mig=false;
    /* if n, modeling; if y, migration */

    if (mig) { /* migration */
	data = sf_input("in");
	image = sf_output("out");

	if (!sf_histint(data,"n1",&nh));
	if (!sf_histfloat(data,"d1",&dh));

	if (!sf_histint(data,"n2",&nx));
	if (!sf_histfloat(data,"d2",&dx));

	if (!sf_histint(data,"n3",&nt));
	if (!sf_histfloat(data,"d3",&dt));

	if (!sf_getint("nz",&nz)) sf_error("Need nz=");
	/* time samples (if migration) */
	if (!sf_getfloat("dz",&dz)) sf_error("Need dz=");
	/* time sampling (if migration) */

	sf_putint(image,"n1",nz);
	sf_putfloat(image,"d1",dz);
	sf_putstring(image,"label1","Depth");

	sf_putint(image,"n3",1); /* stack for now */
    } else { /* modeling */
	image = sf_input("in");
	data = sf_output("out");

	if (!sf_histint(image,"n1",&nz));
	if (!sf_histfloat(image,"d1",&dz));

	if (!sf_histint(image,"n2",&nx));
	if (!sf_histfloat(image,"d2",&dx));

	if (!sf_getint("nt",&nt)) sf_error("Need nt=");
	/* time samples (if modeling) */
	if (!sf_getfloat("dt",&dt)) sf_error("Need dt=");
	/* time sampling (if modeling) */

	if (!sf_getint("nh",&nh)) sf_error("Need nh=");
        /* offset samples (if modeling) */
	if (!sf_getfloat("dh",&dh)) sf_error("Need dh=");
	/* offset sampling (if modeling) */

	sf_putint(data,"n1",nh);
	sf_putfloat(data,"d1",dh);
	sf_putstring(data,"label1","Half-Offset");

	sf_putint(data,"n3",nt);
	sf_putfloat(data,"d3",dt);
	sf_putstring(data,"label3","Time");
	sf_putstring(data,"unit3","s");
    }

    if (!sf_getbool("cmplx",&cmplx)) cmplx=false; /* use complex FFT */
    nk = fft3_init(cmplx,1,nh,nx,nz,&nh2,&nx2,&nz2);

    nzx = nz*nx*nh;
    nzx2 = nz2*nx2*nh2;

    img = sf_floatalloc2(nz,nx);
    dat = sf_floatalloc2(nh,nx);

    /* propagator matrices */
    left = sf_input("left");
    right = sf_input("right");
    middle = sf_input("middle");

    if (!sf_histint(middle,"n1",&m1)) sf_error("No n1= in middle");
    if (!sf_histint(middle,"n2",&m2)) sf_error("No n2= in middle");

    if (!sf_histint(left,"n1",&n2) || n2 != nzx) sf_error("Need n1=%d in left",nzx);
    if (!sf_histint(left,"n2",&n2) || n2 != m1)  sf_error("Need n2=%d in left",m1);
    
    if (!sf_histint(right,"n1",&n2) || n2 != m2) sf_error("Need n1=%d in right",m2);
    if (!sf_histint(right,"n2",&n2) || n2 != nk) sf_error("Need n2=%d in right",nk);
 
    lft = sf_floatalloc2(nzx,m1);
    mid = sf_floatalloc2(m1,m2);
    rht = sf_floatalloc2(m2,nk);

    sf_floatread(lft[0],nzx*m1,left);
    sf_floatread(mid[0],m1*m2,middle);
    sf_floatread(rht[0],m2*nk,right);

    curr = sf_floatalloc(nzx2);
    prev = sf_floatalloc(nzx);

    cwave  = sf_complexalloc(nk);
    cwavem = sf_complexalloc(nk);
    wave = sf_floatalloc2(nzx2,m2);

    for (iz=0; iz < nzx; iz++) {
	prev[iz]=0.;
    }

    for (iz=0; iz < nzx2; iz++) {
	curr[iz]=0.;
    }


    if (mig) { /* migration */
	/* step backward in time */
	it1 = nt-1;
	it2 = -1;
	its = -1;	
    } else { /* modeling */
	sf_floatread(img[0],nz*nx,image);

	/* transpose and initialize at zero offset */
	for (iz=0; iz < nz; iz++) {
	    for (ix=0; ix < nx; ix++) {
		curr[nh2*(ix+iz*nx2)]=img[ix][iz];
	    }
	}
	
	/* step forward in time */
	it1 = 0;
	it2 = nt;
	its = +1;
    }


    /* time stepping */
    for (it=it1; it != it2; it += its) {
	sf_warning("it=%d;",it);

	if (mig) { /* migration <- read data */
	    sf_floatread(dat[0],nx*nh,data);
	} else {
	    for (ix=0; ix < nx; ix++) {
		for (ih=0; ih < nh; ih++) {
		    dat[ix][ih] = 0.;
		}
	    }
	}

	/* at z=0 */
	for (ix=0; ix < nx; ix++) {
	    for (ih=0; ih < nh; ih++) {
		if (mig) {
		    curr[ix*nh2+ih] += dat[ix][ih];
		} else {
		    dat[ix][ih] = curr[ix*nh2+ih];
		}
	    }
	}

	/* matrix multiplication */
	fft3(curr,cwave);

	for (im = 0; im < m2; im++) {
	    for (ik = 0; ik < nk; ik++) {
#ifdef SF_HAS_COMPLEX_H
		cwavem[ik] = cwave[ik]*rht[ik][im];
#else
		cwavem[ik] = sf_crmul(cwave[ik],rht[ik][im]);
#endif
	    }
	    ifft3(wave[im],cwavem);
	}

	for (iz=0; iz < nz; iz++) {
	    for (ix = 0; ix < nx; ix++) {
		for (ih=0; ih < nh; ih++) {	
		    i = ih+nh*(ix+iz*nx);   /* original grid */
		    j = ih+nh2*(ix+iz*nx2); /* padded grid */
		
		    old = c = curr[j];
		    c += c - prev[i];
		    prev[i] = old;

		    for (im = 0; im < m2; im++) {
			for (ik = 0; ik < m1; ik++) {
			    c += lft[ik][i]*mid[im][ik]*wave[im][j];
			}
		    }
		    
		    curr[j] = c;
		}
	    }
	}
	
	if (!mig) { /* modeling -> write out data */
	    sf_floatwrite(dat[0],nx*nh,data);
	}
    }
    sf_warning(".");

    if (mig) {
	/* transpose */
	for (iz=0; iz < nz; iz++) {
	    for (ix=0; ix < nx; ix++) {
		img[ix][iz] = curr[nh2*(ix+iz*nx2)];
	    }
	}

	sf_floatwrite(img[0],nz*nx,image);
    }

    exit(0);
}
