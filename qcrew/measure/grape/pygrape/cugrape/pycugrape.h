#include "constants.h"
#include <complex>
#include <array>

void init_gpu_memory();
void free_gpu_memory();
void load_states(int nvar, R *psi0, R *psif);
void get_states(int nvar, R *states);
void grape_step(R *ctrls, R *ovlp_r, R *ovlp_i, R *d_ovlp_i, R *d_ovlp_r);
//R get_cost();
//void get_d_cost(R *d_cost);
