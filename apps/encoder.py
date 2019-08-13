from short_url import UrlEncoder
from django.conf import settings


class Encoder:
    def __init__(self, alphabet):
        self.encoder = UrlEncoder(alphabet=alphabet)

    def int2string(self, value):
        return self.encoder.encode_url(value)

    def string2int(self, value):
        return self.encoder.decode_url(value)


encoder = Encoder(alphabet=settings.DEFAULT_ALPHABET)
