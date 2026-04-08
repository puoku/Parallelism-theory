#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

bool check_close(double a, double b) {
  return std::abs(a - b) < 1e-8;
}

bool test_sin_file(const std::filesystem::path& path) {
  std::ifstream in(path);
  if (!in) {
    return false;
  }
  std::string line;
  std::getline(in, line);

  while (std::getline(in, line)) {
    std::stringstream ss(line);
    std::string id_str;
    std::string arg_str;
    std::string result_str;
    std::getline(ss, id_str, ';');
    std::getline(ss, arg_str, ';');
    std::getline(ss, result_str, ';');
    const double arg = std::stod(arg_str);
    const double result = std::stod(result_str);
    if (!check_close(std::sin(arg), result)) {
      return false;
    }
  }
  return true;
}

bool test_sqrt_file(const std::filesystem::path& path) {
  std::ifstream in(path);
  if (!in) {
    return false;
  }
  std::string line;
  std::getline(in, line);

  while (std::getline(in, line)) {
    std::stringstream ss(line);
    std::string id_str;
    std::string arg_str;
    std::string result_str;
    std::getline(ss, id_str, ';');
    std::getline(ss, arg_str, ';');
    std::getline(ss, result_str, ';');
    const double arg = std::stod(arg_str);
    const double result = std::stod(result_str);
    if (!check_close(std::sqrt(arg), result)) {
      return false;
    }
  }
  return true;
}

bool test_pow_file(const std::filesystem::path& path) {
  std::ifstream in(path);
  if (!in) {
    return false;
  }
  std::string line;
  std::getline(in, line);

  while (std::getline(in, line)) {
    std::stringstream ss(line);
    std::string id_str;
    std::string x_str;
    std::string y_str;
    std::string result_str;
    std::getline(ss, id_str, ';');
    std::getline(ss, x_str, ';');
    std::getline(ss, y_str, ';');
    std::getline(ss, result_str, ';');
    const double x = std::stod(x_str);
    const double y = std::stod(y_str);
    const double result = std::stod(result_str);
    if (!check_close(std::pow(x, y), result)) {
      return false;
    }
  }
  return true;
}

int main() {
  const std::filesystem::path dir = "results";

  const bool ok_sin = test_sin_file(dir / "sin_results.txt");
  const bool ok_sqrt = test_sqrt_file(dir / "sqrt_results.txt");
  const bool ok_pow = test_pow_file(dir / "pow_results.txt");

  if (ok_sin && ok_sqrt && ok_pow) {
    std::cout << "All files are correct\n";
    return 0;
  }

  std::cerr << "Test failed\n";
  return 1;
}
