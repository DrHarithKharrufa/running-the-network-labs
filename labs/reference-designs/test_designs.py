"""Offline checks of Appendix C's planning data; no hardware or NOS claims."""
from pathlib import Path
from ipaddress import ip_network
from decimal import Decimal
from math import ceil
import json,unittest,itertools
D=json.loads((Path(__file__).with_name('designs.json')).read_text())
class Designs(unittest.TestCase):
    def disjoint(self,strings,parent):
        nets=[ip_network(s) for s in strings];p=ip_network(parent)
        for n in nets:self.assertTrue(n.subnet_of(p))
        for a,b in itertools.combinations(nets,2):self.assertFalse(a.overlaps(b))
    def test_aldergate_staff_and_access(self):
        a=D['aldergate'];self.assertEqual(sum(a['staff']),1200);self.assertEqual(ceil(a['wired_endpoints']/a['access_ports']),17);self.assertEqual(ceil(a['wired_endpoints']/a['planned_usable_ports']),21)
    def test_aldergate_ipv4_partition(self):
        a=D['aldergate'];parts=a['ipv4_sites']+a['ipv4_unallocated'];self.disjoint(parts,a['ipv4_parent']);self.assertEqual(sum(ip_network(p).num_addresses for p in parts),65536)
    def test_aldergate_ipv6_sites(self):
        a=D['aldergate'];self.disjoint(a['ipv6_sites'],a['ipv6_parent']);self.assertEqual(2**(64-56),256)
    def test_smaller_site_subnets_partition(self):
        a=D['aldergate']
        for base in [32,48]:
            parts=[f'10.10.{base+offset}.0/{prefix}' for offset,prefix in a['smaller_site_offsets']];self.disjoint(parts,f'10.10.{base}.0/20');self.assertEqual(sum(ip_network(p).num_addresses for p in parts),4096)
    def test_aldergate_internet_failure_budget(self):
        a=D['aldergate'];demand=a['internet_observed_mbps']*a['growth_factor'];self.assertEqual(demand,750);self.assertEqual(a['surviving_circuit_mbps']-demand,250)
    def test_kestrel_demand_and_utilisation_gate(self):
        k=D['kestrel'];load=Decimal(k['subscribers']*k['subscriber_mbps']+k['business_circuits']*k['business_cir_mbps'])/1000*Decimal(str(k['growth_factor']));self.assertEqual(load,Decimal('362.5'));self.assertLess(load,k['single_span_gbps']);self.assertGreater(load/Decimal(str(k['planning_utilisation'])),k['single_span_gbps']);self.assertEqual((load/Decimal('.70')).quantize(Decimal('.01')),Decimal('517.86'))
    def test_kestrel_shared_pools(self):
        k=D['kestrel'];self.disjoint(k['pop_pools'],k['shared_parent']);self.assertEqual(sum(ip_network(p).num_addresses for p in k['pop_pools']),ip_network(k['shared_parent']).num_addresses)
    def test_kestrel_ipv6_service_pools(self):
        k=D['kestrel'];self.disjoint([k['ipv6_business'],k['ipv6_residential'],k['ipv6_infrastructure']],k['ipv6_parent']);self.assertEqual(2**(48-ip_network(k['ipv6_business']).prefixlen),1024);self.assertGreaterEqual(1024,k['business_circuits']);self.assertEqual(2**(56-ip_network(k['ipv6_residential']).prefixlen),65536);self.assertGreaterEqual(65536,k['subscribers']*k['growth_factor']);self.assertLess(2**(48-40),k['business_circuits'])
    def test_kestrel_bng_surviving_capacity(self):
        k=D['kestrel'];self.assertEqual(k['subscribers']*k['growth_factor'],k['surviving_bng_sessions'])
    def test_anvil_site_totals(self):
        a=D['anvil'];self.assertEqual(sum(a['workload_leaves']),80);self.assertEqual(sum(a['spines']),12);self.assertEqual(sum(a['server_interfaces']),1696);self.assertEqual(20*24+4*16+8*8,608);self.assertEqual(8*8,a['gpu_nodes']);self.assertEqual(80+3*a['borders_per_hall'],86)
    def test_anvil_links_optics_and_pools(self):
        a=D['anvil'];links=[(leaves+a['borders_per_hall'])*spines for leaves,spines in zip(a['workload_leaves'],a['spines'])];self.assertEqual(links,[272,52,52]);self.assertEqual(sum(links)*2,752);self.assertEqual(a['border_to_dci_links']*2,24);self.disjoint(a['loopback_pools']+a['link_pools'],a['underlay_parent']);self.assertTrue(all(n<=2**(31-ip_network(p).prefixlen) for n,p in zip(links,a['link_pools'])))
    def test_anvil_spine_cages_and_failure_ratios(self):
        a=D['anvil'];used=[n+a['borders_per_hall']+a['spine_reserved_cages'] for n in a['spine_workload_cages']];self.assertEqual(used,[20,30,30]);self.assertTrue(all(n<=32 for n in used));self.assertEqual(600/100,6);self.assertEqual(400/100,4);self.assertEqual(600/(7*25),24/7)
if __name__=='__main__':unittest.main(verbosity=2)
