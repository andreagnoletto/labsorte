"""Gráfico de linha em SVG, sem dependências: só calcula as coordenadas."""

from decimal import Decimal


def _fmt(value: float) -> str:
    return f"{value:g}"


def polyline(values, width: int = 640, height: int = 180, baseline: Decimal | None = None, extra=None) -> dict:
    """Coordenadas de uma polilinha SVG para ``values`` (ordem cronológica).

    ``baseline`` (por exemplo, o saldo inicial) entra na escala e vira uma
    linha de referência em ``baseline_y``. Coordenadas saem como strings prontas
    para o SVG, imunes à localização de números do template. ``extra`` é uma lista de séries
    adicionais desenhadas na mesma escala (``extra_points``), cada uma
    espalhada pela largura inteira.
    """
    values = [Decimal(v) for v in values]
    extra = [[Decimal(v) for v in series] for series in (extra or [])]
    result = {
        "width": width,
        "height": height,
        "points": "",
        "extra_points": [],
        "min": None,
        "max": None,
        "baseline_y": None,
    }
    if not values:
        return result
    everything = values + [v for series in extra for v in series]
    low, high = min(everything), max(everything)
    if baseline is not None:
        low, high = min(low, baseline), max(high, baseline)
    span = high - low

    def x_of(index: int, count: int) -> float:
        return 0.0 if count == 1 else width * index / (count - 1)

    def y_of(value: Decimal) -> float:
        return height / 2 if span == 0 else float((high - value) / span) * height

    def to_points(series) -> str:
        return " ".join(f"{_fmt(x_of(i, len(series)))},{_fmt(y_of(v))}" for i, v in enumerate(series))

    result["points"] = to_points(values)
    result["extra_points"] = [to_points(series) for series in extra if series]
    result["min"], result["max"] = low, high
    if baseline is not None:
        result["baseline_y"] = _fmt(y_of(baseline))
    return result
