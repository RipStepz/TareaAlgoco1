# Compilador
CXX = g++
CXXFLAGS = -std=c++17 -O2 -Wall

# Archivos
MAIN = sorting.cpp
ALGO = algorithms/mergesort.cpp algorithms/quicksort.cpp algorithms/sort.cpp

# Ejecutable
TARGET = sorting

# Regla principal
all: $(TARGET)

# Cómo construir el ejecutable
$(TARGET): $(MAIN) $(ALGO)
	$(CXX) $(CXXFLAGS) $(MAIN) $(ALGO) -o $(TARGET)

# Limpiar binarios
clean:
	rm -f $(TARGET)