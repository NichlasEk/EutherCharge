#include "../firmware/reference/feedback.hpp"
#include <iostream>
#include <limits>
using namespace euthercharge::reference;
int main() {
    Feedback23 f23; Feedback4 f4; Input3Condition q;
    char type; unsigned a,b,c;
    while(std::cin>>type) {
        if(type=='F') {
            if(!(std::cin>>a>>b>>c)||a>4095||b>4095||c>4095) return 2;
            const bool ready23=f23.push(a,b),ready4=f4.push(c);
            std::cout<<"F "<<ready23<<' '<<ready4<<' '<<f23.value2<<' '<<f23.value3<<' '<<f4.value<<' '
                <<unsigned(f23.count)<<' '<<unsigned(f4.count)<<' '<<f23.sum2<<' '<<f23.sum3<<' '<<f4.sum<<'\n';
        } else if(type=='Q') {
            if(!(std::cin>>a)||a>65535) return 2;
            const auto adjusted=q.update(a);
            std::cout<<"Q "<<adjusted<<' '<<q.qualified<<' '<<q.zeroFault<<' '<<unsigned(q.recoveryCount)
                <<' '<<unsigned(q.qualifyingCount)<<' '<<unsigned(q.zeroCount)<<'\n';
        } else return 2;
    }
    return std::cin.eof()?0:2;
}
