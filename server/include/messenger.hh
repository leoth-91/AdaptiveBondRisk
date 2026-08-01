#pragma once

#include <chrono>
#include <optional>
#include <string>

#include <zmq.hpp>

namespace adaptive_bond_risk
{

class Messenger
{
  public:
    Messenger(std::string address, std::chrono::milliseconds receive_timeout,
              std::chrono::milliseconds send_timeout);

    Messenger(const Messenger&)            = delete;
    Messenger& operator=(const Messenger&) = delete;
    Messenger(Messenger&&)                 = delete;
    Messenger& operator=(Messenger&&)      = delete;

    [[nodiscard]] std::optional<std::string> receive();
    void send(const std::string& message);

    [[nodiscard]] const std::string& address() const noexcept;

  private:
    std::string address_;
    zmq::context_t context_;
    zmq::socket_t socket_;
};

}    // namespace adaptive_bond_risk
