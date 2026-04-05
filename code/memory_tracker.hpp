#ifndef MEMORY_TRACKER_HPP
#define MEMORY_TRACKER_HPP

#include <cstddef>
#include <cstdlib>
#include <new>
#include <atomic>
#include <algorithm>

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

// Guardamos el tamaño antes del bloque reservado
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

#include <chrono>
#include <functional>

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

#endif

