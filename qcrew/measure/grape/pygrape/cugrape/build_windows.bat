CALL "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\vcvarsall.bat" amd64
nvcc --gpu-architecture=compute_30 --gpu-code=compute_30,sm_30 -std=c++11 kernel.cu -lib -o kernel.a -I./contrib/thrust -O3
"C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\amd64\cl.exe" pycugrape.cpp kernel.a /I contrib\pybind11\include /I C:\Anaconda\include /LD "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v8.0\lib\x64\cudart.lib" /link /LIBPATH:"C:\Anaconda\libs" /out:pycugrape.pyd 
