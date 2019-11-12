cmake_minimum_required(VERSION 3.10)

project(pylibra)

set(CMAKE_C_STANDARD 11)

find_package(PythonExtensions REQUIRED)

add_library(_pylibra MODULE "pylibra/_pylibra.c")
python_extension_module(_pylibra)
install(TARGETS _pylibra LIBRARY DESTINATION pylibra)


target_include_directories(_pylibra PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/../libra-dev/include")
target_link_directories(_pylibra PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/../libra-dev/target/debug")
target_link_libraries(_pylibra "libra_dev")

IF(APPLE)
    target_link_libraries(_pylibra "-framework Security")
elseif(WIN32)

else()
    target_link_libraries(_pylibra "pthread")
    target_link_libraries(_pylibra "dl")
    target_link_libraries(_pylibra "m")
endif()
