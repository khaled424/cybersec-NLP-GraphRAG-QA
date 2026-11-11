"""MITRE ATT&CK (Enterprise) references for entities recognised by the cyber NER.

Only unambiguous, well-established mappings are listed: an analyst must be able to trust the
link. Entities without an entry are simply shown without ATT&CK reference.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

ATTACK_URL = "https://attack.mitre.org"


@dataclass(frozen=True)
class AttackRef:
    attack_id: str  # T1566, T1558.003, S0002, G0016
    name: str
    kind: str  # technique | software | group
    tactic: str = ""

    @property
    def url(self) -> str:
        if self.kind == "technique":
            return f"{ATTACK_URL}/techniques/{self.attack_id.replace('.', '/')}/"
        return f"{ATTACK_URL}/{'software' if self.kind == 'software' else 'groups'}/{self.attack_id}/"

    def to_dict(self) -> dict[str, str]:
        return {**asdict(self), "url": self.url}


def _t(attack_id: str, name: str, tactic: str) -> AttackRef:
    return AttackRef(attack_id, name, "technique", tactic)


# NER canonical key -> ATT&CK technique (attack vectors and tools)
TECHNIQUES: dict[str, AttackRef] = {
    "phishing": _t("T1566", "Phishing", "Accès initial"),
    "spear phishing": _t("T1566", "Phishing", "Accès initial"),
    "sql injection": _t("T1190", "Exploit Public-Facing Application", "Accès initial"),
    "command injection": _t("T1190", "Exploit Public-Facing Application", "Accès initial"),
    "remote code execution": _t("T1190", "Exploit Public-Facing Application", "Accès initial"),
    "rce": _t("T1190", "Exploit Public-Facing Application", "Accès initial"),
    "deserialization": _t("T1190", "Exploit Public-Facing Application", "Accès initial"),
    "log4shell": _t("T1190", "Exploit Public-Facing Application", "Accès initial"),
    "proxylogon": _t("T1190", "Exploit Public-Facing Application", "Accès initial"),
    "supply chain attack": _t("T1195", "Supply Chain Compromise", "Accès initial"),
    "drive-by download": _t("T1189", "Drive-by Compromise", "Accès initial"),
    "watering hole": _t("T1189", "Drive-by Compromise", "Accès initial"),
    "brute force": _t("T1110", "Brute Force", "Accès aux identifiants"),
    "password spraying": _t("T1110.003", "Brute Force: Password Spraying", "Accès aux identifiants"),
    "credential stuffing": _t("T1110.004", "Brute Force: Credential Stuffing", "Accès aux identifiants"),
    "kerberoasting": _t("T1558.003", "Steal or Forge Kerberos Tickets: Kerberoasting", "Accès aux identifiants"),
    "golden ticket": _t("T1558.001", "Steal or Forge Kerberos Tickets: Golden Ticket", "Accès aux identifiants"),
    "man-in-the-middle": _t("T1557", "Adversary-in-the-Middle", "Accès aux identifiants"),
    "arp spoofing": _t("T1557.002", "Adversary-in-the-Middle: ARP Cache Poisoning", "Accès aux identifiants"),
    "privilege escalation": _t("T1068", "Exploitation for Privilege Escalation", "Élévation de privilèges"),
    "printnightmare": _t("T1068", "Exploitation for Privilege Escalation", "Élévation de privilèges"),
    "dll hijacking": _t("T1574.001", "Hijack Execution Flow: DLL", "Persistance"),
    "pass-the-hash": _t("T1550.002", "Use Alternate Authentication Material: Pass the Hash", "Mouvement latéral"),
    "lateral movement": _t("T1021", "Remote Services", "Mouvement latéral"),
    "eternalblue": _t("T1210", "Exploitation of Remote Services", "Mouvement latéral"),
    "zerologon": _t("T1210", "Exploitation of Remote Services", "Mouvement latéral"),
    "ransomware": _t("T1486", "Data Encrypted for Impact", "Impact"),
    "ddos": _t("T1498", "Network Denial of Service", "Impact"),
    "denial of service": _t("T1498", "Network Denial of Service", "Impact"),
    "typosquatting": _t("T1583.001", "Acquire Infrastructure: Domains", "Développement de ressources"),
    "malvertising": _t("T1583.008", "Acquire Infrastructure: Malvertising", "Développement de ressources"),
    # tools -> technique they are typically used for
    "mimikatz": _t("T1003.001", "OS Credential Dumping: LSASS Memory", "Accès aux identifiants"),
    "psexec": _t("T1569.002", "System Services: Service Execution", "Exécution"),
    "responder": _t("T1557.001", "Adversary-in-the-Middle: LLMNR/NBT-NS Poisoning", "Accès aux identifiants"),
    "nmap": _t("T1046", "Network Service Discovery", "Découverte"),
    "hashcat": _t("T1110.002", "Brute Force: Password Cracking", "Accès aux identifiants"),
    "john the ripper": _t("T1110.002", "Brute Force: Password Cracking", "Accès aux identifiants"),
    "hydra": _t("T1110", "Brute Force", "Accès aux identifiants"),
    "bloodhound": _t("T1087.002", "Account Discovery: Domain Account", "Découverte"),
}

SOFTWARE: dict[str, AttackRef] = {k: AttackRef(i, n, "software") for k, (i, n) in {
    "mimikatz": ("S0002", "Mimikatz"), "cobalt strike": ("S0154", "Cobalt Strike"), "psexec": ("S0029", "PsExec"),
    "bloodhound": ("S0521", "BloodHound"), "impacket": ("S0357", "Impacket"), "responder": ("S0174", "Responder"),
    "emotet": ("S0367", "Emotet"), "trickbot": ("S0266", "TrickBot"), "wannacry": ("S0366", "WannaCry"),
    "notpetya": ("S0368", "NotPetya"), "ryuk": ("S0446", "Ryuk"), "conti": ("S0575", "Conti"),
    "qakbot": ("S0650", "QakBot"), "revil": ("S0496", "REvil"), "dridex": ("S0384", "Dridex"),
    "stuxnet": ("S0603", "Stuxnet"), "agent tesla": ("S0331", "Agent Tesla"), "njrat": ("S0385", "njRAT"),
    "carbanak": ("S0030", "Carbanak"), "icedid": ("S0483", "IcedID"), "sunburst": ("S0559", "SUNBURST"),
    "blackenergy": ("S0089", "BlackEnergy"), "shamoon": ("S0140", "Shamoon"), "industroyer": ("S0604", "Industroyer"),
    "olympic destroyer": ("S0365", "Olympic Destroyer"), "plugx": ("S0013", "PlugX"), "gh0st": ("S0032", "gh0st RAT"),
    "duqu": ("S0038", "Duqu"), "flame": ("S0143", "Flame"), "lokibot": ("S0447", "LokiBot"), "maze": ("S0449", "Maze"),
    "bad rabbit": ("S0606", "Bad Rabbit"),
}.items()}

GROUPS: dict[str, AttackRef] = {k: AttackRef(i, n, "group") for k, (i, n) in {
    "apt28": ("G0007", "APT28"), "fancy bear": ("G0007", "APT28"), "apt29": ("G0016", "APT29"),
    "cozy bear": ("G0016", "APT29"), "apt41": ("G0096", "APT41"), "lazarus": ("G0032", "Lazarus Group"),
    "sandworm": ("G0034", "Sandworm Team"), "fin7": ("G0046", "FIN7"), "turla": ("G0010", "Turla"),
    "scattered spider": ("G1015", "Scattered Spider"), "equation group": ("G0020", "Equation"),
    "kimsuky": ("G0094", "Kimsuky"), "apt1": ("G0006", "APT1"), "apt3": ("G0022", "APT3"), "apt10": ("G0045", "menuPass"),
    "apt33": ("G0064", "APT33"), "wizard spider": ("G0102", "Wizard Spider"), "lapsus$": ("G1004", "LAPSUS$"),
    "charming kitten": ("G0059", "Magic Hound"),
}.items()}


def attack_references(entities: list[dict]) -> list[dict[str, str]]:
    """Unique ATT&CK references (techniques, then software, then groups) for NER entities."""
    refs: dict[str, AttackRef] = {}
    for entity in entities:
        key, label = str(entity["key"]).lower(), entity["label"]
        if label == "ATTACK_ID":
            refs.setdefault(entity["key"], _t(entity["key"], "Technique citée dans le signalement", ""))
        for table in (TECHNIQUES, SOFTWARE, GROUPS):
            ref = table.get(key)
            if ref:
                refs.setdefault(ref.attack_id, ref)
    order = {"technique": 0, "software": 1, "group": 2}
    return [r.to_dict() for r in sorted(refs.values(), key=lambda r: (order[r.kind], r.attack_id))]
