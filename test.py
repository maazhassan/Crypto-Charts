import base64
encrypted="FkYSDwtXXB4SRlpSFB4KEwQbHBMVTUYCFQRYXAwGFB9PFANNRgQJHFFcAAQFXUQUHggHBxUaQEpK QVtaT11XDhMEHgFWVQhGTVpPVVoFCAQMDVlcAxVGWlIUHhgPDRULX1wJRk1aT0ZYDwMIDhsTGVdB RgkJUlxKTUFdDltWSkFbWk9DUANARgc="
my_eyes=str.encode("maazh49")
decoded=base64.b64decode(encrypted)
decrypted=""
for i in range(0,len(decoded)):
    decrypted+=chr((my_eyes[i%len(my_eyes)] ^ decoded[i]))
print(decrypted)