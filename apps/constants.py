METHOD_CHOICES = (
    ('aes-128-gcm', 'aes-128-gcm'),
    ('aes-192-gcm', 'aes-192-gcm'),
    ('aes-256-gcm', 'aes-256-gcm'),
    ('aes-128-cfb', 'aes-128-cfb'),
    ('aes-192-cfb', 'aes-192-cfb'),
    ('aes-256-cfb', 'aes-256-cfb'),
    ('aes-128-ctr', 'aes-128-ctr'),
    ('aes-192-ctr', 'aes-192-ctr'),
    ('aes-256-ctr', 'aes-256-ctr'),
    ('rc4-md5', 'rc4-md5'),
    ('bf-cfb', 'bf-cfb'),
    ('salsa20', 'salsa20'),
    ('chacha20', 'chacha20'),
    ('chacha20-ietf', 'chacha20-ietf'),
    ('camellia-128-cfb', 'camellia-128-cfb'),
    ('camellia-192-cfb', 'camellia-192-cfb'),
    ('camellia-256-cfb', 'camellia-256-cfb'),
    ('chacha20-ietf-poly1305', 'chacha20-ietf-poly1305'),
    ('none', 'none'),
)

PROTOCOL_CHOICES = (
    ('auth_sha1_v4', 'auth_sha1_v4'),
    ('auth_aes128_md5', 'auth_aes128_md5'),
    ('auth_aes128_sha1', 'auth_aes128_sha1'),
    ('auth_chain_a', 'auth_chain_a'),
    ('origin', 'origin'),
)


OBFS_CHOICES = (
    ('plain', 'plain'),
    ('http_simple', 'http_simple'),
    ('http_simple_compatible', 'http_simple_compatible'),
    ('http_post', 'http_post'),
    ('tls1.2_ticket_auth', 'tls1.2_ticket_auth'),
)

COUNTRIES_CHOICES = (
    ('US', '美国'),
    ('CN', '中国'),
    ('HK', '香港'),
    ('JP', '日本'),
    ('FR', '法国'),
    ('DE', '德国'),
    ('KR', '韩国'),
    ('JE', '泽西岛'),
    ('NZ', '新西兰'),
    ('MX', '墨西哥'),
    ('CA', '加拿大'),
    ('BR', '巴西'),
    ('CU', '古巴'),
    ('CZ', '捷克'),
    ('EG', '埃及'),
    ('FI', '芬兰'),
    ('GR', '希腊'),
    ('GU', '关岛'),
    ('IS', '冰岛'),
    ('MO', '澳门'),
    ('NL', '荷兰'),
    ('NO', '挪威'),
    ('PL', '波兰'),
    ('IT', '意大利'),
    ('IE', '爱尔兰'),
    ('AR', '阿根廷'),
    ('PT', '葡萄牙'),
    ('AU', '澳大利亚'),
    ('RU', '俄罗斯联邦'),
    ('CF', '中非共和国'),
)

THEME_CHOICES = (
    ("default", "default"),
    ("darkly", "darkly"),
    ("flatly", "flatly"),
    ("journal", "journal"),
    ("materia", "materia"),
    ("minty", "minty"),
    ("spacelab", "spacelab"),
    ("superhero", "superhero"),
)


# 判断节点在线时间间隔
NODE_TIME_OUT = 75

# 默认缓存时间
DEFUALT_CACHE_TTL = 60 * 60 * 2
NODE_USER_INFO_TTL = 60 * 5
