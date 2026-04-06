#include <iostream>
#include <filesystem>
#include <cstddef>
#include <cstdlib>
#include <new>
#include <atomic>
#include <algorithm>
#include <chrono>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <unordered_set>
#include <cmath>
#include <stdexcept>
#include <memory>
#include <limits>
namespace MemoryTracker {
    inline std::atomic<std::size_t> current_bytes{0};
    inline std::atomic<std::size_t> peak_bytes{0};
    inline std::atomic<bool> tracking_enabled{false};

    inline void reset() {
        current_bytes = 0;
        peak_bytes = 0;
    }

    inline void start() {
        reset();
        tracking_enabled = true;
    }

    inline void stop() {
        tracking_enabled = false;
    }

    inline std::size_t current() {
        return current_bytes.load();
    }

    inline std::size_t peak() {
        return peak_bytes.load();
    }

    inline void add_allocation(std::size_t bytes) {
        if (!tracking_enabled) return;

        std::size_t new_current = current_bytes.fetch_add(bytes) + bytes;
        std::size_t old_peak = peak_bytes.load();

        while (new_current > old_peak &&
               !peak_bytes.compare_exchange_weak(old_peak, new_current)) {
        }
    }

    inline void remove_allocation(std::size_t bytes) {
        if (!tracking_enabled) return;
        current_bytes.fetch_sub(bytes);
    }
}

template <typename T>
struct CountingAllocator {
    using value_type = T;

    CountingAllocator() noexcept = default;

    template <typename U>
    CountingAllocator(const CountingAllocator<U>&) noexcept {}

    T* allocate(std::size_t n) {
        if (n > std::numeric_limits<std::size_t>::max() / sizeof(T)) {
            throw std::bad_alloc();
        }

        std::size_t bytes = n * sizeof(T);
        MemoryTracker::add_allocation(bytes);

        return std::allocator<T>{}.allocate(n);
    }

    void deallocate(T* p, std::size_t n) noexcept {
        std::size_t bytes = n * sizeof(T);
        MemoryTracker::remove_allocation(bytes);

        std::allocator<T>{}.deallocate(p, n);
    }

    template <typename U>
    bool operator==(const CountingAllocator<U>&) const noexcept {
        return true;
    }

    template <typename U>
    bool operator!=(const CountingAllocator<U>&) const noexcept {
        return false;
    }
};
struct Measurement {
    double time_ms;
    std::size_t peak_bytes;
};

template <typename F>
Measurement measure_algorithm(F&& algorithm) {
    MemoryTracker::start();
    auto start = std::chrono::high_resolution_clock::now();
    algorithm();
    auto end = std::chrono::high_resolution_clock::now();
    MemoryTracker::stop();

    std::chrono::duration<double, std::milli> elapsed = end - start;
    return {elapsed.count(), MemoryTracker::peak()};
}


using namespace std;
namespace fs = std::filesystem;

using Row = std::vector<int, CountingAllocator<int>>;
using Matrix = std::vector<Row, CountingAllocator<Row>>;

#include "algorithms/naive.cpp"
#include "algorithms/strassen.cpp"

Matrix leerMatriz(const string& ruta) {
    ifstream file(ruta);

    if (!file.is_open()) {
        cerr << "Error al abrir: " << ruta << "\n";
        exit(1);
    }

    Matrix mat;
    string linea;

    while (getline(file, linea)) {
        if (linea.empty()) continue;

        stringstream ss(linea);
        Row fila;
        int x;

        while (ss >> x) {
            fila.push_back(x);
        }

        if (!fila.empty()) {
            mat.push_back(fila);
        }
    }

    return mat;
}

int main() {
    string carpeta = "data/matrix_input";

    for (const auto& entry : fs::directory_iterator(carpeta)) {
        string nombre_archivo = entry.path().filename().string();

        // solo procesar los archivos _1.txt
        if (nombre_archivo.find("_1.txt") == string::npos) {
            continue;
        }

        string ruta1 = entry.path().string();

        string nombre_par = nombre_archivo;
        nombre_par.replace(nombre_par.size() - 6, 6, "_2.txt");

        string ruta2 = carpeta + "/" + nombre_par;

        if (!fs::exists(ruta2)) {
            cerr << "No existe el par de: " << nombre_archivo << "\n";
            continue;
        }

        Matrix mat1 = leerMatriz(ruta1);
        Matrix mat2 = leerMatriz(ruta2);

        Matrix res_naive = multiplyNaive(mat1, mat2);
        Matrix res_strassen = multiply(mat1, mat2);

        cout << "Caso procesado:\n";
        cout << "  " << nombre_archivo << " y " << nombre_par << "\n";
        cout << "  Resultado naive: " << res_naive.size() << "x";
        if (!res_naive.empty()) cout << res_naive[0].size();
        else cout << 0;
        cout << "\n";

        cout << "  Resultado strassen: " << res_strassen.size() << "x";
        if (!res_strassen.empty()) cout << res_strassen[0].size();
        else cout << 0;
        cout << "\n";

        if (res_naive == res_strassen) {
            cout << "  Ambos resultados coinciden\n";
        } else {
            cout << "  OJO: los resultados NO coinciden\n";
        }

        cout << "--------------------------\n";
    }

    return 0;
}