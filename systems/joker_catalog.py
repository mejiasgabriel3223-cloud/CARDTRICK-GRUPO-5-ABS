"""Catálogo de metadatos de los Jokers jugables."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JokerMetadata:
    display_name: str
    description: str
    rarity: str
    price: int

    @property
    def sell_price(self) -> int:
        return max(1, self.price // 2)


# El catálogo está separado del comportamiento para que la entidad Joker
# conserve una responsabilidad clara: estado + polimorfismo.
JOKER_CATALOG: dict[str, JokerMetadata] = {
    "CorazonesPLUS": JokerMetadata("Corazones PLUS", "+1 Mult por cada corazón de la mano jugada.", "Poco común", 8),
    "DiamantesPLUS": JokerMetadata("Diamantes PLUS", "+1 Mult por cada diamante de la mano jugada.", "Poco común", 8),
    "TrebolesPLUS": JokerMetadata("Tréboles PLUS", "+1 Mult por cada trébol de la mano jugada.", "Poco común", 8),
    "EspadasPLUS": JokerMetadata("Picas PLUS", "+1 Mult por cada pica de la mano jugada.", "Poco común", 8),
    "ChipsterJoker": JokerMetadata("Chipster", "+50 fichas por cada carta jugada.", "Común", 7),
    "RealezaJoker": JokerMetadata("Comodín de la Realeza", "+50 fichas por carta y +30 por cada figura.", "Poco común", 12),
    "DonutJoker": JokerMetadata("Dona Glaseada", "+100 fichas por carta durante 3 usos; luego se rompe.", "Poco común", 10),
    "PalomitasJoker": JokerMetadata("Caja de Palomitas", "+150 fichas por carta durante 2 usos; luego se rompe.", "Raro", 14),
    "Ruleta": JokerMetadata("Cofre de la Fortuna", "25% de probabilidad de añadir +120 fichas por carta.", "Raro", 15),
    "BolaDeNieveJoker": JokerMetadata("Bola de Nieve", "Otorga +20 fichas por carta y aumenta su bono en +10 cada mano.", "Poco común", 13),
    "AsEnLaMangaJoker": JokerMetadata("As en la Manga", "+50 fichas por cada As de la mano.", "Poco común", 11),
    "PimientoJoker": JokerMetadata("Pimiento Picante", "+200 fichas por carta durante una sola mano.", "Raro", 16),
    "VidrioFinoJoker": JokerMetadata("Vidrio Fino", "+3 Mult por carta durante 3 usos.", "Raro", 15),
    "RamenJoker": JokerMetadata("Tazón de Ramen", "+9 Mult por carta durante 4 usos.", "Raro", 17),
    "HeladoJoker": JokerMetadata("Helado Derretido", "+15 Mult por carta durante 2 usos.", "Raro", 20),
    "LetItRide": JokerMetadata("Let It Ride", "+15 Mult por carta pagando $2 por mano.", "Raro", 18),
    "AvariciaDesatada": JokerMetadata("Avaricia Desatada", "+1 Mult por cada $5 que tengas.", "Raro", 19),
    "MaestroDelParJoker": JokerMetadata("Maestro del Par", "+2 Mult cuando juegas un Par.", "Poco común", 10),
    "OjoDeAguilaJoker": JokerMetadata("Ojo de Águila", "+1.5 Mult cuando juegas Carta Alta.", "Común", 7),
    "GranDobleJoker": JokerMetadata("Gran Doble", "+3 Mult cuando juegas Doble Par.", "Poco común", 11),
    "TriadaJoker": JokerMetadata("Tríada", "+4 Mult cuando juegas Trío.", "Poco común", 13),
    "CaminanteJoker": JokerMetadata("Caminante", "+5 Mult cuando juegas Escalera.", "Raro", 15),
    "PokerMaestroJoker": JokerMetadata("Póker Maestro", "+8 Mult cuando juegas Póker.", "Raro", 18),
    "PrismaJoker": JokerMetadata("Prisma", "+5 Mult cuando juegas Color.", "Raro", 16),
    "CasaLlenaJoker": JokerMetadata("Casa Llena", "+6 Mult cuando juegas Full House.", "Raro", 17),
    "CoronaImperialJoker": JokerMetadata("Corona Imperial", "+12 Mult cuando juegas Escalera de Color.", "Legendario", 24),
    "InversionistaJoker": JokerMetadata("Inversionista", "Al superar una ciega, gana $1 por cada $5 guardados.", "Poco común", 12),
    "RecicladorJoker": JokerMetadata("Reciclador", "Al superar una ciega, gana $2 por cada 5 descartes realizados.", "Poco común", 11),
    "TarjetaDeCreditoJoker": JokerMetadata("Tarjeta de Crédito", "Permite quedar hasta -$20 cuando compras en la tienda.", "Raro", 14),
    "BrendaMadagascarJoker": JokerMetadata("Brenda Madagascar", "Consume el Joker de la izquierda y aumenta su Mult acumulado.", "Legendario", 25),
    "RepeticionJoker": JokerMetadata("Repetición", "Reaplica los bonos acumulados de las cartas jugadas.", "Raro", 16),
    "FavoritoJoker": JokerMetadata("Joker Favorito", "+20 fichas y +3 Mult si juegas tu mano más frecuente.", "Raro", 17),
}


def metadata_for(class_name: str) -> JokerMetadata:
    """Devuelve metadatos seguros incluso para un Joker no registrado."""
    return JOKER_CATALOG.get(
        class_name,
        JokerMetadata(class_name, "Efecto especial.", "Común", 6),
    )
