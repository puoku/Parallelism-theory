cmake_minimum_required(VERSION 3.16)
project(first_task CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(USE_FLOAT "Use float instead of double" OFF)

add_executable(first_task first_task.cpp)

if(USE_FLOAT)
    target_compile_definitions(first_task PRIVATE ARRAY_FLOAT)
endif()
