/* Lab 39.2 --- the same dropper WITHOUT its bounds check, so you can read the
 * verifier's refusal in its own words.
 *
 * This compiles cleanly. clang has no idea it is wrong. The kernel verifier
 * rejects it at load time with a message naming the offset it would have read
 * and stating that the offset is outside the packet.
 *
 * That is the point worth taking away: the verifier proves memory safety and
 * termination properties about the program. It does NOT prove your policy is
 * right. A program that passes the verifier can still drop the wrong traffic.
 *
 *   clang -O2 -g -target bpf -I/usr/include/x86_64-linux-gnu -c xdp_unsafe.c -o xdp_unsafe.o
 */
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>
struct { __uint(type, BPF_MAP_TYPE_HASH); __uint(max_entries, 1024);
         __type(key, __u32); __type(value, __u64); } blocklist SEC(".maps");
/* DELIBERATELY WRONG: reads the IP header without checking data_end. */
SEC("xdp") int xdp_drop(struct xdp_md *ctx)
{
    void *data = (void *)(long)ctx->data;
    struct ethhdr *eth = data;
    struct iphdr *ip = (void *)(eth + 1);
    __u32 src = ip->saddr;                 /* <-- unbounded access */
    if (bpf_map_lookup_elem(&blocklist, &src)) return XDP_DROP;
    return XDP_PASS;
}
char _license[] SEC("license") = "GPL";
