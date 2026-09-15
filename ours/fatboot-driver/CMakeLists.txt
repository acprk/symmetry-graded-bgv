cmake_minimum_required(VERSION 3.16)
project(bgv_bts)

SET(CMAKE_CXX_STANDARD 17)

find_package(helib REQUIRED)

add_executable(fatboot fatboot.cpp)
target_link_libraries(fatboot helib ntl gmp)
