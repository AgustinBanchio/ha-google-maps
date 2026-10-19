import json
from pathlib import Path
import sys
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa,padding
from cryptography.hazmat.primitives import hashes,serialization
sys.path.insert(0,str(Path(__file__).parents[2]/"tools"))
from provision_data_token import provision


def test_upgrade_adds_only_scoped_key_and_encrypts_handoff(tmp_path,capsys):
    root=tmp_path/"private";root.mkdir();(root/"data").mkdir()
    (root/"store-key").write_bytes(b"SYNTHETIC_EXISTING_KEY")
    (root/"data/session.json").write_bytes(b"SYNTHETIC_EXISTING_ENCRYPTED_STATE")
    before={str(p.relative_to(root)):p.read_bytes() for p in root.rglob("*") if p.is_file()}
    key=rsa.generate_private_key(public_exponent=65537,key_size=3072)
    recipient=tmp_path/"recipient.pem";recipient.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo))
    envelope=tmp_path/"handoff.bin"
    provision(root,recipient,envelope,assign_ownership=False)
    document=json.loads(key.decrypt(envelope.read_bytes(),padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=b"collector-data-handoff-v1")))
    assert document["data_token"]==(root/"data-token").read_text()
    assert document["data_token"].encode() not in envelope.read_bytes()
    assert all((root/name).read_bytes()==data for name,data in before.items())
    assert not capsys.readouterr().out
    with pytest.raises(ValueError):provision(root,recipient,envelope,assign_ownership=False)
