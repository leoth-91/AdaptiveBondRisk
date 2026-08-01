#include "messenger.hh"

#include <cerrno>
#include <stdexcept>
#include <utility>

namespace adaptive_bond_risk
{

Messenger::Messenger(std::string address,
                     const std::chrono::milliseconds receive_timeout,
                     const std::chrono::milliseconds send_timeout)
    : address_(std::move(address)), context_(1),
      socket_(context_, zmq::socket_type::rep)
{
    socket_.set(zmq::sockopt::linger, 0);
    socket_.set(zmq::sockopt::rcvtimeo, static_cast<int>(receive_timeout.count()));
    socket_.set(zmq::sockopt::sndtimeo, static_cast<int>(send_timeout.count()));
    socket_.bind(address_);
}

std::optional<std::string> Messenger::receive()
{
    zmq::message_t request;
    std::optional<std::size_t> result;
    try {
        result = socket_.recv(request, zmq::recv_flags::none);
    } catch ( const zmq::error_t& error ) {
        if ( error.num() == EINTR ) {
            return std::nullopt;
        }
        throw;
    }

    if ( !result.has_value() ) {
        return std::nullopt;
    }

    const auto* data = static_cast<const char*>(request.data());
    return std::string(data, request.size());
}

void Messenger::send(const std::string& message)
{
    const auto result = socket_.send(zmq::buffer(message), zmq::send_flags::none);
    if ( !result.has_value() ) {
        throw std::runtime_error("Timed out while sending a response");
    }
}

const std::string& Messenger::address() const noexcept
{
    return address_;
}

}    // namespace adaptive_bond_risk
