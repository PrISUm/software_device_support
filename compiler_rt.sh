TAG=llvmorg-16.0.6
CONTAINER=$(docker create --rm alpine:latest /bin/sh -c "while true; do sleep 1000; done")
docker start $CONTAINER

# Prepare source tree
docker exec -i $CONTAINER /bin/sh <<EOF
# Note: Samurai is a different implementation of Ninja, default on Alpine Linux
apk add curl clang cmake lld musl-dev samurai llvm16-dev llvm16-static
URL=https://github.com/llvm/llvm-project/archive/refs/tags/$TAG.tar.gz
curl -L \$URL -o $TAG.tar.gz
tar xzf $TAG.tar.gz
EOF

# Compile for armv6-m
docker exec -i $CONTAINER /bin/sh <<EOF
cd llvm-project-$TAG/compiler-rt && rm -rf build && mkdir -p build && cd build

cmake .. \
  -G Ninja \
  -DCMAKE_AR=\$(llvm-config --bindir)/llvm-ar \
  -DCMAKE_ASM_COMPILER_TARGET="armv6m-none-eabi" \
  -DCMAKE_ASM_FLAGS="--target=armv6m-none-eabi -g -O3 -mthumb -mfloat-abi=soft -mcpu=cortex-m0plus -flto -ffreestanding" \
  -DCMAKE_C_COMPILER=clang \
  -DCMAKE_C_COMPILER_TARGET="armv6m-none-eabi" \
  -DCMAKE_C_FLAGS="--target=armv6m-none-eabi -g -O3 -mthumb -mfloat-abi=soft -mcpu=cortex-m0plus -flto -ffreestanding" \
  -DCMAKE_EXE_LINKER_FLAGS="-fuse-ld=lld" \
  -DCMAKE_NM=\$(llvm-config --bindir)/llvm-nm \
  -DCMAKE_RANLIB=\$(llvm-config --bindir)/llvm-ranlib \
  -DCOMPILER_RT_BUILD_BUILTINS=ON \
  -DCOMPILER_RT_BUILD_LIBFUZZER=OFF \
  -DCOMPILER_RT_BUILD_MEMPROF=OFF \
  -DCOMPILER_RT_BUILD_PROFILE=OFF \
  -DCOMPILER_RT_BUILD_SANITIZERS=OFF \
  -DCOMPILER_RT_BUILD_XRAY=OFF \
  -DCOMPILER_RT_DEFAULT_TARGET_ONLY=ON \
  -DCOMPILER_RT_BAREMETAL_BUILD=ON \
  -DCMAKE_C_COMPILER_WORKS=YES \
  -DCMAKE_CXX_COMPILER_WORKS=YES
ninja
EOF
docker cp $CONTAINER:/llvm-project-$TAG/compiler-rt/build/lib/linux/libclang_rt.builtins-armv6m.a .

# Compile for avr
docker exec -i $CONTAINER /bin/sh <<EOF
cd llvm-project-$TAG/compiler-rt && rm -rf build && mkdir -p build && cd build

cmake .. \
  -G Ninja \
  -DCMAKE_AR=\$(llvm-config --bindir)/llvm-ar \
  -DCMAKE_ASM_COMPILER_TARGET="avr-none-eabi" \
  -DCMAKE_ASM_FLAGS="--target=avr-none-eabi -g -O3 -mmcu=atmega328p -flto -ffreestanding" \
  -DCMAKE_C_COMPILER=clang \
  -DCMAKE_C_COMPILER_TARGET="avr-none-eabi" \
  -DCMAKE_C_FLAGS="--target=avr-none-eabi -g -O3 -mmcu=atmega328p -flto -ffreestanding" \
  -DCMAKE_EXE_LINKER_FLAGS="-fuse-ld=lld" \
  -DCMAKE_NM=\$(llvm-config --bindir)/llvm-nm \
  -DCMAKE_RANLIB=\$(llvm-config --bindir)/llvm-ranlib \
  -DCOMPILER_RT_BUILD_BUILTINS=ON \
  -DCOMPILER_RT_BUILD_LIBFUZZER=OFF \
  -DCOMPILER_RT_BUILD_MEMPROF=OFF \
  -DCOMPILER_RT_BUILD_PROFILE=OFF \
  -DCOMPILER_RT_BUILD_SANITIZERS=OFF \
  -DCOMPILER_RT_BUILD_XRAY=OFF \
  -DCOMPILER_RT_DEFAULT_TARGET_ONLY=ON \
  -DCOMPILER_RT_BAREMETAL_BUILD=ON \
  -DCMAKE_C_COMPILER_WORKS=YES \
  -DCMAKE_CXX_COMPILER_WORKS=YES
ninja
EOF
docker cp $CONTAINER:/llvm-project-$TAG/compiler-rt/build/lib/linux/libclang_rt.builtins-avr.a libclang_rt.builtins-avr-atmega328p.a

echo $CONTAINER
#docker stop $CONTAINER