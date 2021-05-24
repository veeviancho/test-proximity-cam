$ pip3 install requirements.txt

Additionally, if needed: Installing pyrealsense2 on Mac
Source: https://github.com/IntelRealSense/librealsense/issues/5275

$ git clone https://github.com/IntelRealSense/librealsense
$ cd librealsense
$ mkdir build & cd build
$ cmake ../ -DBUILD_PYTHON_BINDINGS=bool:true
$ make -j4
$ sudo make install
You should still be in the /build directory so now you want to find the .so files. cd wrapper & cd python
You'll see a bunch of .so files in here, just copy them and then paste them to the root project directory of your project that you want to use pyrealsense2 in. Then you can just import pyrealsense2 in your project modules using import pyrealsense2