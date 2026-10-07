// One explicitly selected input per bounded process; adapt the limit to the domain.
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <vector>

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size);

int main(int argc, char **argv) {
    constexpr size_t max_bytes = 1024 * 1024;
    if (argc != 2) {
        std::fputs("expected one corpus file\n", stderr);
        return 2;
    }
    std::error_code error;
    auto status = std::filesystem::symlink_status(argv[1], error);
    if (error || !std::filesystem::is_regular_file(status)) {
        std::fputs("input is not an accessible regular file\n", stderr);
        return 2;
    }
    std::ifstream input(argv[1], std::ios::binary);
    if (!input) {
        std::fputs("cannot open input\n", stderr);
        return 2;
    }
    std::vector<uint8_t> data;
    char block[4096];
    while (input) {
        input.read(block, sizeof(block));
        const auto count = static_cast<size_t>(input.gcount());
        if (count > max_bytes - data.size()) {
            std::fputs("input exceeds qualification bound\n", stderr);
            return 2;
        }
        data.insert(data.end(), block, block + count);
    }
    if (input.bad() || !input.eof()) {
        std::fputs("incomplete input read\n", stderr);
        return 2;
    }
    const uint8_t empty = 0;
    const int result = LLVMFuzzerTestOneInput(data.empty() ? &empty : data.data(), data.size());
    if (result != 0 && result != -1) {
        std::fputs("unexpected target callback result\n", stderr);
        return 2;
    }
    std::printf("replayed-bytes=%zu callback=%d\n", data.size(), result);
    return 0;
}
