"""Map ISINs to issuer names for readable chart labels."""

# Known ISIN prefix (6 or 8 chars) to issuer name
ISIN_TO_ISSUER = {
    # Technology
    "US037833": "Apple",
    "US594918": "Microsoft",
    "US023135": "Amazon",
    "US02079K": "Alphabet",
    "US30303M": "Meta",
    "US68389X": "Oracle",
    "US17275R": "Cisco",
    "US458140": "Intel",
    "US459200": "IBM",
    "US79466L": "Salesforce",
    "US00724F": "Adobe",
    "US67066G": "NVIDIA",
    # Financials
    "US46625H": "JPMorgan",
    "US46647P": "JPMorgan",
    "US060505": "Bank of America",
    "US06051G": "Bank of America",
    "US172967": "Citigroup",
    "US949746": "Wells Fargo",
    "US95001A": "Wells Fargo",
    "US38141G": "Goldman Sachs",
    "US617446": "Morgan Stanley",
    "US902973": "US Bancorp",
    "US693475": "PNC Financial",
    "US808513": "Charles Schwab",
    "US025816": "Amex",
    "US084664": "Berkshire",
    "US59156R": "MetLife",
    # Healthcare
    "US478160": "J&J",
    "US91324P": "UnitedHealth",
    "US717081": "Pfizer",
    "US002824": "Abbott Labs",
    "US58933Y": "Merck",
    "US00287Y": "AbbVie",
    "US110122": "Bristol-Myers",
    "US532457": "Eli Lilly",
    "US126650": "CVS Health",
    # Consumer
    "US742718": "P&G",
    "US191216": "Coca-Cola",
    "US713448": "PepsiCo",
    "US931142": "Walmart",
    "US437076": "Home Depot",
    "US654106": "Nike",
    "US580135": "McDonald's",
    "US855244": "Starbucks",
    "US87612E": "Target",
    "US22160K": "Costco",
    # Automotive
    "US345370": "Ford",
    "US37045V": "GM",
    "US88160R": "Tesla",
    # Energy & Utilities
    "US30231G": "Exxon Mobil",
    "US166764": "Chevron",
    "US20825C": "ConocoPhillips",
    "US65339F": "NextEra Energy",
    "US26441C": "Duke Energy",
    "US842587": "Southern Co.",
    "US25746U": "Dominion Energy",
    # Telecom & Media
    "US92343V": "Verizon",
    "US00206R": "AT&T",
    "US872590": "T-Mobile",
    "US20030N": "Comcast",
    "US254687": "Disney",
    "US16117M": "Charter Comm.",
    # Industrials
    "US097023": "Boeing",
    "US149123": "Caterpillar",
    "US88579Y": "3M",
    "US369604": "GE",
    "US438516": "Honeywell",
    "US539830": "Lockheed Martin",
    "US755111": "Raytheon",
    # Government
    "US912810": "US Treasury",
    "US912828": "US Treasury",
    "US91282C": "US Treasury",
}


def extract_issuer_name(isin: str) -> str:
    """Extract readable issuer name from ISIN code.

    Args:
        isin: ISIN code (e.g., "US037833CK68")

    Returns:
        Issuer name (e.g., "Apple") or fallback like "Bond-US0378"
    """
    if not isin or len(isin) < 6:
        return "Unknown"

    # Try 8-character prefix first, then 6
    for length in (8, 6):
        prefix = isin[:length]
        if prefix in ISIN_TO_ISSUER:
            return ISIN_TO_ISSUER[prefix]

    # Fallback: readable short label
    return f"Bond-{isin[:6]}"


def shorten_label(name: str, max_length: int = 15) -> str:
    """Shorten a name for chart axis labels.

    Args:
        name: Full issuer name
        max_length: Maximum character length

    Returns:
        Shortened name
    """
    if len(name) <= max_length:
        return name
    return name[: max_length - 2] + ".."
