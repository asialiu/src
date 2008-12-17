import sys, os, string, re, commands, types, py_compile

import SCons



# Make sure error messages stand out visually
def stderr_write(message):
    sys.stderr.write('\n  %s\n' % message)

def pycompile(target, source, env):
    "convert py to pyc "
    for i in range(0,len(source)):
        py_compile.compile(source[i].abspath,target[i].abspath)
    return py_success


toheader = re.compile(r'\n((?:\n[^\n]+)+)\n'                     
                      '\s*\/\*(\^|\<(?:[^>]|\>[^*]|\>\*[^/])*\>)\*\/')
kandr = re.compile(r'\s*\{?\s*$') # K&R style function definitions end with {

def header(target=None,source=None,env=None):
# generate a header file
    inp = open(str(source[0]),'r')
    text = string.join(inp.readlines(),'')
    inp.close()
    file = str(target[0])
    prefix = env.get('prefix','')
    define = prefix + string.translate(os.path.basename(file),
                                       string.maketrans('.','_'))
    out = open(file,'w')
    out.write('/* This file is automatically generated. DO NOT EDIT! */\n\n')
    out.write('#ifndef _' + define + '\n')
    out.write('#define _' + define + '\n\n')
    for extract in toheader.findall(text):
        if extract[1] == '^':
            out.write(extract[0]+'\n\n')
        else:
            function = kandr.sub('',extract[0])
            out.write(function+';\n')
            out.write('/*'+extract[1]+'*/\n\n')
    out.write('#endif\n')
    out.close()
    return py_success

include = re.compile(r'#include\s*\"([^\"]+)\.h\"')

# find dependencies for C 
def depends(env,list,file):
    filename = string.replace(env.File(file+'.c').abspath,'build/','',1)
    fd = open(filename,'r')
    for line in fd.readlines():
        for inc in include.findall(line):
            if inc not in list and inc[0] != '_':
                list.append(inc)
                depends(env,list,inc)
    fd.close()


include90 = re.compile(r'^[^!]*use\s+(\S+)')

# find dependencies for Fortran-90
def depends90(env,list,file):
    filename = string.replace(env.File(file+'.f90').abspath,'build/','',1)
    fd = open(filename,'r')
    for line in fd.readlines():
        for inc in include90.findall(line):
            if inc not in list and inc != 'rsf':
                list.append(inc)
                depends90(env,list,inc)
    fd.close()

def included(node,env,path):
    file = os.path.basename(str(node))
    file = re.sub('\.[^\.]+$','',file)
    contents = node.get_contents()
    includes = include.findall(contents)
    if file in includes:
        includes.remove(file)
    return map(lambda x: x + '.h',includes)

local_include = re.compile(r'\s*\#include\s*\"([^\"]+)')

def includes(list,file):
    global local_include
    fd = open(file,'r')
    for line in fd.readlines():
         match = local_include.match(line)
         if match:
             other = os.path.join(os.path.dirname(file),match.group(1))
             if not other in list:
                 includes(list,other)
    list.append(file)
    fd.close()

def merge(target=None,source=None,env=None):
    global local_include
    sources = map(str,source)
    incs = []
    for src in sources:
        if not src in incs:
            includes(incs,src)
    out = open(str(target[0]),'w')
    for src in incs:
        inp = open(src,'r')
        for line in inp.readlines():
            if not local_include.match(line):
                out.write(line)
        inp.close()
    out.close()
    return py_success

def docmerge(target=None,source=None,env=None):
    outfile = target[0].abspath
    out = open(outfile,'w')
    out.write('import rsfdoc\n\n')
    for src in map(str,source):
        inp = open(src,'r')
        for line in inp.readlines():
                out.write(line)
        inp.close()
    alias = env.get('alias',{})
    for prog in alias.keys():
        out.write("rsfdoc.progs['%s']=%s\n" % (prog,alias[prog]))
    out.close()
    py_compile.compile(outfile,outfile+'c')
    return py_success

def pycompile_emit(target, source, env):
    target.append(str(target[0])+'c')
    return target,source 


def placeholder(target=None,source=None,env=None):
    filename = str(target[0])
    out = open(filename,'w')
    var = env.get('var')
    out.write('#!/usr/bin/env python\n')
    out.write('import sys\n\n')
    out.write('sys.stderr.write(\'\'\'\n%s is not installed.\n')
    out.write('Check $RSFROOT/lib/rsfconfig.py for ' + var)
    out.write('\nand reinstall if necessary.')
    package = env.get('package')
    if package:
        out.write('\nPossible missing packages: ' + package)
    out.write('\n\'\'\' % sys.argv[0])\nsys.exit(1)\n')
    out.close()
    os.chmod(filename,0775)
    return py_success

