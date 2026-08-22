cmake_minimum_required(VERSION 3.20)

project(
    AdaptiveBondRisk
    VERSION 0.1.0
    DESCRIPTION "Adaptive Monte Carlo estimation of fixed-income tail risk"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include(CTest)

# Prefer libraries from an active Conda environment as one consistent
# toolchain. Otherwise CMake can combine Conda Protobuf with Homebrew Abseil
# headers and libraries, which are not binary-compatible.
if(DEFINED ENV{CONDA_PREFIX})
    list(PREPEND CMAKE_PREFIX_PATH "$ENV{CONDA_PREFIX}")

    set(CONDA_CMAKE_DIR "$ENV{CONDA_PREFIX}/lib/cmake")
    if(EXISTS "${CONDA_CMAKE_DIR}/protobuf")
        set(
            Protobuf_DIR
            "${CONDA_CMAKE_DIR}/protobuf"
            CACHE PATH "Protobuf CMake package directory" FORCE
        )
    endif()
    if(EXISTS "${CONDA_CMAKE_DIR}/absl")
        set(
            absl_DIR
            "${CONDA_CMAKE_DIR}/absl"
            CACHE PATH "Abseil CMake package directory" FORCE
        )
    endif()
    if(EXISTS "${CONDA_CMAKE_DIR}/utf8_range")
        set(
            utf8_range_DIR
            "${CONDA_CMAKE_DIR}/utf8_range"
            CACHE PATH "utf8_range CMake package directory" FORCE
        )
    endif()
endif()

find_package(ZeroMQ CONFIG QUIET)
if(TARGET libzmq)
    set(ZEROMQ_TARGET libzmq)
else()
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(ZeroMQ REQUIRED IMPORTED_TARGET libzmq)
    set(ZEROMQ_TARGET PkgConfig::ZeroMQ)
endif()
find_file(CPPZMQ_HEADER NAMES zmq.hpp REQUIRED)
find_package(Protobuf CONFIG REQUIRED)
find_package(CLI11 CONFIG REQUIRED)

set(PROTO_FILE "${CMAKE_CURRENT_SOURCE_DIR}/proto/messages.proto")
set(GENERATED_DIR "${CMAKE_CURRENT_BINARY_DIR}/generated")
set(GENERATED_CPP_DIR "${GENERATED_DIR}/cpp")
set(GENERATED_PYTHON_DIR "${GENERATED_DIR}/python")
set(GENERATED_CPPZMQ_DIR "${GENERATED_DIR}/cppzmq")
set(GENERATED_PROTO_SOURCE "${GENERATED_CPP_DIR}/messages.pb.cc")
set(GENERATED_PROTO_HEADER "${GENERATED_CPP_DIR}/messages.pb.h")
set(GENERATED_PYTHON_SOURCE "${GENERATED_PYTHON_DIR}/messages_pb2.py")
set(PROTOBUF_TOOLCHAIN_STAMP "${GENERATED_DIR}/protobuf-toolchain.txt")

# Regenerate the bindings when CMake selects a different Protobuf installation.
# This matters when switching between, for example, Homebrew and Conda.
file(
    GENERATE
    OUTPUT "${PROTOBUF_TOOLCHAIN_STAMP}"
    CONTENT
        "version=${Protobuf_VERSION}\nprotoc=$<TARGET_FILE:protobuf::protoc>\n"
)

# cppzmq consists of a single header. Copying only that header avoids adding a
# package manager's general include directory (for example /opt/homebrew/include)
# where an unrelated Protobuf installation could shadow the selected one.
file(MAKE_DIRECTORY "${GENERATED_CPPZMQ_DIR}")
configure_file(
    "${CPPZMQ_HEADER}"
    "${GENERATED_CPPZMQ_DIR}/zmq.hpp"
    COPYONLY
)

set(SERVER_MAIN "${CMAKE_CURRENT_SOURCE_DIR}/server/main.cc")
set(
    SERVER_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/server/src/fixed_rate_bond.cc"
    "${CMAKE_CURRENT_SOURCE_DIR}/server/src/gaussian_shock_sampler.cc"
    "${CMAKE_CURRENT_SOURCE_DIR}/server/src/messenger.cc"
    "${CMAKE_CURRENT_SOURCE_DIR}/server/src/portfolio.cc"
    "${CMAKE_CURRENT_SOURCE_DIR}/server/src/request_handler.cc"
    "${CMAKE_CURRENT_SOURCE_DIR}/server/src/yield_curve.cc"
)
set(
    SERVER_HEADERS
    "${CMAKE_CURRENT_SOURCE_DIR}/server/include/fixed_rate_bond.hh"
    "${CMAKE_CURRENT_SOURCE_DIR}/server/include/gaussian_shock_sampler.hh"
    "${CMAKE_CURRENT_SOURCE_DIR}/server/include/messenger.hh"
    "${CMAKE_CURRENT_SOURCE_DIR}/server/include/portfolio.hh"
    "${CMAKE_CURRENT_SOURCE_DIR}/server/include/request_handler.hh"
    "${CMAKE_CURRENT_SOURCE_DIR}/server/include/yield_curve.hh"
)

add_custom_command(
    OUTPUT
        "${GENERATED_PROTO_SOURCE}"
        "${GENERATED_PROTO_HEADER}"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${GENERATED_CPP_DIR}"
    COMMAND
        $<TARGET_FILE:protobuf::protoc>
        --cpp_out "${GENERATED_CPP_DIR}"
        --proto_path "${CMAKE_CURRENT_SOURCE_DIR}/proto"
        "${PROTO_FILE}"
    DEPENDS
        "${PROTO_FILE}"
        "${PROTOBUF_TOOLCHAIN_STAMP}"
        protobuf::protoc
    COMMENT "Generating C++ Protocol Buffer sources"
    VERBATIM
)

add_custom_command(
    OUTPUT "${GENERATED_PYTHON_SOURCE}"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${GENERATED_PYTHON_DIR}"
    COMMAND
        $<TARGET_FILE:protobuf::protoc>
        --python_out "${GENERATED_PYTHON_DIR}"
        --proto_path "${CMAKE_CURRENT_SOURCE_DIR}/proto"
        "${PROTO_FILE}"
    DEPENDS
        "${PROTO_FILE}"
        "${PROTOBUF_TOOLCHAIN_STAMP}"
        protobuf::protoc
    COMMENT "Generating Python Protocol Buffer module"
    VERBATIM
)

add_custom_target(
    generate_python_proto ALL
    DEPENDS "${GENERATED_PYTHON_SOURCE}"
)

set(STAGED_CODE_DIR "${CMAKE_CURRENT_BINARY_DIR}/code")
set(STAGED_INCLUDE_DIR "${STAGED_CODE_DIR}/include")
set(STAGED_SOURCE_DIR "${STAGED_CODE_DIR}/src")
set(STAGED_PROTO_DIR "${STAGED_CODE_DIR}/proto")

add_custom_target(
    stage_server_sources ALL
    COMMAND "${CMAKE_COMMAND}" -E make_directory
        "${STAGED_INCLUDE_DIR}"
        "${STAGED_SOURCE_DIR}"
        "${STAGED_PROTO_DIR}"
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different
        "${SERVER_MAIN}"
        "${STAGED_CODE_DIR}/main.cc"
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different
        ${SERVER_HEADERS}
        "${GENERATED_PROTO_HEADER}"
        "${STAGED_INCLUDE_DIR}"
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different
        ${SERVER_SOURCES}
        "${GENERATED_PROTO_SOURCE}"
        "${STAGED_SOURCE_DIR}"
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different
        "${PROTO_FILE}"
        "${STAGED_PROTO_DIR}/messages.proto"
    DEPENDS
        "${SERVER_MAIN}"
        ${SERVER_HEADERS}
        ${SERVER_SOURCES}
        "${PROTO_FILE}"
        "${GENERATED_PROTO_SOURCE}"
        "${GENERATED_PROTO_HEADER}"
    COMMENT "Copying server source snapshot to ${STAGED_CODE_DIR}"
    VERBATIM
)

add_library(
    adaptive_bond_risk_protocol STATIC
    "${GENERATED_PROTO_SOURCE}"
    "${GENERATED_PROTO_HEADER}"
)
target_include_directories(
    adaptive_bond_risk_protocol
    PUBLIC "${GENERATED_CPP_DIR}"
)
target_link_libraries(
    adaptive_bond_risk_protocol
    PUBLIC protobuf::libprotobuf
)

add_library(
    adaptive_bond_risk_server_core STATIC
    ${SERVER_SOURCES}
)
target_include_directories(
    adaptive_bond_risk_server_core
    BEFORE
    PUBLIC
        server/include
        "${GENERATED_CPPZMQ_DIR}"
    PRIVATE
        "$<TARGET_PROPERTY:protobuf::libprotobuf,INTERFACE_INCLUDE_DIRECTORIES>"
)
target_link_libraries(
    adaptive_bond_risk_server_core
    PUBLIC
        adaptive_bond_risk_protocol
        ${ZEROMQ_TARGET}
)
target_compile_definitions(
    adaptive_bond_risk_server_core
    PRIVATE ADAPTIVE_BOND_RISK_VERSION="${PROJECT_VERSION}"
)

add_executable(
    adaptive_bond_risk_server
    "${SERVER_MAIN}"
)
target_link_libraries(
    adaptive_bond_risk_server
    PRIVATE
        adaptive_bond_risk_server_core
        CLI11::CLI11
)
target_compile_definitions(
    adaptive_bond_risk_server
    PRIVATE ADAPTIVE_BOND_RISK_VERSION="${PROJECT_VERSION}"
)

if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    target_compile_options(
        adaptive_bond_risk_server_core
        PRIVATE -Wall -Wextra -Wpedantic
    )
    target_compile_options(
        adaptive_bond_risk_server
        PRIVATE -Wall -Wextra -Wpedantic
    )
elseif(MSVC)
    target_compile_options(adaptive_bond_risk_server_core PRIVATE /W4)
    target_compile_options(adaptive_bond_risk_server PRIVATE /W4)
endif()

if(BUILD_TESTING)
    find_package(Catch2 3 CONFIG REQUIRED)
    find_package(Python3 REQUIRED COMPONENTS Interpreter)

    add_executable(
        adaptive_bond_risk_cpp_tests
        tests/cpp/test_finance.cc
        tests/cpp/test_gaussian_shock_sampler.cc
        tests/cpp/test_request_handler.cc
    )
    target_link_libraries(
        adaptive_bond_risk_cpp_tests
        PRIVATE
            adaptive_bond_risk_server_core
            Catch2::Catch2WithMain
    )

    add_test(
        NAME cpp_unit_tests
        COMMAND adaptive_bond_risk_cpp_tests
    )
    set_tests_properties(
        cpp_unit_tests
        PROPERTIES LABELS "unit;cpp"
    )

    add_test(
        NAME server_help
        COMMAND adaptive_bond_risk_server --help
    )
    set_tests_properties(
        server_help
        PROPERTIES
            LABELS "unit;cpp"
            PASS_REGULAR_EXPRESSION "AdaptiveBondRisk simulation server"
    )

    add_test(
        NAME server_rejects_negative_timeout
        COMMAND
            adaptive_bond_risk_server
            --receive-timeout-ms -1
    )
    set_tests_properties(
        server_rejects_negative_timeout
        PROPERTIES
            LABELS "unit;cpp"
            WILL_FAIL TRUE
    )

    add_test(
        NAME python_unit_tests
        COMMAND
            "${Python3_EXECUTABLE}" -m pytest
            "${CMAKE_CURRENT_SOURCE_DIR}/tests/python/test_client.py"
            "${CMAKE_CURRENT_SOURCE_DIR}/tests/python/test_financial_metrics.py"
            "${CMAKE_CURRENT_SOURCE_DIR}/tests/python/test_shock_distribution.py"
    )
    set_tests_properties(
        python_unit_tests
        PROPERTIES
            LABELS "unit;python"
            ENVIRONMENT
                "ADAPTIVE_BOND_RISK_CLIENT_MODULE_DIR=${CMAKE_CURRENT_SOURCE_DIR}/client/module;ADAPTIVE_BOND_RISK_GENERATED_PYTHON_DIR=${GENERATED_PYTHON_DIR}"
    )

    add_test(
        NAME server_integration_test
        COMMAND
            "${Python3_EXECUTABLE}" -m pytest
            "${CMAKE_CURRENT_SOURCE_DIR}/tests/python/test_server_integration.py"
    )
    set_tests_properties(
        server_integration_test
        PROPERTIES
            LABELS "integration;python"
            TIMEOUT 15
            ENVIRONMENT
                "ADAPTIVE_BOND_RISK_CLIENT_MODULE_DIR=${CMAKE_CURRENT_SOURCE_DIR}/client/module;ADAPTIVE_BOND_RISK_GENERATED_PYTHON_DIR=${GENERATED_PYTHON_DIR};ADAPTIVE_BOND_RISK_SERVER=$<TARGET_FILE:adaptive_bond_risk_server>;ADAPTIVE_BOND_RISK_DATA_DIR=${CMAKE_CURRENT_SOURCE_DIR}/data"
    )
endif()

message(STATUS "ZeroMQ target: ${ZEROMQ_TARGET}")
message(STATUS "cppzmq header: ${CPPZMQ_HEADER}")
message(STATUS "Protobuf version: ${Protobuf_VERSION}")
message(
    STATUS
    "Generated Python protocol module: ${GENERATED_PYTHON_SOURCE}"
)
