#include <iostream>
#include <vector>
using namespace std;

Matrix multiplyNaive(Matrix &mat1, Matrix &mat2) {
    int n = mat1.size(), m = mat1[0].size(), q = mat2[0].size();

    Matrix res(n, Row(q, 0));

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < q; j++) {
            for (int k = 0; k < m; k++) {
                res[i][j] += mat1[i][k] * mat2[k][j];
            }
        }
    }

    return res;
}