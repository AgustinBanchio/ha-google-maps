"""Host-side acceptance for a disposable project; never targets the HA stack."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import time
from urllib.request import Request, urlopen
from http.cookiejar import CookieJar
from urllib.request import build_opener, HTTPCookieProcessor, ProxyHandler

ROOT = Path(__file__).resolve().parents[1]
PROJECT = "google-maps-collector-acceptance"
IMAGE = "google-maps-collector:acceptance"


def command(args, **kwargs):
    return subprocess.check_output(args, text=True, **kwargs).strip()


def wait(predicate, seconds=45):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        try:
            if predicate():
                return
        except (OSError, ValueError, KeyError, subprocess.CalledProcessError):
            pass
        time.sleep(0.5)
    raise AssertionError("acceptance deadline expired")


LAUNCHER = '''
import json
from pathlib import Path
from google_maps_collector import google_maps, service
from google_maps_collector.__main__ import main
control = Path('/acceptance/control.json')
class SyntheticGoogle:
    def poll(self, jar):
        data = json.loads(control.read_text())
        if data.get('reject'):
            raise google_maps.InvalidSession()
        return [google_maps.Person('synthetic-acceptance-person', 0.5, 0.25, 25, data['timestamp'], data['battery'])], jar
    def close(self):
        pass
original = service.Service
class SyntheticService(original):
    def __init__(self, config, store, google):
        super().__init__(config, store, google, lambda: json.loads(control.read_text())['now'])
google_maps.GoogleMaps = SyntheticGoogle
service.Service = SyntheticService
main()
'''


def run(directory, build=True):
    assert directory.is_absolute() and not directory.exists()
    directory.mkdir(mode=0o700, parents=True)
    revision = command(['git', 'rev-parse', 'HEAD'], cwd=ROOT)
    if build:
        subprocess.run(['docker', 'build', '-f', 'deploy/Dockerfile', '--build-arg',
            'SOURCE_REVISION=' + revision, '-t', IMAGE, '.'], cwd=ROOT, check=True)
    image_id = command(['docker', 'image', 'inspect', '--format', '{{.Id}}', IMAGE])
    # Only this newly created synthetic directory is mounted for provisioning.
    bootstrap = """from pathlib import Path
import sys
sys.path.insert(0, '/repo/tools')
from bootstrap_collector import bootstrap
bootstrap(Path('/acceptance/private'), 'synthetic-acceptance-admin')
"""
    subprocess.run(['docker','run','--rm','--network','none','--user','0:0',
        '--mount',f'type=bind,src={directory},dst=/acceptance',
        'google-maps-collector-test-tests','/repo/collector/.venv/bin/python','-c',bootstrap],check=True)
    (directory/'runtime.py').write_text(LAUNCHER)
    os.chmod(directory, 0o755)
    state = {'now': time.time(), 'timestamp': time.time()-5, 'battery': 73}
    def save_control():
        temporary = directory/'control.next'
        temporary.write_text(json.dumps(state)); temporary.chmod(0o644)
        os.replace(temporary, directory/'control.json')
    save_control()
    env_file = directory/'compose.env'
    env_file.write_text(f'COLLECTOR_IMAGE={image_id}\nCOLLECTOR_PRIVATE_DIR={directory}/private\n')
    config = json.loads(command(['docker','compose','--env-file',str(env_file),'-f','deploy/compose.yaml','config','--format','json'],cwd=ROOT))
    config['name'] = PROJECT
    for section in ('networks', 'secrets'):
        for key, item in config.get(section, {}).items():
            if 'name' in item:
                item['name'] = PROJECT + '_' + key
    config['services']['collector']['entrypoint'] = ['python','/acceptance/runtime.py']
    config['services']['collector']['ports'][0]['published'] = '18787'
    config['services']['collector']['environment']['POLL_SECONDS'] = '15'
    config['services']['collector']['volumes'].append({'type':'bind','source':str(directory),
        'target':'/acceptance','read_only':True})
    config['services']['broker'].pop('ports',None)
    config_file = directory/'compose.json'
    config_file.write_text(json.dumps(config))
    compose = ['docker','compose','-p',PROJECT,'-f',str(config_file)]
    events = []
    opener = build_opener(ProxyHandler({}), HTTPCookieProcessor(CookieJar()))
    def request(path, payload=None, headers=None):
        req = Request('http://127.0.0.1:18787'+path, data=payload,
            headers={'Host':'127.0.0.1:8787','Origin':'http://127.0.0.1:8787', **(headers or {})})
        with opener.open(req,timeout=5) as response:
            return json.loads(response.read())
    def login():
        return request('/login',json.dumps({'password':'synthetic-acceptance-admin'}).encode(),
            {'Content-Type':'application/json'})['csrf_token']
    def status():
        return request('/status')
    def import_cookie(csrf):
        body=(b'--synthetic\r\nContent-Disposition: form-data; name="cookies"; filename="synthetic.txt"\r\n'
              b'Content-Type: text/plain\r\n\r\n# Netscape HTTP Cookie File\n'
              b'.google.com\tTRUE\t/\tTRUE\t0\t__Secure-1PSID\tSYNTHETIC_SECRET\n\r\n--synthetic--\r\n')
        return request('/cookies',body,{'Content-Type':'multipart/form-data; boundary=synthetic','X-CSRF-Token':csrf})
    def broker_state():
        code="""import json,time
from threading import Event
from pathlib import Path
import paho.mqtt.client as p
out={}; done=Event()
c=p.Client(p.CallbackAPIVersion.VERSION2)
c.username_pw_set('homeassistant',Path('/acceptance/private/ha-password').read_text())
c.on_connect=lambda c,u,f,r,prop:c.subscribe('google_maps_collector/#',qos=1)
def message(c,u,m):
 out[m.topic]=m.payload.decode()
c.on_message=message
c.connect('broker',1883);c.loop_start();time.sleep(2);c.disconnect();c.loop_stop()
print(json.dumps(out))
"""
        return json.loads(command(['docker','run','--rm','--network',PROJECT+'_collector',
            '--mount',f'type=bind,src={directory},dst=/acceptance,readonly',
            'google-maps-collector-test-tests','/repo/collector/.venv/bin/python','-c',code]))
    try:
        subprocess.run(compose+['up','-d'],check=True)
        wait(lambda: command(compose+['exec','-T','collector','python','-m','google_maps_collector','--healthcheck'])=='')
        csrf=login()
        assert status()['session_status']=='credential_required'
        import_cookie(csrf)
        assert status()['session_status']=='ready'
        initial=broker_state()
        topic=next(t for t in initial if t.endswith('/location'))
        identity=topic.split('/')[1]
        source=json.loads(initial[topic])['source_timestamp']
        events.append('synthetic import and ARM64 non-root startup passed')
        before=command(compose+['exec','-T','collector','python','-c',
            "from pathlib import Path;import hashlib;print(hashlib.sha256(Path('/run/secrets/store-key').read_bytes()).hexdigest())"])
        subprocess.run(compose+['restart','broker'],check=True)
        wait(lambda: broker_state().get('google_maps_collector/availability')=='online')
        assert json.loads(broker_state()[topic])['source_timestamp']==source
        subprocess.run(compose+['up','-d','--force-recreate','collector','broker'],check=True)
        wait(lambda: command(compose+['exec','-T','collector','python','-m','google_maps_collector','--healthcheck'])=='')
        csrf=login()
        wait(lambda: status()['session_status']=='ready')
        after=command(compose+['exec','-T','collector','python','-c',
            "from pathlib import Path;import hashlib;print(hashlib.sha256(Path('/run/secrets/store-key').read_bytes()).hexdigest())"])
        assert after==before
        replay=broker_state()
        assert json.loads(replay[topic])['source_timestamp']==source
        events.append('broker restart and both-container recreation preserve session key and identity')
        # Battery-only changes keep the exact source timestamp/location payload.
        state['battery']=42;save_control();import_cookie(csrf)
        assert json.loads(broker_state()[topic])['source_timestamp']==source
        state['reject']=True;save_control()
        try: import_cookie(csrf);raise AssertionError('invalid import accepted')
        except Exception as error:
            from urllib.error import HTTPError
            assert isinstance(error,HTTPError) and error.code==400
        assert status()['session_status']=='ready'
        state['reject']=False;state['now']+=901;save_control()
        wait(lambda: broker_state().get(f'google_maps_collector/{identity}/availability')=='offline')
        events.append('rejected replacement and independent stale-fix availability passed')
        logs=command(compose+['logs','--no-color'])
        assert 'SYNTHETIC_SECRET' not in logs
        assert 'synthetic-acceptance-person' not in logs
        events.append('container logs contain no credential/contact canaries')
        # Inspect selected fields, never dump container environments.
        selected=command(compose+['exec','-T','collector','python','-c','import os;print(os.getuid())'])
        assert selected=='10001'
        result={'passed':events,'source_revision':revision,'image_id':image_id,'architecture':'arm64'}
        (directory/'result.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result))
    finally:
        subprocess.run(compose+['down'],check=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',required=True,type=Path)
    parser.add_argument('--no-build',action='store_true')
    args=parser.parse_args()
    run(args.directory,args.no_build is False)
