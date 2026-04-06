# Compilador
CXX = g++
CXXFLAGS = -std=c++17 -O2 -Wall

# Ejecutable
TARGET = matrix

# Regla por defecto
all: $(TARGET)

# Compilar (solo sorting.cpp)
$(TARGET): matrix_multiplication.cpp
	$(CXX) $(CXXFLAGS) matrix_multiplication.cpp -o $(TARGET)

# Ejecutar
run: $(TARGET)
	./$(TARGET)

# Limpiar binarios
clean:
	rm -f $(TARGET)