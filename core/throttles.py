from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AuthLoginRateThrottle(AnonRateThrottle):
    """
    Throttle for password-based login.
    Limits anonymous callers to prevent brute-force attacks.
    Rate configured via THROTTLE_RATES['auth_login'] in settings.
    """

    scope = "auth_login"


class PinLoginRateThrottle(AnonRateThrottle):
    """
    Throttle for PIN-based login.
    Tighter limit because PINs are shorter than passwords.
    Rate configured via THROTTLE_RATES['pin_login'] in settings.
    """

    scope = "pin_login"


class BurstRateThrottle(UserRateThrottle):
    """Short-window burst limit for authenticated users (per-minute cap)."""

    scope = "burst"


class SustainedRateThrottle(UserRateThrottle):
    """Long-window sustained limit for authenticated users (per-day cap)."""

    scope = "sustained"
