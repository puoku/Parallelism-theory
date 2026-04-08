#include <chrono>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <thread>
#include <vector>

struct Range {
  long long begin = 0;
  long long end = 0;
};

Range split_range(long long n, int threads, int tid) {
  const long long base = n / threads;
  const long long rem = n % threads;
  const long long begin = tid * base + (tid < rem ? tid : rem);
  const long long size = base + (tid < rem ? 1 : 0);
  return Range{begin, begin + size};
}

int main(int argc, char** argv) {
  long long n = 20000;
  int threads = 1;

  if (argc >= 2) n = std::atoll(argv[1]);
  if (argc >= 3) threads = std::atoi(argv[2]);

  if (n <= 0 || threads <= 0) {
    std::cerr << "Usage: ./task3_1_matvec_threads N THREADS\n";
    return 1;
  }

  std::vector<double> A(static_cast<size_t>(n) * static_cast<size_t>(n));
  std::vector<double> x(static_cast<size_t>(n));
  std::vector<double> y(static_cast<size_t>(n), 0.0);

  auto t0 = std::chrono::steady_clock::now();

  {
    std::vector<std::thread> workers;
    workers.reserve(static_cast<size_t>(threads));

    for (int tid = 0; tid < threads; ++tid) {
      workers.emplace_back([&, tid] {
        const Range r = split_range(n, threads, tid);
        for (long long i = r.begin; i < r.end; ++i) {
          for (long long j = 0; j < n; ++j) {
            A[static_cast<size_t>(i) * static_cast<size_t>(n) + static_cast<size_t>(j)] =
                1.0 / (1.0 + static_cast<double>((i + j) % 1024));
          }
          x[static_cast<size_t>(i)] = 1.0 + static_cast<double>(i % 97) * 0.001;
          y[static_cast<size_t>(i)] = 0.0;
        }
      });
    }

    for (auto& worker : workers) {
      worker.join();
    }
  }

  auto t1 = std::chrono::steady_clock::now();

  {
    std::vector<std::thread> workers;
    workers.reserve(static_cast<size_t>(threads));

    for (int tid = 0; tid < threads; ++tid) {
      workers.emplace_back([&, tid] {
        const Range r = split_range(n, threads, tid);
        for (long long i = r.begin; i < r.end; ++i) {
          double sum = 0.0;
          for (long long j = 0; j < n; ++j) {
            sum += A[static_cast<size_t>(i) * static_cast<size_t>(n) + static_cast<size_t>(j)] *
                   x[static_cast<size_t>(j)];
          }
          y[static_cast<size_t>(i)] = sum;
        }
      });
    }

    for (auto& worker : workers) {
      worker.join();
    }
  }

  auto t2 = std::chrono::steady_clock::now();

  std::vector<double> partial_sums(static_cast<size_t>(threads), 0.0);
  {
    std::vector<std::thread> workers;
    workers.reserve(static_cast<size_t>(threads));

    for (int tid = 0; tid < threads; ++tid) {
      workers.emplace_back([&, tid] {
        const Range r = split_range(n, threads, tid);
        double local_sum = 0.0;
        for (long long i = r.begin; i < r.end; ++i) {
          local_sum += y[static_cast<size_t>(i)];
        }
        partial_sums[static_cast<size_t>(tid)] = local_sum;
      });
    }

    for (auto& worker : workers) {
      worker.join();
    }
  }

  double checksum = 0.0;
  for (double part : partial_sums) {
    checksum += part;
  }

  const double init_s = std::chrono::duration<double>(t1 - t0).count();
  const double matvec_s = std::chrono::duration<double>(t2 - t1).count();
  const double total_s = std::chrono::duration<double>(t2 - t0).count();

  std::cout << std::fixed << std::setprecision(6)
            << "N=" << n
            << " threads=" << threads
            << " init_s=" << init_s
            << " matvec_s=" << matvec_s
            << " total_s=" << total_s
            << " checksum=" << checksum << "\n";

  return 0;
}
