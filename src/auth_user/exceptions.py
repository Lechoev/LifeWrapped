class AuthError(Exception):
    pass


class TokenExpiredError(AuthError):
    pass


class InvalidTokenError(AuthError):
    pass


class InvalidVerificationCodeError(Exception):
    pass


class ExpiredVerificationCodeError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class RefreshTokenNotFoundError(Exception):
    pass


class RefreshTokenExpiredError(Exception):
    pass
