import pytest
import os
import json
from app.core.encryptor import AESEncryptor, EncryptedData

@pytest.fixture
def passphrase():
    return "test-secure-passphrase-123"

@pytest.fixture
def encryptor(passphrase):
    return AESEncryptor(passphrase=passphrase)

def test_encryption_decryption_loop(encryptor):
    """Test full cycle of encryption and decryption."""
    original_text = b"Secret corporate data"
    
    # Encrypt
    encrypted_data = encryptor.encrypt(original_text)
    assert isinstance(encrypted_data, EncryptedData)
    assert encrypted_data.ciphertext != original_text
    
    # Decrypt
    decrypted_text = encryptor.decrypt(encrypted_data)
    assert decrypted_text == original_text

def test_file_encryption(encryptor, tmp_path):
    """Test encrypting and decrypting a physical file."""
    # Create dummy input file
    input_file = tmp_path / "input.txt"
    input_file.write_text("Hello World")
    
    enc_file = tmp_path / "output.enc"
    
    # Encrypt to file
    encryptor.encrypt_file(str(input_file), str(enc_file))
    
    assert enc_file.exists()
    
    # Read encrypted content (should be JSON structure)
    with open(enc_file, 'r') as f:
        content = json.load(f)
        assert "ciphertext" in content
        assert "iv" in content
        assert "salt" in content

    # Decrypt to new file
    dec_file = tmp_path / "restored.txt"
    encryptor.decrypt_file(str(enc_file), str(dec_file))
    
    assert dec_file.read_text() == "Hello World"

def test_invalid_passphrase(encryptor):
    """Ensure decryption fails explicitly with a wrong key."""
    data = b"Sensitive"
    encrypted = encryptor.encrypt(data)
    
    wrong_encryptor = AESEncryptor("wrong-password-000")
    
    with pytest.raises(Exception):
        wrong_encryptor.decrypt(encrypted)