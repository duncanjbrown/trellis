#!/usr/bin/env python

import os
import time

from subprocess import Popen, PIPE, STDOUT

certs_dir = "{{ letsencrypt_certs_dir }}"
sites = {{ wordpress_sites }}
sites = dict((k, v) for k, v in sites.items() if v['ssl']['provider'] == 'letsencrypt')

script = "{{ acme_tiny_software_directory }}/acme_tiny.py"

for name, site in sites.iteritems():
    cert_path = os.path.join(certs_dir, name + ".cert")
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
    else:
        f = open(cert_path, 'w')
        f.write(cert)
        f.close()
