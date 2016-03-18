#!/usr/bin/env python

import os
import sys
import time

from subprocess import Popen, PIPE, STDOUT

intermediate_cert_path = "{{ letsencrypt_intermediate_cert_path }}"
certs_dir = "{{ letsencrypt_certs_dir }}"
sites = {{ wordpress_sites }}
sites = dict((k, v) for k, v in sites.items() if v['ssl']['provider'] == 'letsencrypt')

script = "{{ acme_tiny_software_directory }}/acme_tiny.py"
failed = False

for name, site in sites.iteritems():
    cert_path = os.path.join(certs_dir, name + ".cert")
    bundled_cert_path = os.path.join(certs_dir, name + "-bundled.cert")
    hosts = site['site_hosts']

    if os.access(cert_path, os.F_OK):
        stat = os.stat(cert_path)
        print "Certificate file " + cert_path + " already exists"

        if time.time() - stat.st_mtime < {{ letsencrypt_min_renewal_age }} * 86400:
            print "  The certificate is younger than {{ letsencrypt_min_renewal_age }} days. Not creating a new certificate.\n"
            continue

    host = ",".join(hosts)

    print "Generating certificate for " + host
    args = [
        "/usr/bin/env", "python", script,

        "--ca",
        "{{ letsencrypt_ca }}",
        "--account-key",
        "{{ letsencrypt_account_key }}",
        "--csr",
        "{{ acme_tiny_data_directory }}/csrs/" + name + ".csr",
        "--acme-dir",
        "{{ acme_tiny_challenges_directory }}"
    ]

    cmd = "/usr/bin/env " + " ".join(args)

    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
    cert = p.stdout.read()
    p.stdin.close()

    if p.wait() != 0:
        print "error while generating certificate for " + host
        print p.stderr.read()
        failed = True
    else:
        cert_file = open(cert_path, 'w')
        cert_file.write(cert)
        cert_file.close()

        intermediate_cert = open(intermediate_cert_path, 'r').read()
        bundled_cert = "".join([cert, intermediate_cert])

        bundled_file = open(bundled_cert_path, 'w')
        bundled_file.write(bundled_cert)
        bundled_file.close()

        print "Created certificate for " + host

if failed:
    sys.exit(1)
else:
    sys.exit(0)
