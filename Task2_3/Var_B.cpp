#include <omp.h>

#include <chrono>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <vector>

int main(int argc, char** argv) {
  const int MAX_ITER = 200000;
  const double EPS = 1e-5;
  long long N = 20000;

  int threads = omp_get_max_threads();
  if (argc >= 2) N = std::atoll(argv[1]);
  if (argc >= 3) threads = std::atoi(argv[2]);
  if (N <= 0 || threads <= 0) return 1;

  const double B = static_cast<double>(N) + 1.0;
  const double TAU = 1.0 / static_cast<double>(N + 1);

  omp_set_num_threads(threads);

  std::vector<double> x(static_cast<size_t>(N), 0.0);
  std::vector<double> x_next(static_cast<size_t>(N), 0.0);

  int iterations = 0;
  bool done = false;

  auto t0 = std::chrono::steady_clock::now();

#pragma omp parallel shared(x, x_next, done, iterations)
  {
    double s = 0.0;
    double diff = 0.0;

    for (int it = 0; it < MAX_ITER; ++it) {
#pragma omp single
      {
        s = 0.0;
        diff = 0.0;
      }

#pragma omp for reduction(+ : s)
      for (long long i = 0; i < N; ++i) s += x[static_cast<size_t>(i)];

#pragma omp for reduction(max : diff)
      for (long long i = 0; i < N; ++i) {
        double oldv = x[static_cast<size_t>(i)];
        double r = s + oldv - B;
        double nv = oldv - TAU * r;
        x_next[static_cast<size_t>(i)] = nv;
        double d = std::fabs(nv - oldv);
        if (d > diff) diff = d;
      }

#pragma omp single
      {
        x.swap(x_next);
        iterations = it + 1;
        if (diff < EPS) done = true;
      }

#pragma omp barrier
      if (done) break;
    }
  }

  double max_error = 0.0;
#pragma omp parallel for reduction(max : max_error)
  for (long long i = 0; i < N; ++i) {
    double e = std::fabs(x[static_cast<size_t>(i)] - 1.0);
    if (e > max_error) max_error = e;
  }

  auto t1 = std::chrono::steady_clock::now();
  double time_s = std::chrono::duration<double>(t1 - t0).count();

  std::cout << std::fixed << std::setprecision(12)
            << "variant=B"
            << " threads=" << threads
            << " N=" << N
            << " iterations=" << iterations
            << " max_error_to_one=" << max_error
            << " time_s=" << time_s << "\n";

  return 0;
}
