cmake_minimum_required(VERSION 3.10)
project(sgbgv_bench CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE RelWithDebInfo)
endif()

# These binaries link against *vanilla* HElib -- they are stage-level harnesses
# that build their own contexts and evaluate the digit-extraction polynomial
# directly, so they do NOT need the patch in ../../ours/.  Point helib_DIR at
# whichever HElib install you have:
#
#   cmake -Dhelib_DIR=/path/to/helib/share/cmake/helib ..
#
find_package(helib REQUIRED)

foreach(gen 12 13 14 15)
  add_executable(bench_m${gen} bench_m${gen}.cpp)
  target_link_libraries(bench_m${gen} helib)
endforeach()
