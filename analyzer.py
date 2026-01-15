import re

class RuleExtractor:
    def __init__(self, text):
        self.text = text

    def extract_critical_rules(self):
        """
        Extracts top 3 critical rules: Passport Validity, Photos, Biometrics.
        """
        rules = []
        
        # Passport Validity
        passport_match = re.search(r"(pasaport|travel document).*?(en az|geçerli).*?(\d+\s*ay|\d+\s*yıl)", self.text, re.IGNORECASE)
        if passport_match:
            rules.append(f"⚠️ Pasaport Geçerliliği: {passport_match.group(0)}")
        else:
            rules.append("⚠️ Pasaport Geçerliliği: En az 6 ay önerilir (Dokümanda bulunamadı)")

        # Photos
        photo_match = re.search(r"(biyometrik|fotoğraf).*?(\d\.\d\s*x\s*\d\.\d|\d\s*x\s*\d)", self.text, re.IGNORECASE)
        if photo_match:
            rules.append(f"📸 Fotoğraf: {photo_match.group(0)}")
        
        # Biometrics hint (simple check)
        if "parmak izi" in self.text.lower() or "biyometri" in self.text.lower():
            rules.append("Fingerprint: Son 59 ayda verilmemişse şahsen başvuru gerekir.")

        # Cap at 3
        while len(rules) < 3:
            rules.append("Ek kural bulunamadı.")
            
        return rules[:3]

    def extract_fees(self):
        """
        Extracts visa fees.
        """
        # Look for currency amounts near keywords
        fees = []
        matches = re.findall(r"(vize|harç|ücret).*?(\d{2,3})\s*(€|EUR|TL|USD|\$)", self.text, re.IGNORECASE)
        for m in matches:
            fees.append(f"{m[1]} {m[2]}")
        
        return list(set(fees)) if fees else ["Belirtilmemiş"]

    def extract_insurance_limit(self):
        """
        Extracts insurance coverage requirement.
        """
        match = re.search(r"(sigorta|teminat).*?(\d{2,3}[\.,]?\d{0,3})\s*(€|EUR|Euro)", self.text, re.IGNORECASE)
        if match:
            return f"{match.group(2)} {match.group(3)}"
        return "30.000 € (Standart)"

    def analyze_checklist_items(self):
        """
        Attempts to list potential checklist items by looking for bullet points or numbered lists.
        """
        items = []
        # Simple heuristic: lines starting with -, *, 1., or specific keywords
        lines = self.text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) < 5 or "sayfa" in line.lower(): 
                continue # Skip short rubbish
            
            # Pattern for list items
            if re.match(r"^(\d+\.|-|\*|•)\s+", line):
                clean_line = re.sub(r"^(\d+\.|-|\*|•)\s+", "", line)
                items.append(clean_line)
            # Fallback for document names
            elif any(x in line.lower() for x in ["belge", "form", "dilekçe", "bordro", "banka", "rezervasyon", "sigorta"]):
                items.append(line)
                
        return items if items else ["Otomatik liste çıkarılamadı. Lütfen metni kontrol edin."]

    def get_upsell_opportunities(self):
        """
        Returns flags for upsell.
        """
        upsells = {
            "insurance": False,
            "flight_hotel": False,
            "vip": False
        }
        
        lower_text = self.text.lower()
        
        if "sigorta" in lower_text or "teminat" in lower_text:
            upsells["insurance"] = True
            
        if any(x in lower_text for x in ["uçak", "otel", "konaklama", "rezervasyon", "bilet"]):
            upsells["flight_hotel"] = True
            
        if "vip" in lower_text or "eksper" in lower_text:
            upsells["vip"] = True
            
        return upsells
