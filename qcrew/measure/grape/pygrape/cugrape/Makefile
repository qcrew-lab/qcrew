PYTHON=$(shell python3-config --cflags --ldflags)
THRUST=-I./contrib/thrust
PYBIND11=-I./contrib/pybind11/include $(PYTHON)
#CUDA=-L/usr/local/cuda/lib64 -lcudart
CUDA=-L/usr/local/cuda-8.0/lib64 -lcudart
#CFLAGS=-std=c++11 -flto -fvisibility=hidden -Wall -Wextra -Wconversion -fPIC

#pycugrape.so: pycugrape.o
#	g++ -fPIC -shared -Wl,-soname,pycugrape.so -o pycugrape.so

pycugrape.so: pycugrape.cpp kernel.a
	c++ -fPIC -O3 -shared -std=c++11 $(PYBIND11) pycugrape.cpp -o pycugrape.so kernel.a $(CUDA)

kernel.a: kernel.cu pycugrape.h constants.h
	nvcc --gpu-architecture=compute_61 --gpu-code=compute_61,sm_61 -std=c++11 --compiler-options "-fPIC" kernel.cu -lib -o kernel.a $(THRUST) --ptxas-options=-v -O3
#-lineinfo -keep
#--maxrregcount=20
#-keep

clean:
	rm -rf *.a *.o *.so

test: pycugrape.so
	python3 test.py

