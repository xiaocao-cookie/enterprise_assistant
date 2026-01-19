from enum import Enum

class Env(str, Enum):
    """ 项目的环境，开发/生产/测试... """
    dev = "dev"
    prod = "prod"
    production = "production"
    staging = "staging"


class JwtAlg(str, Enum):
    """ JWT 的算法 """
    HS256 = "HS256"
    RS256 = "RS256"