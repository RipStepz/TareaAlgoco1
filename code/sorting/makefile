# Compilador
CXX = g++
CXXFLAGS = -std=c++17 -O2 -Wall

# Ejecutable
TARGET = sorting

# Regla por defecto
all: $(TARGET)

# Compilar (solo sorting.cpp)
$(TARGET): sorting.cpp
	$(CXX) $(CXXFLAGS) sorting.cpp -o $(TARGET)

# Ejecutar
run: $(TARGET)
	./$(TARGET)

# Limpiar binarios
clean:
	rm -f $(TARGET)