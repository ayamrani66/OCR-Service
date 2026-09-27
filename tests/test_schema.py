
from src.schemas.invoice_schema import OcrResult

# Cas 1 
donnees_brutes = {"invoices": [{"document_type": "invoice"}]}
resultat = OcrResult.model_validate(donnees_brutes)
print("=== Cas 1 : données minimalistes ===")
print(resultat.model_dump())
print()

# Cas 2 
donnees_completes = {
    "invoices": [
        {
            "pages": [1, 2],
            "document_type": "invoice",
            "vendor": {"name": "ACME Corp", "address": "12 rue du Test", "tax_number": "IF123456"},
            "client": {"name": "Client SARL", "address": None, "email": None, "tax_number": None},
            "number": "INV-2026-001",
            "issued_at": "2026-09-01",
            "due_at": "2026-10-01",
            "currency": "MAD",
            "line_items": [
                {"description": "Prestation A", "quantity": 2, "unit_price": 150, "tax_rate": 0.20, "total": 300},
            ],
            "sub_total": 300,
            "tax_total": 60,
            "grand_total": 360,
            "raw_text": "ACME Corp - Facture INV-2026-001 ...",
        }
    ]
}
resultat2 = OcrResult.model_validate(donnees_completes)
print("=== Cas 2 : données complètes ===")
print(resultat2.model_dump())
print()

# Cas 3
print("=== Cas 3 : donnée invalide (quantity = texte au lieu de nombre) ===")
try:
    OcrResult.model_validate({"invoices": [{"line_items": [{"quantity": "pas-un-nombre"}]}]})
except Exception as e:
    print("Erreur attendue, Pydantic a bien détecté le problème :")
    print(e)