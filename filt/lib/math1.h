/* This file is automatically generated. DO NOT EDIT! */

#ifndef _sf_math1_h
#define _sf_math1_h

#include "file.h"

#define SF_PI (3.141592653589793)

void sf_math_evaluate (int len /* stack length */, 
		       int nbuf /* buffer length */, 
		       float** fbuf /* number buffers */, 
		       float** fst /* stack */);
/*< Evaluate a mathematical expression from stack >*/

int sf_math_parse (char* output /* expression */, 
		   sf_file out  /* parameter file */);
/*< Parse a mathematical expression, returns stack length >*/

#endif
