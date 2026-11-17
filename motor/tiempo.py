"""Conversion de horas HH:MM a minutos enteros y de vuelta.

DECISION sobre horas como 25:10 (el GTFS cuenta el servicio de madrugada como
parte del dia anterior): NO se envuelven. 25:10 se guarda como 1510 minutos.
Asi el servicio que pasa de medianoche sigue en orden dentro del mismo dia de
servicio y se puede comparar con un simple <. Esta decision va en el README (R12).
"""


def hora_a_minutos(texto):
    """'HH:MM' -> minutos desde las 00:00. O(1). Lanza ValueError si es invalida."""
    partes = texto.strip().split(":")
    if len(partes) != 2:
        raise ValueError("Hora invalida: " + texto)
    horas = int(partes[0])
    minutos = int(partes[1])
    if horas < 0 or minutos < 0 or minutos > 59:
        raise ValueError("Hora invalida: " + texto)
    return horas * 60 + minutos


def minutos_a_hora(minutos):
    """Minutos -> 'HH:MM'. Si pasa de 24 horas se conserva (1510 -> '25:10')."""
    return f"{minutos // 60:02d}:{minutos % 60:02d}"
