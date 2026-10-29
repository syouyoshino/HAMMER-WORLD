"""Exact, bounded physical-radius handling for opt-in V11 planets."""
from decimal import Decimal, localcontext, InvalidOperation
import re

TAU_MICRO = 6_283_185
PI_SCALE = 1_000_000
DETAIL_WIDTH = 1024
DETAIL_HEIGHT = 640
MAX_RADIUS_BYTES = 256
MAX_SIGNIFICANT_DIGITS = 64
ADJUSTED_EXPONENT_LIMIT = 2_147_483_647
_DECIMAL_TEXT = re.compile(r"^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$")
PHYSICAL_WAVELENGTHS_M = {"continental":"4e6", "shelf":"1.2e6", "island":"3e5",
                         "coast":"7.5e4", "inlet":"2e4", "mountain":"8e5",
                         "crater":"1.5e5", "lake":"2.5e5"}


def canonical_radius(value):
    """Validate a decimal radius and return canonical scientific notation."""
    if not isinstance(value, str) or len(value.encode("utf8")) > MAX_RADIUS_BYTES or not _DECIMAL_TEXT.fullmatch(value):
        raise ValueError("radius_m must be a positive decimal string of at most 256 bytes")
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError("radius_m must be a finite positive decimal string") from None
    if not number.is_finite() or number <= 0:
        raise ValueError("radius_m must be finite and positive")
    sign, digits, exponent = number.as_tuple()
    if len(digits) > MAX_SIGNIFICANT_DIGITS:
        raise ValueError("radius_m exceeds 64 significant digits")
    adjusted = number.adjusted()
    if adjusted > ADJUSTED_EXPONENT_LIMIT or adjusted < -2_147_483_648:
        raise ValueError("radius_m adjusted exponent exceeds the supported signed 32-bit range")
    # Remove trailing coefficient zeroes without Decimal.normalize(), whose
    # result depends on the ambient precision.
    digits = list(digits)
    while len(digits) > 1 and digits[-1] == 0:
        digits.pop()
        exponent += 1
    coefficient = "".join(str(d) for d in digits)
    mantissa = coefficient[0] + ("." + coefficient[1:] if len(coefficient) > 1 else "")
    scientific_exponent = exponent + len(digits) - 1
    return ("-" if sign else "") + mantissa + "e" + str(scientific_exponent)


def _decimal(canonical):
    return Decimal(canonical)


def metadata(radius_m):
    canonical = canonical_radius(radius_m)
    radius = _decimal(canonical)
    with localcontext() as ctx:
        ctx.prec = 96
        ctx.Emax = ADJUSTED_EXPONENT_LIMIT + 96
        ctx.Emin = -ADJUSTED_EXPONENT_LIMIT - 96
        circumference = radius * TAU_MICRO / PI_SCALE
        # Surface detail is sampled around the equator at 1024 columns.
        sample = circumference / DETAIL_WIDTH
        return {"radius_m": canonical,
                "equatorial_circumference_m_approx": format(circumference, "E").lower(),
                "equatorial_sample_m_approx": format(sample, "E").lower(),
                "circumference_factor_approx": "6.283185",
                "detail_width_px": DETAIL_WIDTH,
                "detail_height_px": DETAIL_HEIGHT}


def physical_octave_periods(radius_m):
    """Return bounded per-band physical wavelengths and sampled periods."""
    canonical=canonical_radius(radius_m)
    info=metadata(canonical)
    radius=_decimal(canonical)
    result={}
    with localcontext() as ctx:
        ctx.prec=96; ctx.Emax=ADJUSTED_EXPONENT_LIMIT+96; ctx.Emin=-ADJUSTED_EXPONENT_LIMIT-96
        circumference=radius*TAU_MICRO/PI_SCALE
        sample=Decimal(info["equatorial_sample_m_approx"])
        for index,(name,raw) in enumerate(PHYSICAL_WAVELENGTHS_M.items()):
            wavelength=Decimal(raw)
            if wavelength>=circumference:
                period=max(4,512//(2**index))
                status="generalized"
            else:
                pixels=wavelength/sample
                if pixels<4:
                    period=0; status="attenuated"
                elif pixels>DETAIL_WIDTH//2:
                    period=DETAIL_WIDTH//2; status="generalized"
                else:
                    period=max(4,int(pixels)); status="resolved"
            result[name]={"wavelength_m":format(wavelength,"E").lower(),
                          "sample_period_px":str(period),"status":status}
    return result


def radius_for_planet(global_radius=None, per_planet=None, planet_ids=()):
    """Resolve explicit global/per-planet values; V11 requires complete coverage."""
    if global_radius is None and per_planet is None:
        raise ValueError("planet-v11 requires explicit --radius-m or --planet-radius-m")
    if per_planet is None:
        per_planet = {}
    if not isinstance(per_planet, dict) or any(k not in planet_ids for k in per_planet):
        raise ValueError("planet radius override references an unknown planet")
    if global_radius is None and set(per_planet) != set(planet_ids):
        raise ValueError("planet-v11 requires a radius for every planet")
    base = canonical_radius(global_radius) if global_radius is not None else None
    return {pid: canonical_radius(per_planet[pid]) if pid in per_planet else base for pid in planet_ids}
