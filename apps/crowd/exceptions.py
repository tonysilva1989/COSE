class RankingError(Exception):
    pass


class RedisError(Exception):
    pass


class EmptyKeyError(RedisError):
    def __init__(self, keyname):
        self.keyname = keyname

    def __str__(self):
        return "The key '{0}' is empty.".format(self.keyname)