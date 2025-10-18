cmake_minimum_required(VERSION 3.4.1)

project(python_bootstrap)

add_library(
    python_bootstrap
    SHARED
    python_bootstrap.c
)

find_library(
    log-lib
    log
)

# Find python library. The name is libpython<PYTHON_VERSION>.so
# The library is in src/main/jniLibs/${ANDROID_ABI}
# We can add this directory to the link directories.
link_directories(${CMAKE_SOURCE_DIR}/../jniLibs/${ANDROID_ABI})

target_link_libraries(
    python_bootstrap
    python${PYTHON_VERSION}
    ${log-lib}
)