#include "request_handler.hh"

#include <string>

#include <catch2/catch_test_macros.hpp>

#include "messages.pb.h"

namespace protocol = adaptive_bond_risk::protocol;

namespace
{

protocol::Response send_request(const protocol::Request& request)
{
    adaptive_bond_risk::RequestHandler handler;
    protocol::Response response;

    const std::string serialized_response =
        handler.handle(request.SerializeAsString());
    REQUIRE(response.ParseFromString(serialized_response));

    return response;
}

}    // namespace

TEST_CASE("A ping returns its request ID, message, and server version")
{
    protocol::Request request;
    request.set_request_id(42);
    request.mutable_ping()->set_message("hello");

    const protocol::Response response = send_request(request);

    REQUIRE(response.success());
    REQUIRE(response.error().empty());
    REQUIRE(response.request_id() == 42);
    REQUIRE(response.has_ping());
    REQUIRE(response.ping().message() == "pong: hello");
    REQUIRE(response.ping().server_version() == "0.1.0");
}

TEST_CASE("An empty ping returns a plain pong")
{
    protocol::Request request;
    request.set_request_id(7);
    request.mutable_ping();

    const protocol::Response response = send_request(request);

    REQUIRE(response.success());
    REQUIRE(response.ping().message() == "pong");
}

TEST_CASE("A request without an operation returns a structured error")
{
    protocol::Request request;
    request.set_request_id(9);

    const protocol::Response response = send_request(request);

    REQUIRE_FALSE(response.success());
    REQUIRE(response.request_id() == 9);
    REQUIRE(response.error() == "The request does not contain an operation");
    REQUIRE_FALSE(response.has_ping());
}

TEST_CASE("Malformed bytes return a structured error")
{
    adaptive_bond_risk::RequestHandler handler;
    protocol::Response response;

    const std::string malformed_message(1, static_cast<char>(0x80));
    const std::string serialized_response = handler.handle(malformed_message);

    REQUIRE(response.ParseFromString(serialized_response));
    REQUIRE_FALSE(response.success());
    REQUIRE(response.error() ==
            "The request is not a valid Protocol Buffer message");
}
