"""Rule-based cyber NER (regex + curated gazetteers) aligned with STIX 2.1 object types.

Labels and their STIX 2.1 counterpart:

==============  =========================  =========================================
Label           STIX type                  Detection
==============  =========================  =========================================
IP              ipv4-addr                  regex + ``ipaddress`` validation
CVE             vulnerability              ``CVE-YYYY-NNNN+``
ATTACK_ID       attack-pattern (ATT&CK)    ``T1234`` / ``T1234.001``
HASH            file:hashes                hex of length 32/40/64
MALWARE         malware                    gazetteer of named families
TOOL            tool                       gazetteer of offensive/defensive tools
THREAT_ACTOR    threat-actor               gazetteer
SOFTWARE        software                   gazetteer of products/protocols
VECTOR          attack-pattern (name)      gazetteer of attack techniques
TARGET          identity (sector)          gazetteer of targeted sectors
==============  =========================  =========================================

The extractor returns character spans so it can also produce *silver* BIO labels to
fine-tune a BERT/SecBERT token classifier (Notebook 1).
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import asdict, dataclass

GAZETTEER: dict[str, tuple[str, ...]] = {
    "MALWARE": (
        "emotet", "wannacry", "notpetya", "lockbit", "conti", "ryuk", "trickbot", "stuxnet",
        "qakbot", "qbot", "revil", "mirai", "agent tesla", "njrat", "redline", "zeus", "dridex",
        "cobalt strike", "petya", "blackcat", "darkside", "maze", "sodinokibi", "icedid",
        "lokibot", "formbook", "gh0st", "plugx", "shamoon", "triton", "industroyer", "olympic destroyer",
        "pegasus", "flame", "duqu", "carbanak", "wellmess", "sunburst", "blackenergy", "bad rabbit",
    ),
    "TOOL": (
        "mimikatz", "metasploit", "bloodhound", "nmap", "sliver", "wireshark", "burp suite",
        "nessus", "shodan", "sqlmap", "hydra", "hashcat", "john the ripper", "psexec", "impacket",
        "responder", "powersploit", "empire", "netcat", "tcpdump", "nikto", "aircrack-ng",
        "ghidra", "ida pro", "volatility", "yara", "snort", "suricata", "zeek", "osquery",
    ),
    "THREAT_ACTOR": (
        "apt28", "apt29", "apt41", "apt1", "apt3", "apt10", "apt33", "lazarus", "sandworm",
        "fin7", "turla", "fancy bear", "cozy bear", "scattered spider", "equation group",
        "kimsuky", "charming kitten", "lapsus$", "wizard spider", "evil corp",
    ),
    "SOFTWARE": (
        "windows", "linux", "macos", "android", "ios", "active directory", "exchange", "sharepoint",
        "office 365", "microsoft 365", "apache", "nginx", "tomcat", "wordpress", "mysql",
        "postgresql", "mongodb", "redis", "oracle", "vmware", "cisco", "fortinet", "palo alto",
        "citrix", "chrome", "firefox", "java", "php", "log4j", "struts", "openssl", "docker",
        "kubernetes", "jenkins", "gitlab", "splunk", "elasticsearch", "powershell", "openssh",
        "sql server", "iis", "outlook", "bash", "node.js", "spring", "confluence", "jira",
        "sap", "aws", "azure", "gcp", "okta", "kerberos", "ntlm", "ldap", "rdp", "smb", "ssh",
        "dns", "tls", "ssl", "http", "bluetooth", "wi-fi", "vpn",
    ),
    "VECTOR": (
        "sql injection", "cross-site scripting", "xss", "csrf", "ssrf", "xxe", "phishing",
        "spear phishing", "buffer overflow", "ddos", "denial of service", "man-in-the-middle",
        "privilege escalation", "lateral movement", "brute force", "credential stuffing",
        "password spraying", "social engineering", "command injection", "directory traversal",
        "path traversal", "deserialization", "remote code execution", "rce", "zero-day",
        "ransomware", "supply chain attack", "watering hole", "drive-by download",
        "dll hijacking", "pass-the-hash", "kerberoasting", "golden ticket", "session hijacking",
        "clickjacking", "dns spoofing", "arp spoofing", "typosquatting", "malvertising",
        "side-channel", "rowhammer", "spectre", "meltdown", "heartbleed", "log4shell",
        "eternalblue", "printnightmare", "zerologon", "proxylogon", "shellshock",
    ),
    "TARGET": (
        "healthcare", "hospital", "financial sector", "bank", "banking", "government",
        "energy sector", "critical infrastructure", "power grid", "telecommunications",
        "retail", "university", "manufacturing", "industrial control system",
        "ics", "scada", "military", "e-commerce", "pharmaceutical",
        "transportation", "aviation", "water utility", "smart grid", "iot devices",
    ),
}

# French (and alternative) surface forms mapped to the canonical English gazetteer entry, so a
# question asked in French links to the same graph node as the English corpus.
ALIASES: dict[str, tuple[str, str]] = {
    "injection sql": ("VECTOR", "sql injection"), "injections sql": ("VECTOR", "sql injection"),
    "hameçonnage": ("VECTOR", "phishing"), "rançongiciel": ("VECTOR", "ransomware"),
    "rançongiciels": ("VECTOR", "ransomware"), "déni de service": ("VECTOR", "denial of service"),
    "élévation de privilèges": ("VECTOR", "privilege escalation"),
    "escalade de privilèges": ("VECTOR", "privilege escalation"),
    "mouvement latéral": ("VECTOR", "lateral movement"), "mouvements latéraux": ("VECTOR", "lateral movement"),
    "force brute": ("VECTOR", "brute force"), "ingénierie sociale": ("VECTOR", "social engineering"),
    "exécution de code à distance": ("VECTOR", "remote code execution"),
    "chaîne d'approvisionnement": ("VECTOR", "supply chain attack"),
    "hôpital": ("TARGET", "hospital"), "hôpitaux": ("TARGET", "hospital"), "santé": ("TARGET", "healthcare"),
    "banque": ("TARGET", "bank"), "banques": ("TARGET", "bank"), "gouvernement": ("TARGET", "government"),
    "secteur bancaire": ("TARGET", "banking"), "bancaire": ("TARGET", "banking"),
    "secteur financier": ("TARGET", "financial sector"), "secteur de la santé": ("TARGET", "healthcare"),
    "infrastructure critique": ("TARGET", "critical infrastructure"),
    "infrastructures critiques": ("TARGET", "critical infrastructure"),
}

# Higher value wins when two spans overlap with the same length.
_PRIORITY = {
    "CVE": 9, "IP": 9, "HASH": 9, "ATTACK_ID": 9, "THREAT_ACTOR": 8, "MALWARE": 7, "TOOL": 6,
    "VECTOR": 5, "TARGET": 4, "SOFTWARE": 3,
}
_REGEXES = {
    "CVE": re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE),
    "IP": re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?!\w|\.\d)"),
    "ATTACK_ID": re.compile(r"\bT1\d{3}(?:\.\d{3})?\b"),
    "HASH": re.compile(r"\b(?:[a-fA-F0-9]{64}|[a-fA-F0-9]{40}|[a-fA-F0-9]{32})\b"),
}
LABELS = tuple(_PRIORITY)


@dataclass(frozen=True)
class Entity:
    text: str
    label: str
    start: int
    end: int
    canonical: str | None = None  # gazetteer entry when the surface form differs (plural, alias)

    @property
    def key(self) -> str:
        """Canonical identifier used as graph node name (CVE upper-case, others lower-case)."""
        if self.label in ("CVE", "ATTACK_ID"):
            return self.text.upper()
        if self.label == "IP":
            return self.text
        if self.canonical:
            return self.canonical
        lowered = self.text.lower()
        alias = ALIASES.get(lowered)
        return alias[1] if alias else lowered

    def to_dict(self) -> dict[str, object]:
        data = {**asdict(self), "key": self.key}
        data.pop("canonical")
        return data


def _gazetteer_regex(terms: tuple[str, ...]) -> re.Pattern[str]:
    """Whole-term match, allowing a plural ``s``/``es`` (``hospitals`` -> ``hospital``)."""
    alternatives = sorted({re.escape(t) for t in terms}, key=len, reverse=True)
    return re.compile(r"(?<![\w-])(?:" + "|".join(alternatives) + r")(?:e?s)?(?![\w-])", re.IGNORECASE)


def _singular(surface: str, terms: set[str]) -> str | None:
    """Gazetteer entry for a matched surface form, or ``None`` if the surface is the entry itself."""
    lowered = surface.lower()
    if lowered in terms or lowered in ALIASES:
        return None
    for suffix in ("es", "s"):
        if lowered.endswith(suffix) and lowered[: -len(suffix)] in terms:
            return lowered[: -len(suffix)]
    return None


class CyberNER:
    """Deterministic span extractor; ``labels`` restricts the entity types returned."""

    def __init__(self, gazetteer: dict[str, tuple[str, ...]] | None = None, labels: tuple[str, ...] = LABELS):
        self.labels = labels
        terms_by_label = {label: list(terms) for label, terms in (gazetteer or GAZETTEER).items()}
        for alias, (label, _) in ALIASES.items():
            terms_by_label.setdefault(label, []).append(alias)
        self._gazetteer = {label: _gazetteer_regex(tuple(terms)) for label, terms in terms_by_label.items() if terms}
        self._terms = {t.lower() for terms in terms_by_label.values() for t in terms}

    def extract(self, text: str) -> list[Entity]:
        candidates: list[Entity] = []
        for label, pattern in _REGEXES.items():
            for match in pattern.finditer(text):
                if label == "IP" and not _valid_ip(match.group(0)):
                    continue
                candidates.append(Entity(match.group(0), label, match.start(), match.end()))
        for label, pattern in self._gazetteer.items():
            for m in pattern.finditer(text):
                singular = _singular(m.group(0), self._terms)
                if singular is None and m.group(0).lower() not in self._terms and m.group(0).lower() not in ALIASES:
                    continue  # e.g. "iis" matched as "ii"+"s": not a real plural of an entry
                canonical = ALIASES[singular][1] if singular in ALIASES else singular
                candidates.append(Entity(m.group(0), label, m.start(), m.end(), canonical))
        return [e for e in _resolve_overlaps(candidates) if e.label in self.labels]

    def extract_keys(self, text: str) -> set[tuple[str, str]]:
        """Unique ``(key, label)`` pairs, convenient for graph construction and indexing."""
        return {(e.key, e.label) for e in self.extract(text)}

    def bio_tags(self, tokens: list[tuple[int, int]], text: str) -> list[str]:
        """Silver BIO tags for pre-tokenised offsets (used to fine-tune a token classifier)."""
        tags = ["O"] * len(tokens)
        for entity in self.extract(text):
            inside = [i for i, (s, e) in enumerate(tokens) if s >= entity.start and e <= entity.end and e > s]
            for rank, i in enumerate(inside):
                tags[i] = ("B-" if rank == 0 else "I-") + entity.label
        return tags


def _valid_ip(value: str) -> bool:
    """Valid IPv4 that does not look like a version or section number (all octets < 10, e.g. 3.6.5.2)."""
    try:
        ipaddress.IPv4Address(value)
    except ValueError:
        return False
    return not all(int(octet) < 10 for octet in value.split("."))


def _resolve_overlaps(candidates: list[Entity]) -> list[Entity]:
    """Keep the longest span, then the highest-priority label, among overlapping candidates."""
    ordered = sorted(candidates, key=lambda e: (-(e.end - e.start), -_PRIORITY[e.label], e.start))
    kept: list[Entity] = []
    for entity in ordered:
        if all(entity.end <= k.start or entity.start >= k.end for k in kept):
            kept.append(entity)
    return sorted(kept, key=lambda e: e.start)
