#include <iostream>
#include <filesystem>
#include <cstddef>
#include <cstdlib>
#include <new>
#include <atomic>
#include <algorithm>
#include <chrono>
#include <functional>
#include <fstream>

#include "algorithms/mergesort.cpp"
#include "algorithms/quicksort.cpp"
#include "algorithms/sort.cpp"

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

    inline void add_allocation(std::size_t size) {
        if (!tracking_enabled) return;
        std::size_t new_current = current_bytes.fetch_add(size) + size;
        std::size_t old_peak = peak_bytes.load();
        while (new_current > old_peak &&
               !peak_bytes.compare_exchange_weak(old_peak, new_current)) {
        }
    }

    inline void remove_allocation(std::size_t size) {
        if (!tracking_enabled) return;
        current_bytes.fetch_sub(size);
    }
}

inline void* operator new(std::size_t size) {
    std::size_t total = size + sizeof(std::size_t);
    void* raw = std::malloc(total);
    if (!raw) throw std::bad_alloc();

    *static_cast<std::size_t*>(raw) = size;
    MemoryTracker::add_allocation(size);

    return static_cast<char*>(raw) + sizeof(std::size_t);
}

inline void operator delete(void* ptr) noexcept {
    if (!ptr) return;

    void* raw = static_cast<char*>(ptr) - sizeof(std::size_t);
    std::size_t size = *static_cast<std::size_t*>(raw);
    MemoryTracker::remove_allocation(size);
    std::free(raw);
}

inline void operator delete(void* ptr, std::size_t) noexcept {
    if (!ptr) return;

    void* raw = static_cast<char*>(ptr) - sizeof(std::size_t);
    std::size_t size = *static_cast<std::size_t*>(raw);
    MemoryTracker::remove_allocation(size);
    std::free(raw);
}

inline void* operator new[](std::size_t size) {
    std::size_t total = size + sizeof(std::size_t);
    void* raw = std::malloc(total);
    if (!raw) throw std::bad_alloc();

    *static_cast<std::size_t*>(raw) = size;
    MemoryTracker::add_allocation(size);

    return static_cast<char*>(raw) + sizeof(std::size_t);
}

inline void operator delete[](void* ptr) noexcept {
    if (!ptr) return;

    void* raw = static_cast<char*>(ptr) - sizeof(std::size_t);
    std::size_t size = *static_cast<std::size_t*>(raw);
    MemoryTracker::remove_allocation(size);
    std::free(raw);
}

inline void operator delete[](void* ptr, std::size_t) noexcept {
    if (!ptr) return;

    void* raw = static_cast<char*>(ptr) - sizeof(std::size_t);
    std::size_t size = *static_cast<std::size_t*>(raw);
    MemoryTracker::remove_allocation(size);
    std::free(raw);
}
struct Measurement {
    double time_ms;
    std::size_t peak_bytes;
};

Measurement measure_algorithm(const std::function<void()>& algorithm) {
    MemoryTracker::start();

    auto start = std::chrono::high_resolution_clock::now();
    algorithm();
    auto end = std::chrono::high_resolution_clock::now();

    MemoryTracker::stop();

    std::chrono::duration<double, std::milli> elapsed = end - start;

    return {elapsed.count(), MemoryTracker::peak()};
}

using namespace std;
namespace fs = filesystem;

vector<int> leerArchivo(const string& ruta) {
    ifstream file(ruta);
    cout << "La ruta es: " << ruta << endl;
    if (!file.is_open()) {
        cerr << "Error al abrir: " << ruta << "\n";
        exit(1);
    }

    vector<int> arr;
    int x;

    while (file >> x) {
        arr.push_back(x);
    }

    return arr;
}

int main() {
    string carpeta = "data/array_input";
    //int i = 0;
    for (const auto& entry : fs::directory_iterator(carpeta)) {

        string ruta = entry.path().string();
        string nombre_archivo = entry.path().filename().string();
        cout <<"Nombre del Archivo: " << nombre_archivo << endl;
       
        vector<int> arr = leerArchivo(ruta);
        /*
        nombre_archivo = nombre_archivo.substr(0, nombre_archivo.find("."));

        stringstream ss(nombre_archivo);
        string n, t, d, m;

        getline(ss, n, '_');
        getline(ss, t, '_');
        getline(ss, d, '_');
        getline(ss, m, '_');

        cout << "n: " << n << "\n";
        cout << "t: " << t << "\n";
        cout << "d: " << d << "\n";
        cout << "m: " << m << "\n" <<"\n";
        */

        // MERGE SORT
        vector<int> a1 = arr;
        Measurement m1 = measure_algorithm([&]() {
            mergeSort(a1, 0, a1.size() - 1);
        });

        // QUICK SORT
        vector<int> a2 = arr;
        Measurement m2 = measure_algorithm([&]() {
            quickSort(a2, 0, a2.size() - 1);
        });

        // STD SORT
        vector<int> a3 = arr;
        Measurement m3 = measure_algorithm([&]() {
            sortArray(a3);
        });
        string carpeta_out = "data/measurements/";

        string ruta_out = carpeta_out + nombre_archivo;

        ofstream out(ruta_out);

        if (!out.is_open()) {
            cerr << "Error al crear archivo: " << ruta_out << endl;
            return 1;
        }

        out << "MergeSort: "
            << m1.time_ms << " ms, "
            << m1.peak_bytes << " bytes\n";

        out << "QuickSort: "
            << m2.time_ms << " ms, "
            << m2.peak_bytes << " bytes\n";

        out << "StdSort: "
            << m3.time_ms << " ms, "
            << m3.peak_bytes << " bytes\n";

        out.close();
        
        // if(i==0){
        //     break;
        // }
    }

    return 0;

}