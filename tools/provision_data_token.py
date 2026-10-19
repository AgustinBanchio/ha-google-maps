"""Add ONLY a new data-access key to an existing private collector deployment.

No Google cookie, encryption key, admin verifier or broker password is read.
The newly generated key is delivered encrypted to an owner recipient.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def provision(directory, recipient_file, envelope, *, assign_ownership=True):
    directory = Path(directory)
    target = directory / "data-token"
    if (not directory.is_dir() or directory.is_symlink() or target.exists()
            or envelope.exists() or not (directory / "data").is_dir()
            or not (directory / "store-key").is_file()):
        raise ValueError("refuse incomplete or repeated provisioning")
    recipient = serialization.load_pem_public_key(recipient_file.read_bytes())
    if not isinstance(recipient, rsa.RSAPublicKey) or recipient.key_size < 3072:
        raise ValueError("invalid handoff recipient")
    token = secrets.token_urlsafe(32)
    plaintext = json.dumps({"endpoint":"http://127.0.0.1:8787","data_token":token}).encode()
    ciphertext = recipient.encrypt(plaintext,padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),
        algorithm=hashes.SHA256(),label=b"collector-data-handoff-v1"))
    created = False
    envelope_created = False
    try:
        with target.open("xb") as output:
            created = True
            os.chmod(target,0o400)
            output.write(token.encode());output.flush();os.fsync(output.fileno())
        if os.name == "posix" and assign_ownership:
            os.chown(target,10001,10001)
        with envelope.open("xb") as output:
            envelope_created = True
            os.chmod(envelope,0o600)
            output.write(ciphertext);output.flush();os.fsync(output.fileno())
        if os.name == "posix":
            descriptor=os.open(directory,os.O_DIRECTORY)
            try:os.fsync(descriptor)
            finally:os.close(descriptor)
    except Exception:
        if envelope_created:
            envelope.unlink()
        if created:
            os.chmod(target,0o600);target.unlink()
        raise


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory",type=Path,required=True)
    parser.add_argument("--recipient",type=Path,required=True)
    parser.add_argument("--envelope",type=Path,required=True)
    args=parser.parse_args()
    provision(args.directory,args.recipient,args.envelope)
    print("data_access_key_created_and_encrypted")
