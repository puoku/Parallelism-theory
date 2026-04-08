#include <cmath>
#include <condition_variable>
#include <cstdint>
#include <cstdlib>
#include <deque>
#include <filesystem>
#include <fstream>
#include <functional>
#include <future>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <random>
#include <string>
#include <thread>
#include <unordered_map>

template <typename T>
T fun_sin(T arg) {
  return std::sin(arg);
}

template <typename T>
T fun_sqrt(T arg) {
  return std::sqrt(arg);
}

template <typename T>
T fun_pow(T x, T y) {
  return std::pow(x, y);
}

template <typename T>
class TaskServer {
 public:
  using TaskType = std::function<T()>;

  void start() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (running_) {
      return;
    }
    stop_requested_ = false;
    running_ = true;
    worker_ = std::thread(&TaskServer::worker_loop, this);
  }

  void stop() {
    {
      std::lock_guard<std::mutex> lock(mutex_);
      if (!running_) {
        return;
      }
      stop_requested_ = true;
    }
    cv_.notify_all();
    if (worker_.joinable()) {
      worker_.join();
    }
    std::lock_guard<std::mutex> lock(mutex_);
    running_ = false;
  }

  std::size_t add_task(TaskType task) {
    std::promise<T> promise;
    std::shared_future<T> future = promise.get_future().share();

    std::lock_guard<std::mutex> lock(mutex_);
    const std::size_t id = next_id_++;
    results_[id] = future;
    tasks_.push_back(QueuedTask{id, std::move(task), std::move(promise)});
    cv_.notify_one();
    return id;
  }

  T request_result(std::size_t id_res) {
    std::shared_future<T> future;
    {
      std::lock_guard<std::mutex> lock(mutex_);
      future = results_.at(id_res);
    }

    const T value = future.get();

    {
      std::lock_guard<std::mutex> lock(mutex_);
      results_.erase(id_res);
    }

    return value;
  }

  ~TaskServer() {
    stop();
  }

 private:
  struct QueuedTask {
    std::size_t id = 0;
    TaskType task;
    std::promise<T> promise;
  };

  void worker_loop() {
    for (;;) {
      QueuedTask task;

      {
        std::unique_lock<std::mutex> lock(mutex_);
        cv_.wait(lock, [&] { return stop_requested_ || !tasks_.empty(); });

        if (tasks_.empty()) {
          if (stop_requested_) {
            break;
          }
          continue;
        }

        task = std::move(tasks_.front());
        tasks_.pop_front();
      }

      try {
        task.promise.set_value(task.task());
      } catch (...) {
        task.promise.set_exception(std::current_exception());
      }
    }
  }

  std::mutex mutex_;
  std::condition_variable cv_;
  std::deque<QueuedTask> tasks_;
  std::unordered_map<std::size_t, std::shared_future<T>> results_;
  std::thread worker_;
  bool running_ = false;
  bool stop_requested_ = false;
  std::size_t next_id_ = 1;
};

struct ClientConfig {
  std::size_t task_count = 100;
  std::uint64_t seed = 0;
  std::string file_name;
};

void run_sin_client(TaskServer<double>& server, const ClientConfig& config,
                    const std::filesystem::path& out_dir) {
  std::mt19937_64 rng(config.seed);
  std::uniform_real_distribution<double> dist(-1000.0, 1000.0);
  std::ofstream out(out_dir / config.file_name);
  out << "id;arg;result\n";
  out << std::fixed << std::setprecision(12);

  for (std::size_t i = 0; i < config.task_count; ++i) {
    const double arg = dist(rng);
    const std::size_t id = server.add_task([arg] { return fun_sin(arg); });
    const double result = server.request_result(id);
    out << id << ';' << arg << ';' << result << '\n';
  }
}

void run_sqrt_client(TaskServer<double>& server, const ClientConfig& config,
                     const std::filesystem::path& out_dir) {
  std::mt19937_64 rng(config.seed);
  std::uniform_real_distribution<double> dist(0.0, 1000000.0);
  std::ofstream out(out_dir / config.file_name);
  out << "id;arg;result\n";
  out << std::fixed << std::setprecision(12);

  for (std::size_t i = 0; i < config.task_count; ++i) {
    const double arg = dist(rng);
    const std::size_t id = server.add_task([arg] { return fun_sqrt(arg); });
    const double result = server.request_result(id);
    out << id << ';' << arg << ';' << result << '\n';
  }
}

void run_pow_client(TaskServer<double>& server, const ClientConfig& config,
                    const std::filesystem::path& out_dir) {
  std::mt19937_64 rng(config.seed);
  std::uniform_real_distribution<double> base_dist(1.0, 10.0);
  std::uniform_real_distribution<double> exp_dist(1.0, 5.0);
  std::ofstream out(out_dir / config.file_name);
  out << "id;x;y;result\n";
  out << std::fixed << std::setprecision(12);

  for (std::size_t i = 0; i < config.task_count; ++i) {
    const double x = base_dist(rng);
    const double y = exp_dist(rng);
    const std::size_t id = server.add_task([x, y] { return fun_pow(x, y); });
    const double result = server.request_result(id);
    out << id << ';' << x << ';' << y << ';' << result << '\n';
  }
}

int main(int argc, char** argv) {
  std::size_t n = 100;
  if (argc >= 2) {
    const long long parsed = std::atoll(argv[1]);
    if (parsed <= 5 || parsed >= 10000) {
      std::cerr << "Usage: ./task3_2 N, where 5 < N < 10000\n";
      return 1;
    }
    n = static_cast<std::size_t>(parsed);
  }

  const std::filesystem::path out_dir = "results";
  std::filesystem::create_directories(out_dir);

  TaskServer<double> server;
  server.start();

  const ClientConfig sin_cfg{n, 12345ULL, "sin_results.txt"};
  const ClientConfig sqrt_cfg{n, 23456ULL, "sqrt_results.txt"};
  const ClientConfig pow_cfg{n, 34567ULL, "pow_results.txt"};

  std::thread sin_client(run_sin_client, std::ref(server), std::cref(sin_cfg), std::cref(out_dir));
  std::thread sqrt_client(run_sqrt_client, std::ref(server), std::cref(sqrt_cfg),
                          std::cref(out_dir));
  std::thread pow_client(run_pow_client, std::ref(server), std::cref(pow_cfg), std::cref(out_dir));

  sin_client.join();
  sqrt_client.join();
  pow_client.join();

  server.stop();

  std::cout << "Done. Results saved in " << out_dir.string() << "\n";
  std::cout << "Files:\n";
  std::cout << "  " << (out_dir / sin_cfg.file_name).string() << "\n";
  std::cout << "  " << (out_dir / sqrt_cfg.file_name).string() << "\n";
  std::cout << "  " << (out_dir / pow_cfg.file_name).string() << "\n";

  return 0;
}
