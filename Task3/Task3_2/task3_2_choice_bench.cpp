#include <chrono>
#include <cmath>
#include <condition_variable>
#include <cstdint>
#include <cstdlib>
#include <deque>
#include <functional>
#include <future>
#include <iomanip>
#include <iostream>
#include <list>
#include <map>
#include <mutex>
#include <random>
#include <thread>
#include <unordered_map>
#include <vector>

template <class QueueContainer, class ResultContainer, bool UseConditionVariable>
class ServerVariant {
 public:
  using TaskType = std::function<double()>;

  void start() {
    worker_ = std::thread(&ServerVariant::worker_loop, this);
  }

  void stop() {
    {
      std::lock_guard<std::mutex> lock(mutex_);
      stop_requested_ = true;
    }
    cv_.notify_all();
    if (worker_.joinable()) {
      worker_.join();
    }
  }

  std::size_t add_task(TaskType task) {
    std::promise<double> promise;
    std::shared_future<double> future = promise.get_future().share();

    std::lock_guard<std::mutex> lock(mutex_);
    const std::size_t id = next_id_++;
    results_[id] = future;
    tasks_.push_back(std::make_pair(std::move(task), std::move(promise)));
    if constexpr (UseConditionVariable) {
      cv_.notify_one();
    }
    return id;
  }

  double request_result(std::size_t id) {
    std::shared_future<double> future;
    {
      std::lock_guard<std::mutex> lock(mutex_);
      future = results_.at(id);
    }
    const double value = future.get();
    {
      std::lock_guard<std::mutex> lock(mutex_);
      results_.erase(id);
    }
    return value;
  }

  ~ServerVariant() {
    stop();
  }

 private:
  void worker_loop() {
    for (;;) {
      std::pair<std::function<double()>, std::promise<double>> item;
      bool has_task = false;

      if constexpr (UseConditionVariable) {
        std::unique_lock<std::mutex> lock(mutex_);
        cv_.wait(lock, [&] { return stop_requested_ || !tasks_.empty(); });
        if (!tasks_.empty()) {
          item = std::move(tasks_.front());
          tasks_.pop_front();
          has_task = true;
        } else if (stop_requested_) {
          break;
        }
      } else {
        {
          std::lock_guard<std::mutex> lock(mutex_);
          if (!tasks_.empty()) {
            item = std::move(tasks_.front());
            tasks_.pop_front();
            has_task = true;
          } else if (stop_requested_) {
            break;
          }
        }
        if (!has_task) {
          std::this_thread::yield();
        }
      }

      if (!has_task) {
        continue;
      }

      item.second.set_value(item.first());
    }
  }

  std::mutex mutex_;
  std::condition_variable cv_;
  QueueContainer tasks_;
  ResultContainer results_;
  std::thread worker_;
  bool stop_requested_ = false;
  std::size_t next_id_ = 1;
};

template <class Server>
double run_one(Server& server, std::size_t n) {
  std::mt19937_64 rng(12345ULL);
  std::uniform_real_distribution<double> dist(0.0, 1000.0);
  double checksum = 0.0;

  for (std::size_t i = 0; i < n; ++i) {
    const double arg = dist(rng);
    const std::size_t id = server.add_task([arg] { return std::sin(arg); });
    checksum += server.request_result(id);
  }

  return checksum;
}

template <class Server>
double best_time(std::size_t n, int repeats, const char* name) {
  double best = -1.0;
  double checksum = 0.0;

  for (int run = 0; run < repeats; ++run) {
    Server server;
    server.start();
    const auto t0 = std::chrono::steady_clock::now();
    checksum = run_one(server, n);
    const auto t1 = std::chrono::steady_clock::now();
    server.stop();
    const double time_s = std::chrono::duration<double>(t1 - t0).count();
    if (best < 0.0 || time_s < best) {
      best = time_s;
    }
  }

  std::cout << std::fixed << std::setprecision(6)
            << name << " best_time_s=" << best
            << " checksum=" << checksum << "\n";
  return best;
}

int main(int argc, char** argv) {
  std::size_t n = 30000;
  int repeats = 3;

  if (argc >= 2) {
    n = static_cast<std::size_t>(std::atoll(argv[1]));
  }
  if (argc >= 3) {
    repeats = std::atoi(argv[2]);
  }

  using FastVariant =
      ServerVariant<std::deque<std::pair<std::function<double()>, std::promise<double>>>,
                    std::unordered_map<std::size_t, std::shared_future<double>>, true>;

  using SlowContainerVariant =
      ServerVariant<std::list<std::pair<std::function<double()>, std::promise<double>>>,
                    std::map<std::size_t, std::shared_future<double>>, true>;

  using PollVariant =
      ServerVariant<std::deque<std::pair<std::function<double()>, std::promise<double>>>,
                    std::unordered_map<std::size_t, std::shared_future<double>>, false>;

  const double fast = best_time<FastVariant>(n, repeats, "cv+deque+unordered_map");
  const double slow = best_time<SlowContainerVariant>(n, repeats, "cv+list+map");
  const double poll = best_time<PollVariant>(n, repeats, "poll+deque+unordered_map");

  std::cout << "best_variant="
            << ((fast <= slow && fast <= poll) ? "cv+deque+unordered_map"
                                               : (poll <= slow ? "poll+deque+unordered_map"
                                                               : "cv+list+map"))
            << "\n";

  return 0;
}
