import json,re,streamlit as st
from google import genai
from google.genai import types
def ask(prompt,system="Be accurate and evidence-based."):
 key=st.secrets.get("GEMINI_API_KEY","")
 if not key: st.error("Set GEMINI_API_KEY in Streamlit Secrets."); st.stop()
 model=st.secrets.get("GEMINI_MODEL","gemini-3.8-flash")
 r=genai.Client(api_key=key).models.generate_content(model=model,contents=prompt,config=types.GenerateContentConfig(system_instruction=system,temperature=0.2))
 if not getattr(r,"text",None): raise ValueError("Empty Gemini response")
 return r.text.strip()
def parse(s):
 s=re.sub(r"^```(?:json)?\\s*|\\s*```$","",s.strip(),flags=re.I)
 try:return json.loads(s)
 except Exception:
  for a,b in [("{","}"),("[","]")]:
   i,j=s.find(a),s.rfind(b)
   if i>=0 and j>i:return json.loads(s[i:j+1])
  raise ValueError("Gemini returned invalid JSON; retry.")
def err(e):return f"{type(e).__name__}: {str(e)[:250]}"
