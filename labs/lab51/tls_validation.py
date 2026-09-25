#!/usr/bin/env python3
"""Execute certificate-validation cases on loopback with temporary test keys.

Python 3.11+ with cryptography. Binds only 127.0.0.1 on an ephemeral port;
does not contact a CA, modify a trust store or retain private keys.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import platform
import socket
import ssl
import tempfile
import threading

import cryptography
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def receive_exact(stream, count):
    data = bytearray()
    while len(data) < count:
        chunk = stream.recv(count - len(data))
        if not chunk:
            raise RuntimeError('Peer closed before completing the test message')
        data.extend(chunk)
    return bytes(data)


def make_ca(label, *, path_length=0, cert_sign=True):
    """A self-signed CA. path_length and keyCertSign are parameters because
    the cases below need to vary exactly those two things."""
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, label)])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=30))
            .add_extension(x509.BasicConstraints(ca=True, path_length=path_length), True)
            .add_extension(x509.KeyUsage(False, False, False, False, False,
                                        cert_sign, True, False, False), True)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), False)
            .sign(key, hashes.SHA256()))
    return key, cert


def make_intermediate(issuer_key, issuer_cert, label, *, path_length=0,
                      cert_sign=True):
    """A CA certificate issued by another CA.

    cert_sign exists so that a certificate can be marked CA:TRUE while
    keyUsage withholds keyCertSign --- which must be tested as an
    INTERMEDIATE beneath the trusted root, not as a separate self-signed CA,
    or the chain fails as untrusted and the keyUsage is never reached.
    """
    key = ec.generate_private_key(ec.SECP256R1())
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder()
            .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, label)]))
            .issuer_name(issuer_cert.subject).public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=20))
            .add_extension(x509.BasicConstraints(ca=True, path_length=path_length), True)
            .add_extension(x509.KeyUsage(False, False, False, False, False,
                                        cert_sign, True, False, False), True)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), False)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(
                issuer_key.public_key()), False)
            .sign(issuer_key, hashes.SHA256()))
    return key, cert


def make_leaf(ca_key, ca_cert, *, name='localhost', validity='current', server=True):
    key = ec.generate_private_key(ec.SECP256R1())
    now = datetime.now(timezone.utc)
    periods = {'current': (-1, 7), 'expired': (-7, -1), 'future': (1, 7)}
    before, after = periods[validity]
    cert = (x509.CertificateBuilder()
            .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)]))
            .issuer_name(ca_cert.subject).public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now + timedelta(days=before))
            .not_valid_after(now + timedelta(days=after))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), True)
            .add_extension(x509.SubjectAlternativeName([x509.DNSName(name)]), False)
            .add_extension(x509.KeyUsage(True, False, False, False, False,
                                        False, False, False, False), True)
            .add_extension(x509.ExtendedKeyUsage([
                ExtendedKeyUsageOID.SERVER_AUTH if server else ExtendedKeyUsageOID.CLIENT_AUTH
            ]), False)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), False)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), False)
            .sign(ca_key, hashes.SHA256()))
    return key, cert


def exchange(directory, key, cert, trusted_ca, *, check_name=True, chain=()):
    key_file, cert_file = directory / 'server-key.pem', directory / 'server-cert.pem'
    key_file.write_bytes(key.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    # A server presents its leaf followed by any intermediates, in order.
    pem = cert.public_bytes(serialization.Encoding.PEM)
    for extra in chain:
        pem += extra.public_bytes(serialization.Encoding.PEM)
    cert_file.write_bytes(pem)
    server = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server.minimum_version = server.maximum_version = ssl.TLSVersion.TLSv1_3
    server.load_cert_chain(cert_file, key_file)
    client = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    client.minimum_version = client.maximum_version = ssl.TLSVersion.TLSv1_3
    client.load_verify_locations(cadata=trusted_ca.public_bytes(serialization.Encoding.PEM).decode('ascii'))
    client.check_hostname = check_name
    client.hostname_checks_common_name = False
    client.verify_mode = ssl.CERT_REQUIRED
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(('127.0.0.1', 0))
    listener.listen(1)
    listener.settimeout(5)
    address = listener.getsockname()
    server_result = {}

    def serve():
        try:
            with listener:
                raw, _ = listener.accept()
                raw.settimeout(5)
                with raw:
                    with server.wrap_socket(raw, server_side=True) as secure:
                        if receive_exact(secure, 4) != b'ping':
                            raise RuntimeError('Unexpected test request')
                        secure.sendall(b'pong')
                        server_result['application_exchange'] = True
        except ssl.SSLError as exc:
            # Certificate-rejection cases commonly send an alert to the server.
            server_result['tls_alert'] = str(exc)
        except ConnectionResetError as exc:
            # Windows may reset rather than deliver an alert after client rejection.
            server_result['peer_reset'] = str(exc)
        except Exception as exc:
            server_result['unexpected_error'] = repr(exc)

    worker = threading.Thread(target=serve, daemon=True)
    worker.start()
    result = {'hostname_check': check_name, 'chain_validation': True}
    try:
        with socket.create_connection(address, timeout=5) as raw:
            with client.wrap_socket(raw, server_hostname='localhost') as secure:
                secure.sendall(b'ping')
                received = receive_exact(secure, 4)
                if received != b'pong':
                    raise RuntimeError('Unexpected test response')
                result.update(accepted=True, tls_version=secure.version(), cipher=secure.cipher()[0])
    except ssl.SSLCertVerificationError as exc:
        result.update(accepted=False, verification_code=exc.verify_code,
                      verification_message=exc.verify_message)
    finally:
        worker.join(6)
        listener.close()
    if worker.is_alive() or 'unexpected_error' in server_result:
        raise RuntimeError(f'Loopback server failed: {server_result}')
    if result.get('accepted') and not server_result.get('application_exchange'):
        raise RuntimeError('Client accepted without a completed application exchange')
    return result


def run():
    ca_key, ca = make_ca('Network book temporary trusted CA', path_length=1)
    wrong_key, wrong_ca = make_ca('Network book temporary untrusted CA')
    # A leaf certificate. Its signature works; it is not permitted to issue.
    imposter_key, imposter = make_leaf(ca_key, ca, name='imposter.example')
    # An intermediate, and a second one beneath it, to overrun path_length=1.
    mid_key, mid = make_intermediate(ca_key, ca, 'Intermediate one', path_length=0)
    deep_key, deep = make_intermediate(mid_key, mid, 'Intermediate two', path_length=0)
    # Marked CA:TRUE, issued by the TRUSTED root so the chain reaches the
    # anchor, but keyUsage withholds keyCertSign. Making this a separate
    # self-signed CA would fail as untrusted and never test the keyUsage at
    # all --- a case whose label claims one thing while its mechanism does
    # another, which is the defect this book keeps finding elsewhere.
    nosign_key, nosign = make_intermediate(ca_key, ca, 'Intermediate without '
                                           'keyCertSign', cert_sign=False)

    cases = [
        # label, issuer key, issuer cert, leaf options, hostname check,
        # expected acceptance, chain presented, what the case is about
        ('trusted_name_and_chain', ca_key, ca, {}, True, True, (),
         'the control: everything correct'),
        ('untrusted_issuer', wrong_key, wrong_ca, {}, True, False, (),
         'signature valid, issuer not trusted'),
        ('wrong_dns_name', ca_key, ca, {'name': 'wrong.example'}, True, False, (),
         'chain valid, identity wrong'),
        ('expired', ca_key, ca, {'validity': 'expired'}, True, False, (),
         'chain valid, validity period past'),
        ('not_yet_valid', ca_key, ca, {'validity': 'future'}, True, False, (),
         'chain valid, validity period future'),
        ('wrong_extended_key_usage', ca_key, ca, {'server': False}, True, False, (),
         'chain and name valid, certificate not for this purpose'),
        ('wrong_name_with_identity_check_disabled', ca_key, ca,
         {'name': 'wrong.example'}, False, True, (),
         'what turning the identity check off actually buys an attacker'),
        ('leaf_used_as_issuer', imposter_key, imposter, {}, True, False, (imposter,),
         'A LEAF SIGNED THIS. The signature verifies and basicConstraints '
         'says CA:FALSE, so the chain must be refused on a rule that has '
         'nothing to do with cryptography.'),
        ('path_length_exceeded', deep_key, deep, {}, True, False, (deep, mid),
         'Every signature in this chain is valid. The root permits one '
         'intermediate and two were presented.'),
        ('intermediate_without_cert_sign', nosign_key, nosign, {}, True, False,
         (nosign,),
         'The chain reaches the trusted root and every signature verifies. '
         'basicConstraints says CA:TRUE and keyUsage withholds keyCertSign, '
         'so this intermediate may not issue the certificate it just issued.'),
    ]
    results = []
    with tempfile.TemporaryDirectory(prefix='netbook-tls-') as folder:
        for label, issuer_key, issuer, options, check_name, expected, chain, about in cases:
            key, cert = make_leaf(issuer_key, issuer, **options)
            observed = exchange(Path(folder), key, cert, ca,
                                check_name=check_name, chain=chain)
            passed = observed['accepted'] == expected
            if observed['accepted']:
                passed = passed and observed['tls_version'] == 'TLSv1.3'
            results.append(dict(case=label, about=about,
                                expected_acceptance=expected, passed=passed,
                                **observed))
    rejected_not_by_signature = [
        c for c in results
        if not c['accepted'] and c['case'] in
        ('wrong_dns_name', 'expired', 'not_yet_valid', 'wrong_extended_key_usage',
         'leaf_used_as_issuer', 'path_length_exceeded',
         'intermediate_without_cert_sign')]
    return {'scope': 'Executed TLS 1.3 loopback certificate, chain and hostname '
                     'validation. No PQC, no revocation check, no '
                     'forward-secrecy test and no performance measurement.',
            'python': platform.python_version(), 'openssl': ssl.OPENSSL_VERSION,
            'cryptography': cryptography.__version__, 'cases': results,
            'rejections_not_caused_by_a_bad_signature':
                [c['case'] for c in rejected_not_by_signature],
            'finding': ('%d of the %d rejections above involve a chain in which '
                        'every signature is cryptographically valid. Validating '
                        'a certificate is not checking a chain of signatures; '
                        'it is checking a chain of signatures AND the '
                        'constraints each certificate carries about what it may '
                        'be used for, by whom, for which name, and for how '
                        'long.' % (len(rejected_not_by_signature),
                                   sum(1 for c in results if not c['accepted']))),
            'passed': all(c['passed'] for c in results)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = run()
    payload = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(payload + '\n', encoding='utf8')
    print(payload)
    raise SystemExit(0 if report['passed'] else 1)
