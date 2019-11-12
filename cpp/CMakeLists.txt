set(CMAKE_CXX_STANDARD 11)

add_executable(cpp-client main.cc)

target_include_directories(cpp-client PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/../libra-dev/include")
target_link_directories(cpp-client PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/../libra-dev/target/debug")
target_link_libraries(cpp-client PRIVATE "libra_dev")

IF(APPLE)
    target_link_libraries(cpp-client PRIVATE "-framework Security")
elseif(WIN32)

else()
    target_link_libraries(cpp-client PRIVATE "pthread")
    target_link_libraries(cpp-client PRIVATE "dl")
    target_link_libraries(cpp-client PRIVATE "m")
endif()
