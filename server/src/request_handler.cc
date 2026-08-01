#include "request_handler.hh"

#include <exception>
#include <stdexcept>
#include <string>

#include "messages.pb.h"

namespace adaptive_bond_risk
{
namespace
{

namespace protocol = adaptive_bond_risk::protocol;

std::string serialize_response(const protocol::Response& response)
{
    std::string serialized;
    if ( !response.SerializeToString(&serialized) ) {
        throw std::runtime_error("Failed to serialize the response");
    }
    return serialized;
}

}    // namespace

std::string RequestHandler::handle(const std::string& serialized_request) const
{
    protocol::Request request;
    protocol::Response response;

    if ( !request.ParseFromString(serialized_request) ) {
        response.set_success(false);
        response.set_error("The request is not a valid Protocol Buffer message");
        return serialize_response(response);
    }

    response.set_request_id(request.request_id());

    try {
        switch ( request.payload_case() ) {
        case protocol::Request::kPing: {
            response.set_success(true);
            auto* ping = response.mutable_ping();
            ping->set_message(request.ping().message().empty()
                                  ? "pong"
                                  : "pong: " + request.ping().message());
            ping->set_server_version(ADAPTIVE_BOND_RISK_VERSION);
            break;
        }
        case protocol::Request::PAYLOAD_NOT_SET:
            response.set_success(false);
            response.set_error("The request does not contain an operation");
            break;
        }
    } catch ( const std::exception& error ) {
        response.Clear();
        response.set_request_id(request.request_id());
        response.set_success(false);
        response.set_error(error.what());
    }

    return serialize_response(response);
}

}    // namespace adaptive_bond_risk
