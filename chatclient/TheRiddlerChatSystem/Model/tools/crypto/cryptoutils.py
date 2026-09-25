import traceback

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import base64

BLOCK_SIZE = 16  # Bytes

# Padding functions
pad = lambda s: bytes(s) + bytes((BLOCK_SIZE - len(s) % BLOCK_SIZE) * \
                                 chr(BLOCK_SIZE - len(s) % BLOCK_SIZE).encode())
unpad = lambda s: s[:-ord(s[-1:])]

me = '[CryptoTools]'


class CryptoTools:
    '''
    Constructor for CryptoPractice Class
    '''

    def __init__(self):
        self.key = None
        self.iv = None
        self.hmac = None
        self.salt = None
        self.mode = AES.MODE_CBC
        self.cipher = None
        self.hash = None
        self.nonce = None
        self.tag = None

    def RandomKey256(self):
        """
        Generates a Random key of 256 bits
        Returns 256 bit random key
        """
        key = get_random_bytes(32)  # generate a random 256bit key
        return key

    def RandomKey128(self):
        """
        Generates a Random key of 128 bits
        returns 128 bit random key
        """
        key = get_random_bytes(16)
        return key

    def RandomNumber(self, size):
        """
        Generate a Random Number in this case will be known as a salt
        @size is the size in bytes of the random number to be generated
        Returns random number of user defined size
        """
        salt = get_random_bytes(size)
        self.salt = salt
        return salt

    def Sha256(self, mesg):
        """
        Sha256 digest
        @mesg is the data to hash
        returns SHA256 of a message
        """
        self.hash = SHA256.new()
        self.hash.update(mesg)
        hash = self.hash.digest()
        return hash

    '''
    AES-EAX encrypt
    @plaintext is the data to encrypt
    @key is the key to be used for encryption
    Returns ciphertext which is the encrypted data
    '''

    def AesEncryptEAX(self, plaintext, key, mac_len=16):
        self.cipher = AES.new(key, AES.MODE_EAX, nonce=self.nonce)
        self.nonce = self.cipher.nonce
        self.mode = AES.MODE_EAX
        ciphertext, self.tag = self.cipher.encrypt_and_digest(plaintext)
        # need to append self.tag to ciphertext in case an object doens't store that
        # tag anymore.
        # need to find out how many bytes the tag is for a 256 bit key A: mac_len=16bytes
        # setting mac_len to be the maximum value which is 16 bytes.

        return ciphertext + self.tag

    def AesDecryptEAX(self, cipherdata, key):
        """
        AES-EAX decrypt
        @cipherdata is encrypted data
        @key is key to be used for decryption (same key for encryption)
        returns the plain text of the encyrpted data
        """
        print(b'AES-Decrypt:' + self.nonce)
        self.cipher = AES.new(key, AES.MODE_EAX, nonce=self.nonce)
        self.nonce = self.cipher.nonce
        self.mode = AES.MODE_EAX
        plaintext = self.cipher.decrypt(cipherdata[:len(cipherdata) - 16])
        # print("plaintext: " + str(plaintext))
        try:
            self.tag = cipherdata[len(cipherdata) - 16:]
            self.cipher.verify(self.tag)
            return plaintext
        except ValueError:
            print(me + 'Key incorrect or message is corrupted')

    def AesCbcEncrypt(self, key, iv, plaintext):
        """
        AES-CBC encryption, encrypts data
        @key is the key for encyrption
        @iv is the initialization vector (usually salt + key)
        @plaintext is data to be encyrpted
        Returns cipher text
        """
        paddedplain = pad(plaintext)
        self.cipher = AES.new(key, AES.MODE_CBC, iv)
        self.mode = AES.MODE_CBC
        try:
            cipher_text = self.cipher.encrypt(paddedplain)
        except:
            exc_typ, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback, limit=3, file=sys.stdout)

        return cipher_text



    def AesCbcDecrypt(self, key, iv, ciphertext):
        """
        AES-CBC decryption, decrypts data
        @key is the key for encryption
        @iv is the initialization vector (salt + key, usually)
        @ciphertext is the encyrpted data to be decrypted
        """
        self.cipher = AES.new(key, AES.MODE_CBC, iv)
        self.mode = AES.MODE_CBC
        plaintext = self.cipher.decrypt(ciphertext)
        return unpad(plaintext)



    def RSAEncrypt(self, key, plaintext):
        """
        RSA Encrypt, Encypts an arbitrary amount of data
        TODO:Integrate with pycryptodome
        @key is the key for encryption
        @plaintext is the plaintext data to be encrypted
        """
        chunkarray = []
        ciphertext = b''
        padding = 11  # PKCS1_OAEP padding length
        start = 0
        maxChunk = int(((key.size_in_bits() / 8) - 2 - (32 * 2)))
        self.cipher = PKCS1_OAEP.new(key)
        endpoint = len(plaintext)

        while start < endpoint:
            if len(plaintext) > (key.size_in_bits() / 8 - padding):
                # split the ciphertext into chunks
                chunkEnd = start + maxChunk
                if chunkEnd > endpoint:
                    chunkEnd = endpoint
                chunk = plaintext[start:chunkEnd]
                print('DEBUG: length of chunk: ' + str(len(chunk)))
                start = chunkEnd
                ciphertext += self.cipher.encrypt(chunk)
            else:
                chunk = plaintext
                ciphertext += self.cipher.encrypt(chunk)
                break

        return ciphertext



    def RSADecrypt(self, key, cipherText):
        """
        RSA Encrypt, Encypts an arbitrary amount of data
        @key is the key for encryption
        @ciphertext is the plaintext data to be encrypted
        """
        chunkarray = []
        plaintext = b''
        padding = 11  # PKCS1_OAEP padding length
        start = 0
        maxChunk = int(key.size_in_bits() / 8)
        endpoint = len(cipherText)
        self.cipher = PKCS1_OAEP.new(key)

        try:
            while start < (endpoint):
                chunkEnd = start + maxChunk
                if (endpoint - start) <= (key.size_in_bits() / 8):
                    chunkEnd = endpoint
                    chunk = cipherText[start:chunkEnd]
                    plaintext += self.cipher.decrypt(chunk)
                    break

                if chunkEnd > endpoint:
                    chunkEnd = endpoint
                    chunk = cipherText[start:chunkEnd]
                else:
                    chunk = cipherText[start:chunkEnd]
                    print(me + 'DEBUG> length of start: ' + str(start))

                start = chunkEnd
                plaintext += self.cipher.decrypt(chunk)
            return plaintext

        except OSError as e:
            print(me + 'ERROR: ' + str(e))

    def RSAGenerateKey(self, keyLength):
        return RSA.generate(keyLength)



if __name__ == '__main__':
    """
    Testing AES EAX, AESCBC encryption/decryption, RSA encrypt/decryption
    as well as random256 bit key
    """
    crypt = CryptoTools()
    crypt.key = crypt.RandomKey256()
    b64 = base64.urlsafe_b64encode(str(crypt.key).encode())
    print(me + 'INFO> b64 key: ' + str(b64))
    crypt.salt = crypt.RandomNumber(16)
    print(me + 'INFO> length of salt: ' + str(len(crypt.salt)))
    derivedkey = crypt.Sha256(crypt.salt + crypt.key)
    print(me + 'INFO> derived key b64: ' + str(base64.urlsafe_b64encode(str(derivedkey).encode())))
    data = b'well hello to the world'
    # AES-EAX
    ciphertext = crypt.AesEncryptEAX(data, crypt.key)
    print(me + 'INFO> AES_EAX ciphertext: ' + str(ciphertext))
    print(me + 'INFO> AES_EAX decrypt: ' + str(crypt.AesDecryptEAX(ciphertext, crypt.key)))
    # AES-CBC
    plaintext = b'secret message A through b and possibly c'
    n = 16 - (len(plaintext) % 16)
    plaintext = bytes(plaintext) + bytes(b'\x00') * n
    print(str(plaintext))
    print(me + 'INFO> ' + str(len(bytes(plaintext))))
    ciphertext1 = crypt.AesCbcEncrypt(derivedkey, crypt.salt, bytes(plaintext))
    print(me + 'INFO> AES-CBC Encrypt ' + str(ciphertext1))
    print(me + 'INFO> Length of cipher: ' + str(len(ciphertext1)))
    decrypted = crypt.AesCbcDecrypt(derivedkey, crypt.salt, ciphertext1)
    print(me + 'INFO> AES-CBC Decrypt ' + str(decrypted))

    RSAKey = crypt.RSAGenerateKey(4096)
    privateKey = RSA.importKey(RSAKey.exportKey())
    plaintext = b'hello from the RSA world of messaging'
    ciphertext = crypt.RSAEncrypt(RSAKey.publickey(), plaintext)
    print(me + 'CIPHERTEXT: ' + str(ciphertext))
    decrypted = crypt.RSADecrypt(privateKey, ciphertext)
    print(me + 'PLAINTEXT: ' + str(decrypted))
    print('#####TESTING PACKETS OVER PADDING######')
    plaintext = b'hello from the RSA world of messaging' * 300
    ciphertext = crypt.RSAEncrypt(RSAKey.publickey(), plaintext)
    print(me + 'CIPHERTEXT: ' + str(ciphertext))
    decrypted = crypt.RSADecrypt(privateKey, ciphertext)
    print(me + 'PLAINTEXT: ' + str(decrypted))
