#include <iostream>
#include <vector>
#include <cmath>

#ifdef ARRAY_FLOAT
using T = float;
#else
using T = double;
#endif

int main() {
    const int N = 10000000;
    std::vector<T> a(N);

    for (int i = 0; i < N; ++i) {
        T x = static_cast<T>(2.0 * M_PI) * static_cast<T>(i) / static_cast<T>(N - 1);
        a[i] = std::sin(x);
    }

    double sum = 0.0;
    for (int i = 0; i < N; ++i) {
        sum += static_cast<double>(a[i]);
    }

    std::cout << "Sum: " << sum << std::endl;

    return 0;
}
