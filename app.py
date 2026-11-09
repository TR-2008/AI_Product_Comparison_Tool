import io,json,streamlit as st,pandas as pd
from pypdf import PdfReader
from docx import Document
from common import ask,parse,err
st.set_page_config(page_title="AI Product Comparison",page_icon="🛒",layout="wide")
st.title("🛒 AI Product Comparison Tool")
st.write("Upload two or more product specifications and compare them against your needs.")
def extract(f):
 b=f.getvalue(); n=f.name.lower()
 if n.endswith(".pdf"): return "\\n".join(f"[{f.name} page {i+1}] "+(p.extract_text() or "") for i,p in enumerate(PdfReader(io.BytesIO(b)).pages))
 if n.endswith(".docx"): return "\\n".join(p.text for p in Document(io.BytesIO(b)).paragraphs)
 if n.endswith(".txt"): return b.decode("utf-8",errors="replace")
 if n.endswith(".csv"): return pd.read_csv(io.BytesIO(b)).fillna("").to_string(index=False)
 raise ValueError("Unsupported file format")
with st.sidebar:
 files=st.file_uploader("Product files",type=["pdf","docx","txt","csv"],accept_multiple_files=True)
 limit=st.slider("Maximum characters per file",2000,14000,8000,1000)
req=st.text_area("Requirements and hard constraints",placeholder="Budget, minimum RAM, warranty, size, features...")
priorities=st.multiselect("Priority factors",["Price/value","Performance","Warranty","Battery","Build quality","Portability"],default=["Price/value","Performance"])
if st.button("Compare products",type="primary",disabled=not files or len(req.strip())<10):
 try:
  docs=[]
  for f in files:
   t=extract(f).strip()
   if len(t)>30: docs.append({"file":f.name,"text":t[:limit]})
   else: st.warning(f"No extractable text in {f.name}; scanned PDFs need OCR.")
  if len(docs)<2: st.error("Upload at least two readable documents.")
  else:
   prompt=("Compare ONLY from supplied documents. Return JSON with keys summary, comparison (list of criterion and values map), products (name,source,strengths,weaknesses,unknowns,evidence), tradeoffs, recommendations (product,best_for,reasons,cautions). "
   "Never invent specifications or prices. Missing facts must be Not specified. Respect hard constraints; if none qualifies, say so. Flag conflicts. "
   f"Requirements: {req}. Priorities: {priorities}. Documents: {json.dumps(docs,ensure_ascii=False)}")
   with st.spinner("Comparing with Gemini..."): st.session_state.result=parse(ask(prompt,"You are a neutral product analyst. Never fabricate product facts."))
 except Exception as e: st.error(err(e))
r=st.session_state.get("result")
if r:
 st.subheader("Summary"); st.write(r.get("summary",""))
 rows=r.get("comparison",[])
 if rows: st.dataframe(pd.DataFrame([{"Criterion":x.get("criterion",""),**x.get("values",{})} for x in rows]),use_container_width=True,hide_index=True)
 for x in r.get("products",[]):
  with st.expander(x.get("name","Product")):
   for k in ["strengths","weaknesses","unknowns","evidence"]:
    st.markdown("**"+k.title()+"**")
    for v in x.get(k,[]): st.write("- "+v)
 st.subheader("Trade-offs")
 for x in r.get("tradeoffs",[]): st.write("- "+x)
 st.subheader("Recommendations")
 for x in r.get("recommendations",[]):
  st.markdown(f"**{x.get('product')} — {x.get('best_for')}**")
  for y in x.get("reasons",[]): st.write("- "+y)
  for y in x.get("cautions",[]): st.caption("Caution: "+y)
 st.download_button("Download JSON",json.dumps(r,ensure_ascii=False,indent=2),"comparison.json","application/json")
st.caption("Verify critical specifications with the original manufacturer or seller.")
