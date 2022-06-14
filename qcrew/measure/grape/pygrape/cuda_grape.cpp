#include <string.h>
//#include <thrust/complex.h>
//#include <cuComplex.h>
#include <random>

const int DIM = %(dim)d;
const int NCTRLS = %(nctrls)d;
const int PLEN = %(plen)d;
const int NSTATE = %(nstate)d;
const int MAXNNZ = %(maxnnz)d;
const int TAYLOR_ORDER = %(taylor_order)d;

typedef float R;
//typedef thrust::complex<float> C;
//#define conj thrust::conj
//#define abs thrust::abs

class Complex {
private:
    R x, y;
public:
    Complex() {}
    Complex(R r, R i) { x = r; y = i; }
    friend Complex operator+(const Complex &c1, const Complex &c2);
    friend Complex operator*(const Complex &c1, const Complex &c2);
};

Complex operator+(const Complex &c1, const Complex &c2) {
    return Complex(c1.x + c2.x, c1.y + c2.y);
}
Complex operator*(const Complex &c1, const Complex &c2) {
    return Complex(c1.x*c2.x - c1.y*c2.y, c1.x*c1.y + c1.y*c2.x);
}



__device__ int Hp[2][NCTRLS][MAXNNZ];
__device__ __constant__ int Hj[2][NCTRLS][DIM+1];
__device__ R Hx[2][NCTRLS][MAXNNZ][2];
__device__ R ctrls[PLEN][NCTRLS];
__device__ R all_psi_ks[2][NSTATE][PLEN+1][2][DIM][2];
__device__ R d_psi_ks[2][NSTATE][PLEN+1][2][NCTRLS][DIM][2];
__device__ R psi_outs[NSTATE][PLEN][DIM][2];
__device__ R d_psi_outs[NSTATE][PLEN][NCTRLS][DIM][2];
__device__ R states[3][NSTATE][PLEN+1][DIM][2];
__device__ R costs[NSTATE][PLEN];
__device__ R d_costs[NSTATE][PLEN][NCTRLS];

//__global__
//void Lrho()
//{
//    int i = threadIdx.y;
//    int j = threadIdx.x;
//
//    {# convert matrix indices into tensor indices #}
//    {% for dim in mode_dims %}
//    i{{loop.index}} = i % {{dim}};
//    j{{loop.index}} = j % {{dim}};
//    i /= {{dim}};
//    j /= {{dim}};
//    {% endfor %}
//
//    R val = 0;
//    int ik, i_src, oob;
//    {% for HT in HTERMS %}
//    i_src = 0;
//    oob = 0;
//    R coef = {{HT.coef}};
//    {% for dim in reversed(mode_dims) %}
//    {% set k = nmodes - loop.index0 %}
//    {% if loop.index > 1 %}
//    i_src *= {{dim}}
//    {% endif %}
//    ik = i{{k}} + {{HT.delta_n[k]}};
//    oob = ((ik >= 0) && (ik < {{dim}}) : oob ? 1;
//    i_src += ik;
//    coef *= pow(ik, {{HT.n_power[k]}});
//    coef *= ADATA{{HT.delta_n}}[ik];
//    {% endfor %}
//    if (!oob) {
//        val += coef * rho[{{tot_dim}}*i_src + j];
//    }
//    {% endfor %}
//}

__global__
void spmv_row(int Ap[MAXNNZ], int Aj[DIM+1], R Ax[MAXNNZ][2], R Xx[DIM][2], R Yx[DIM][2], R Zx[DIM][2], R pf)
{
    __shared__ R sXx[DIM][2];
    int i = threadIdx.x;
    sXx[i][0] = Xx[i][0];
    sXx[i][1] = Xx[i][1];
    __syncthreads();
    R sum_r = 0;
    R sum_i = 0;
    for(int jj = Ap[i]; jj < Ap[i+1]; jj++){
        sum_r += Ax[jj][0] * sXx[Aj[jj]][0] - Ax[jj][1] * sXx[Aj[jj]][1];
        sum_i += Ax[jj][0] * sXx[Aj[jj]][1] + Ax[jj][1] * sXx[Aj[jj]][0];
    }
    sum_r *= pf;
    sum_i *= pf;
    Yx[i][0] += sum_r;
    Yx[i][1] += sum_i;
    Zx[i][0] += sum_r;
    Zx[i][1] += sum_i;
}


__device__
void spmv(int Ap[MAXNNZ], int Aj[DIM+1], R Ax[MAXNNZ][2], R Xx[DIM][2], R Yx[DIM][2], R Zx[DIM][2], R pf)
{
    // Y -> Y + pf*AX
    // Z -> Z + pf*AX
    spmv_row<<<1,DIM>>>(Ap, Aj, Ax, Xx, Yx, Zx, pf);
}


__device__
void Hv(int ct, int c_idx, R v_in[DIM][2], R v_out1[DIM][2], R v_out2[DIM][2], R pf)
{
    spmv(Hp[ct][c_idx], Hj[ct][c_idx], Hx[ct][c_idx], v_in, v_out1, v_out2, pf);
}


__device__
void H_state(int ct, R ctrls[NCTRLS], R psi_in[DIM][2], R psi_out[DIM][2], R psi_acc[DIM][2], R pf)
{
    // psi_out -> (pf*H)psi_in
    // psi_acc -> psi_acc + (pf*H)psi_in

    memset(psi_out, 0, 2*DIM*sizeof(R));
    // TODO: Parallelize this
    for (int i = 0; i < NCTRLS; i++) {
        Hv(ct, i, psi_in, psi_out, psi_acc, ctrls[i]*pf);
    }
}


__global__
void H_state_grad(int ct, R ctrls[NCTRLS], R psi_in[DIM][2],
                  R d_psi_in[NCTRLS][DIM][2], R d_psi_out[NCTRLS][DIM][2],
                  R d_psi_acc[NCTRLS][DIM][2], R pf)
{
    int c_idx = blockIdx.x;
    memset(d_psi_out, 0, 2*DIM*NCTRLS*sizeof(R));
    Hv(ct, c_idx, psi_in, d_psi_out[c_idx], d_psi_acc[c_idx], pf);
    H_state(ct, ctrls, d_psi_in[c_idx], d_psi_out[c_idx], d_psi_acc[c_idx], pf);
}


__device__
void prop_state(int ct, R ctrls[NCTRLS], R psi_in[DIM][2], R psi_out[DIM][2], R psi_ks[2][DIM][2])
{
    memcpy(psi_ks[0], psi_in, 2*DIM*sizeof(R));
    memcpy(psi_out, psi_in, 2*DIM*sizeof(R));
    int idx = 0;
    for (int k = 0; k < TAYLOR_ORDER; k++){
        H_state(ct, ctrls, psi_ks[idx], psi_ks[1-idx], psi_out, 1.0/k);
        idx = 1 - idx;
    }
}


__device__
void prop_state_grad(int ct, R ctrls[NCTRLS], R psi_in[DIM][2], R psi_out[DIM][2], R d_psi_out[NCTRLS][DIM][2],
                     R psi_ks[2][DIM][2], R d_psi_ks[2][NCTRLS][DIM][2])
{
    memcpy(psi_ks[0], psi_in, 2*DIM*sizeof(R));
    memcpy(psi_out, psi_in, 2*DIM*sizeof(R));
    int idx = 0;

    for (int k = 0; k < TAYLOR_ORDER; k++) {
        R pf = 1.0/k;
        H_state(ct, ctrls, psi_ks[idx], psi_ks[1-idx], psi_out, pf);
        H_state_grad<<<NCTRLS,1>>>(
            ct, ctrls, psi_ks[idx], d_psi_ks[idx], d_psi_ks[1-idx], d_psi_out, pf
        );
        idx = 1 - idx;
    }
}



__global__
void full_prop_state()
{
    int ct = blockIdx.x;
    int j = blockIdx.y;
    for (int i = 0; i < PLEN; i++) {
        prop_state(ct, ctrls[i], states[ct][j][i], states[ct][j][i+1], all_psi_ks[ct][j][i]);
    }
}


__global__
void make_intermediate()
{
    int s_idx = blockIdx.x;
    int t_idx = blockIdx.y;
    /* R psi[DIM][2] = states[0][state_idx][t_idx]; */
    /* R chi[DIM][2] = states[1][state_idx][PLEN - t_idx]; */
    /* R phi[DIM][2] = states[2][state_idx][t_idx]; */
    R a = ((R) t_idx) / PLEN;
    R b = ((R) (PLEN - t_idx)) / PLEN;
    for (int i = 0; i < DIM; i++) {
        states[2][s_idx][t_idx][i][0] = a*states[0][s_idx][t_idx][i][0] + b*states[1][s_idx][PLEN-t_idx][i][0];
        states[2][s_idx][t_idx][i][1] = a*states[0][s_idx][t_idx][i][1] + b*states[1][s_idx][PLEN-t_idx][i][1];
        /* phi[i][1] = a*psi[i][1] + b*chi[i][1]; */
    }
}


__global__
void get_cost_grad()
{
    int s_idx = blockIdx.x;
    int t_idx = blockIdx.y;
    /* R psi_in[DIM][2] = states[2][s_idx][t_idx]; */
    /* R psi_targ[DIM][2] = states[2][s_idx][t_idx+1]; */
    /* C psi_out[DIM]; */
    /* C d_psi_out[NCTRLS][DIM]; */
    prop_state_grad(0, ctrls[t_idx], states[2][s_idx][t_idx], psi_outs[s_idx][t_idx],
                    d_psi_outs[s_idx][t_idx], all_psi_ks[0][s_idx][t_idx], d_psi_ks[0][s_idx][t_idx]);
    R ovlp_r = 0;
    R ovlp_i = 0;
    for (int i=0; i<DIM; i++) {
        ovlp_r += states[2][s_idx][t_idx+1][i][0] * psi_outs[s_idx][t_idx][i][0];
        ovlp_r += states[2][s_idx][t_idx+1][i][1] * psi_outs[s_idx][t_idx][i][1];
        ovlp_i += states[2][s_idx][t_idx+1][i][0] * psi_outs[s_idx][t_idx][i][1];
        ovlp_i -= states[2][s_idx][t_idx+1][i][1] * psi_outs[s_idx][t_idx][i][0];
    }
    costs[s_idx][t_idx] = ovlp_r*ovlp_r + ovlp_i*ovlp_i;
    for (int j = 0; j < NCTRLS; j++) {
        R d_ovlp_r = 0;
        R d_ovlp_i = 0;
        for (int i = 0; i < DIM; i++) {
            d_ovlp_r += states[2][s_idx][t_idx+1][i][0] * d_psi_outs[s_idx][t_idx][j][i][0];
            d_ovlp_r += states[2][s_idx][t_idx+1][i][1] * d_psi_outs[s_idx][t_idx][j][i][1];
            d_ovlp_i += states[2][s_idx][t_idx+1][i][0] * d_psi_outs[s_idx][t_idx][j][i][1];
            d_ovlp_i += states[2][s_idx][t_idx+1][i][1] * d_psi_outs[s_idx][t_idx][j][i][0];
        }
        d_costs[s_idx][t_idx][j] = 2*(d_ovlp_r*ovlp_r + d_ovlp_i*ovlp_i);
    }
}


/* __global__ */
/* void sum_costs(R costs[NSTATE][PLEN], R d_costs[NSTATE][NCTRLS][PLEN]) */
/* { */
/*     int tid = threadIdx.x; */

/*     // Reduce NSTATE axis */
/*     R c = 0; */
/*     for (int i=0; i < NSTATE; i++) { */
/*         c += costs[i][tid]; */
/*     } */
/*     costs[0][tid] = c; */
/*     for (int j=0; j < NCTRLS; j++) { */
/*         c = 0; */
/*         for (int i=0; i < NSTATE; i++) { */
/*             c += d_costs[i][j][tid]; */
/*         } */
/*         d_costs[0][j][tid] = c; */
/*     } */
/*     __syncthreads() */
/* } */
