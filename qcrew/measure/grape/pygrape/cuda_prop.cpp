const int DIM = %(dim)d;
const int NCTRLS = %(nctrls)d;
const int PLEN = %(plen)d;
const int NSTATE = %(nstate)d;
const int MAXNNZ = %(maxnnz)d;
const int TAYLOR_ORDER = %(taylor_order)d;

typedef float R;

class Complex {
private:
    R x, y;
public:
    Complex() {}
    Complex(R r, R i) { x = r; y = i; }
    friend Complex operator+(const Complex &c1, const Complex &c2);
    friend Complex operator*(const Complex &c1, const Complex &c2);
    friend Complex operator*(const R &r, const Complex &c);
    friend Complex operator*(const Complex &c, const R &r);
};

Complex operator+(const Complex &c1, const Complex &c2) {
    return Complex(c1.x + c2.x, c1.y + c2.y);
}
Complex operator*(const Complex &c1, const Complex &c2) {
    return Complex(c1.x*c2.x - c1.y*c2.y, c1.x*c1.y + c1.y*c2.x);
}
Complex operator*(const R &r, const Complex &c) {
    return Complex(r*c.x, r*c.y);
}
Complex operator*(const Complex &c, const R &r) {
    return Complex(r*c.x, r*c.y);
}
typedef Complex C;

__device__ int Hj[NCTRLS+1][MAXNNZ];
__device__ int Hp[NCTRLS+1][DIM+1];
__device__ C Hx[NCTRLS+1][MAXNNZ][2];
__device__ R ctrls[PLEN][NCTRLS];
__device__ C all_psi_ks[2][NSTATE][PLEN+1][2][DIM];
__device__ C psi_outs[NSTATE][PLEN][DIM];
__device__ C states[2][NSTATE][PLEN+1][DIM];

__device__
void Hv_row(int n_hmt, int n_row, R Xx[DIM][2], R Yx[DIM][2], R Zx[DIM][2], R pf)
{
    __shared__ C sXx[DIM];
    sXx[n_row] = Xx[n_row];
    __syncthreads();
    C sum = 0;
    for(int jj = Hp[n_hmt][n_row]; jj < Hp[n_hmt][n_row+1]; jj++){
        sum += Hx[n_hmt] * sXx[Hj[n_hmt][jj]];
    }
    sum *= pf;
    Yx[i][0] += sum_r;
    Yx[i][1] += sum_i;
    Zx[i][0] += sum_r;
    Zx[i][1] += sum_i;
}

//__device__
void spmv(int Ap[MAXNNZ], int Aj[DIM+1], R Ax[MAXNNZ][2], R Xx[DIM][2], R Yx[DIM][2], R Zx[DIM][2], R pf)
{
    // Y -> Y + pf*AX
    // Z -> Z + pf*AX
    spmv_row<<<1,DIM>>>(Ap, Aj, Ax, Xx, Yx, Zx, pf);
}


//__device__
void Hv(int ct, int c_idx, R v_in[DIM][2], R v_out1[DIM][2], R v_out2[DIM][2], R pf)
{
    spmv(Hp[ct][c_idx], Hj[ct][c_idx], Hx[ct][c_idx], v_in, v_out1, v_out2, pf);
}


//__device__
void H_state(int ct, R ctrls[NCTRLS], R psi_in[DIM][2], R psi_out[DIM][2], R psi_acc[DIM][2], R pf)
{
    // psi_out -> (pf*H)psi_in
    // psi_acc -> psi_acc + (pf*H)psi_in

    memset(psi_out, 0, 2*DIM*sizeof(R));
    // TODO: Parallelize this
    R cpf;
    for (int i = 0; i <= NCTRLS; i++) {
        if (i > 0) {
            cpf =  ctrls[i-1]*pf;
        } else {
            cpf = pf;
        }

        Hv(ct, i, psi_in, psi_out, psi_acc, cpf);
    }
}

//__device__
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

//__global__
void full_prop_state()
{
    int ct = 0; //blockIdx.x;
    int j = 0; //blockIdx.y;
    for (int i = 0; i < PLEN; i++) {
        prop_state(ct, ctrls[i], states[ct][j][i], states[ct][j][i+1], all_psi_ks[ct][j][i]);
    }
}
