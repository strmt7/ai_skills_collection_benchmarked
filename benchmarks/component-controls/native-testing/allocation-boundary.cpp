#include <cstddef>
int main(int argc, char**) {
    volatile std::size_t index = argc == 1 ? 3 : 4;
    volatile int* values = new int[4];
    values[index] = 42;
    int result = values[3] == 42 ? 0 : 1;
    delete[] values;
    return result;
}
