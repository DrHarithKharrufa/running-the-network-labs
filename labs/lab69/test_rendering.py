import unittest
from copy import deepcopy
from jinja2 import UndefinedError
from one_template_four_vendors import INTENT,TARGETS,ENV,render,render_all

class RenderingTests(unittest.TestCase):
    def test_determinism(self):self.assertEqual(render_all(),render_all())
    def test_intent_not_mutated(self):
        old=deepcopy(INTENT);render_all();self.assertEqual(old,INTENT)
    def test_platform_specific_names(self):
        for target,mapping in TARGETS.items():self.assertIn(mapping['interface'],render(target))
    def test_switchport_prerequisites(self):
        for target in ['Cisco IOS-XE','Arista EOS']:
            self.assertIn(' switchport\n switchport mode access\n switchport access vlan 30',render(target))
    def test_junos_els_membership(self):
        text=render('Juniper Junos');self.assertIn('interface-mode access',text);self.assertIn('set vlans VLAN30 vlan-id 30',text)
    def test_srlinux_bridge_is_explicit(self):
        text=render('Nokia SR Linux')
        for token in ['vlan-tagging true','subinterface 0','type bridged','untagged {','network-instance VLAN30','type mac-vrf','interface ethernet-1/8.0']:self.assertIn(token,text)
        self.assertNotIn('vlan { access',text)
    def test_srlinux_service_label_is_not_an_ingress_tag(self):self.assertNotIn('vlan-id 30',render('Nokia SR Linux'))
    def test_vlan_change_reaches_every_target(self):
        new=dict(INTENT,vlan=40)
        for target in TARGETS:
            self.assertNotEqual(render(target),render(target,new));self.assertIn('40',render(target,new))
    def test_missing_field_fails(self):
        new=deepcopy(INTENT);del new['vlan']
        with self.assertRaises(ValueError):render('Cisco IOS-XE',new)
    def test_unknown_field_fails(self):
        with self.assertRaises(ValueError):render('Cisco IOS-XE',dict(INTENT,command='shutdown'))
    def test_unknown_mode_fails(self):
        for mode in ['routed','trunk','acess',None]:
            with self.subTest(mode=mode),self.assertRaises(ValueError):render('Cisco IOS-XE',dict(INTENT,mode=mode))
    def test_bad_vlan_fails(self):
        for vlan in [0,4095,True,'30',30.0]:
            with self.subTest(vlan=vlan),self.assertRaises(ValueError):render('Cisco IOS-XE',dict(INTENT,vlan=vlan))
    def test_newline_and_delimiter_injection_fails(self):
        for text in ['x\nshutdown','x\rshutdown','x"; delete interfaces','x\t shutdown','']:
            with self.subTest(text=text),self.assertRaises(ValueError):render('Nokia SR Linux',dict(INTENT,description=text))
    def test_unsupported_target_fails(self):
        with self.assertRaises(ValueError):render('Unknown NOS')
    def test_strict_undefined(self):
        with self.assertRaises(UndefinedError):ENV.from_string('{{ missing }}').render()
    def test_templates_do_not_emit_apply_commands(self):
        for text in render_all().values():
            self.assertNotIn('commit now',text);self.assertNotIn('write memory',text)

if __name__=='__main__':unittest.main()
