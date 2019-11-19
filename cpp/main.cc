#include <string>

#include "data.h"

#include <iostream>

typedef std::basic_string<unsigned char> byte_string;

// C++98 guarantees that '0', '1', ... '9' are consecutive.
// It only guarantees that 'a' ... 'f' and 'A' ... 'F' are
// in increasing order, but the only two alternative encodings
// of the basic source character set that are still used by
// anyone today (ASCII and EBCDIC) make them consecutive.
unsigned char hexval(unsigned char c) {
    if ('0' <= c && c <= '9')
        return c - '0';
    else if ('a' <= c && c <= 'f')
        return c - 'a' + 10;
    else if ('A' <= c && c <= 'F')
        return c - 'A' + 10;
    else abort();
}

byte_string hex2bin(const std::string &in) {
    byte_string result;
    result.reserve(in.length() / 2);
    for (auto p = in.begin(); p != in.end(); p++) {
        unsigned char c = hexval(*p);
        p++;
        if (p == in.end()) break; // incomplete last digit - should report error
        c = (c << 4) + hexval(*p); // + takes precedence over <<
        result.push_back(c);
    }
    return result;
}

constexpr char hexmap[] = {'0', '1', '2', '3', '4', '5', '6', '7',
                           '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'};

std::string hexStr(unsigned char *data, int len) {
    std::string s(len * 2, ' ');
    for (int i = 0; i < len; ++i) {
        s[2 * i] = hexmap[(data[i] & 0xF0) >> 4];
        s[2 * i + 1] = hexmap[data[i] & 0x0F];
    }
    return s;
}

int main() {
    std::basic_string<unsigned char> blob = hex2bin(
            "020000002100000001674deac5e7fca75f00ca92b1ba3697f5f01ef585011beea7b361150f4504638f0800000002000000000000002100000001a208df134fefed8442b1f01fab59071898f5a1af5164e12c594de55a7004a91c8e0000002000000036ccb9ba8b4f0cd1f3e2d99338806893dff7478c69acee9b8e1247c053783a4800e876481700000000000200000000000000200000000b14ed4f5af8f8f077c7ec4313c6d395b9a7eb5f41eab9ec15367215ca9e420a01000000000000002000000032f56f77b09773aa64c78ee39943da7ec73f91cd757e325098e11b3edc4eccb10100000000000000"
    );

    struct CDevAccountResource account_resource = account_resource_from_lcs(blob.c_str(), blob.length());
    std::cout << "balance: " << account_resource.balance
              << std::endl
              << "sequence: " << account_resource.sequence
              << std::endl
              << "authentication_key: " << hexStr(account_resource.authentication_key, 32)
              << std::endl
              << "delegated_key_rotation_capability: " << account_resource.delegated_key_rotation_capability
              << std::endl
              << "delegated_withdrawal_capability: " << account_resource.delegated_withdrawal_capability
              << std::endl;

    struct CEventHandle sent_events = account_resource.sent_events;
    std::cout << "sent events count: " << sent_events.count << std::endl;

    std::cout << "sent events key:" << hexStr(sent_events.key, 32);
    std::cout << std::endl;

    struct CEventHandle received_events = account_resource.received_events;
    std::cout << "received events count: " << received_events.count;
    std::cout << std::endl;

    std::cout << "sent events key:" << hexStr(received_events.key, 32);
    std::cout << std::endl;


}