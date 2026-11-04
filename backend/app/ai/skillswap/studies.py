"""Catálogo de estudios y relación entre ellos: reglas puras, sin LLM ni base de datos.

Dos personas tienen el mismo estudio si eligieron el mismo título, y estudios parecidos
si sus títulos son de la misma familia, aunque uno sea de FP y otro de universidad.
Para añadir un estudio basta con añadirlo a `_CATALOG`.
"""

from dataclasses import dataclass
from enum import Enum

MEDIO = "Grado Medio"
SUPERIOR = "Grado Superior"
UNIVERSIDAD = "Universidad"
BACHILLERATO = "Bachillerato"
OTRO = "Otros"


class StudyRelation(str, Enum):
    DIRECT = "direct"
    SIMILAR = "similar"


@dataclass(frozen=True)
class Study:
    code: str
    name: str
    level: str
    family: str | None
    # "Otros estudios de..." agrupa títulos distintos, así que nunca es el mismo estudio.
    is_generic: bool = False


_CATALOG: dict[str, list[tuple[str, str, str]]] = {
    "Informática": [
        ("smr", "Sistemas Microinformáticos y Redes", MEDIO),
        ("asir", "Administración de Sistemas Informáticos en Red", SUPERIOR),
        ("dam", "Desarrollo de Aplicaciones Multiplataforma", SUPERIOR),
        ("daw", "Desarrollo de Aplicaciones Web", SUPERIOR),
        ("ing-informatica", "Ingeniería Informática", UNIVERSIDAD),
        ("ing-software", "Ingeniería del Software", UNIVERSIDAD),
        ("ing-computadores", "Ingeniería de Computadores", UNIVERSIDAD),
        ("ciberseguridad", "Ingeniería de Ciberseguridad", UNIVERSIDAD),
        ("ciencia-datos", "Ciencia e Ingeniería de Datos", UNIVERSIDAD),
        ("ia", "Inteligencia Artificial", UNIVERSIDAD),
    ],
    "Electrónica y telecomunicaciones": [
        ("inst-telecom", "Instalaciones de Telecomunicaciones", MEDIO),
        ("inst-electricas", "Instalaciones Eléctricas y Automáticas", MEDIO),
        ("sist-telecom", "Sistemas de Telecomunicaciones e Informáticos", SUPERIOR),
        ("automatizacion", "Automatización y Robótica Industrial", SUPERIOR),
        ("mant-electronico", "Mantenimiento Electrónico", SUPERIOR),
        ("sist-electrotecnicos", "Sistemas Electrotécnicos y Automatizados", SUPERIOR),
        ("ing-telecom", "Ingeniería de Telecomunicación", UNIVERSIDAD),
        ("ing-electronica", "Ingeniería Electrónica Industrial y Automática", UNIVERSIDAD),
        ("ing-electrica", "Ingeniería Eléctrica", UNIVERSIDAD),
    ],
    "Industria y mecánica": [
        ("mecanizado", "Mecanizado", MEDIO),
        ("soldadura", "Soldadura y Calderería", MEDIO),
        ("electromecanica", "Electromecánica de Vehículos Automóviles", MEDIO),
        ("automocion", "Automoción", SUPERIOR),
        ("diseno-mecanico", "Diseño en Fabricación Mecánica", SUPERIOR),
        ("mecatronica", "Mecatrónica Industrial", SUPERIOR),
        ("ing-mecanica", "Ingeniería Mecánica", UNIVERSIDAD),
        ("ing-industrial", "Ingeniería en Tecnologías Industriales", UNIVERSIDAD),
        ("ing-aeroespacial", "Ingeniería Aeroespacial", UNIVERSIDAD),
    ],
    "Construcción": [
        ("proyectos-edificacion", "Proyectos de Edificación", SUPERIOR),
        ("proyectos-obra-civil", "Proyectos de Obra Civil", SUPERIOR),
        ("arquitectura", "Arquitectura", UNIVERSIDAD),
        ("ing-civil", "Ingeniería Civil", UNIVERSIDAD),
    ],
    "Administración y empresa": [
        ("gestion-admin", "Gestión Administrativa", MEDIO),
        ("admin-finanzas", "Administración y Finanzas", SUPERIOR),
        ("asistencia-direccion", "Asistencia a la Dirección", SUPERIOR),
        ("ade", "Administración y Dirección de Empresas", UNIVERSIDAD),
        ("economia", "Economía", UNIVERSIDAD),
        ("finanzas-contabilidad", "Finanzas y Contabilidad", UNIVERSIDAD),
    ],
    "Comercio y marketing": [
        ("actividades-comerciales", "Actividades Comerciales", MEDIO),
        ("marketing-publicidad", "Marketing y Publicidad", SUPERIOR),
        ("comercio-internacional", "Comercio Internacional", SUPERIOR),
        ("gestion-ventas", "Gestión de Ventas y Espacios Comerciales", SUPERIOR),
        ("marketing", "Marketing e Investigación de Mercados", UNIVERSIDAD),
    ],
    "Sanidad": [
        ("auxiliar-enfermeria", "Cuidados Auxiliares de Enfermería", MEDIO),
        ("farmacia-parafarmacia", "Farmacia y Parafarmacia", MEDIO),
        ("emergencias", "Emergencias Sanitarias", MEDIO),
        ("laboratorio-clinico", "Laboratorio Clínico y Biomédico", SUPERIOR),
        ("imagen-diagnostico", "Imagen para el Diagnóstico y Medicina Nuclear", SUPERIOR),
        ("higiene-bucodental", "Higiene Bucodental", SUPERIOR),
        ("dietetica", "Dietética", SUPERIOR),
        ("medicina", "Medicina", UNIVERSIDAD),
        ("enfermeria", "Enfermería", UNIVERSIDAD),
        ("farmacia", "Farmacia", UNIVERSIDAD),
        ("fisioterapia", "Fisioterapia", UNIVERSIDAD),
    ],
    "Educación y servicios sociales": [
        ("dependencia", "Atención a Personas en Situación de Dependencia", MEDIO),
        ("educacion-infantil-fp", "Educación Infantil", SUPERIOR),
        ("integracion-social", "Integración Social", SUPERIOR),
        ("animacion-sociocultural", "Animación Sociocultural y Turística", SUPERIOR),
        ("magisterio-infantil", "Maestro en Educación Infantil", UNIVERSIDAD),
        ("magisterio-primaria", "Maestro en Educación Primaria", UNIVERSIDAD),
        ("pedagogia", "Pedagogía", UNIVERSIDAD),
        ("psicologia", "Psicología", UNIVERSIDAD),
        ("trabajo-social", "Trabajo Social", UNIVERSIDAD),
    ],
    "Imagen, sonido y diseño": [
        ("video-dj-sonido", "Vídeo Disc-Jockey y Sonido", MEDIO),
        ("animacion-3d", "Animaciones 3D, Juegos y Entornos Interactivos", SUPERIOR),
        ("realizacion", "Realización de Proyectos Audiovisuales y Espectáculos", SUPERIOR),
        ("sonido", "Sonido para Audiovisuales y Espectáculos", SUPERIOR),
        ("comunicacion-audiovisual", "Comunicación Audiovisual", UNIVERSIDAD),
        ("periodismo", "Periodismo", UNIVERSIDAD),
        ("bellas-artes", "Bellas Artes", UNIVERSIDAD),
        ("diseno", "Diseño", UNIVERSIDAD),
    ],
    "Hostelería y turismo": [
        ("cocina", "Cocina y Gastronomía", MEDIO),
        ("servicios-restauracion", "Servicios en Restauración", MEDIO),
        ("direccion-cocina", "Dirección de Cocina", SUPERIOR),
        ("alojamientos", "Gestión de Alojamientos Turísticos", SUPERIOR),
        ("agencias-viajes", "Agencias de Viajes y Gestión de Eventos", SUPERIOR),
        ("turismo", "Turismo", UNIVERSIDAD),
        ("gastronomia", "Ciencias Gastronómicas", UNIVERSIDAD),
    ],
    "Actividad física y deporte": [
        ("guia-medio-natural", "Guía en el Medio Natural y de Tiempo Libre", MEDIO),
        ("animacion-sociodeportiva", "Enseñanza y Animación Sociodeportiva", SUPERIOR),
        ("acondicionamiento-fisico", "Acondicionamiento Físico", SUPERIOR),
        ("cafyd", "Ciencias de la Actividad Física y del Deporte", UNIVERSIDAD),
    ],
    "Ciencias": [
        ("quimica-industrial", "Química Industrial", SUPERIOR),
        ("matematicas", "Matemáticas", UNIVERSIDAD),
        ("fisica", "Física", UNIVERSIDAD),
        ("quimica", "Química", UNIVERSIDAD),
        ("biologia", "Biología", UNIVERSIDAD),
        ("biotecnologia", "Biotecnología", UNIVERSIDAD),
    ],
    "Derecho y humanidades": [
        ("derecho", "Derecho", UNIVERSIDAD),
        ("historia", "Historia", UNIVERSIDAD),
        ("filologia", "Filología", UNIVERSIDAD),
        ("traduccion", "Traducción e Interpretación", UNIVERSIDAD),
    ],
    "Bachillerato": [
        ("bach-ciencias", "Ciencias y Tecnología", BACHILLERATO),
        ("bach-sociales", "Humanidades y Ciencias Sociales", BACHILLERATO),
        ("bach-artes", "Artes", BACHILLERATO),
        ("bach-general", "General", BACHILLERATO),
    ],
}

GENERIC_PREFIX = "otros-"


def _slug(text: str) -> str:
    table = str.maketrans("áéíóúñ", "aeioun")
    return "-".join(text.lower().translate(table).replace(",", "").split())


STUDIES: dict[str, Study] = {}
for _family, _entries in _CATALOG.items():
    for _code, _name, _level in _entries:
        STUDIES[_code] = Study(_code, _name, _level, _family)
    _generic = GENERIC_PREFIX + _slug(_family)
    STUDIES[_generic] = Study(_generic, f"Otros estudios de {_family}", OTRO, _family, is_generic=True)
# Sin familia: no se relaciona con nadie, porque no se sabe qué estudia.
STUDIES["otros"] = Study("otros", "Otros estudios", OTRO, None, is_generic=True)

FAMILIES: tuple[str, ...] = tuple(_CATALOG)


def study_relation(first_code: str | None, second_code: str | None) -> StudyRelation | None:
    first, second = STUDIES.get(first_code or ""), STUDIES.get(second_code or "")
    if first is None or second is None or first.family is None or first.family != second.family:
        return None
    if first.code == second.code and not first.is_generic:
        return StudyRelation.DIRECT
    return StudyRelation.SIMILAR


def codes_in_family(family: str | None) -> list[str]:
    return [study.code for study in STUDIES.values() if family is not None and study.family == family]


def study_label(code: str | None) -> str | None:
    study = STUDIES.get(code or "")
    if study is None:
        return None
    return study.name if study.level == OTRO else f"{study.level} · {study.name}"
