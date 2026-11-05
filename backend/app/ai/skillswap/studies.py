"""Catálogo de estudios y relación entre ellos: reglas puras, sin LLM ni base de datos.

Dos personas tienen el mismo estudio si eligieron el mismo título, y estudios parecidos
si sus títulos son de la misma familia, aunque uno sea de FP y otro de universidad.
Para añadir un estudio basta con añadirlo a `_CATALOG`.
"""

from dataclasses import dataclass
from enum import Enum

MEDIO = "Intermediate Vocational"
SUPERIOR = "Higher Vocational"
UNIVERSIDAD = "University"
BACHILLERATO = "Upper Secondary"
OTRO = "Other"


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
    "Computing": [
        ("smr", "Microcomputer Systems and Networks", MEDIO),
        ("asir", "Network Computer Systems Administration", SUPERIOR),
        ("dam", "Cross-Platform Application Development", SUPERIOR),
        ("daw", "Web Application Development", SUPERIOR),
        ("ing-informatica", "Computer Engineering", UNIVERSIDAD),
        ("ing-software", "Software Engineering", UNIVERSIDAD),
        ("ing-computadores", "Computer Hardware Engineering", UNIVERSIDAD),
        ("ciberseguridad", "Cybersecurity Engineering", UNIVERSIDAD),
        ("ciencia-datos", "Data Science and Engineering", UNIVERSIDAD),
        ("ia", "Artificial Intelligence", UNIVERSIDAD),
    ],
    "Electronics and telecommunications": [
        ("inst-telecom", "Telecommunications Installations", MEDIO),
        ("inst-electricas", "Electrical and Automated Installations", MEDIO),
        ("sist-telecom", "Telecommunications and Computer Systems", SUPERIOR),
        ("automatizacion", "Industrial Automation and Robotics", SUPERIOR),
        ("mant-electronico", "Electronic Maintenance", SUPERIOR),
        ("sist-electrotecnicos", "Electrotechnical and Automated Systems", SUPERIOR),
        ("ing-telecom", "Telecommunications Engineering", UNIVERSIDAD),
        ("ing-electronica", "Industrial Electronics and Automation Engineering", UNIVERSIDAD),
        ("ing-electrica", "Electrical Engineering", UNIVERSIDAD),
    ],
    "Industry and mechanics": [
        ("mecanizado", "Machining", MEDIO),
        ("soldadura", "Welding and Boilermaking", MEDIO),
        ("electromecanica", "Motor Vehicle Electromechanics", MEDIO),
        ("automocion", "Automotive", SUPERIOR),
        ("diseno-mecanico", "Mechanical Manufacturing Design", SUPERIOR),
        ("mecatronica", "Industrial Mechatronics", SUPERIOR),
        ("ing-mecanica", "Mechanical Engineering", UNIVERSIDAD),
        ("ing-industrial", "Industrial Technologies Engineering", UNIVERSIDAD),
        ("ing-aeroespacial", "Aerospace Engineering", UNIVERSIDAD),
    ],
    "Construction": [
        ("proyectos-edificacion", "Building Projects", SUPERIOR),
        ("proyectos-obra-civil", "Civil Works Projects", SUPERIOR),
        ("arquitectura", "Architecture", UNIVERSIDAD),
        ("ing-civil", "Civil Engineering", UNIVERSIDAD),
    ],
    "Administration and business": [
        ("gestion-admin", "Administrative Management", MEDIO),
        ("admin-finanzas", "Administration and Finance", SUPERIOR),
        ("asistencia-direccion", "Executive Assistance", SUPERIOR),
        ("ade", "Business Administration", UNIVERSIDAD),
        ("economia", "Economics", UNIVERSIDAD),
        ("finanzas-contabilidad", "Finance and Accounting", UNIVERSIDAD),
    ],
    "Commerce and marketing": [
        ("actividades-comerciales", "Commercial Activities", MEDIO),
        ("marketing-publicidad", "Marketing and Advertising", SUPERIOR),
        ("comercio-internacional", "International Trade", SUPERIOR),
        ("gestion-ventas", "Sales and Retail Space Management", SUPERIOR),
        ("marketing", "Marketing and Market Research", UNIVERSIDAD),
    ],
    "Healthcare": [
        ("auxiliar-enfermeria", "Nursing Assistant Care", MEDIO),
        ("farmacia-parafarmacia", "Pharmacy and Parapharmacy", MEDIO),
        ("emergencias", "Medical Emergencies", MEDIO),
        ("laboratorio-clinico", "Clinical and Biomedical Laboratory", SUPERIOR),
        ("imagen-diagnostico", "Diagnostic Imaging and Nuclear Medicine", SUPERIOR),
        ("higiene-bucodental", "Dental Hygiene", SUPERIOR),
        ("dietetica", "Dietetics", SUPERIOR),
        ("medicina", "Medicine", UNIVERSIDAD),
        ("enfermeria", "Nursing", UNIVERSIDAD),
        ("farmacia", "Pharmacy", UNIVERSIDAD),
        ("fisioterapia", "Physiotherapy", UNIVERSIDAD),
    ],
    "Education and social services": [
        ("dependencia", "Care for Dependent People", MEDIO),
        ("educacion-infantil-fp", "Early Childhood Education", SUPERIOR),
        ("integracion-social", "Social Integration", SUPERIOR),
        ("animacion-sociocultural", "Sociocultural and Tourism Activities", SUPERIOR),
        ("magisterio-infantil", "Early Childhood Teaching", UNIVERSIDAD),
        ("magisterio-primaria", "Primary Teaching", UNIVERSIDAD),
        ("pedagogia", "Pedagogy", UNIVERSIDAD),
        ("psicologia", "Psychology", UNIVERSIDAD),
        ("trabajo-social", "Social Work", UNIVERSIDAD),
    ],
    "Image, sound and design": [
        ("video-dj-sonido", "Video, DJ and Sound", MEDIO),
        ("animacion-3d", "3D Animation, Games and Interactive Environments", SUPERIOR),
        ("realizacion", "Audiovisual and Live Show Production", SUPERIOR),
        ("sonido", "Sound for Audiovisuals and Live Shows", SUPERIOR),
        ("comunicacion-audiovisual", "Audiovisual Communication", UNIVERSIDAD),
        ("periodismo", "Journalism", UNIVERSIDAD),
        ("bellas-artes", "Fine Arts", UNIVERSIDAD),
        ("diseno", "Design", UNIVERSIDAD),
    ],
    "Hospitality and tourism": [
        ("cocina", "Cooking and Gastronomy", MEDIO),
        ("servicios-restauracion", "Restaurant Services", MEDIO),
        ("direccion-cocina", "Kitchen Management", SUPERIOR),
        ("alojamientos", "Tourist Accommodation Management", SUPERIOR),
        ("agencias-viajes", "Travel Agencies and Event Management", SUPERIOR),
        ("turismo", "Tourism", UNIVERSIDAD),
        ("gastronomia", "Gastronomic Sciences", UNIVERSIDAD),
    ],
    "Physical activity and sport": [
        ("guia-medio-natural", "Nature and Leisure Guide", MEDIO),
        ("animacion-sociodeportiva", "Sports Teaching and Community Activities", SUPERIOR),
        ("acondicionamiento-fisico", "Physical Conditioning", SUPERIOR),
        ("cafyd", "Physical Activity and Sports Sciences", UNIVERSIDAD),
    ],
    "Sciences": [
        ("quimica-industrial", "Industrial Chemistry", SUPERIOR),
        ("matematicas", "Mathematics", UNIVERSIDAD),
        ("fisica", "Physics", UNIVERSIDAD),
        ("quimica", "Chemistry", UNIVERSIDAD),
        ("biologia", "Biology", UNIVERSIDAD),
        ("biotecnologia", "Biotechnology", UNIVERSIDAD),
    ],
    "Law and humanities": [
        ("derecho", "Law", UNIVERSIDAD),
        ("historia", "History", UNIVERSIDAD),
        ("filologia", "Philology", UNIVERSIDAD),
        ("traduccion", "Translation and Interpreting", UNIVERSIDAD),
    ],
    "Upper Secondary": [
        ("bach-ciencias", "Science and Technology", BACHILLERATO),
        ("bach-sociales", "Humanities and Social Sciences", BACHILLERATO),
        ("bach-artes", "Arts", BACHILLERATO),
        ("bach-general", "General", BACHILLERATO),
    ],
}

# Códigos ya guardados en perfiles: nunca deben cambiar, aunque se traduzca la familia.
_GENERIC_CODES: dict[str, str] = {
    "Computing": "otros-informatica",
    "Electronics and telecommunications": "otros-electronica-y-telecomunicaciones",
    "Industry and mechanics": "otros-industria-y-mecanica",
    "Construction": "otros-construccion",
    "Administration and business": "otros-administracion-y-empresa",
    "Commerce and marketing": "otros-comercio-y-marketing",
    "Healthcare": "otros-sanidad",
    "Education and social services": "otros-educacion-y-servicios-sociales",
    "Image, sound and design": "otros-imagen-sonido-y-diseno",
    "Hospitality and tourism": "otros-hosteleria-y-turismo",
    "Physical activity and sport": "otros-actividad-fisica-y-deporte",
    "Sciences": "otros-ciencias",
    "Law and humanities": "otros-derecho-y-humanidades",
    "Upper Secondary": "otros-bachillerato",
}

STUDIES: dict[str, Study] = {}
for _family, _entries in _CATALOG.items():
    for _code, _name, _level in _entries:
        STUDIES[_code] = Study(_code, _name, _level, _family)
    _generic = _GENERIC_CODES[_family]
    STUDIES[_generic] = Study(_generic, f"Other {_family} studies", OTRO, _family, is_generic=True)
# Sin familia: no se relaciona con nadie, porque no se sabe qué estudia.
STUDIES["otros"] = Study("otros", "Other studies", OTRO, None, is_generic=True)

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
