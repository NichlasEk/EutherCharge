#pragma once
#include <cstdint>

namespace euthercharge::reference {
// Raw-unit reference behavior, reconstructed from H-6CS ROM routines.
// No GPIO, ADC drivers, charge policy or power-stage enable interface.
struct Feedback23 {
    std::uint16_t sum2=0, sum3=0, value2=0, value3=0;
    std::uint8_t count=0;
    bool push(std::uint16_t raw2, std::uint16_t raw3) noexcept {
        sum2=static_cast<std::uint16_t>(sum2+(raw2>1300?1300:raw2));
        sum3=static_cast<std::uint16_t>(sum3+(raw3>1300?1300:raw3));
        if(++count<50) return false;
        value2=sum2/32; value3=sum3/32;
        sum2=sum3=0; count=0;
        return true;
    }
};
struct Feedback4 {
    std::uint16_t sum=0, value=0;
    std::uint8_t count=0;
    bool push(std::uint16_t raw) noexcept {
        const auto half=static_cast<std::uint16_t>(raw/2);
        sum=static_cast<std::uint16_t>(sum+(half>500?500:half));
        if(++count<126) return false;
        value=sum/64; sum=0; count=0;
        return true;
    }
};
struct Input3Condition {
    bool qualified=false, zeroFault=false;
    std::uint8_t recoveryCount=0, qualifyingCount=0, zeroCount=0;
    std::uint16_t update(std::uint16_t value) noexcept {
        if(value==0) {
            qualifyingCount=recoveryCount=0; qualified=false;
            if(!zeroFault && ++zeroCount>=2) {zeroCount=0; zeroFault=true;}
            return 0;
        }
        zeroCount=0;
        if(zeroFault && ++recoveryCount>=20) {
            recoveryCount=0; zeroFault=false; qualified=false; qualifyingCount=0;
            return value; // ROM returns before subtracting10 on this recovery event.
        }
        value=value>=11?static_cast<std::uint16_t>(value-10):0;
        if(value<25) {qualified=false; qualifyingCount=0;}
        else if(!qualified && ++qualifyingCount>=4) {qualified=true; qualifyingCount=0;}
        return value;
    }
};
} // namespace euthercharge::reference
