#include "messenger.hh"
#include "request_handler.hh"

#include <atomic>
#include <chrono>
#include <csignal>
#include <cstdint>
#include <exception>
#include <iostream>
#include <string>

#include <CLI/CLI.hpp>

namespace
{

struct ServerOptions {
    std::string address{"tcp://127.0.0.1:5555"};
    int receive_timeout_ms{250};
    int send_timeout_ms{5'000};
    std::uint64_t max_requests{0};
};

std::atomic_bool keep_running{true};

void handle_signal(int)
{
    keep_running = false;
}

void configure_cli(CLI::App& app, ServerOptions& options)
{
    app.add_option("--address", options.address, "ZeroMQ server endpoint");
    app.add_option("--receive-timeout-ms", options.receive_timeout_ms,
                   "Receive polling interval in milliseconds")
        ->check(CLI::NonNegativeNumber);
    app.add_option("--send-timeout-ms", options.send_timeout_ms,
                   "Send timeout in milliseconds")
        ->check(CLI::NonNegativeNumber);
    app.add_option("--max-requests", options.max_requests,
                   "Stop after this many requests; zero serves indefinitely")
        ->check(CLI::NonNegativeNumber);
}

}    // namespace

int main(int argc, char* argv[])
{
    ServerOptions options;
    CLI::App app{"AdaptiveBondRisk simulation server"};
    configure_cli(app, options);

    try {
        app.parse(argc, argv);
    } catch ( const CLI::ParseError& error ) {
        return app.exit(error);
    }

    try {
        std::signal(SIGINT, handle_signal);
        std::signal(SIGTERM, handle_signal);

        adaptive_bond_risk::Messenger messenger(
            options.address, std::chrono::milliseconds(options.receive_timeout_ms),
            std::chrono::milliseconds(options.send_timeout_ms));
        const adaptive_bond_risk::RequestHandler request_handler;

        std::cout << "AdaptiveBondRisk server " << ADAPTIVE_BOND_RISK_VERSION
                  << " listening on " << messenger.address() << '\n';

        std::uint64_t handled_requests = 0;
        while ( keep_running && (options.max_requests == 0 ||
                                 handled_requests < options.max_requests) ) {

            const auto request = messenger.receive();

            if ( !request.has_value() ) {
                continue;
            }

            const std::string response = request_handler.handle(request.value());
            messenger.send(response);

            ++handled_requests;
            std::cout << "Handled request " << handled_requests << '\n';
        }

        std::cout << "Server stopped after " << handled_requests << " request(s)\n";
        return 0;
    } catch ( const std::exception& error ) {
        std::cerr << "Server error: " << error.what() << '\n';
        return 1;
    }
}
