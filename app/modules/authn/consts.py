REFRESH_SEPARATOR = "."

MAX_REFRESH_TOKEN_LEN = 4096
MAX_RID_LEN = 64                    # Redis 键的最大长度
MAX_SECRET_LEN = 256                # JWT 密钥的最大长度

REDIS_PREFIX_REFRESH = "auth:refresh:"
REDIS_PREFIX_TOKENVER = "auth:tokenver:"

RL_AUTH_REGISTER = "auth_register"
RL_AUTH_LOGIN = "auth_login"
RL_AUTH_REFRESH = "auth_refresh"