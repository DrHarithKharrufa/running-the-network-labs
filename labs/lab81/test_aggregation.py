import ipaddress as ip
import unittest
from aggregation import allocate, exact_cover, topology, trace, rd_encoding


class AddressTests(unittest.TestCase):
    def test_equal_allocated_counts(self):
        for flat in (False, True):
            result = allocate(interleaved=flat)
            all_nets = [n for ns in result.values() for n in ns]
            self.assertEqual(len(all_nets), 512)
            self.assertEqual(len(set(all_nets)), 512)

    def test_hierarchical_cover(self):
        self.assertEqual(exact_cover(allocate()), {str(r): [f'10.{r}.0.0/17'] for r in range(4)})

    def test_interleaved_regional_cover(self):
        self.assertEqual([len(ns) for ns in exact_cover(allocate(interleaved=True)).values()], [128]*4)

    def test_common_exit_counterexample(self):
        all_nets = [n for ns in allocate(interleaved=True).values() for n in ns]
        self.assertEqual(list(ip.collapse_addresses(all_nets)), [ip.ip_network('10.64.0.0/15')])

    def test_growth_inside_reservation(self):
        self.assertEqual(exact_cover(allocate(sites=17))['0'], ['10.0.0.0/17', '10.0.128.0/21'])
        for n in allocate(sites=32)[0]:
            self.assertTrue(n.subnet_of(ip.ip_network('10.0.0.0/16')))
        self.assertEqual(len(allocate(sites=16)[0]), 128)
        self.assertEqual(len(allocate(sites=32)[0]), 256)

    def test_dimensions_are_not_hardcoded(self):
        for flat in (False, True):
            self.assertEqual(sum(map(len, allocate(3, 5, 2, flat).values())), 30)

    def test_bounds(self):
        for args in ((0, 16, 8), (17, 1, 1), (4, 33, 8), (4, 16, 9), (True, 1, 1), (1, 1.5, 1)):
            with self.subTest(args=args), self.assertRaises(ValueError): allocate(*args)

    def test_normal_forwarding(self):
        self.assertEqual(trace(topology(), '10.0.0.10')['result'], 'DELIVERED:A')
        self.assertEqual(trace(topology(), '10.0.1.10')['result'], 'DELIVERED:B')

    def test_partial_summary_discards_missing_child(self):
        routes = topology(up=('A',))
        self.assertEqual(trace(routes, '10.0.0.10')['result'], 'DELIVERED:A')
        self.assertEqual(trace(routes, '10.0.1.10')['result'], 'DISCARD')

    def test_missing_discard_loops_to_upstream_default(self):
        result = trace(topology(up=('A',), discard=False), '10.0.1.10')
        self.assertEqual(result, {'path': ['C', 'R', 'C'], 'result': 'LOOP'})

    def test_all_policy_withdraws_healthy_child_too(self):
        routes = topology(up=('A',), policy='all')
        self.assertEqual(routes['C'], [])
        for dst in ('10.0.0.10', '10.0.1.10'):
            self.assertEqual(trace(routes, dst)['result'], 'NO_ROUTE')

    def test_any_withdraws_after_last_child(self):
        self.assertEqual(topology(up=())['C'], [])

    def test_always_can_blackhole_every_child(self):
        self.assertEqual(trace(topology(up=(), policy='always'), '10.0.0.10')['result'], 'DISCARD')

    def test_specific_exception_beats_summary(self):
        routes = topology(up=('A',), exception=True)
        self.assertEqual(trace(routes, '10.0.1.10'), {'path': ['C', 'R2'], 'result': 'DELIVERED:B'})
        self.assertEqual(trace(routes, '10.0.0.10')['path'], ['C', 'R'])

    def test_outside_summary(self):
        self.assertEqual(trace(topology(), '10.0.2.10')['result'], 'NO_ROUTE')

    def test_policy_validation(self):
        for kw in ({'policy':'auto'}, {'up':['A','A']}, {'up':['X']}, {'discard':1}, {'exception':1}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):topology(**kw)

    def test_rd_widths_and_exact_bytes(self):
        self.assertEqual(rd_encoding(0, 64496, 81001), '0000fbf000013c69')
        self.assertEqual(rd_encoding(1, '192.0.2.81', 101), '0001c00002510065')
        self.assertEqual(rd_encoding(2, 65536, 101), '0002000100000065')

    def test_rd_local_boundary(self):
        for kind, admin, limit in ((0, 64496, 2**32), (1, '192.0.2.81', 2**16), (2, 65536, 2**16)):
            self.assertEqual(len(rd_encoding(kind, admin, limit-1)), 16)
            with self.assertRaises(ValueError):rd_encoding(kind, admin, limit)
        with self.assertRaises(ValueError):rd_encoding(2, 65536, 81001)

    def test_rd_type_matters(self):
        self.assertNotEqual(rd_encoding(0, 64496, 101), rd_encoding(2, 64496, 101))

    def test_rd_invalid_inputs(self):
        for args in ((0,65536,1),(2,2**32,1),(1,'2001:db8::1',1),(True,1,1),(0,1,True),(0,1,-1)):
            with self.subTest(args=args), self.assertRaises(ValueError):rd_encoding(*args)

    def test_point_to_point_address_arithmetic(self):
        self.assertEqual([str(a) for a in ip.ip_network('10.255.0.0/31').hosts()], ['10.255.0.0','10.255.0.1'])
        self.assertEqual([str(a) for a in ip.ip_network('2001:db8:8100:1::10/127').hosts()], ['2001:db8:8100:1::10','2001:db8:8100:1::11'])

    def test_ipv6_site_capacity(self):
        self.assertEqual(2**(64-48), 65536)
        self.assertEqual(2**(64-56), 256)
        self.assertEqual(2**(56-48), 256)


if __name__ == '__main__':
    unittest.main()
