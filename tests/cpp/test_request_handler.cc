#include "request_handler.hh"

#include <cstdint>
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

namespace
{

protocol::Request build_simulate_losses_request(std::uint64_t request_id,
                                                std::uint32_t num_samples,
                                                std::uint64_t seed)
{
    protocol::Request request;
    request.set_request_id(request_id);

    protocol::SimulateLossesRequest* simulate = request.mutable_simulate_losses();

    protocol::YieldCurvePoint* point = simulate->add_base_yield_curve();
    point->set_maturity(1.0);
    point->set_zero_rate(0.02);

    protocol::BondPosition* position = simulate->add_positions();
    position->set_id("BOND");
    position->set_face_value(1000.0);
    position->set_coupon_rate(0.0);
    position->set_time_to_maturity(1.0);
    position->set_coupon_frequency(1);
    position->set_time_to_next_coupon(1.0);
    position->set_quantity(1.0);

    simulate->add_mean(0.0);
    simulate->add_covariance(0.0002);
    simulate->set_num_samples(num_samples);
    simulate->set_seed(seed);

    return request;
}

}    // namespace

TEST_CASE("A loss simulation returns the requested number of correctly-sized samples")
{
    const protocol::Response response =
        send_request(build_simulate_losses_request(21, 10, 7));

    REQUIRE(response.success());
    REQUIRE(response.has_simulate_losses());
    REQUIRE(response.simulate_losses().samples_size() == 10);
    for ( const protocol::LossSample& sample : response.simulate_losses().samples() ) {
        REQUIRE(sample.shock_size() == 1);
    }
}

TEST_CASE("A loss simulation is reproducible for a fixed seed")
{
    const protocol::Response first =
        send_request(build_simulate_losses_request(22, 5, 3));
    const protocol::Response second =
        send_request(build_simulate_losses_request(22, 5, 3));

    REQUIRE(first.simulate_losses().samples_size() ==
           second.simulate_losses().samples_size());
    for ( int i = 0; i < first.simulate_losses().samples_size(); ++i ) {
        REQUIRE(first.simulate_losses().samples(i).loss() ==
               second.simulate_losses().samples(i).loss());
        REQUIRE(first.simulate_losses().samples(i).shock(0) ==
               second.simulate_losses().samples(i).shock(0));
    }
}

TEST_CASE("A loss simulation rejects a mean length that does not match the curve")
{
    protocol::Request request = build_simulate_losses_request(23, 1, 1);
    request.mutable_simulate_losses()->add_mean(0.0);

    const protocol::Response response = send_request(request);

    REQUIRE_FALSE(response.success());
    REQUIRE(response.error() ==
            "The shock mean length must match the number of yield-curve points");
}
