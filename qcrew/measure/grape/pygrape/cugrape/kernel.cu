#include "pycugrape.h"
#include <stdio.h>
#include <stdlib.h>
#include <thrust/complex.h>
#include <math.h>
typedef thrust::complex<R> C;

#define idxctrls(t, nctrl) ((nctrl) + NCTRLS*(t) )
const int ctrls_size = NCTRLS*PLEN;
#define idxstates0(ct, nstate, t, nrow, ri) ((ri) + 2*((nrow) + 46*((t) + (PLEN+1)*((nstate) + NSTATE*(ct)))))
#define psi_out0(t, ri) states[idxstates0(ct, nstate, t, nrow, ri)]
#define psi_out_ct0(t, ri) states[idxstates0(1-(ct), nstate, PLEN-(t), nrow, ri)]
#define idxstates1(ct, nstate, t, nrow, ri) ((ri) + 2*((nrow) + 48*((t) + (PLEN+1)*((nstate) + NSTATE*(ct)))))
#define psi_out1(t, ri) states[idxstates1(ct, nstate, t, nrow, ri)]
#define psi_out_ct1(t, ri) states[idxstates1(1-(ct), nstate, PLEN-(t), nrow, ri)]
#define idxstates2(ct, nstate, t, nrow, ri) ((ri) + 2*((nrow) + 50*((t) + (PLEN+1)*((nstate) + NSTATE*(ct)))))
#define psi_out2(t, ri) states[idxstates2(ct, nstate, t, nrow, ri)]
#define psi_out_ct2(t, ri) states[idxstates2(1-(ct), nstate, PLEN-(t), nrow, ri)]
#define idxstates3(ct, nstate, t, nrow, ri) ((ri) + 2*((nrow) + 52*((t) + (PLEN+1)*((nstate) + NSTATE*(ct)))))
#define psi_out3(t, ri) states[idxstates3(ct, nstate, t, nrow, ri)]
#define psi_out_ct3(t, ri) states[idxstates3(1-(ct), nstate, PLEN-(t), nrow, ri)]

#define gpuErrchk(ans) { gpuAssert((ans), __FILE__, __LINE__); }
inline void gpuAssert(cudaError_t code, const char *file, int line, bool abort = true)
{
    if (code != cudaSuccess)
    {
        fprintf(stderr, "GPUassert: %s %s %d\n", cudaGetErrorString(code), file, line);
        if (abort) exit(code);
    }
}


__device__ double atomicAddD(double* address, double val)
{
    unsigned long long int* address_as_ull =
                              (unsigned long long int*)address;
    unsigned long long int old = *address_as_ull, assumed;

    do {
        assumed = old;
        old = atomicCAS(address_as_ull, assumed,
                        __double_as_longlong(val +
                               __longlong_as_double(assumed)));

    // Note: uses integer comparison to avoid hang in case of NaN (since NaN != NaN)
    } while (assumed != old);

    return __longlong_as_double(old);
}

R *ctrls_d; // [PLEN][NCTRLS];


R *states_d0;
R *ovlp_r_d0;
R *ovlp_i_d0;
R *d_ovlps_r_d0;
R *d_ovlps_i_d0;

__global__
void prop_state_kernel0_noct(R *ctrls, R *states)
{
    const unsigned int ct = 0;
    const unsigned int nstate = blockIdx.y;
    const unsigned int nrow = threadIdx.x;
    __shared__ C s_psik[2][46];
    __syncthreads();
    const short s = ct ? -1 : 1;

    int nrow_cur = nrow;
    const int i_dst0 = nrow_cur % 23;
    nrow_cur /= 23;
    const int i_dst1 = nrow_cur % 2;
    nrow_cur /= 2;

    /* R psi_out_v = psi_out(0, ri); */
    R psi_out_v_r = psi_out0(0, 0);
    R psi_out_v_i = psi_out0(0, 1);
    for (int t = 1; t <= PLEN; t++) {
        int ctrl_t = ct ? (PLEN - t) : (t-1);
        int idx = 0;
        s_psik[0][nrow] = C::complex(psi_out_v_r, psi_out_v_i);

        for (int k = 1; k <= TAYLOR_ORDER; k++) {
            // psi_k -> (pf*H)psi_k
            // psi_out -> psi_out + (pf*H)psi_k
            __syncthreads();

            // TODO: Parallelize this
            R cpf, pf;
            C ppf, t_ppf, H_psi_k_sum;
            int i_src, src_row, valid;
            H_psi_k_sum = 0;
                    cpf = 1.0 / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -1.73415914478e-05);
                            ppf *= i_dst0 * i_dst0;
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, -0.774088429845);
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 0.774088429845);
                            ppf *= i_dst1 * i_dst1;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 0.0126591104295);
                            ppf *= i_dst0 ;
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, -8.16814089933e-06);
                            ppf *= i_dst0 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 8.16814089933e-06);
                            ppf *= i_dst0 * i_dst0;
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 0;
                        src_row = src_row * 23 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 0)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - -1;
                        src_row = src_row * 23 + i_src;
                            valid = valid && (i_src < 23);
                                pf *= sqrt((R) (i_src - 0));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 1;
                        src_row = src_row * 23 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 1)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0125663706144, 0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - -1;
                        src_row = src_row * 23 + i_src;
                            valid = valid && (i_src < 23);
                                pf *= sqrt((R) (i_src - 0));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(-0.0125663706144, -0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 1;
                        src_row = src_row * 23 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 2)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - -1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src < 2);
                                pf *= sqrt((R) (i_src - 0));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 23 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 23 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 3)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0125663706144, 0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - -1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src < 2);
                                pf *= sqrt((R) (i_src - 0));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 23 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(-0.0125663706144, -0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 23 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
            s_psik[1-idx][nrow] = H_psi_k_sum;
            psi_out_v_r += H_psi_k_sum.real();
            psi_out_v_i += H_psi_k_sum.imag();

            // swap psi_k and psi_k_next
            idx = 1 - idx;
        }

        psi_out0(t, 0) = psi_out_v_r;
        psi_out0(t, 1) = psi_out_v_i;
    }
}
__global__
void prop_state_kernel0_withct(R *ctrls, R *states)
{
    const unsigned int ct = 1;
    const unsigned int nstate = blockIdx.y;
    const unsigned int nrow = threadIdx.x;
    __shared__ C s_psik[2][46];
    __syncthreads();
    const short s = ct ? -1 : 1;

    int nrow_cur = nrow;
    const int i_dst0 = nrow_cur % 23;
    nrow_cur /= 23;
    const int i_dst1 = nrow_cur % 2;
    nrow_cur /= 2;

    /* R psi_out_v = psi_out(0, ri); */
    R psi_out_v_r = psi_out0(0, 0);
    R psi_out_v_i = psi_out0(0, 1);
    for (int t = 1; t <= PLEN; t++) {
        int ctrl_t = ct ? (PLEN - t) : (t-1);
        int idx = 0;
        s_psik[0][nrow] = C::complex(psi_out_v_r, psi_out_v_i);

        for (int k = 1; k <= TAYLOR_ORDER; k++) {
            // psi_k -> (pf*H)psi_k
            // psi_out -> psi_out + (pf*H)psi_k
            __syncthreads();

            // TODO: Parallelize this
            R cpf, pf;
            C ppf, t_ppf, H_psi_k_sum;
            int i_src, src_row, valid;
            H_psi_k_sum = 0;
                    cpf = 1.0 / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -1.73415914478e-05);
                            ppf *= i_dst0 * i_dst0;
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, -0.774088429845);
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 0.774088429845);
                            ppf *= i_dst1 * i_dst1;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 0.0126591104295);
                            ppf *= i_dst0 ;
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, -8.16814089933e-06);
                            ppf *= i_dst0 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 8.16814089933e-06);
                            ppf *= i_dst0 * i_dst0;
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 0;
                        src_row = src_row * 23 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 0)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - -1;
                        src_row = src_row * 23 + i_src;
                            valid = valid && (i_src < 23);
                                pf *= sqrt((R) (i_src - 0));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 1;
                        src_row = src_row * 23 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 1)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0125663706144, 0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - -1;
                        src_row = src_row * 23 + i_src;
                            valid = valid && (i_src < 23);
                                pf *= sqrt((R) (i_src - 0));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(-0.0125663706144, -0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 1;
                        src_row = src_row * 23 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 2)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - -1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src < 2);
                                pf *= sqrt((R) (i_src - 0));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 23 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 23 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 3)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0125663706144, 0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - -1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src < 2);
                                pf *= sqrt((R) (i_src - 0));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 23 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(-0.0125663706144, -0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 23 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
            s_psik[1-idx][nrow] = H_psi_k_sum;
            psi_out_v_r += H_psi_k_sum.real();
            psi_out_v_i += H_psi_k_sum.imag();

            // swap psi_k and psi_k_next
            idx = 1 - idx;
        }

        psi_out0(t, 0) = psi_out_v_r;
        psi_out0(t, 1) = psi_out_v_i;
    }
}

__global__
void ovlps_grad_kernel0(R *ctrls, R *states, R *ovlp_r, R *ovlp_i, R *d_ovlps_r, R *d_ovlps_i)
{
    const unsigned int ct = 0;
    const unsigned int t = blockIdx.x;
    const unsigned int nstate = blockIdx.y;
    const unsigned int d_nc = blockIdx.z;
    const unsigned int nrow = threadIdx.x;

    int s = ct ? -1 : 1;

    int nrow_cur = nrow;
    const int i_dst0 = nrow_cur % 23;
    nrow_cur /= 23;
    const int i_dst1 = nrow_cur % 2;
    nrow_cur /= 2;

    C psi_out_v = C::complex(psi_out0(t, 0), psi_out0(t, 1));
    C d_psi_out_v = C::complex(0, 0);
        __shared__ C s_psik[2][46];
        __shared__ C s_d_psik[2][46];
        __syncthreads();
        int idx = 0;
        s_psik[0][nrow] = psi_out_v;
        s_d_psik[0][nrow] = d_psi_out_v;

    for (int k = 1; k <= TAYLOR_ORDER; k++) {
        // psi_k -> (pf*H)psi_k
        // psi_out -> psi_out + (pf*H)psi_k
        __syncthreads();

        R cpf, pf;
        C ppf, t_ppf, H_psi_k_sum, d_H_psi_k_sum;
        int i_src, src_row, valid;
        H_psi_k_sum = 0;
        d_H_psi_k_sum = 0;
                cpf = 1.0;
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -1.73415914478e-05);
                        ppf *= i_dst0 * i_dst0;
                        ppf *= i_dst1 ;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, -0.774088429845);
                        ppf *= i_dst1 ;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, 0.774088429845);
                        ppf *= i_dst1 * i_dst1;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, 0.0126591104295);
                        ppf *= i_dst0 ;
                        ppf *= i_dst1 ;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, -8.16814089933e-06);
                        ppf *= i_dst0 ;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, 8.16814089933e-06);
                        ppf *= i_dst0 * i_dst0;
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - 0;
                    src_row = src_row * 23 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == -1)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                cpf = ctrls[idxctrls(t, 0)];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -0.0125663706144);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - -1;
                    src_row = src_row * 23 + i_src;
                        valid = valid && (i_src < 23);
                            pf *= sqrt((R) (i_src - 0));
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 0)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -0.0125663706144);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - 1;
                    src_row = src_row * 23 + i_src;
                        valid = valid && (i_src >= 0);
                            pf *= sqrt((R) (i_src + 1));
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 0)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                cpf = ctrls[idxctrls(t, 1)];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0125663706144, 0.0);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - -1;
                    src_row = src_row * 23 + i_src;
                        valid = valid && (i_src < 23);
                            pf *= sqrt((R) (i_src - 0));
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 1)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(-0.0125663706144, -0.0);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - 1;
                    src_row = src_row * 23 + i_src;
                        valid = valid && (i_src >= 0);
                            pf *= sqrt((R) (i_src + 1));
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 1)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                cpf = ctrls[idxctrls(t, 2)];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -0.0125663706144);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - -1;
                    src_row = src_row * 2 + i_src;
                        valid = valid && (i_src < 2);
                            pf *= sqrt((R) (i_src - 0));
                    i_src = i_dst0 - 0;
                    src_row = src_row * 23 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 2)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -0.0125663706144);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 1;
                    src_row = src_row * 2 + i_src;
                        valid = valid && (i_src >= 0);
                            pf *= sqrt((R) (i_src + 1));
                    i_src = i_dst0 - 0;
                    src_row = src_row * 23 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 2)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                cpf = ctrls[idxctrls(t, 3)];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0125663706144, 0.0);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - -1;
                    src_row = src_row * 2 + i_src;
                        valid = valid && (i_src < 2);
                            pf *= sqrt((R) (i_src - 0));
                    i_src = i_dst0 - 0;
                    src_row = src_row * 23 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 3)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(-0.0125663706144, -0.0);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 1;
                    src_row = src_row * 2 + i_src;
                        valid = valid && (i_src >= 0);
                            pf *= sqrt((R) (i_src + 1));
                    i_src = i_dst0 - 0;
                    src_row = src_row * 23 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 3)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];

        s_psik[1-idx][nrow] = H_psi_k_sum;
        s_d_psik[1-idx][nrow] = d_H_psi_k_sum;

        // swap psi_k and psi_k_next
        idx = 1 - idx;

        psi_out_v += H_psi_k_sum;
        d_psi_out_v += d_H_psi_k_sum;
    }

    // reuse shared memory for calculation of overlaps
    // - for conjugate
    s_psik[idx][nrow] = C::complex(psi_out_ct0(t+1, 0), -psi_out_ct0(t+1, 1)) * psi_out_v;
    s_d_psik[idx][nrow] = C::complex(psi_out_ct0(t+1, 0), -psi_out_ct0(t+1, 1)) * d_psi_out_v;
    __syncthreads();
        if (nrow < 23) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 23];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 23];
        }
        __syncthreads();
        if (nrow < 11) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 12];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 12];
        }
        __syncthreads();
        if (nrow < 6) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 6];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 6];
        }
        __syncthreads();
        if (nrow < 3) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 3];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 3];
        }
        __syncthreads();
        if (nrow < 1) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 2];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 2];
        }
        __syncthreads();
        if (nrow < 1) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 1];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 1];
        }
        __syncthreads();

    if (nrow == 0) {
        if ((t == 0) && (d_nc == 0)) {
            atomicAddD(ovlp_r, s_psik[idx][0].real());
            atomicAddD(ovlp_i, s_psik[idx][0].imag());
        }
        atomicAddD(d_ovlps_r + d_nc + NCTRLS*t, s_d_psik[idx][0].real());
        atomicAddD(d_ovlps_i + d_nc + NCTRLS*t, s_d_psik[idx][0].imag());
    }
}


R *states_d1;
R *ovlp_r_d1;
R *ovlp_i_d1;
R *d_ovlps_r_d1;
R *d_ovlps_i_d1;

__global__
void prop_state_kernel1_noct(R *ctrls, R *states)
{
    const unsigned int ct = 0;
    const unsigned int nstate = blockIdx.y;
    const unsigned int nrow = threadIdx.x;
    __shared__ C s_psik[2][48];
    __syncthreads();
    const short s = ct ? -1 : 1;

    int nrow_cur = nrow;
    const int i_dst0 = nrow_cur % 24;
    nrow_cur /= 24;
    const int i_dst1 = nrow_cur % 2;
    nrow_cur /= 2;

    /* R psi_out_v = psi_out(0, ri); */
    R psi_out_v_r = psi_out1(0, 0);
    R psi_out_v_i = psi_out1(0, 1);
    for (int t = 1; t <= PLEN; t++) {
        int ctrl_t = ct ? (PLEN - t) : (t-1);
        int idx = 0;
        s_psik[0][nrow] = C::complex(psi_out_v_r, psi_out_v_i);

        for (int k = 1; k <= TAYLOR_ORDER; k++) {
            // psi_k -> (pf*H)psi_k
            // psi_out -> psi_out + (pf*H)psi_k
            __syncthreads();

            // TODO: Parallelize this
            R cpf, pf;
            C ppf, t_ppf, H_psi_k_sum;
            int i_src, src_row, valid;
            H_psi_k_sum = 0;
                    cpf = 1.0 / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -1.73415914478e-05);
                            ppf *= i_dst0 * i_dst0;
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, -0.774088429845);
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 0.774088429845);
                            ppf *= i_dst1 * i_dst1;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 0.0126591104295);
                            ppf *= i_dst0 ;
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, -8.16814089933e-06);
                            ppf *= i_dst0 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 8.16814089933e-06);
                            ppf *= i_dst0 * i_dst0;
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 0;
                        src_row = src_row * 24 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 0)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - -1;
                        src_row = src_row * 24 + i_src;
                            valid = valid && (i_src < 24);
                                pf *= sqrt((R) (i_src - 0));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 1;
                        src_row = src_row * 24 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 1)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0125663706144, 0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - -1;
                        src_row = src_row * 24 + i_src;
                            valid = valid && (i_src < 24);
                                pf *= sqrt((R) (i_src - 0));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(-0.0125663706144, -0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 1;
                        src_row = src_row * 24 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 2)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - -1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src < 2);
                                pf *= sqrt((R) (i_src - 0));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 24 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 24 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 3)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0125663706144, 0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - -1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src < 2);
                                pf *= sqrt((R) (i_src - 0));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 24 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(-0.0125663706144, -0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 24 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
            s_psik[1-idx][nrow] = H_psi_k_sum;
            psi_out_v_r += H_psi_k_sum.real();
            psi_out_v_i += H_psi_k_sum.imag();

            // swap psi_k and psi_k_next
            idx = 1 - idx;
        }

        psi_out1(t, 0) = psi_out_v_r;
        psi_out1(t, 1) = psi_out_v_i;
    }
}
__global__
void prop_state_kernel1_withct(R *ctrls, R *states)
{
    const unsigned int ct = 1;
    const unsigned int nstate = blockIdx.y;
    const unsigned int nrow = threadIdx.x;
    __shared__ C s_psik[2][48];
    __syncthreads();
    const short s = ct ? -1 : 1;

    int nrow_cur = nrow;
    const int i_dst0 = nrow_cur % 24;
    nrow_cur /= 24;
    const int i_dst1 = nrow_cur % 2;
    nrow_cur /= 2;

    /* R psi_out_v = psi_out(0, ri); */
    R psi_out_v_r = psi_out1(0, 0);
    R psi_out_v_i = psi_out1(0, 1);
    for (int t = 1; t <= PLEN; t++) {
        int ctrl_t = ct ? (PLEN - t) : (t-1);
        int idx = 0;
        s_psik[0][nrow] = C::complex(psi_out_v_r, psi_out_v_i);

        for (int k = 1; k <= TAYLOR_ORDER; k++) {
            // psi_k -> (pf*H)psi_k
            // psi_out -> psi_out + (pf*H)psi_k
            __syncthreads();

            // TODO: Parallelize this
            R cpf, pf;
            C ppf, t_ppf, H_psi_k_sum;
            int i_src, src_row, valid;
            H_psi_k_sum = 0;
                    cpf = 1.0 / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -1.73415914478e-05);
                            ppf *= i_dst0 * i_dst0;
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, -0.774088429845);
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 0.774088429845);
                            ppf *= i_dst1 * i_dst1;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 0.0126591104295);
                            ppf *= i_dst0 ;
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, -8.16814089933e-06);
                            ppf *= i_dst0 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 8.16814089933e-06);
                            ppf *= i_dst0 * i_dst0;
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 0;
                        src_row = src_row * 24 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 0)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - -1;
                        src_row = src_row * 24 + i_src;
                            valid = valid && (i_src < 24);
                                pf *= sqrt((R) (i_src - 0));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 1;
                        src_row = src_row * 24 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 1)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0125663706144, 0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - -1;
                        src_row = src_row * 24 + i_src;
                            valid = valid && (i_src < 24);
                                pf *= sqrt((R) (i_src - 0));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(-0.0125663706144, -0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 1;
                        src_row = src_row * 24 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 2)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - -1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src < 2);
                                pf *= sqrt((R) (i_src - 0));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 24 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 24 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 3)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0125663706144, 0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - -1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src < 2);
                                pf *= sqrt((R) (i_src - 0));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 24 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(-0.0125663706144, -0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 24 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
            s_psik[1-idx][nrow] = H_psi_k_sum;
            psi_out_v_r += H_psi_k_sum.real();
            psi_out_v_i += H_psi_k_sum.imag();

            // swap psi_k and psi_k_next
            idx = 1 - idx;
        }

        psi_out1(t, 0) = psi_out_v_r;
        psi_out1(t, 1) = psi_out_v_i;
    }
}

__global__
void ovlps_grad_kernel1(R *ctrls, R *states, R *ovlp_r, R *ovlp_i, R *d_ovlps_r, R *d_ovlps_i)
{
    const unsigned int ct = 0;
    const unsigned int t = blockIdx.x;
    const unsigned int nstate = blockIdx.y;
    const unsigned int d_nc = blockIdx.z;
    const unsigned int nrow = threadIdx.x;

    int s = ct ? -1 : 1;

    int nrow_cur = nrow;
    const int i_dst0 = nrow_cur % 24;
    nrow_cur /= 24;
    const int i_dst1 = nrow_cur % 2;
    nrow_cur /= 2;

    C psi_out_v = C::complex(psi_out1(t, 0), psi_out1(t, 1));
    C d_psi_out_v = C::complex(0, 0);
        __shared__ C s_psik[2][48];
        __shared__ C s_d_psik[2][48];
        __syncthreads();
        int idx = 0;
        s_psik[0][nrow] = psi_out_v;
        s_d_psik[0][nrow] = d_psi_out_v;

    for (int k = 1; k <= TAYLOR_ORDER; k++) {
        // psi_k -> (pf*H)psi_k
        // psi_out -> psi_out + (pf*H)psi_k
        __syncthreads();

        R cpf, pf;
        C ppf, t_ppf, H_psi_k_sum, d_H_psi_k_sum;
        int i_src, src_row, valid;
        H_psi_k_sum = 0;
        d_H_psi_k_sum = 0;
                cpf = 1.0;
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -1.73415914478e-05);
                        ppf *= i_dst0 * i_dst0;
                        ppf *= i_dst1 ;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, -0.774088429845);
                        ppf *= i_dst1 ;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, 0.774088429845);
                        ppf *= i_dst1 * i_dst1;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, 0.0126591104295);
                        ppf *= i_dst0 ;
                        ppf *= i_dst1 ;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, -8.16814089933e-06);
                        ppf *= i_dst0 ;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, 8.16814089933e-06);
                        ppf *= i_dst0 * i_dst0;
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - 0;
                    src_row = src_row * 24 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == -1)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                cpf = ctrls[idxctrls(t, 0)];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -0.0125663706144);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - -1;
                    src_row = src_row * 24 + i_src;
                        valid = valid && (i_src < 24);
                            pf *= sqrt((R) (i_src - 0));
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 0)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -0.0125663706144);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - 1;
                    src_row = src_row * 24 + i_src;
                        valid = valid && (i_src >= 0);
                            pf *= sqrt((R) (i_src + 1));
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 0)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                cpf = ctrls[idxctrls(t, 1)];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0125663706144, 0.0);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - -1;
                    src_row = src_row * 24 + i_src;
                        valid = valid && (i_src < 24);
                            pf *= sqrt((R) (i_src - 0));
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 1)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(-0.0125663706144, -0.0);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - 1;
                    src_row = src_row * 24 + i_src;
                        valid = valid && (i_src >= 0);
                            pf *= sqrt((R) (i_src + 1));
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 1)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                cpf = ctrls[idxctrls(t, 2)];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -0.0125663706144);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - -1;
                    src_row = src_row * 2 + i_src;
                        valid = valid && (i_src < 2);
                            pf *= sqrt((R) (i_src - 0));
                    i_src = i_dst0 - 0;
                    src_row = src_row * 24 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 2)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -0.0125663706144);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 1;
                    src_row = src_row * 2 + i_src;
                        valid = valid && (i_src >= 0);
                            pf *= sqrt((R) (i_src + 1));
                    i_src = i_dst0 - 0;
                    src_row = src_row * 24 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 2)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                cpf = ctrls[idxctrls(t, 3)];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0125663706144, 0.0);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - -1;
                    src_row = src_row * 2 + i_src;
                        valid = valid && (i_src < 2);
                            pf *= sqrt((R) (i_src - 0));
                    i_src = i_dst0 - 0;
                    src_row = src_row * 24 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 3)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(-0.0125663706144, -0.0);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 1;
                    src_row = src_row * 2 + i_src;
                        valid = valid && (i_src >= 0);
                            pf *= sqrt((R) (i_src + 1));
                    i_src = i_dst0 - 0;
                    src_row = src_row * 24 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 3)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];

        s_psik[1-idx][nrow] = H_psi_k_sum;
        s_d_psik[1-idx][nrow] = d_H_psi_k_sum;

        // swap psi_k and psi_k_next
        idx = 1 - idx;

        psi_out_v += H_psi_k_sum;
        d_psi_out_v += d_H_psi_k_sum;
    }

    // reuse shared memory for calculation of overlaps
    // - for conjugate
    s_psik[idx][nrow] = C::complex(psi_out_ct1(t+1, 0), -psi_out_ct1(t+1, 1)) * psi_out_v;
    s_d_psik[idx][nrow] = C::complex(psi_out_ct1(t+1, 0), -psi_out_ct1(t+1, 1)) * d_psi_out_v;
    __syncthreads();
        if (nrow < 24) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 24];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 24];
        }
        __syncthreads();
        if (nrow < 12) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 12];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 12];
        }
        __syncthreads();
        if (nrow < 6) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 6];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 6];
        }
        __syncthreads();
        if (nrow < 3) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 3];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 3];
        }
        __syncthreads();
        if (nrow < 1) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 2];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 2];
        }
        __syncthreads();
        if (nrow < 1) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 1];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 1];
        }
        __syncthreads();

    if (nrow == 0) {
        if ((t == 0) && (d_nc == 0)) {
            atomicAddD(ovlp_r, s_psik[idx][0].real());
            atomicAddD(ovlp_i, s_psik[idx][0].imag());
        }
        atomicAddD(d_ovlps_r + d_nc + NCTRLS*t, s_d_psik[idx][0].real());
        atomicAddD(d_ovlps_i + d_nc + NCTRLS*t, s_d_psik[idx][0].imag());
    }
}


R *states_d2;
R *ovlp_r_d2;
R *ovlp_i_d2;
R *d_ovlps_r_d2;
R *d_ovlps_i_d2;

__global__
void prop_state_kernel2_noct(R *ctrls, R *states)
{
    const unsigned int ct = 0;
    const unsigned int nstate = blockIdx.y;
    const unsigned int nrow = threadIdx.x;
    __shared__ C s_psik[2][50];
    __syncthreads();
    const short s = ct ? -1 : 1;

    int nrow_cur = nrow;
    const int i_dst0 = nrow_cur % 25;
    nrow_cur /= 25;
    const int i_dst1 = nrow_cur % 2;
    nrow_cur /= 2;

    /* R psi_out_v = psi_out(0, ri); */
    R psi_out_v_r = psi_out2(0, 0);
    R psi_out_v_i = psi_out2(0, 1);
    for (int t = 1; t <= PLEN; t++) {
        int ctrl_t = ct ? (PLEN - t) : (t-1);
        int idx = 0;
        s_psik[0][nrow] = C::complex(psi_out_v_r, psi_out_v_i);

        for (int k = 1; k <= TAYLOR_ORDER; k++) {
            // psi_k -> (pf*H)psi_k
            // psi_out -> psi_out + (pf*H)psi_k
            __syncthreads();

            // TODO: Parallelize this
            R cpf, pf;
            C ppf, t_ppf, H_psi_k_sum;
            int i_src, src_row, valid;
            H_psi_k_sum = 0;
                    cpf = 1.0 / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -1.73415914478e-05);
                            ppf *= i_dst0 * i_dst0;
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, -0.774088429845);
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 0.774088429845);
                            ppf *= i_dst1 * i_dst1;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 0.0126591104295);
                            ppf *= i_dst0 ;
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, -8.16814089933e-06);
                            ppf *= i_dst0 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 8.16814089933e-06);
                            ppf *= i_dst0 * i_dst0;
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 0;
                        src_row = src_row * 25 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 0)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - -1;
                        src_row = src_row * 25 + i_src;
                            valid = valid && (i_src < 25);
                                pf *= sqrt((R) (i_src - 0));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 1;
                        src_row = src_row * 25 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 1)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0125663706144, 0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - -1;
                        src_row = src_row * 25 + i_src;
                            valid = valid && (i_src < 25);
                                pf *= sqrt((R) (i_src - 0));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(-0.0125663706144, -0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 1;
                        src_row = src_row * 25 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 2)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - -1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src < 2);
                                pf *= sqrt((R) (i_src - 0));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 25 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 25 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 3)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0125663706144, 0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - -1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src < 2);
                                pf *= sqrt((R) (i_src - 0));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 25 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(-0.0125663706144, -0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 25 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
            s_psik[1-idx][nrow] = H_psi_k_sum;
            psi_out_v_r += H_psi_k_sum.real();
            psi_out_v_i += H_psi_k_sum.imag();

            // swap psi_k and psi_k_next
            idx = 1 - idx;
        }

        psi_out2(t, 0) = psi_out_v_r;
        psi_out2(t, 1) = psi_out_v_i;
    }
}
__global__
void prop_state_kernel2_withct(R *ctrls, R *states)
{
    const unsigned int ct = 1;
    const unsigned int nstate = blockIdx.y;
    const unsigned int nrow = threadIdx.x;
    __shared__ C s_psik[2][50];
    __syncthreads();
    const short s = ct ? -1 : 1;

    int nrow_cur = nrow;
    const int i_dst0 = nrow_cur % 25;
    nrow_cur /= 25;
    const int i_dst1 = nrow_cur % 2;
    nrow_cur /= 2;

    /* R psi_out_v = psi_out(0, ri); */
    R psi_out_v_r = psi_out2(0, 0);
    R psi_out_v_i = psi_out2(0, 1);
    for (int t = 1; t <= PLEN; t++) {
        int ctrl_t = ct ? (PLEN - t) : (t-1);
        int idx = 0;
        s_psik[0][nrow] = C::complex(psi_out_v_r, psi_out_v_i);

        for (int k = 1; k <= TAYLOR_ORDER; k++) {
            // psi_k -> (pf*H)psi_k
            // psi_out -> psi_out + (pf*H)psi_k
            __syncthreads();

            // TODO: Parallelize this
            R cpf, pf;
            C ppf, t_ppf, H_psi_k_sum;
            int i_src, src_row, valid;
            H_psi_k_sum = 0;
                    cpf = 1.0 / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -1.73415914478e-05);
                            ppf *= i_dst0 * i_dst0;
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, -0.774088429845);
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 0.774088429845);
                            ppf *= i_dst1 * i_dst1;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 0.0126591104295);
                            ppf *= i_dst0 ;
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, -8.16814089933e-06);
                            ppf *= i_dst0 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 8.16814089933e-06);
                            ppf *= i_dst0 * i_dst0;
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 0;
                        src_row = src_row * 25 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 0)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - -1;
                        src_row = src_row * 25 + i_src;
                            valid = valid && (i_src < 25);
                                pf *= sqrt((R) (i_src - 0));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 1;
                        src_row = src_row * 25 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 1)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0125663706144, 0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - -1;
                        src_row = src_row * 25 + i_src;
                            valid = valid && (i_src < 25);
                                pf *= sqrt((R) (i_src - 0));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(-0.0125663706144, -0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 1;
                        src_row = src_row * 25 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 2)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - -1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src < 2);
                                pf *= sqrt((R) (i_src - 0));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 25 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 25 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 3)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0125663706144, 0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - -1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src < 2);
                                pf *= sqrt((R) (i_src - 0));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 25 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(-0.0125663706144, -0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 25 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
            s_psik[1-idx][nrow] = H_psi_k_sum;
            psi_out_v_r += H_psi_k_sum.real();
            psi_out_v_i += H_psi_k_sum.imag();

            // swap psi_k and psi_k_next
            idx = 1 - idx;
        }

        psi_out2(t, 0) = psi_out_v_r;
        psi_out2(t, 1) = psi_out_v_i;
    }
}

__global__
void ovlps_grad_kernel2(R *ctrls, R *states, R *ovlp_r, R *ovlp_i, R *d_ovlps_r, R *d_ovlps_i)
{
    const unsigned int ct = 0;
    const unsigned int t = blockIdx.x;
    const unsigned int nstate = blockIdx.y;
    const unsigned int d_nc = blockIdx.z;
    const unsigned int nrow = threadIdx.x;

    int s = ct ? -1 : 1;

    int nrow_cur = nrow;
    const int i_dst0 = nrow_cur % 25;
    nrow_cur /= 25;
    const int i_dst1 = nrow_cur % 2;
    nrow_cur /= 2;

    C psi_out_v = C::complex(psi_out2(t, 0), psi_out2(t, 1));
    C d_psi_out_v = C::complex(0, 0);
        __shared__ C s_psik[2][50];
        __shared__ C s_d_psik[2][50];
        __syncthreads();
        int idx = 0;
        s_psik[0][nrow] = psi_out_v;
        s_d_psik[0][nrow] = d_psi_out_v;

    for (int k = 1; k <= TAYLOR_ORDER; k++) {
        // psi_k -> (pf*H)psi_k
        // psi_out -> psi_out + (pf*H)psi_k
        __syncthreads();

        R cpf, pf;
        C ppf, t_ppf, H_psi_k_sum, d_H_psi_k_sum;
        int i_src, src_row, valid;
        H_psi_k_sum = 0;
        d_H_psi_k_sum = 0;
                cpf = 1.0;
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -1.73415914478e-05);
                        ppf *= i_dst0 * i_dst0;
                        ppf *= i_dst1 ;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, -0.774088429845);
                        ppf *= i_dst1 ;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, 0.774088429845);
                        ppf *= i_dst1 * i_dst1;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, 0.0126591104295);
                        ppf *= i_dst0 ;
                        ppf *= i_dst1 ;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, -8.16814089933e-06);
                        ppf *= i_dst0 ;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, 8.16814089933e-06);
                        ppf *= i_dst0 * i_dst0;
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - 0;
                    src_row = src_row * 25 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == -1)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                cpf = ctrls[idxctrls(t, 0)];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -0.0125663706144);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - -1;
                    src_row = src_row * 25 + i_src;
                        valid = valid && (i_src < 25);
                            pf *= sqrt((R) (i_src - 0));
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 0)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -0.0125663706144);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - 1;
                    src_row = src_row * 25 + i_src;
                        valid = valid && (i_src >= 0);
                            pf *= sqrt((R) (i_src + 1));
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 0)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                cpf = ctrls[idxctrls(t, 1)];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0125663706144, 0.0);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - -1;
                    src_row = src_row * 25 + i_src;
                        valid = valid && (i_src < 25);
                            pf *= sqrt((R) (i_src - 0));
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 1)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(-0.0125663706144, -0.0);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - 1;
                    src_row = src_row * 25 + i_src;
                        valid = valid && (i_src >= 0);
                            pf *= sqrt((R) (i_src + 1));
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 1)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                cpf = ctrls[idxctrls(t, 2)];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -0.0125663706144);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - -1;
                    src_row = src_row * 2 + i_src;
                        valid = valid && (i_src < 2);
                            pf *= sqrt((R) (i_src - 0));
                    i_src = i_dst0 - 0;
                    src_row = src_row * 25 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 2)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -0.0125663706144);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 1;
                    src_row = src_row * 2 + i_src;
                        valid = valid && (i_src >= 0);
                            pf *= sqrt((R) (i_src + 1));
                    i_src = i_dst0 - 0;
                    src_row = src_row * 25 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 2)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                cpf = ctrls[idxctrls(t, 3)];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0125663706144, 0.0);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - -1;
                    src_row = src_row * 2 + i_src;
                        valid = valid && (i_src < 2);
                            pf *= sqrt((R) (i_src - 0));
                    i_src = i_dst0 - 0;
                    src_row = src_row * 25 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 3)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(-0.0125663706144, -0.0);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 1;
                    src_row = src_row * 2 + i_src;
                        valid = valid && (i_src >= 0);
                            pf *= sqrt((R) (i_src + 1));
                    i_src = i_dst0 - 0;
                    src_row = src_row * 25 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 3)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];

        s_psik[1-idx][nrow] = H_psi_k_sum;
        s_d_psik[1-idx][nrow] = d_H_psi_k_sum;

        // swap psi_k and psi_k_next
        idx = 1 - idx;

        psi_out_v += H_psi_k_sum;
        d_psi_out_v += d_H_psi_k_sum;
    }

    // reuse shared memory for calculation of overlaps
    // - for conjugate
    s_psik[idx][nrow] = C::complex(psi_out_ct2(t+1, 0), -psi_out_ct2(t+1, 1)) * psi_out_v;
    s_d_psik[idx][nrow] = C::complex(psi_out_ct2(t+1, 0), -psi_out_ct2(t+1, 1)) * d_psi_out_v;
    __syncthreads();
        if (nrow < 25) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 25];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 25];
        }
        __syncthreads();
        if (nrow < 12) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 13];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 13];
        }
        __syncthreads();
        if (nrow < 6) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 7];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 7];
        }
        __syncthreads();
        if (nrow < 3) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 4];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 4];
        }
        __syncthreads();
        if (nrow < 2) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 2];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 2];
        }
        __syncthreads();
        if (nrow < 1) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 1];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 1];
        }
        __syncthreads();

    if (nrow == 0) {
        if ((t == 0) && (d_nc == 0)) {
            atomicAddD(ovlp_r, s_psik[idx][0].real());
            atomicAddD(ovlp_i, s_psik[idx][0].imag());
        }
        atomicAddD(d_ovlps_r + d_nc + NCTRLS*t, s_d_psik[idx][0].real());
        atomicAddD(d_ovlps_i + d_nc + NCTRLS*t, s_d_psik[idx][0].imag());
    }
}


R *states_d3;
R *ovlp_r_d3;
R *ovlp_i_d3;
R *d_ovlps_r_d3;
R *d_ovlps_i_d3;

__global__
void prop_state_kernel3_noct(R *ctrls, R *states)
{
    const unsigned int ct = 0;
    const unsigned int nstate = blockIdx.y;
    const unsigned int nrow = threadIdx.x;
    __shared__ C s_psik[2][52];
    __syncthreads();
    const short s = ct ? -1 : 1;

    int nrow_cur = nrow;
    const int i_dst0 = nrow_cur % 26;
    nrow_cur /= 26;
    const int i_dst1 = nrow_cur % 2;
    nrow_cur /= 2;

    /* R psi_out_v = psi_out(0, ri); */
    R psi_out_v_r = psi_out3(0, 0);
    R psi_out_v_i = psi_out3(0, 1);
    for (int t = 1; t <= PLEN; t++) {
        int ctrl_t = ct ? (PLEN - t) : (t-1);
        int idx = 0;
        s_psik[0][nrow] = C::complex(psi_out_v_r, psi_out_v_i);

        for (int k = 1; k <= TAYLOR_ORDER; k++) {
            // psi_k -> (pf*H)psi_k
            // psi_out -> psi_out + (pf*H)psi_k
            __syncthreads();

            // TODO: Parallelize this
            R cpf, pf;
            C ppf, t_ppf, H_psi_k_sum;
            int i_src, src_row, valid;
            H_psi_k_sum = 0;
                    cpf = 1.0 / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -1.73415914478e-05);
                            ppf *= i_dst0 * i_dst0;
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, -0.774088429845);
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 0.774088429845);
                            ppf *= i_dst1 * i_dst1;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 0.0126591104295);
                            ppf *= i_dst0 ;
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, -8.16814089933e-06);
                            ppf *= i_dst0 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 8.16814089933e-06);
                            ppf *= i_dst0 * i_dst0;
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 0;
                        src_row = src_row * 26 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 0)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - -1;
                        src_row = src_row * 26 + i_src;
                            valid = valid && (i_src < 26);
                                pf *= sqrt((R) (i_src - 0));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 1;
                        src_row = src_row * 26 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 1)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0125663706144, 0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - -1;
                        src_row = src_row * 26 + i_src;
                            valid = valid && (i_src < 26);
                                pf *= sqrt((R) (i_src - 0));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(-0.0125663706144, -0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 1;
                        src_row = src_row * 26 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 2)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - -1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src < 2);
                                pf *= sqrt((R) (i_src - 0));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 26 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 26 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 3)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0125663706144, 0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - -1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src < 2);
                                pf *= sqrt((R) (i_src - 0));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 26 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(-0.0125663706144, -0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 26 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
            s_psik[1-idx][nrow] = H_psi_k_sum;
            psi_out_v_r += H_psi_k_sum.real();
            psi_out_v_i += H_psi_k_sum.imag();

            // swap psi_k and psi_k_next
            idx = 1 - idx;
        }

        psi_out3(t, 0) = psi_out_v_r;
        psi_out3(t, 1) = psi_out_v_i;
    }
}
__global__
void prop_state_kernel3_withct(R *ctrls, R *states)
{
    const unsigned int ct = 1;
    const unsigned int nstate = blockIdx.y;
    const unsigned int nrow = threadIdx.x;
    __shared__ C s_psik[2][52];
    __syncthreads();
    const short s = ct ? -1 : 1;

    int nrow_cur = nrow;
    const int i_dst0 = nrow_cur % 26;
    nrow_cur /= 26;
    const int i_dst1 = nrow_cur % 2;
    nrow_cur /= 2;

    /* R psi_out_v = psi_out(0, ri); */
    R psi_out_v_r = psi_out3(0, 0);
    R psi_out_v_i = psi_out3(0, 1);
    for (int t = 1; t <= PLEN; t++) {
        int ctrl_t = ct ? (PLEN - t) : (t-1);
        int idx = 0;
        s_psik[0][nrow] = C::complex(psi_out_v_r, psi_out_v_i);

        for (int k = 1; k <= TAYLOR_ORDER; k++) {
            // psi_k -> (pf*H)psi_k
            // psi_out -> psi_out + (pf*H)psi_k
            __syncthreads();

            // TODO: Parallelize this
            R cpf, pf;
            C ppf, t_ppf, H_psi_k_sum;
            int i_src, src_row, valid;
            H_psi_k_sum = 0;
                    cpf = 1.0 / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -1.73415914478e-05);
                            ppf *= i_dst0 * i_dst0;
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, -0.774088429845);
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 0.774088429845);
                            ppf *= i_dst1 * i_dst1;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 0.0126591104295);
                            ppf *= i_dst0 ;
                            ppf *= i_dst1 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, -8.16814089933e-06);
                            ppf *= i_dst0 ;
                        t_ppf += ppf;
                        ppf = C::complex(0.0, 8.16814089933e-06);
                            ppf *= i_dst0 * i_dst0;
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 0;
                        src_row = src_row * 26 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 0)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - -1;
                        src_row = src_row * 26 + i_src;
                            valid = valid && (i_src < 26);
                                pf *= sqrt((R) (i_src - 0));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 1;
                        src_row = src_row * 26 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 1)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0125663706144, 0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - -1;
                        src_row = src_row * 26 + i_src;
                            valid = valid && (i_src < 26);
                                pf *= sqrt((R) (i_src - 0));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(-0.0125663706144, -0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 0;
                        src_row = src_row * 2 + i_src;
                        i_src = i_dst0 - 1;
                        src_row = src_row * 26 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 2)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - -1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src < 2);
                                pf *= sqrt((R) (i_src - 0));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 26 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0, -0.0125663706144);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 26 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    cpf = ctrls[idxctrls(ctrl_t, 3)] / k;
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(0.0125663706144, 0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - -1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src < 2);
                                pf *= sqrt((R) (i_src - 0));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 26 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                    valid = 1;
                    src_row = 0;
                    t_ppf = 0;
                        ppf = C::complex(-0.0125663706144, -0.0);
                        t_ppf += ppf;
                    pf = 1;
                        i_src = i_dst1 - 1;
                        src_row = src_row * 2 + i_src;
                            valid = valid && (i_src >= 0);
                                pf *= sqrt((R) (i_src + 1));
                        i_src = i_dst0 - 0;
                        src_row = src_row * 26 + i_src;
                    src_row *= valid;
                    pf = valid ? pf : 0.0;
                    H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
            s_psik[1-idx][nrow] = H_psi_k_sum;
            psi_out_v_r += H_psi_k_sum.real();
            psi_out_v_i += H_psi_k_sum.imag();

            // swap psi_k and psi_k_next
            idx = 1 - idx;
        }

        psi_out3(t, 0) = psi_out_v_r;
        psi_out3(t, 1) = psi_out_v_i;
    }
}

__global__
void ovlps_grad_kernel3(R *ctrls, R *states, R *ovlp_r, R *ovlp_i, R *d_ovlps_r, R *d_ovlps_i)
{
    const unsigned int ct = 0;
    const unsigned int t = blockIdx.x;
    const unsigned int nstate = blockIdx.y;
    const unsigned int d_nc = blockIdx.z;
    const unsigned int nrow = threadIdx.x;

    int s = ct ? -1 : 1;

    int nrow_cur = nrow;
    const int i_dst0 = nrow_cur % 26;
    nrow_cur /= 26;
    const int i_dst1 = nrow_cur % 2;
    nrow_cur /= 2;

    C psi_out_v = C::complex(psi_out3(t, 0), psi_out3(t, 1));
    C d_psi_out_v = C::complex(0, 0);
        __shared__ C s_psik[2][52];
        __shared__ C s_d_psik[2][52];
        __syncthreads();
        int idx = 0;
        s_psik[0][nrow] = psi_out_v;
        s_d_psik[0][nrow] = d_psi_out_v;

    for (int k = 1; k <= TAYLOR_ORDER; k++) {
        // psi_k -> (pf*H)psi_k
        // psi_out -> psi_out + (pf*H)psi_k
        __syncthreads();

        R cpf, pf;
        C ppf, t_ppf, H_psi_k_sum, d_H_psi_k_sum;
        int i_src, src_row, valid;
        H_psi_k_sum = 0;
        d_H_psi_k_sum = 0;
                cpf = 1.0;
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -1.73415914478e-05);
                        ppf *= i_dst0 * i_dst0;
                        ppf *= i_dst1 ;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, -0.774088429845);
                        ppf *= i_dst1 ;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, 0.774088429845);
                        ppf *= i_dst1 * i_dst1;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, 0.0126591104295);
                        ppf *= i_dst0 ;
                        ppf *= i_dst1 ;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, -8.16814089933e-06);
                        ppf *= i_dst0 ;
                    t_ppf += ppf;
                    ppf = C::complex(0.0, 8.16814089933e-06);
                        ppf *= i_dst0 * i_dst0;
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - 0;
                    src_row = src_row * 26 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == -1)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                cpf = ctrls[idxctrls(t, 0)];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -0.0125663706144);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - -1;
                    src_row = src_row * 26 + i_src;
                        valid = valid && (i_src < 26);
                            pf *= sqrt((R) (i_src - 0));
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 0)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -0.0125663706144);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - 1;
                    src_row = src_row * 26 + i_src;
                        valid = valid && (i_src >= 0);
                            pf *= sqrt((R) (i_src + 1));
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 0)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                cpf = ctrls[idxctrls(t, 1)];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0125663706144, 0.0);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - -1;
                    src_row = src_row * 26 + i_src;
                        valid = valid && (i_src < 26);
                            pf *= sqrt((R) (i_src - 0));
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 1)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(-0.0125663706144, -0.0);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 0;
                    src_row = src_row * 2 + i_src;
                    i_src = i_dst0 - 1;
                    src_row = src_row * 26 + i_src;
                        valid = valid && (i_src >= 0);
                            pf *= sqrt((R) (i_src + 1));
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 1)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                cpf = ctrls[idxctrls(t, 2)];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -0.0125663706144);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - -1;
                    src_row = src_row * 2 + i_src;
                        valid = valid && (i_src < 2);
                            pf *= sqrt((R) (i_src - 0));
                    i_src = i_dst0 - 0;
                    src_row = src_row * 26 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 2)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0, -0.0125663706144);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 1;
                    src_row = src_row * 2 + i_src;
                        valid = valid && (i_src >= 0);
                            pf *= sqrt((R) (i_src + 1));
                    i_src = i_dst0 - 0;
                    src_row = src_row * 26 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 2)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                cpf = ctrls[idxctrls(t, 3)];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(0.0125663706144, 0.0);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - -1;
                    src_row = src_row * 2 + i_src;
                        valid = valid && (i_src < 2);
                            pf *= sqrt((R) (i_src - 0));
                    i_src = i_dst0 - 0;
                    src_row = src_row * 26 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 3)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];
                valid = 1;
                src_row = 0;
                t_ppf = 0;
                    ppf = C::complex(-0.0125663706144, -0.0);
                    t_ppf += ppf;
                pf = 1.0 / k;
                    i_src = i_dst1 - 1;
                    src_row = src_row * 2 + i_src;
                        valid = valid && (i_src >= 0);
                            pf *= sqrt((R) (i_src + 1));
                    i_src = i_dst0 - 0;
                    src_row = src_row * 26 + i_src;
                src_row *= valid;
                pf = valid ? pf : 0.0;
                H_psi_k_sum += (s * cpf * pf) * t_ppf * s_psik[idx][src_row];
                d_H_psi_k_sum += (s * cpf * pf) * t_ppf * s_d_psik[idx][src_row];
                if (d_nc == 3)
                    d_H_psi_k_sum += (s * pf) * t_ppf * s_psik[idx][src_row];

        s_psik[1-idx][nrow] = H_psi_k_sum;
        s_d_psik[1-idx][nrow] = d_H_psi_k_sum;

        // swap psi_k and psi_k_next
        idx = 1 - idx;

        psi_out_v += H_psi_k_sum;
        d_psi_out_v += d_H_psi_k_sum;
    }

    // reuse shared memory for calculation of overlaps
    // - for conjugate
    s_psik[idx][nrow] = C::complex(psi_out_ct3(t+1, 0), -psi_out_ct3(t+1, 1)) * psi_out_v;
    s_d_psik[idx][nrow] = C::complex(psi_out_ct3(t+1, 0), -psi_out_ct3(t+1, 1)) * d_psi_out_v;
    __syncthreads();
        if (nrow < 26) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 26];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 26];
        }
        __syncthreads();
        if (nrow < 13) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 13];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 13];
        }
        __syncthreads();
        if (nrow < 6) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 7];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 7];
        }
        __syncthreads();
        if (nrow < 3) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 4];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 4];
        }
        __syncthreads();
        if (nrow < 2) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 2];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 2];
        }
        __syncthreads();
        if (nrow < 1) {
            s_psik[idx][nrow] += s_psik[idx][nrow + 1];
            s_d_psik[idx][nrow] += s_d_psik[idx][nrow + 1];
        }
        __syncthreads();

    if (nrow == 0) {
        if ((t == 0) && (d_nc == 0)) {
            atomicAddD(ovlp_r, s_psik[idx][0].real());
            atomicAddD(ovlp_i, s_psik[idx][0].imag());
        }
        atomicAddD(d_ovlps_r + d_nc + NCTRLS*t, s_d_psik[idx][0].real());
        atomicAddD(d_ovlps_i + d_nc + NCTRLS*t, s_d_psik[idx][0].imag());
    }
}



void grape_step(R *ctrls, R *ovlp_r, R *ovlp_i, R *d_ovlp_r, R *d_ovlp_i)
{
    gpuErrchk(cudaMemcpy(ctrls_d, ctrls, NCTRLS*PLEN*sizeof(R), cudaMemcpyHostToDevice));
    cudaStream_t stream0;
    cudaStreamCreate(&stream0);
    cudaStream_t stream1;
    cudaStreamCreate(&stream1);
    cudaStream_t stream2;
    cudaStreamCreate(&stream2);
    cudaStream_t stream3;
    cudaStreamCreate(&stream3);
    dim3 blocks(1, NSTATE, 1);
    dim3 blocks_ovlp(PLEN, NSTATE, NCTRLS);
    cudaMemsetAsync(ovlp_r_d0, 0, sizeof(R), stream0);
    cudaMemsetAsync(ovlp_i_d0, 0, sizeof(R), stream0);
    cudaMemsetAsync(d_ovlps_r_d0, 0, ctrls_size*sizeof(R), stream0);
    cudaMemsetAsync(d_ovlps_i_d0, 0, ctrls_size*sizeof(R), stream0);
    cudaMemsetAsync(ovlp_r_d1, 0, sizeof(R), stream1);
    cudaMemsetAsync(ovlp_i_d1, 0, sizeof(R), stream1);
    cudaMemsetAsync(d_ovlps_r_d1, 0, ctrls_size*sizeof(R), stream1);
    cudaMemsetAsync(d_ovlps_i_d1, 0, ctrls_size*sizeof(R), stream1);
    cudaMemsetAsync(ovlp_r_d2, 0, sizeof(R), stream2);
    cudaMemsetAsync(ovlp_i_d2, 0, sizeof(R), stream2);
    cudaMemsetAsync(d_ovlps_r_d2, 0, ctrls_size*sizeof(R), stream2);
    cudaMemsetAsync(d_ovlps_i_d2, 0, ctrls_size*sizeof(R), stream2);
    cudaMemsetAsync(ovlp_r_d3, 0, sizeof(R), stream3);
    cudaMemsetAsync(ovlp_i_d3, 0, sizeof(R), stream3);
    cudaMemsetAsync(d_ovlps_r_d3, 0, ctrls_size*sizeof(R), stream3);
    cudaMemsetAsync(d_ovlps_i_d3, 0, ctrls_size*sizeof(R), stream3);
    dim3 threads0(46, 1, 1);
    prop_state_kernel0_noct<<<blocks, threads0, 0, stream0>>>(ctrls_d, states_d0);
    prop_state_kernel0_withct<<<blocks, threads0, 0, stream0>>>(ctrls_d, states_d0);
    ovlps_grad_kernel0<<<blocks_ovlp, threads0, 0, stream0>>>(
        ctrls_d, states_d0, ovlp_r_d0, ovlp_i_d0,
        d_ovlps_r_d0, d_ovlps_i_d0
    );
    dim3 threads1(48, 1, 1);
    prop_state_kernel1_noct<<<blocks, threads1, 0, stream1>>>(ctrls_d, states_d1);
    prop_state_kernel1_withct<<<blocks, threads1, 0, stream1>>>(ctrls_d, states_d1);
    ovlps_grad_kernel1<<<blocks_ovlp, threads1, 0, stream1>>>(
        ctrls_d, states_d1, ovlp_r_d1, ovlp_i_d1,
        d_ovlps_r_d1, d_ovlps_i_d1
    );
    dim3 threads2(50, 1, 1);
    prop_state_kernel2_noct<<<blocks, threads2, 0, stream2>>>(ctrls_d, states_d2);
    prop_state_kernel2_withct<<<blocks, threads2, 0, stream2>>>(ctrls_d, states_d2);
    ovlps_grad_kernel2<<<blocks_ovlp, threads2, 0, stream2>>>(
        ctrls_d, states_d2, ovlp_r_d2, ovlp_i_d2,
        d_ovlps_r_d2, d_ovlps_i_d2
    );
    dim3 threads3(52, 1, 1);
    prop_state_kernel3_noct<<<blocks, threads3, 0, stream3>>>(ctrls_d, states_d3);
    prop_state_kernel3_withct<<<blocks, threads3, 0, stream3>>>(ctrls_d, states_d3);
    ovlps_grad_kernel3<<<blocks_ovlp, threads3, 0, stream3>>>(
        ctrls_d, states_d3, ovlp_r_d3, ovlp_i_d3,
        d_ovlps_r_d3, d_ovlps_i_d3
    );
    cudaMemcpyAsync(d_ovlp_r + 0*ctrls_size, d_ovlps_r_d0, ctrls_size*sizeof(R),
                    cudaMemcpyDeviceToHost, stream0);
    cudaMemcpyAsync(d_ovlp_i + 0*ctrls_size, d_ovlps_i_d0, ctrls_size*sizeof(R),
                    cudaMemcpyDeviceToHost, stream0);
    cudaMemcpyAsync(ovlp_r + 0, ovlp_r_d0, sizeof(R), cudaMemcpyDeviceToHost, stream0);
    cudaMemcpyAsync(ovlp_i + 0, ovlp_i_d0, sizeof(R), cudaMemcpyDeviceToHost, stream0);
    cudaMemcpyAsync(d_ovlp_r + 1*ctrls_size, d_ovlps_r_d1, ctrls_size*sizeof(R),
                    cudaMemcpyDeviceToHost, stream1);
    cudaMemcpyAsync(d_ovlp_i + 1*ctrls_size, d_ovlps_i_d1, ctrls_size*sizeof(R),
                    cudaMemcpyDeviceToHost, stream1);
    cudaMemcpyAsync(ovlp_r + 1, ovlp_r_d1, sizeof(R), cudaMemcpyDeviceToHost, stream1);
    cudaMemcpyAsync(ovlp_i + 1, ovlp_i_d1, sizeof(R), cudaMemcpyDeviceToHost, stream1);
    cudaMemcpyAsync(d_ovlp_r + 2*ctrls_size, d_ovlps_r_d2, ctrls_size*sizeof(R),
                    cudaMemcpyDeviceToHost, stream2);
    cudaMemcpyAsync(d_ovlp_i + 2*ctrls_size, d_ovlps_i_d2, ctrls_size*sizeof(R),
                    cudaMemcpyDeviceToHost, stream2);
    cudaMemcpyAsync(ovlp_r + 2, ovlp_r_d2, sizeof(R), cudaMemcpyDeviceToHost, stream2);
    cudaMemcpyAsync(ovlp_i + 2, ovlp_i_d2, sizeof(R), cudaMemcpyDeviceToHost, stream2);
    cudaMemcpyAsync(d_ovlp_r + 3*ctrls_size, d_ovlps_r_d3, ctrls_size*sizeof(R),
                    cudaMemcpyDeviceToHost, stream3);
    cudaMemcpyAsync(d_ovlp_i + 3*ctrls_size, d_ovlps_i_d3, ctrls_size*sizeof(R),
                    cudaMemcpyDeviceToHost, stream3);
    cudaMemcpyAsync(ovlp_r + 3, ovlp_r_d3, sizeof(R), cudaMemcpyDeviceToHost, stream3);
    cudaMemcpyAsync(ovlp_i + 3, ovlp_i_d3, sizeof(R), cudaMemcpyDeviceToHost, stream3);
    cudaDeviceSynchronize(); gpuErrchk(cudaGetLastError());
    cudaStreamDestroy(stream0);
    cudaStreamDestroy(stream1);
    cudaStreamDestroy(stream2);
    cudaStreamDestroy(stream3);
}

void init_gpu_memory()
{
    cudaDeviceSetSharedMemConfig(cudaSharedMemBankSizeEightByte);
    gpuErrchk(cudaMalloc(&ctrls_d, ctrls_size * sizeof(R)));

    int states_size;
    states_size = 2*NSTATE*(PLEN+1)*46*2;
    gpuErrchk(cudaMalloc(&states_d0, states_size * sizeof(R)));
    gpuErrchk(cudaMemset(states_d0, 0, states_size*sizeof(R)));

    gpuErrchk(cudaMalloc(&ovlp_r_d0, sizeof(R)));
    gpuErrchk(cudaMalloc(&ovlp_i_d0, sizeof(R)));

    gpuErrchk(cudaMalloc(&d_ovlps_r_d0, ctrls_size * sizeof(R)));
    gpuErrchk(cudaMemset(d_ovlps_r_d0, 0, ctrls_size*sizeof(R)));
    gpuErrchk(cudaMalloc(&d_ovlps_i_d0, ctrls_size * sizeof(R)));
    gpuErrchk(cudaMemset(d_ovlps_i_d0, 0, ctrls_size*sizeof(R)));
    states_size = 2*NSTATE*(PLEN+1)*48*2;
    gpuErrchk(cudaMalloc(&states_d1, states_size * sizeof(R)));
    gpuErrchk(cudaMemset(states_d1, 0, states_size*sizeof(R)));

    gpuErrchk(cudaMalloc(&ovlp_r_d1, sizeof(R)));
    gpuErrchk(cudaMalloc(&ovlp_i_d1, sizeof(R)));

    gpuErrchk(cudaMalloc(&d_ovlps_r_d1, ctrls_size * sizeof(R)));
    gpuErrchk(cudaMemset(d_ovlps_r_d1, 0, ctrls_size*sizeof(R)));
    gpuErrchk(cudaMalloc(&d_ovlps_i_d1, ctrls_size * sizeof(R)));
    gpuErrchk(cudaMemset(d_ovlps_i_d1, 0, ctrls_size*sizeof(R)));
    states_size = 2*NSTATE*(PLEN+1)*50*2;
    gpuErrchk(cudaMalloc(&states_d2, states_size * sizeof(R)));
    gpuErrchk(cudaMemset(states_d2, 0, states_size*sizeof(R)));

    gpuErrchk(cudaMalloc(&ovlp_r_d2, sizeof(R)));
    gpuErrchk(cudaMalloc(&ovlp_i_d2, sizeof(R)));

    gpuErrchk(cudaMalloc(&d_ovlps_r_d2, ctrls_size * sizeof(R)));
    gpuErrchk(cudaMemset(d_ovlps_r_d2, 0, ctrls_size*sizeof(R)));
    gpuErrchk(cudaMalloc(&d_ovlps_i_d2, ctrls_size * sizeof(R)));
    gpuErrchk(cudaMemset(d_ovlps_i_d2, 0, ctrls_size*sizeof(R)));
    states_size = 2*NSTATE*(PLEN+1)*52*2;
    gpuErrchk(cudaMalloc(&states_d3, states_size * sizeof(R)));
    gpuErrchk(cudaMemset(states_d3, 0, states_size*sizeof(R)));

    gpuErrchk(cudaMalloc(&ovlp_r_d3, sizeof(R)));
    gpuErrchk(cudaMalloc(&ovlp_i_d3, sizeof(R)));

    gpuErrchk(cudaMalloc(&d_ovlps_r_d3, ctrls_size * sizeof(R)));
    gpuErrchk(cudaMemset(d_ovlps_r_d3, 0, ctrls_size*sizeof(R)));
    gpuErrchk(cudaMalloc(&d_ovlps_i_d3, ctrls_size * sizeof(R)));
    gpuErrchk(cudaMemset(d_ovlps_i_d3, 0, ctrls_size*sizeof(R)));
}

void load_states(int nvar, R *psi0, R *psif)
{
    int states_size;
    switch (nvar) {
        case 0:
            states_size = 2*NSTATE*(PLEN+1)*46*2;
            gpuErrchk(cudaMemset(states_d0, 0, states_size*sizeof(R)));
            for (int i = 0; i < NSTATE; i++) {
                gpuErrchk(cudaMemcpy(
                    states_d0 + idxstates0(0, i, 0, 0, 0),
                    psi0 + (2*i*46), 2*46*sizeof(R), cudaMemcpyHostToDevice)
                );
                gpuErrchk(cudaMemcpy(
                    states_d0 + idxstates0(1, i, 0, 0, 0),
                    psif + (2*i*46), 2*46*sizeof(R), cudaMemcpyHostToDevice)
                );
            }
            break;
        case 1:
            states_size = 2*NSTATE*(PLEN+1)*48*2;
            gpuErrchk(cudaMemset(states_d1, 0, states_size*sizeof(R)));
            for (int i = 0; i < NSTATE; i++) {
                gpuErrchk(cudaMemcpy(
                    states_d1 + idxstates1(0, i, 0, 0, 0),
                    psi0 + (2*i*48), 2*48*sizeof(R), cudaMemcpyHostToDevice)
                );
                gpuErrchk(cudaMemcpy(
                    states_d1 + idxstates1(1, i, 0, 0, 0),
                    psif + (2*i*48), 2*48*sizeof(R), cudaMemcpyHostToDevice)
                );
            }
            break;
        case 2:
            states_size = 2*NSTATE*(PLEN+1)*50*2;
            gpuErrchk(cudaMemset(states_d2, 0, states_size*sizeof(R)));
            for (int i = 0; i < NSTATE; i++) {
                gpuErrchk(cudaMemcpy(
                    states_d2 + idxstates2(0, i, 0, 0, 0),
                    psi0 + (2*i*50), 2*50*sizeof(R), cudaMemcpyHostToDevice)
                );
                gpuErrchk(cudaMemcpy(
                    states_d2 + idxstates2(1, i, 0, 0, 0),
                    psif + (2*i*50), 2*50*sizeof(R), cudaMemcpyHostToDevice)
                );
            }
            break;
        case 3:
            states_size = 2*NSTATE*(PLEN+1)*52*2;
            gpuErrchk(cudaMemset(states_d3, 0, states_size*sizeof(R)));
            for (int i = 0; i < NSTATE; i++) {
                gpuErrchk(cudaMemcpy(
                    states_d3 + idxstates3(0, i, 0, 0, 0),
                    psi0 + (2*i*52), 2*52*sizeof(R), cudaMemcpyHostToDevice)
                );
                gpuErrchk(cudaMemcpy(
                    states_d3 + idxstates3(1, i, 0, 0, 0),
                    psif + (2*i*52), 2*52*sizeof(R), cudaMemcpyHostToDevice)
                );
            }
            break;
    }
}

void get_states(int nvar, R *states)
{
    int states_size;
    switch (nvar) {
        case 0:
            states_size = 2*NSTATE*(PLEN+1)*46*2;
            gpuErrchk(cudaMemcpy(states, states_d0, states_size*sizeof(R), cudaMemcpyDeviceToHost));
            break;
        case 1:
            states_size = 2*NSTATE*(PLEN+1)*48*2;
            gpuErrchk(cudaMemcpy(states, states_d1, states_size*sizeof(R), cudaMemcpyDeviceToHost));
            break;
        case 2:
            states_size = 2*NSTATE*(PLEN+1)*50*2;
            gpuErrchk(cudaMemcpy(states, states_d2, states_size*sizeof(R), cudaMemcpyDeviceToHost));
            break;
        case 3:
            states_size = 2*NSTATE*(PLEN+1)*52*2;
            gpuErrchk(cudaMemcpy(states, states_d3, states_size*sizeof(R), cudaMemcpyDeviceToHost));
            break;
    }
}