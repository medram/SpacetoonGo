class SpacetoonGoException(Exception):
    pass


class AccountException(SpacetoonGoException):
    pass


class UnsubscribedAccount(AccountException):
    pass


class AccountPermissionError(AccountException):
    def __init__(self,
                 msg='This SpacetoonGo account can\'t get access to these assets (try a premium account).'):

        self.message = msg
        super().__init__(self.message)


class EpisodeNotFound(SpacetoonGoException):
    pass
