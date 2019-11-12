set(CMAKE_C_STANDARD 11)

add_executable(c-client main.c)

target_include_directories(c-client PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/../libra-dev/include")
target_link_directories(c-client PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/../libra-dev/target/debug")
target_link_libraries(c-client PRIVATE "libra_dev")

IF(APPLE)
    target_link_libraries(c-client PRIVATE "-framework Security")
elseif(WIN32)

else()
    target_link_libraries(c-client PRIVATE "pthread")
    target_link_libraries(c-client PRIVATE "dl")
    target_link_libraries(c-client PRIVATE "m")
endif()
