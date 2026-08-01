#pragma once

#include <string>

namespace adaptive_bond_risk
{

class RequestHandler
{
  public:
    [[nodiscard]] std::string handle(const std::string& serialized_request) const;
};

}    // namespace adaptive_bond_risk
