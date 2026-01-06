import streamlit as st
import requests
from Bio import Entrez
import json
from datetime import datetime
import google.generativeai as genai
from scholarly import scholarly
import PyPDF2
import io
import tempfile

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="Academic Research Assistant",
    layout="wide",
    page_icon="🎓",
    initial_sidebar_state="expanded"
)

# --- STYLING ---
st.markdown("""
<style>
    .stApp {
        background-color: #0E0E0E;
        color: #E0E0E0;
    }
    .paper-card {
        background: rgba(30, 30, 30, 0.8);
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #00d9ff;
        margin: 10px 0;
    }
    .citation-box {
        background: rgba(0, 217, 255, 0.1);
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #00d9ff;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'papers' not in st.session_state:
    st.session_state.papers = []
if 'selected_papers' not in st.session_state:
    st.session_state.selected_papers = []
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = ""
if 'pdf_texts' not in st.session_state:
    st.session_state.pdf_texts = {}  # Store extracted PDF texts by paper ID

# --- SIDEBAR: API KEYS ---
with st.sidebar:
    st.markdown("## ⚙️ Ayarlar")

    st.markdown("### 🔑 API Keys")
    gemini_key = st.text_input(
        "Gemini API Key:",
        type="password",
        value=st.session_state.gemini_api_key,
        help="AI sentezleme için gerekli"
    )
    if gemini_key:
        st.session_state.gemini_api_key = gemini_key
        st.success("✅ Gemini API Key Aktif!")
    else:
        st.warning("⚠️ API Key gerekli")

    email = st.text_input(
        "E-posta (PubMed için):",
        value="researcher@example.com",
        help="PubMed API kullanımı için gerekli"
    )
    if email and email != "researcher@example.com":
        st.success("✅ E-posta ayarlandı")
    else:
        st.info("ℹ️ Varsayılan e-posta kullanılıyor")

    st.markdown("---")
    st.markdown("### 📊 İstatistikler")
    st.metric("Bulunan Makale", len(st.session_state.papers))
    st.metric("Seçili Makale", len(st.session_state.selected_papers))

    st.markdown("---")
    if st.button("🗑️ Tüm Sonuçları Temizle", use_container_width=True):
        st.session_state.papers = []
        st.session_state.selected_papers = []
        st.rerun()

# --- MAIN CONTENT ---
st.markdown("# 🎓 Academic Research Assistant")
st.caption("Akademik makaleleri bul, analiz et, AI ile sentezle")

st.markdown("---")

# --- SEARCH SECTION ---
st.markdown("## 🔍 Makale Arama")

col_search1, col_search2 = st.columns([3, 1])

with col_search1:
    search_query = st.text_input(
        "Araştırma konusu / Anahtar kelimeler:",
        placeholder="Örn: nutrition authorship, machine learning healthcare, climate change...",
        key="search_query_input"
    )

with col_search2:
    max_results = st.number_input(
        "Makale sayısı:",
        min_value=5,
        max_value=100,
        value=20,
        step=5
    )

# Database selection
db_col1, db_col2, db_col3, db_col4, db_col5 = st.columns(5)

with db_col1:
    use_pubmed = st.checkbox("🏥 PubMed", value=True, help="Sağlık, tıp, yaşam bilimleri")
with db_col2:
    use_semantic = st.checkbox("🧠 Semantic Scholar", value=True, help="Tüm bilim alanları, AI destekli")
with db_col3:
    use_google_scholar = st.checkbox("🎓 Google Scholar", value=True, help="Tüm alanlar, en kapsamlı")
with db_col4:
    use_arxiv = st.checkbox("📚 arXiv", value=False, help="Fizik, matematik, bilgisayar bilimi")
with db_col5:
    use_crossref = st.checkbox("🌐 Crossref", value=False, help="Genel akademik yayınlar")

# Search button
if st.button("🔍 ARA", use_container_width=True, type="primary"):
    if not search_query:
        st.error("⚠️ Lütfen bir araştırma konusu girin!")
    else:
        st.session_state.papers = []

        progress_bar = st.progress(0)
        status_text = st.empty()

        # --- PUBMED SEARCH ---
        if use_pubmed:
            status_text.text("🏥 PubMed araştırılıyor...")
            try:
                Entrez.email = email
                handle = Entrez.esearch(db="pubmed", term=search_query, retmax=max_results)
                results = Entrez.read(handle)
                handle.close()

                pmids = results.get("IdList", [])

                for idx, pmid in enumerate(pmids):
                    try:
                        handle = Entrez.efetch(db="pubmed", id=pmid, rettype="medline", retmode="text")
                        record_text = handle.read()
                        handle.close()

                        # Parse MEDLINE format
                        title = ""
                        authors = []
                        journal = ""
                        year = ""
                        abstract = ""

                        for line in record_text.split('\n'):
                            if line.startswith('TI  - '):
                                title = line[6:].strip()
                            elif line.startswith('AU  - '):
                                authors.append(line[6:].strip())
                            elif line.startswith('TA  - '):
                                journal = line[6:].strip()
                            elif line.startswith('DP  - '):
                                year = line[6:10].strip()
                            elif line.startswith('AB  - '):
                                abstract = line[6:].strip()

                        if title:
                            st.session_state.papers.append({
                                "title": title,
                                "authors": ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else ""),
                                "journal": journal,
                                "year": year,
                                "abstract": abstract,
                                "source": "PubMed",
                                "id": f"PMID:{pmid}",
                                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                            })
                    except:
                        continue

                    progress_bar.progress((idx + 1) / len(pmids) * 0.5)

                st.success(f"✅ PubMed: {len([p for p in st.session_state.papers if p['source'] == 'PubMed'])} makale bulundu")
            except Exception as e:
                st.error(f"❌ PubMed hatası: {str(e)}")

        progress_bar.progress(0.5)

        # --- SEMANTIC SCHOLAR SEARCH ---
        if use_semantic:
            status_text.text("🧠 Semantic Scholar araştırılıyor...")
            try:
                url = "https://api.semanticscholar.org/graph/v1/paper/search"
                params = {
                    "query": search_query,
                    "limit": max_results,
                    "fields": "title,authors,year,abstract,citationCount,venue,externalIds,url"
                }

                response = requests.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()

                    for paper in data.get("data", []):
                        authors_list = [a.get("name", "") for a in paper.get("authors", [])]
                        author_str = ", ".join(authors_list[:3]) + (" et al." if len(authors_list) > 3 else "")

                        st.session_state.papers.append({
                            "title": paper.get("title", "N/A"),
                            "authors": author_str,
                            "journal": paper.get("venue", "N/A"),
                            "year": str(paper.get("year", "N/A")),
                            "abstract": paper.get("abstract", "No abstract available"),
                            "source": "Semantic Scholar",
                            "id": paper.get("paperId", ""),
                            "url": paper.get("url", ""),
                            "citations": paper.get("citationCount", 0)
                        })

                    st.success(f"✅ Semantic Scholar: {len([p for p in st.session_state.papers if p['source'] == 'Semantic Scholar'])} makale bulundu")
                else:
                    st.warning(f"⚠️ Semantic Scholar: {response.status_code} hatası")
            except Exception as e:
                st.error(f"❌ Semantic Scholar hatası: {str(e)}")

        progress_bar.progress(0.75)

        # --- ARXIV SEARCH ---
        if use_arxiv:
            status_text.text("📚 arXiv araştırılıyor...")
            try:
                import arxiv

                search = arxiv.Search(
                    query=search_query,
                    max_results=max_results,
                    sort_by=arxiv.SortCriterion.Relevance
                )

                for result in search.results():
                    authors_list = [a.name for a in result.authors]
                    author_str = ", ".join(authors_list[:3]) + (" et al." if len(authors_list) > 3 else "")

                    st.session_state.papers.append({
                        "title": result.title,
                        "authors": author_str,
                        "journal": "arXiv preprint",
                        "year": str(result.published.year),
                        "abstract": result.summary,
                        "source": "arXiv",
                        "id": result.entry_id.split('/')[-1],
                        "url": result.entry_id,
                        "pdf_url": result.pdf_url
                    })

                st.success(f"✅ arXiv: {len([p for p in st.session_state.papers if p['source'] == 'arXiv'])} makale bulundu")
            except Exception as e:
                st.error(f"❌ arXiv hatası: {str(e)}")

        progress_bar.progress(0.85)

        # --- GOOGLE SCHOLAR SEARCH ---
        if use_google_scholar:
            status_text.text("🎓 Google Scholar araştırılıyor...")
            try:
                search_query_formatted = scholarly.search_pubs(search_query)

                count = 0
                for result in search_query_formatted:
                    if count >= max_results:
                        break

                    try:
                        # Get basic info
                        title = result.get('bib', {}).get('title', 'N/A')
                        authors_list = result.get('bib', {}).get('author', [])
                        if isinstance(authors_list, str):
                            authors_list = [authors_list]
                        author_str = ", ".join(authors_list[:3]) + (" et al." if len(authors_list) > 3 else "")

                        year = result.get('bib', {}).get('pub_year', 'N/A')
                        abstract = result.get('bib', {}).get('abstract', 'No abstract available')
                        venue = result.get('bib', {}).get('venue', result.get('bib', {}).get('journal', 'N/A'))
                        citations = result.get('num_citations', 0)
                        url = result.get('pub_url', result.get('eprint_url', ''))

                        # Try to get PDF link
                        pdf_url = None
                        if 'eprint_url' in result:
                            pdf_url = result['eprint_url']

                        st.session_state.papers.append({
                            "title": title,
                            "authors": author_str,
                            "journal": venue,
                            "year": str(year),
                            "abstract": abstract,
                            "source": "Google Scholar",
                            "id": f"GS:{result.get('author_id', [''])[0] if result.get('author_id') else count}",
                            "url": url if url else f"https://scholar.google.com/scholar?q={title.replace(' ', '+')}",
                            "citations": citations,
                            "pdf_url": pdf_url
                        })

                        count += 1
                    except Exception as e:
                        continue

                st.success(f"✅ Google Scholar: {len([p for p in st.session_state.papers if p['source'] == 'Google Scholar'])} makale bulundu")
            except Exception as e:
                st.error(f"❌ Google Scholar hatası: {str(e)}")

        progress_bar.progress(1.0)
        status_text.text("✅ Arama tamamlandı!")

        st.rerun()

# --- DISPLAY RESULTS ---
if st.session_state.papers:
    st.markdown("---")
    st.markdown("## 📚 Bulunan Makaleler")

    # Filters
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        source_filter = st.multiselect(
            "Kaynak filtrele:",
            ["PubMed", "Semantic Scholar", "Google Scholar", "arXiv", "Crossref"],
            default=["PubMed", "Semantic Scholar", "Google Scholar", "arXiv", "Crossref"]
        )

    with filter_col2:
        year_filter = st.slider(
            "Yıl aralığı:",
            1990,
            2025,
            (2015, 2025)
        )

    with filter_col3:
        sort_by = st.selectbox(
            "Sıralama:",
            ["En Yeni", "En Eski", "Alfabetik", "En Çok Alıntılanan"]
        )

    # Filter papers
    filtered_papers = [
        p for p in st.session_state.papers
        if p['source'] in source_filter and
        (p['year'].isdigit() and year_filter[0] <= int(p['year']) <= year_filter[1])
    ]

    # Sort papers
    if sort_by == "En Yeni":
        filtered_papers.sort(key=lambda x: x['year'], reverse=True)
    elif sort_by == "En Eski":
        filtered_papers.sort(key=lambda x: x['year'])
    elif sort_by == "Alfabetik":
        filtered_papers.sort(key=lambda x: x['title'])
    elif sort_by == "En Çok Alıntılanan":
        filtered_papers.sort(key=lambda x: x.get('citations', 0), reverse=True)

    st.caption(f"📊 Toplam {len(filtered_papers)} makale gösteriliyor")

    # Bulk actions
    action_col1, action_col2, action_col3 = st.columns(3)
    with action_col1:
        if st.button("✅ Tümünü Seç", use_container_width=True):
            st.session_state.selected_papers = [p['id'] for p in filtered_papers]
            st.rerun()
    with action_col2:
        if st.button("❌ Seçimi Temizle", use_container_width=True):
            st.session_state.selected_papers = []
            st.rerun()
    with action_col3:
        if st.button("📋 Seçilenleri Export", use_container_width=True):
            selected = [p for p in filtered_papers if p['id'] in st.session_state.selected_papers]
            st.download_button(
                "💾 BibTeX İndir",
                data=generate_bibtex(selected),
                file_name=f"references_{datetime.now().strftime('%Y%m%d')}.bib",
                mime="text/plain"
            )

    st.markdown("---")

    # Display papers
    for idx, paper in enumerate(filtered_papers):
        is_selected = paper['id'] in st.session_state.selected_papers

        with st.container():
            col_check, col_content = st.columns([0.1, 0.9])

            with col_check:
                if st.checkbox("", value=is_selected, key=f"check_{paper['id']}"):
                    if paper['id'] not in st.session_state.selected_papers:
                        st.session_state.selected_papers.append(paper['id'])
                else:
                    if paper['id'] in st.session_state.selected_papers:
                        st.session_state.selected_papers.remove(paper['id'])

            with col_content:
                # Title with link
                st.markdown(f"### [{idx + 1}. {paper['title']}]({paper['url']})")

                # Metadata
                meta_col1, meta_col2, meta_col3 = st.columns(3)
                with meta_col1:
                    st.caption(f"👥 **Yazarlar:** {paper['authors']}")
                with meta_col2:
                    st.caption(f"📅 **Yıl:** {paper['year']}")
                with meta_col3:
                    if 'citations' in paper:
                        st.caption(f"📊 **Alıntı:** {paper['citations']}")

                st.caption(f"📖 **Dergi:** {paper['journal']}")
                st.caption(f"🔗 **Kaynak:** {paper['source']} | ID: {paper['id']}")

                # Abstract
                with st.expander("📄 Özet"):
                    st.write(paper.get('abstract', 'Özet bulunamadı'))

                # Actions
                action_row = st.columns(4)
                with action_row[0]:
                    if st.button("📋 APA Citation", key=f"cite_apa_{paper['id']}", use_container_width=True):
                        citation = generate_apa_citation(paper)
                        st.code(citation, language=None)

                with action_row[1]:
                    if st.button("📋 BibTeX", key=f"cite_bib_{paper['id']}", use_container_width=True):
                        bibtex = generate_bibtex([paper])
                        st.code(bibtex, language=None)

                with action_row[2]:
                    if 'pdf_url' in paper and paper['pdf_url']:
                        if st.button("📖 PDF Oku", key=f"pdf_read_{paper['id']}", use_container_width=True):
                            with st.spinner("PDF indiriliyor ve okunuyor..."):
                                pdf_text, error = extract_text_from_pdf(paper['pdf_url'])
                                if error:
                                    st.error(f"❌ {error}")
                                else:
                                    st.session_state.pdf_texts[paper['id']] = pdf_text
                                    st.success("✅ PDF başarıyla okundu!")
                                    st.rerun()

                with action_row[3]:
                    if 'pdf_url' in paper and paper['pdf_url']:
                        st.link_button("🔗 PDF Link", paper['pdf_url'], use_container_width=True)

                # Show extracted PDF text if available
                if paper['id'] in st.session_state.pdf_texts:
                    with st.expander("📄 PDF Tam Metin (Okunan)", expanded=False):
                        pdf_text = st.session_state.pdf_texts[paper['id']]
                        st.text_area(
                            "PDF İçeriği:",
                            value=pdf_text[:10000] + ("...\n\n[Metin çok uzun, ilk 10000 karakter gösteriliyor]" if len(pdf_text) > 10000 else ""),
                            height=400,
                            key=f"pdf_text_display_{paper['id']}"
                        )
                        st.caption(f"📊 Toplam {len(pdf_text)} karakter | {len(pdf_text.split())} kelime")

                        # Option to clear
                        if st.button("🗑️ PDF Metnini Sil", key=f"clear_pdf_{paper['id']}"):
                            del st.session_state.pdf_texts[paper['id']]
                            st.rerun()

            st.markdown("---")

# --- AI SYNTHESIS SECTION ---
if st.session_state.selected_papers:
    st.markdown("## 🤖 AI ile Literatür Sentezi")
    st.caption(f"{len(st.session_state.selected_papers)} makale seçildi")

    synthesis_type = st.selectbox(
        "Ne yazmak istersin?",
        [
            "📝 Literatür Taraması (Literature Review)",
            "📊 Sistematik İnceleme Özeti",
            "🎯 Araştırma Boşlukları (Research Gaps)",
            "📈 Trend Analizi",
            "💡 Yeni Araştırma Önerileri"
        ]
    )

    language = st.radio(
        "Dil:",
        ["🇹🇷 Türkçe", "🇬🇧 İngilizce"],
        horizontal=True
    )

    if st.button("✨ AI İLE OLUŞTUR", use_container_width=True, type="primary"):
        if not st.session_state.gemini_api_key:
            st.error("⚠️ Lütfen Gemini API Key girin!")
        else:
            selected = [p for p in st.session_state.papers if p['id'] in st.session_state.selected_papers]

            with st.spinner("🤖 AI yazıyor..."):
                try:
                    genai.configure(api_key=st.session_state.gemini_api_key)
                    model = genai.GenerativeModel('gemini-2.5-flash')

                    # Build context from papers
                    papers_context = ""
                    papers_with_full_text = 0
                    for i, paper in enumerate(selected, 1):
                        papers_context += f"\n[{i}] {paper['title']}\n"
                        papers_context += f"Yazarlar: {paper['authors']}\n"
                        papers_context += f"Yıl: {paper['year']}\n"

                        # Use full PDF text if available, otherwise use abstract
                        if paper['id'] in st.session_state.pdf_texts:
                            pdf_text = st.session_state.pdf_texts[paper['id']]
                            # Limit to first 5000 chars to avoid context overflow
                            papers_context += f"Tam Metin: {pdf_text[:5000]}{'...[devam ediyor]' if len(pdf_text) > 5000 else ''}\n"
                            papers_with_full_text += 1
                        else:
                            papers_context += f"Özet: {paper.get('abstract', 'N/A')}\n"

                        papers_context += "-" * 80 + "\n"

                    if papers_with_full_text > 0:
                        st.info(f"ℹ️ {papers_with_full_text} makalenin tam metni AI analizine dahil edildi!")

                    lang = "Türkçe" if "🇹🇷" in language else "İngilizce"

                    prompt = f"""
Sen bir akademik araştırma asistanısın. Aşağıdaki {len(selected)} akademik makaleye dayanarak "{synthesis_type}" yaz.

Makaleler:
{papers_context}

Lütfen:
- {lang} dilinde yaz
- Akademik bir üslup kullan
- Her iddiayı kaynak numarasıyla destekle [1], [2], etc.
- Farklı çalışmaları karşılaştır ve sentezle
- Objektif ve eleştirel bir yaklaşım benimse
- 500-800 kelime arası yaz

Başlıklar ve alt başlıklar kullan. Sonunda kaynakça listesi ekle.
"""

                    response = model.generate_content(prompt)
                    synthesis_text = response.text

                    st.success("✅ Sentez tamamlandı!")

                    st.markdown("### 📄 Oluşturulan Metin:")
                    st.markdown(synthesis_text)

                    # Download button
                    st.download_button(
                        "💾 Word Olarak İndir (.txt)",
                        data=synthesis_text,
                        file_name=f"literature_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )

                except Exception as e:
                    st.error(f"❌ AI hatası: {str(e)}")

# --- HELPER FUNCTIONS ---
def extract_text_from_pdf(pdf_url):
    """Download and extract text from PDF"""
    try:
        # Download PDF
        response = requests.get(pdf_url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            return None, f"PDF indirilemedi (HTTP {response.status_code})"

        # Read PDF
        pdf_file = io.BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # Extract text from all pages
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n\n"

        if not text.strip():
            return None, "PDF'den metin çıkarılamadı (taranmış görsel olabilir)"

        return text, None
    except Exception as e:
        return None, f"PDF okuma hatası: {str(e)}"

def generate_apa_citation(paper):
    """Generate APA format citation"""
    authors = paper['authors']
    year = paper['year']
    title = paper['title']
    journal = paper['journal']

    citation = f"{authors} ({year}). {title}. {journal}."
    return citation

def generate_bibtex(papers):
    """Generate BibTeX format"""
    bibtex = ""
    for paper in papers:
        # Create citation key
        first_author = paper['authors'].split(',')[0].split()[-1].lower()
        year = paper['year']
        key = f"{first_author}{year}"

        bibtex += f"@article{{{key},\n"
        bibtex += f"  title={{{paper['title']}}},\n"
        bibtex += f"  author={{{paper['authors']}}},\n"
        bibtex += f"  journal={{{paper['journal']}}},\n"
        bibtex += f"  year={{{paper['year']}}},\n"
        if 'url' in paper:
            bibtex += f"  url={{{paper['url']}}},\n"
        bibtex += "}\n\n"

    return bibtex

st.markdown("---")
st.caption("🎓 Academic Research Assistant | Powered by AI")
