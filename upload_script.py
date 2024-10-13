import argparse
from getpass import getpass
import http.client
import io
import os
import os.path
import ssl
import sys
import tarfile
import urllib.parse

TIMEOUT = 10
AUTHENTICATIO_REQUEST_HEADERS = {
    'Content-type': 'application/x-www-form-urlencoded'
}
BOUNDARY = b'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'
UPLOAD_REQUEST_HEADERS = {
    'Content-type': 'multipart/form-data; boundary={}'.format(BOUNDARY)
}


def parse_args():
    parser = argparse.ArgumentParser(description='Upload code to PyWar.')
    parser.add_argument('-d', '--directory', metavar='DIR', type=str, required=True,
                        help='Directory to upload.')
    parser.add_argument('-n', '--name', metavar='NAME', type=str, required=True,
                        help='Code name in PyWar.')
    parser.add_argument('-s', '--server', metavar='SERVER', type=str, default='pywar.ddns.net',
                        help='PyWar server for uploading this code to.')
    parser.add_argument('-p', '--port', metavar='PORT', type=int, required=True,
                        help='PyWar server port.')
    parser.add_argument('--tactical-module', metavar='MODULE', type=str, required=True,
                        help='Tactical implementation module name.')
    parser.add_argument('--strategic-module', metavar='MODULE', type=str, required=True,
                        help='Strategic implementation module name.')
    parser.add_argument('--password', metavar='PASSWORD', type=str, default=None,
                        help='Password for logging in to the server')
    return parser.parse_args()


def add_directory_to_tarball(tarball, directory, base_dir=None):
    for filename in os.listdir(directory):
        real_path = os.path.join(directory, filename)
        if base_dir is None:
            arcfilename = filename
        else:
            arcfilename = '/'.join([base_dir, filename])
        if os.path.isfile(real_path):
            tarball.add(real_path, arcfilename)
        elif os.path.isdir(real_path):
            add_directory_to_tarball(tarball, real_path, arcfilename)
        else:
            print('Ignoring', filename, 'for it is not recognized as a file or directory')


def get_password(args):
    return args.password if args.password else getpass()


def get_ssl_context():
    context = ssl.SSLContext()
    context.verify_mode = ssl.CERT_NONE
    return context


def authenticate(args):
    encoded_password = urllib.parse.quote(get_password(args), safe='')
    body = f'password={encoded_password}'

    conn = http.client.HTTPSConnection(args.server, args.port, timeout=TIMEOUT, context=get_ssl_context())
    conn.request('POST', '/login', body, AUTHENTICATIO_REQUEST_HEADERS)
    response = conn.getresponse()
    return response.getheader('Set-Cookie')


def upload_file(args, cookie):
    form_data = {
        'tactical': args.tactical_module,
        'strategic': args.strategic_module,
        'overwrite': 'on',
        'name': args.name,
    }

    body = b''
    for k, v in form_data.items():
        body += '--{}\n'.format(BOUNDARY).encode('utf8')
        body += 'Content-Disposition: form-data; name="{}"\n'.format(k).encode('utf8')
        body += '\n{}\n'.format(v).encode('utf8')

    body += '--{}\n'.format(BOUNDARY).encode('utf8')
    body += b'Content-Disposition: form-data; name="tarball"; filename="code.tar.gz"'
    body += b'Content-Type: application/tar+gzip\n'

    inmemory_tar = io.BytesIO()
    with tarfile.open(fileobj=inmemory_tar, mode='w:gz') as tarball:
        add_directory_to_tarball(tarball, args.directory)

    body += b'\n'
    body += inmemory_tar.getbuffer()
    body += b'\n'
    body += '--{}--\n'.format(BOUNDARY).encode('utf8')

    headers = {'Cookie': cookie}
    headers.update(UPLOAD_REQUEST_HEADERS)

    conn = http.client.HTTPSConnection(args.server, args.port, timeout=TIMEOUT, context=get_ssl_context())
    conn.request('POST', '/code/upload', body, headers)
    response = conn.getresponse()
    if response.status != 302:
        print('Failure:', response.status, response.reason, file=sys.stderr)
    else:
        print('Success')


def main(args):
    cookie = authenticate(args)
    if not cookie:
        print('Invalid password', file=sys.stderr)
    else:
        upload_file(args, cookie)


if __name__ == '__main__':
    args = parse_args()
    main(args)
