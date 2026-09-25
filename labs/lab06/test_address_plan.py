import unittest
from ipaddress import ip_network
from address_plan import validate_allocations,conventional_ipv4_capacity,child_count,load_plan

class AddressPlanTests(unittest.TestCase):
    def test_ipv4_sites_disjoint_and_contained(self):
        p=load_plan()['ipv4']
        self.assertEqual(len(validate_allocations(p['parent'],p['site_blocks'])),3)
    def test_ipv6_sites_disjoint_and_contained(self):
        p=load_plan()['ipv6']
        self.assertEqual(len(validate_allocations(p['parent'],p['site_blocks'])),3)
    def test_overlap_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_allocations('10.10.0.0/16',{'a':'10.10.0.0/19','b':'10.10.16.0/20'})
    def test_outside_parent_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_allocations('10.10.0.0/16',{'a':'10.11.0.0/20'})
    def test_noncanonical_ipv6_is_rejected(self):
        with self.assertRaises(ValueError): child_count('2001:db8:4500::/36',48)
    def test_kestrel_child_capacities(self):
        self.assertEqual(child_count('2001:db8:4000::/36',48),4096)
        self.assertEqual(child_count('2001:db8:4000::/36',56),1048576)
    def test_ipv6_site_capacity(self):
        self.assertEqual(child_count('2001:db8:a1de::/48',56),256)
        self.assertEqual(child_count('2001:db8:a1de::/56',64),256)
    def test_wireless_headroom(self):
        self.assertEqual(conventional_ipv4_capacity('10.10.4.0/22')-950,72)
        self.assertLess(conventional_ipv4_capacity('10.10.4.0/22',3),1045)
    def test_voice_cannot_fit_in_24(self):
        self.assertLess(conventional_ipv4_capacity('10.10.8.0/24'),400)
        self.assertGreaterEqual(conventional_ipv4_capacity('10.10.8.0/23',3),400)
    def test_initial_london_allocations_fill_20(self):
        prefixes=['10.10.0.0/22','10.10.4.0/22','10.10.8.0/23','10.10.10.0/24',
                  '10.10.11.0/24','10.10.12.0/23','10.10.14.0/24','10.10.15.0/24']
        blocks=validate_allocations('10.10.0.0/20',dict(enumerate(prefixes)))
        self.assertEqual(sum(n.num_addresses for _,n in blocks),4096)
    def test_reserved_space_plus_sites_exhaust_parent(self):
        p=load_plan()['ipv4'];allocs=dict(p['site_blocks'])
        allocs.update({f'reserve-{i}':n for i,n in enumerate(p['unallocated'])})
        blocks=validate_allocations(p['parent'],allocs)
        self.assertEqual(sum(n.num_addresses for _,n in blocks),65536)
    def test_point_to_point_addresses(self):
        self.assertEqual([str(x) for x in ip_network('10.254.1.0/31').hosts()],['10.254.1.0','10.254.1.1'])
        self.assertEqual(len(list(ip_network('2001:db8:4500:ffff::/127').hosts())),2)
    def test_public_subscriber_capacity(self):
        self.assertLess(ip_network('198.18.0.0/17').num_addresses,50000)
        self.assertGreater(ip_network('198.18.0.0/16').num_addresses,50000)
    def test_mesh_count(self):
        self.assertEqual(len({(a,b) for a in range(12) for b in range(a+1,12)}),66)
    def test_invalid_reservation_rejected(self):
        for invalid in [-1,True,1.5,300]:
            with self.subTest(value=invalid),self.assertRaises(ValueError):
                conventional_ipv4_capacity('192.0.2.0/24',invalid)
    def test_invalid_child_sizes(self):
        for invalid in [35,129,True,48.5]:
            with self.subTest(value=invalid),self.assertRaises(ValueError):
                child_count('2001:db8:4000::/36',invalid)

    def test_supplied_sparse_graph(self):
        import json
        from pathlib import Path
        g=json.loads(Path(__file__).with_name('sparse-graph.json').read_text())
        edges={tuple(sorted(e)) for e in g['edges']}
        self.assertEqual(len(g['routers']),12);self.assertEqual(len(edges),16)
        self.assertTrue(all(a!=b and a in g['routers'] and b in g['routers'] for a,b in edges))
        self.assertEqual(child_count(g['link_pool'],31),16)
        self.assertGreaterEqual(child_count(g['loopback_pool'],32),12)
        mgmt=validate_allocations(g['management_pool'],dict(enumerate(g['worked_management_prefixes'])))
        self.assertEqual(len(mgmt),4)
        self.assertTrue(all(conventional_ipv4_capacity(str(n),1)>=20 for _,n in mgmt))
        # Check graph connectivity after each single edge loss; this proves only the graph property.
        for failed in edges:
            remaining=edges-{failed};seen={'r01'}
            while True:
                more={b for a,b in remaining if a in seen}|{a for a,b in remaining if b in seen}
                if more<=seen:break
                seen|=more
            self.assertEqual(seen,set(g['routers']))

if __name__=='__main__': unittest.main(verbosity=2)
