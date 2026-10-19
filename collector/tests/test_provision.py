from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
import sys
from cryptography.hazmat.primitives.asymmetric import rsa,padding
from cryptography.hazmat.primitives import hashes,serialization
import json
import pytest
sys.path.insert(0,str(Path(__file__).parents[2]/'tools'))
import provision_collector as module


def test_handoff_is_encrypted_and_never_reprovisioned(tmp_path,monkeypatch,capsys):
    key=rsa.generate_private_key(public_exponent=65537,key_size=3072)
    public=tmp_path/'public.pem'
    public.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo))
    def synthetic_bootstrap(path,password):
        from bootstrap_collector import bootstrap
        return bootstrap(path,password,assign_ownership=False)
    monkeypatch.setattr(module,'bootstrap',synthetic_bootstrap)
    envelope=tmp_path/'owner-envelope.bin'
    module.provision(tmp_path/'private',public,envelope)
    plaintext=key.decrypt(envelope.read_bytes(),padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=b'collector-owner-handoff-v1'))
    data=json.loads(plaintext)
    assert len(data['admin_password'])>=32
    assert data['mqtt_username']=='homeassistant'
    assert data['admin_password'].encode() not in envelope.read_bytes()
    assert not capsys.readouterr().out
    with pytest.raises(ValueError):
        module.provision(tmp_path/'private',public,envelope)
