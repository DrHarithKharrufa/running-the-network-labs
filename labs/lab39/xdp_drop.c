/* Lab 39.2 --- a bounds-checked XDP source-address dropper.
 *
 * Every read past a pointer is preceded by a check against ctx->data_end,
 * because the verifier will reject the program otherwise --- see xdp_unsafe.c
 * for what that rejection looks like. It also means the program is correct for
 * a runt or truncated frame, which is the practical reason the rule exists.
 *
 * SCOPE. Untagged IPv4 source-address matching after bounds checks on the
 * Ethernet and fixed IPv4 base headers. VLAN-tagged traffic, IPv6 and ARP
 * PASS without a blocklist lookup. IPv4 options and fragments STILL undergo
 * source matching: saddr lies in the base header. This is not a complete IPv4
 * validator (version, total length, checksum and full options not validated).
 * An L4 policy needs header-length and fragmentation handling of its own.
 * The executable body is unchanged by this documentation correction.
 *
 * counters[0] dropped, counters[1] passed, counters[2] too short / malformed.
 *
 *   clang -O2 -g -target bpf -I/usr/include/x86_64-linux-gnu -c xdp_drop.c -o xdp_drop.o
 */
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/in.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

struct { __uint(type, BPF_MAP_TYPE_HASH); __uint(max_entries, 1024);
         __type(key, __u32); __type(value, __u64); } blocklist SEC(".maps");
struct { __uint(type, BPF_MAP_TYPE_ARRAY); __uint(max_entries, 3);
         __type(key, __u32); __type(value, __u64); } counters SEC(".maps");

SEC("xdp") int xdp_drop(struct xdp_md *ctx)
{
    void *data = (void *)(long)ctx->data, *end = (void *)(long)ctx->data_end;
    __u32 k;
    __u64 *c;
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > end) { k = 2; c = bpf_map_lookup_elem(&counters, &k); if (c) __sync_fetch_and_add(c, 1); return XDP_PASS; }
    if (eth->h_proto != bpf_htons(ETH_P_IP)) { k = 1; c = bpf_map_lookup_elem(&counters, &k); if (c) __sync_fetch_and_add(c, 1); return XDP_PASS; }
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > end) { k = 2; c = bpf_map_lookup_elem(&counters, &k); if (c) __sync_fetch_and_add(c, 1); return XDP_PASS; }
    if (ip->ihl < 5) { k = 2; c = bpf_map_lookup_elem(&counters, &k); if (c) __sync_fetch_and_add(c, 1); return XDP_PASS; }
    __u32 src = ip->saddr;
    if (bpf_map_lookup_elem(&blocklist, &src)) { k = 0; c = bpf_map_lookup_elem(&counters, &k); if (c) __sync_fetch_and_add(c, 1); return XDP_DROP; }
    k = 1; c = bpf_map_lookup_elem(&counters, &k); if (c) __sync_fetch_and_add(c, 1);
    return XDP_PASS;
}
char _license[] SEC("license") = "GPL";
