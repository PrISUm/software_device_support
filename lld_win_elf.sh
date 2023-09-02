#!/bin/sh
VERSION=16.0.6
TAG=llvmorg-$VERSION
URL=https://github.com/llvm/llvm-project/releases/download/$TAG/LLVM-$VERSION-win64.exe
FILE=$(basename $URL)

[ ! -f $FILE ] && curl -L $URL -o $FILE
rm -rf llvm_win && mkdir llvm_win
(cd llvm_win && 7zz x ../$FILE bin/ld.lld.exe)