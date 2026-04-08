cmake_minimum_required(VERSION 3.16)
project(Task3_1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

find_package(Threads REQUIRED)

add_executable(task3_1_matvec_threads task3_1_matrix_vector.cpp)
target_link_libraries(task3_1_matvec_threads PRIVATE Threads::Threads)
