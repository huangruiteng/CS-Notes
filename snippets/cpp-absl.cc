git clone https://github.com/abseil/abseil-cpp.git
cd abseil-cpp
git checkout 20230802.1
mkdir build && cd build
cmake -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DABSL_BUILD_TESTING=OFF -DABSL_USE_GOOGLETEST_HEAD=OFF -DCMAKE_CXX_STANDARD=14 ..
make -j
make install