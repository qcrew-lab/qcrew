#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include "pycugrape.h"
#include <cstdio>

namespace py = pybind11;

template <typename T>
using nparr = py::array_t<T, py::array::c_style | py::array::forcecast>;

void load_states_numpy(int nvar, nparr<R> psi0, nparr<R> psif)
{
    load_states(nvar, (R *) psi0.request().ptr, (R *) psif.request().ptr);
}

nparr<R> get_states_numpy(int nvar, int dim)
{
    auto states = py::array_t<R>(2*NSTATE*(PLEN+1)*dim*2);
    get_states(nvar, (R *) states.request().ptr);
    return states;
}

py::tuple get_grape_params()
{
    return py::make_tuple(NVAR,NCTRLS,PLEN,NSTATE,MAXNNZ,TAYLOR_ORDER);
}

py::tuple grape_step_numpy(nparr<R> ctrls)
{
    auto ovlps_r = py::array_t<R>(NVAR);
    auto ovlps_i = py::array_t<R>(NVAR);
    auto d_ovlps_r = py::array_t<R>(NVAR*PLEN*NCTRLS);
    auto d_ovlps_i = py::array_t<R>(NVAR*PLEN*NCTRLS);
    grape_step(
        (R *) ctrls.request().ptr,
        (R *) ovlps_r.request().ptr,
        (R *) ovlps_i.request().ptr,
        (R *) d_ovlps_r.request().ptr,
        (R *) d_ovlps_i.request().ptr
    );
    return py::make_tuple(ovlps_r, ovlps_i, d_ovlps_r, d_ovlps_i);
}

PYBIND11_PLUGIN(pycugrape) {
    py::module m("pycugrape", "GRAPE in CUDA in Python");
    m.def("get_grape_params", &get_grape_params);
    m.def("init_gpu_memory", &init_gpu_memory);
    m.def("load_states", &load_states_numpy);
    m.def("get_states", &get_states_numpy);
    m.def("grape_step", &grape_step_numpy);
    return m.ptr();
}
