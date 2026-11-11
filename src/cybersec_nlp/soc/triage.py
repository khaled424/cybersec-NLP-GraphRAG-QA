"""Suggested priority (P1–P4), escalation level and reference playbook for an incident report.

The priority is a transparent **heuristic**: each signal found in the report adds points and is
listed as a reason, so the analyst can confirm or override it. Playbooks follow the phases of
NIST SP 800-61 (containment, eradication, recovery) and must be adapted to internal procedures.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

CRITICAL_TARGETS = {"hospital", "healthcare", "critical infrastructure", "energy sector", "power grid",
                    "industrial control system", "ics", "scada", "government", "water utility", "smart grid"}
IMPACT_VECTORS = {"ransomware", "ddos", "denial of service"}
CREDENTIAL_VECTORS = {"pass-the-hash", "kerberoasting", "golden ticket", "credential stuffing", "password spraying",
                      "brute force", "mimikatz"}
EXPLOIT_VECTORS = {"remote code execution", "rce", "zero-day", "log4shell", "proxylogon", "eternalblue",
                   "printnightmare", "zerologon", "privilege escalation", "sql injection", "command injection"}

# Display names (French SOC vocabulary) of the triage categories (model labels stay in English).
CATEGORY_LABELS = {
    "Malware & Ransomware": "Malware / rançongiciel",
    "Phishing & Social Eng.": "Hameçonnage / ingénierie sociale",
    "Vulnerability & Exploit": "Vulnérabilité / exploitation",
    "Web App Attacks": "Attaque d'application web",
    "Network & Intrusion": "Réseau / intrusion",
    "Identity & Crypto": "Identités / identifiants",
    "Cloud & Governance": "Cloud / conformité",
    "Detection & IR (SOC)": "Détection / réponse à incident",
}


def category_label(category: str) -> str:
    return CATEGORY_LABELS.get(category, category)


PRIORITIES = (  # (minimum score, code, label, response target)
    (7, "P1", "Critique", "prise en charge immédiate, astreinte"),
    (4, "P2", "Élevée", "prise en charge sous 1 h"),
    (2, "P3", "Moyenne", "prise en charge sous 4 h"),
    (0, "P4", "Basse", "traitement en heures ouvrées"),
)
ESCALATION = {"P1": "N3 + CERT / RSSI", "P2": "N2", "P3": "N2", "P4": "N1"}

PLAYBOOKS: dict[str, dict[str, list[str]]] = {
    "Malware & Ransomware": {
        "Confinement": ["Isoler du réseau les postes et serveurs touchés (EDR / VLAN de quarantaine)",
                        "Bloquer les IOC (IP, domaines, empreintes) sur pare-feu, proxy et EDR",
                        "Suspendre les partages et comptes de service utilisés pour la propagation"],
        "Éradication": ["Identifier le vecteur initial et la souche (empreintes, notes de rançon)",
                        "Supprimer les mécanismes de persistance, réinitialiser les identifiants exposés"],
        "Rétablissement": ["Restaurer depuis des sauvegardes saines et vérifiées hors ligne",
                           "Surveillance renforcée des IOC pendant au moins 30 jours"],
    },
    "Phishing & Social Eng.": {
        "Confinement": ["Mettre en quarantaine le message chez tous les destinataires",
                        "Bloquer l'expéditeur, les domaines et URL malveillants (passerelle mail, proxy)"],
        "Éradication": ["Réinitialiser les mots de passe et sessions des utilisateurs ayant cliqué",
                        "Rechercher les règles de transfert et connexions anormales sur les boîtes concernées"],
        "Rétablissement": ["Informer et sensibiliser les destinataires", "Vérifier l'absence d'exfiltration"],
    },
    "Vulnerability & Exploit": {
        "Confinement": ["Restreindre l'exposition du service vulnérable (WAF, filtrage, désactivation temporaire)",
                        "Rechercher des traces d'exploitation dans les journaux applicatifs et système"],
        "Éradication": ["Appliquer le correctif de l'éditeur ou la mesure de contournement officielle",
                        "Inventorier les autres actifs exposés à la même vulnérabilité"],
        "Rétablissement": ["Contrôler la version installée et consigner le résultat dans le ticket",
                           "Ajouter une règle de détection de la tentative d'exploitation"],
    },
    "Web App Attacks": {
        "Confinement": ["Bloquer les sources et motifs d'attaque sur le WAF", "Invalider les sessions suspectes"],
        "Éradication": ["Corriger le code vulnérable (requêtes paramétrées, encodage des sorties)",
                        "Vérifier l'intégrité des données et l'absence de webshell"],
        "Rétablissement": ["Redéployer la version corrigée", "Tests de non-régression de sécurité (DAST)"],
    },
    "Network & Intrusion": {
        "Confinement": ["Bloquer les flux malveillants (pare-feu, IPS), segmenter les zones touchées",
                        "Activer la protection anti-DDoS de l'opérateur si nécessaire"],
        "Éradication": ["Identifier les hôtes compromis et les connexions de commande et contrôle",
                        "Durcir les règles de filtrage et fermer les services inutiles"],
        "Rétablissement": ["Rétablir progressivement les flux", "Surveiller le trafic est-ouest"],
    },
    "Identity & Crypto": {
        "Confinement": ["Désactiver ou réinitialiser les comptes compromis, révoquer jetons et sessions",
                        "Forcer l'authentification multifacteur sur les comptes à privilèges"],
        "Éradication": ["Rechercher les accès réalisés avec les identifiants volés",
                        "Réinitialiser deux fois le compte KRBTGT en cas de Golden Ticket"],
        "Rétablissement": ["Revue des droits et des comptes de service", "Surveillance des authentifications anormales"],
    },
    "Cloud & Governance": {
        "Confinement": ["Restreindre l'accès public aux ressources exposées, révoquer les clés compromises"],
        "Éradication": ["Auditer les politiques IAM et la configuration (CSPM)"],
        "Rétablissement": ["Vérifier les obligations de notification (RGPD : 72 h auprès de la CNIL)",
                           "Mettre à jour les politiques et contrôles de conformité"],
    },
    "Detection & IR (SOC)": {
        "Confinement": ["Qualifier l'alerte et délimiter le périmètre touché"],
        "Éradication": ["Collecter et préserver les preuves (chaîne de custody), analyse forensique"],
        "Rétablissement": ["Retour d'expérience et ajustement des règles de détection"],
    },
}


@dataclass
class Priority:
    code: str
    label: str
    response: str
    escalation: str
    score: int
    reasons: list[str] = field(default_factory=list)


def assess_priority(entities: list[dict], category: str, valid_iocs: int) -> Priority:
    keys = {str(e["key"]).lower() for e in entities}
    labels = {e["label"] for e in entities}
    score, reasons = 0, []

    def add(points: int, reason: str) -> None:
        nonlocal score
        score += points
        reasons.append(f"+{points} · {reason}")

    if keys & IMPACT_VECTORS:
        add(3, "impact sur la disponibilité ou chiffrement (" + ", ".join(sorted(keys & IMPACT_VECTORS)) + ")")
    if "MALWARE" in labels:
        add(2, "famille de malware identifiée")
    if "THREAT_ACTOR" in labels:
        add(2, "acteur de la menace identifié")
    if keys & EXPLOIT_VECTORS or "CVE" in labels:
        add(2, "exploitation de vulnérabilité (CVE ou technique d'exploitation)")
    if keys & CREDENTIAL_VECTORS:
        add(2, "vol ou abus d'identifiants")
    if keys & CRITICAL_TARGETS:
        add(2, "cible critique (" + ", ".join(sorted(keys & CRITICAL_TARGETS)) + ")")
    if valid_iocs:
        add(1, f"{valid_iocs} indicateur(s) de compromission exploitable(s)")
    code, label, response = next((c, lab, r) for minimum, c, lab, r in PRIORITIES if score >= minimum)
    if not reasons:
        reasons.append("aucun signal de gravité détecté")
    return Priority(code, label, response, ESCALATION[code], score, reasons)


# Entities that make a playbook relevant whatever the predicted category (e.g. the triage model
# has no phishing class: too few examples in the corpus).
ENTITY_PLAYBOOKS: tuple[tuple[set[str], str], ...] = (
    ({"phishing", "spear phishing", "social engineering"}, "Phishing & Social Eng."),
    ({"ransomware"}, "Malware & Ransomware"),
    (CREDENTIAL_VECTORS, "Identity & Crypto"),
    ({"sql injection", "xss", "cross-site scripting", "csrf", "ssrf", "xxe", "command injection"}, "Web App Attacks"),
    ({"ddos", "denial of service", "man-in-the-middle", "arp spoofing", "dns spoofing"}, "Network & Intrusion"),
)


def playbooks(category: str, entities: list[dict]) -> list[dict]:
    """Reference playbooks: those triggered by explicit entities first, then the predicted category."""
    keys = {str(e["key"]).lower() for e in entities}
    # Explicit evidence (entities) comes before the weakly supervised category prediction.
    names = [name for trigger, name in ENTITY_PLAYBOOKS if keys & trigger]
    if "MALWARE" in {e["label"] for e in entities}:
        names.insert(0, "Malware & Ransomware")
    names.append(category)
    selected = [n for n in dict.fromkeys(names) if n in PLAYBOOKS] or ["Detection & IR (SOC)"]
    return [{"name": category_label(n), "phases": PLAYBOOKS[n],
             "source": "catégorie prédite" if n == category else "entités du signalement"} for n in selected]


def priority_dict(priority: Priority) -> dict:
    return asdict(priority)
