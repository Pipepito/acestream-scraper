/* Minimal bionic DNS transport for the pinned ARM OCI userland.
 *
 * Bionic loads this name and calls netdClientInitDnsOpenProxy at startup.
 * Only DNS is supplied: Linux owns socket routing, so Android fwmark hooks
 * must not be installed. Build for the target Linux architecture with
 * -nostdlib and the payload's libc.so: POSIX calls bind to bionic, never
 * glibc. Declare only the Linux socket ABI here: glibc's ARMv7 time64
 * headers redirect setsockopt to __setsockopt64, which bionic does not export.
 * These constants/layouts are identical on the two supported ARM targets.
 */
#define AF_UNIX 1
#define SOCK_STREAM 1
#define SOCK_CLOEXEC 02000000
#define SOL_SOCKET 1
#define SO_RCVTIMEO 20
#define SO_SNDTIMEO 21

struct sockaddr_un { unsigned short sun_family; char sun_path[108]; };
struct timeval { long tv_sec; long tv_usec; };
extern int socket(int domain, int type, int protocol);
extern int connect(int fd, const void *address, unsigned int length);
extern int setsockopt(int fd, int level, int option, const void *value, unsigned int length);
extern int close(int fd);

static int dns_open_proxy(void) {
    struct sockaddr_un address = { .sun_family = AF_UNIX,
                                  .sun_path = "/dev/socket/dnsproxyd" };
    struct timeval timeout = { .tv_sec = 10, .tv_usec = 0 };
    int fd = socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0);
    if (fd < 0) return -1;
    if (setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout)) < 0 ||
        setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout)) < 0 ||
        connect(fd, &address, sizeof(address)) < 0) {
        close(fd);
        return -1;
    }
    return fd;
}

void netdClientInitDnsOpenProxy(int (**function)(void)) {
    *function = dns_open_proxy;
}
