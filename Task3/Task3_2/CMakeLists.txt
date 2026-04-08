cmake_minimum_required(VERSION 3.16)
project(Task3_2 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

find_package(Threads REQUIRED)

add_executable(task3_2 task3_2.cpp)
target_link_libraries(task3_2 PRIVATE Threads::Threads)

add_executable(task3_2_choice_bench task3_2_choice_bench.cpp)
target_link_libraries(task3_2_choice_bench PRIVATE Threads::Threads)

add_executable(task3_2_test task3_2_test.cpp)
