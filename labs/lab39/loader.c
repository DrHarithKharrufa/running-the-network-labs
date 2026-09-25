/* Lab 39.2 --- minimal libbpf loader: load, verify, populate the blocklist,
 * attach in generic (SKB) mode, hold, then read the counters and detach.
 *
 * Generic mode is used deliberately. It runs after the kernel has allocated an
 * skb, so it is slower than native driver XDP and slower still than hardware
 * offload --- and it works on interfaces whose driver has no native XDP support,
 * which is what makes this lab runnable anywhere. It is the right mode for
 * learning the mechanism and the wrong mode for measuring anything.
 *
 *   gcc -O2 loader.c -o loader -lbpf -lelf -lz
 *   HOLD=7 ./loader xdp_drop.o <ifname> [ip-to-block]
 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <net/if.h>
#include <linux/if_link.h>
#include <unistd.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
int main(int argc,char**argv){
  if(argc<3){fprintf(stderr,"usage: %s <obj> <ifname> [block-ip]\n",argv[0]);return 2;}
  int ifindex=if_nametoindex(argv[2]);
  if(!ifindex){perror("if_nametoindex");return 1;}
  struct bpf_object *obj=bpf_object__open_file(argv[1],NULL);
  if(!obj){fprintf(stderr,"open failed\n");return 1;}
  if(bpf_object__load(obj)){fprintf(stderr,"load/verify FAILED\n");return 1;}
  struct bpf_program *p=bpf_object__find_program_by_name(obj,"xdp_drop");
  int pfd=bpf_program__fd(p);
  int bl=bpf_object__find_map_fd_by_name(obj,"blocklist");
  int ct=bpf_object__find_map_fd_by_name(obj,"counters");
  if(argc>3){__u32 k; __u64 v=1; inet_pton(AF_INET,argv[3],&k);
    if(bpf_map_update_elem(bl,&k,&v,0)){perror("map_update");return 1;}
    printf("blocked %s\n",argv[3]);}
  if(bpf_xdp_attach(ifindex,pfd,XDP_FLAGS_SKB_MODE,NULL)){perror("xdp_attach");return 1;}
  printf("attached generic to %s\n",argv[2]);
  printf("PRESS:sleep\n"); fflush(stdout);
  sleep(atoi(getenv("HOLD")?:"5"));
  __u32 k; __u64 v;
  for(k=0;k<3;k++){v=0; bpf_map_lookup_elem(ct,&k,&v);
    printf("counter[%u]=%llu\n",k,(unsigned long long)v);}
  bpf_xdp_detach(ifindex,XDP_FLAGS_SKB_MODE,NULL);
  return 0;
}
