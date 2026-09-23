"""Tests de génération PDF (V0.8) : structure, nombre de pages, gestion du cas vide."""
import os
import sys
import json
import io
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pypdf import PdfReader

from services.pdf_service import generate_full_report, generate_service_report
from services.statistics import compute_kpis
from services.quality import quality_report

FIXTURE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "sample_services.json")
SETTINGS = {"application_name": "MIRSAAD", "application_name_ar": "مرصاد", "organisation_name": "Organisation Test"}


def load_services():
    with open(FIXTURE_FILE, encoding="utf-8") as f:
        return json.load(f)["services"]


def test_full_report_page_count_matches_cover_plus_synthesis_plus_services():
    services = load_services()
    kpis = compute_kpis(services)
    quality = quality_report(services)
    pdf_bytes = generate_full_report(services, kpis, quality, SETTINGS)

    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 2 + len(services)  # couverture + synthèse + 1 page par service


def test_full_report_each_service_fits_on_one_page():
    """Non-régression : un bandeau + cartes mal dimensionnés peuvent faire déborder une fiche sur 2 pages."""
    services = load_services()
    kpis = compute_kpis(services)
    quality = quality_report(services)
    pdf_bytes = generate_full_report(services, kpis, quality, SETTINGS)

    reader = PdfReader(io.BytesIO(pdf_bytes))
    # Vérifie qu'aucune page "orpheline" ne répète le nom d'un service déjà vu (signe de débordement)
    seen_names = set()
    for page in reader.pages[2:]:
        text = page.extract_text()
        first_line = text.strip().split("\n")[0] if text.strip() else ""
        assert first_line not in seen_names, f"Le service '{first_line}' semble déborder sur plusieurs pages"
        seen_names.add(first_line)


def test_full_report_empty_portfolio_does_not_crash():
    kpis = compute_kpis([])
    quality = quality_report([])
    pdf_bytes = generate_full_report([], kpis, quality, SETTINGS)

    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 2  # couverture + synthèse uniquement


def test_full_report_contains_organisation_name():
    services = load_services()
    kpis = compute_kpis(services)
    quality = quality_report(services)
    pdf_bytes = generate_full_report(services, kpis, quality, SETTINGS)

    reader = PdfReader(io.BytesIO(pdf_bytes))
    cover_text = reader.pages[0].extract_text()
    assert "Organisation Test" in cover_text


def test_full_report_footer_has_page_numbers():
    services = load_services()[:2]
    kpis = compute_kpis(services)
    quality = quality_report(services)
    pdf_bytes = generate_full_report(services, kpis, quality, SETTINGS)

    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = reader.pages[0].extract_text()
    assert "Page 1 / 4" in text.replace("\n", " ") or "1 / 4" in text


def test_service_report_is_single_page():
    services = load_services()
    pdf_bytes = generate_service_report(services[0], SETTINGS)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 1


def test_service_report_contains_service_name():
    services = load_services()
    svc = next(s for s in services if s["id"] == "APP-T01")
    pdf_bytes = generate_service_report(svc, SETTINGS)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = reader.pages[0].extract_text()
    assert "Portail" in text  # "Démo" peut être coupé par l'extraction de texte bidi


def test_service_report_handles_all_null_fields():
    """Un service très incomplet (comme APP-T05 du fixture) ne doit jamais faire planter la génération."""
    services = load_services()
    svc = next(s for s in services if s["id"] == "APP-T05")
    pdf_bytes = generate_service_report(svc, SETTINGS)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 1


# ---------- Personnalisation page de garde / pied de page ----------

def test_cover_texte_mode_hides_application_name():
    services = load_services()[:1]
    kpis = compute_kpis(services)
    quality = quality_report(services)
    settings = {**SETTINGS, "pdf_cover_mode": "texte", "pdf_custom_text": "Portefeuille de Services"}
    pdf_bytes = generate_full_report(services, kpis, quality, settings)

    reader = PdfReader(io.BytesIO(pdf_bytes))
    cover_text = reader.pages[0].extract_text()
    assert "MIRSAAD" not in cover_text
    assert "Portefeuille de Services" in cover_text
    assert "Organisation Test" in cover_text


def test_cover_logo_mode_shows_application_name():
    services = load_services()[:1]
    kpis = compute_kpis(services)
    quality = quality_report(services)
    settings = {**SETTINGS, "pdf_cover_mode": "logo"}
    pdf_bytes = generate_full_report(services, kpis, quality, settings)

    reader = PdfReader(io.BytesIO(pdf_bytes))
    cover_text = reader.pages[0].extract_text()
    assert "MIRSAAD" in cover_text


def test_footer_vide_mode_has_no_label_left():
    services = load_services()[:1]
    kpis = compute_kpis(services)
    quality = quality_report(services)
    settings = {**SETTINGS, "pdf_footer_mode": "vide"}
    pdf_bytes = generate_full_report(services, kpis, quality, settings)

    reader = PdfReader(io.BytesIO(pdf_bytes))
    footer_text = reader.pages[0].extract_text()
    assert "MIRSAAD" not in footer_text.split("\n")[-1]  # dernière ligne = pied de page


def test_footer_personnalise_mode_shows_custom_text_and_org():
    services = load_services()[:1]
    kpis = compute_kpis(services)
    quality = quality_report(services)
    settings = {**SETTINGS, "pdf_footer_mode": "personnalise", "pdf_custom_text": "Portefeuille de Services"}
    pdf_bytes = generate_full_report(services, kpis, quality, settings)

    reader = PdfReader(io.BytesIO(pdf_bytes))
    footer_text = reader.pages[0].extract_text()
    assert "Portefeuille de Services" in footer_text
    assert "Organisation Test" in footer_text


def test_footer_always_shows_page_number_and_date():
    services = load_services()[:1]
    kpis = compute_kpis(services)
    quality = quality_report(services)
    for footer_mode in ("vide", "personnalise"):
        settings = {**SETTINGS, "pdf_footer_mode": footer_mode}
        pdf_bytes = generate_full_report(services, kpis, quality, settings)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        footer_text = reader.pages[0].extract_text().replace("\n", " ")
        assert "Page 1" in footer_text
        today = datetime.now().strftime("%d/%m/%Y")
        assert today in footer_text


def test_cover_and_footer_custom_text_with_special_characters_do_not_break_pdf():
    """Guillemets/antislash dans le texte personnalisé ne doivent pas casser le CSS généré."""
    services = load_services()[:1]
    kpis = compute_kpis(services)
    quality = quality_report(services)
    settings = {
        **SETTINGS,
        "pdf_cover_mode": "texte",
        "pdf_footer_mode": "personnalise",
        "pdf_custom_text": 'Portefeuille "spécial" \\ test',
    }
    pdf_bytes = generate_full_report(services, kpis, quality, settings)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) >= 1
