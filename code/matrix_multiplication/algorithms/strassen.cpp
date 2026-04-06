#include <iostream>
#include <vector>
#include <cmath>
using namespace std;

// Return the next power of two greater than or equal to n
int nextPowerOfTwo(int n) {
    return pow(2, ceil(log2(n)));
}

// Resize a matrix to newR x newC and 
// fill extra space with zeros
Matrix resizeMatrix(Matrix &mat, int newR, int newC) {
    Matrix resized(newR, Row(newC, 0));
    for (size_t i = 0; i < mat.size(); ++i)
        for (size_t j = 0; j < mat[0].size(); ++j)
            resized[i][j] = mat[i][j];

    return resized;
}

// Perform matrix addition or subtraction 
// of size×size matrices
// sign = 1 for addition, -1 for subtraction
Matrix add(Matrix a, Matrix b, int size, int sign = 1) {
    Matrix res(size, Row(size, 0));
    for (int i = 0; i < size; i++)
        for (int j = 0; j < size; j++)
            res[i][j] = a[i][j] + sign * b[i][j];
    return res;
}

// Recursive implementation of Strassen's 
// matrix multiplication
// Assumes both matrices are size×size 
// and size is a power of 2
Matrix strassen(Matrix mat1, Matrix mat2) {
    int n = mat1.size();

    Matrix res(n, Row(n, 0));
    if (n == 1) {
        res[0][0] = mat1[0][0] * mat2[0][0];
        return res;
    }

    int newSize = n / 2;
    Matrix a11(newSize, Row(newSize));
    Matrix a12(newSize, Row(newSize));
    Matrix a21(newSize, Row(newSize));
    Matrix a22(newSize, Row(newSize));
    Matrix b11(newSize, Row(newSize));
    Matrix b12(newSize, Row(newSize));
    Matrix b21(newSize, Row(newSize));
    Matrix b22(newSize, Row(newSize));

    for (int i = 0; i < newSize; i++)
        for (int j = 0; j < newSize; j++) {
            a11[i][j] = mat1[i][j];
            a12[i][j] = mat1[i][j + newSize];
            a21[i][j] = mat1[i + newSize][j];
            a22[i][j] = mat1[i + newSize][j + newSize];
            b11[i][j] = mat2[i][j];
            b12[i][j] = mat2[i][j + newSize];
            b21[i][j] = mat2[i + newSize][j];
            b22[i][j] = mat2[i + newSize][j + newSize];
        }

    auto m1 = strassen(add(a11, a22, newSize), add(b11, b22, newSize));
    auto m2 = strassen(add(a21, a22, newSize), b11);
    auto m3 = strassen(a11, add(b12, b22, newSize, -1));
    auto m4 = strassen(a22, add(b21, b11, newSize, -1));
    auto m5 = strassen(add(a11, a12, newSize), b22);
    auto m6 = strassen(add(a21, a11, newSize, -1), add(b11, b12, newSize));
    auto m7 = strassen(add(a12, a22, newSize, -1), add(b21, b22, newSize));

    auto c11 = add(add(m1, m4, newSize), add(m7, m5, newSize, -1), newSize);
    auto c12 = add(m3, m5, newSize);
    auto c21 = add(m2, m4, newSize);
    auto c22 = add(add(m1, m3, newSize), add(m6, m2, newSize, -1), newSize);

    for (int i = 0; i < newSize; i++)
        for (int j = 0; j < newSize; j++) {
            res[i][j] = c11[i][j];
            res[i][j + newSize] = c12[i][j];
            res[i + newSize][j] = c21[i][j];
            res[i + newSize][j + newSize] = c22[i][j];
        }

    return res;
}

// Multiply mat1 (n×m) and mat2 (m×q) 
// using Strassen’s method
Matrix multiply(Matrix &mat1, Matrix &mat2) {
    int n = mat1.size(), m = mat1[0].size(), q = mat2[0].size();
    int size = nextPowerOfTwo(max(n, max(m, q)));

    Matrix aPad = resizeMatrix(mat1, size, size);
    Matrix bPad = resizeMatrix(mat2, size, size);

    Matrix cPad = strassen(aPad, bPad);

    Matrix C(n, Row(q, 0));
    for (int i = 0; i < n; i++)
        for (int j = 0; j < q; j++)
            C[i][j] = cPad[i][j];

    return C;
}