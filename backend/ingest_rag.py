"""
Run once before starting backend: python ingest_rag.py
Populates ChromaDB with PMFBY, PMKSY, PM KUSUM, PKVY knowledge.
"""
import chromadb
from chromadb.utils import embedding_functions

DOCUMENTS = [
    {"id": "pmfby_claim", "text": """
PMFBY Claim Process: Intimate loss within 72 hours to bank/insurance company.
Fill Form 4A with farmer name, village, survey number, crop, loss extent.
Claim = (1 - Actual Yield/Threshold Yield) x Sum Insured x Insured Area.
Claim settled via DBT within 60 days of Crop Cutting Experiment data.
If delayed beyond 60 days, farmer entitled to 12% interest per annum.
Grievance: District Grievance Cell → State Committee → CPGRAMS → IRDAI Ombudsman.
Documents: Land record (7-12 extract), bank passbook, sowing certificate, loss intimation receipt.
    """, "metadata": {"scheme": "PMFBY"}},
    {"id": "pmfby_rights", "text": """
PMFBY Farmer Rights: Right to claim settlement within 60 days.
Right to 12% annual interest if claim delayed. Right to surveyor visit within 10 days.
Consumer Forum: District (up to ₹20L), State (₹20L-1Cr), National (above ₹1Cr).
IRDAI Ombudsman: Free, disputes up to ₹30 lakh, resolution 3-6 months.
RTI: Farmer can demand Crop Cutting Experiment video footage under RTI Act.
Common challenge: Wrong crop entry by bank is bank's liability, not farmer's.
    """, "metadata": {"scheme": "PMFBY"}},
    {"id": "pmksy_drip", "text": """
PMKSY Drip Irrigation Subsidy: 55% for general farmers, 90% for small/marginal.
Water saving: 40-70% vs flood irrigation. Yield increase: 20-50%.
Application via pmksy.gov.in or state agriculture department.
Equipment retained for 5 years mandatory.
Compatible with PM KUSUM solar pumps for zero-cost irrigation.
    """, "metadata": {"scheme": "PMKSY"}},
    {"id": "pm_kusum_solar", "text": """
PM KUSUM Component B: 60% Central + 30% State = 90% subsidy on solar pumps.
Farmer pays 10%. 7.5 HP pump costs ~₹3.5 lakh; farmer pays ~₹35,000.
Annual saving: ₹35,000-80,000 in electricity/diesel costs.
Excess solar power sold to DISCOM at ₹3-5/unit (extra income).
Portal: mnre.gov.in/pm-kusum | Apply via state DISCOM or agriculture dept.
    """, "metadata": {"scheme": "PM KUSUM"}},
    {"id": "pkvy_organic", "text": """
PKVY Organic Farming: ₹50,000/hectare over 3 years.
Requires group of 50+ farmers, 50+ contiguous acres.
PGS-India certification provided free after 1 year internal audit.
Organic premium in market: 15-50% higher than conventional produce.
Reduces input costs by ₹5,000-15,000/acre (no chemical fertilizers/pesticides).
Apply via KVK (Krishi Vigyan Kendra) or pgsindia-ncof.gov.in.
    """, "metadata": {"scheme": "PKVY"}},
    {"id": "crop_transition", "text": """
Crop Transition Guide for Water Stress Regions:
Rice → Maize: 50% water saving, similar income, 90-120 days shorter cycle.
Rice → Tur/Pulses: 60-70% water saving, nitrogen fixation saves ₹2,000-3,000/acre next season.
Cotton → Soybean: Lower water, MSP secured, oil demand strong.
Season 1: Partial shift (50% acreage) to maintain income security.
Season 2: Drip irrigation with PMKSY + solar pump with PM KUSUM.
Season 3: Full transition + PKVY organic certification if cluster possible.
    """, "metadata": {"scheme": "KrishiShift"}},
]


def ingest():
    print("🌾 Kavach AI — Ingesting RAG knowledge base...")
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path="./chroma_db")
    try:
        client.delete_collection("kavach_schemes")
    except Exception:
        pass
    collection = client.create_collection("kavach_schemes", embedding_function=ef)
    collection.add(
        documents=[d["text"].strip() for d in DOCUMENTS],
        ids=[d["id"] for d in DOCUMENTS],
        metadatas=[d["metadata"] for d in DOCUMENTS],
    )
    print(f"✅ Ingested {len(DOCUMENTS)} documents.")
    results = collection.query(query_texts=["PMFBY claim settlement deadline"], n_results=1)
    print(f"✅ Test query → {results['ids'][0][0]}")
    print("✅ RAG ready.")


if __name__ == "__main__":
    ingest()