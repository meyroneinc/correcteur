import streamlit as st
import pandas as pd
import os
import numpy as np
import plotly.express as px



# Configuration de la page
st.set_page_config(page_title="Correcteur", layout="wide")

# --- 1. FONCTIONS DE NETTOYAGE ET FORMATAGE ---
def clean_float(val):
    if pd.isna(val) or val == "" or str(val).strip() == "": return 0.0
    try: return float(str(val).replace(',', '.'))
    except ValueError: return 0.0

def format_excel(val):
    return str(round(val, 2)).replace('.', ',')

def format_q_num(val):
    """Supprime le .0 des numéros (1.0 -> 1)"""
    if pd.isna(val): return ""
    try:
        f_val = float(str(val).replace(',', '.'))
        return str(int(f_val)) if f_val.is_integer() else str(f_val)
    except: return str(val)

def clean_latex(text):
    if pd.isna(text): return ""
    text = str(text).replace('\u200b', '')
    replacements = {'&': r'\&', '%': r'\%', '#': r'\#', '{': r'\{', '}': r'\}','π': r'$\pi$',
        'pgcd(nx,ny)=n⋅pgcd(x,y)': r'$pgcd(nx,ny)=n \times pgcd(x,y)$',
        'n \equiv 0 \pmod\{3\}': r'n \equiv 0 \pmod{3}',
        'z3': r'$z_3$',
        'zA': r'$z_A$',
        'zB': r'$z_B$',
        '1+i': r'$1+i$',
        '3-i': r'$3-i$',
        'u_n': r'$u_n$',
        'A2028': r'$A^{2028}$',
        'BA1​A2​': r'$BA_1A_2$',
        '(2​)n>1000': r'$2^{n}>1000$',
        '(2)n': r' $(\sqrt{2})^n$'}
    for key, val in replacements.items(): text = text.replace(key, val)
    return text

# --- 2. CHARGEMENT ET INITIALISATION ---
file_path = 'DS06.csv'


if 'df' not in st.session_state:
    if os.path.exists(file_path):
        st.session_state.df = pd.read_csv(file_path, header=None, sep=None, engine='python')
    else:
        st.error(f"Fichier '{file_path}' introuvable.")
        st.stop()

df = st.session_state.df
student_names = df.iloc[0, 4::2].dropna().tolist()
selected_student = st.selectbox("👤 Sélectionner l'élève :", student_names)

idx_s = student_names.index(selected_student)
col_bool, col_pts = 4 + (idx_s * 2), 5 + (idx_s * 2)
row_appreciation = len(df) - 1

# Initialisation Session State pour l'élève
for i in range(2, len(df)):
    k_ch, k_pt = f"ch_{selected_student}_{i}", f"pts_{selected_student}_{i}"
    if k_ch not in st.session_state:
        st.session_state[k_ch] = (str(df.iloc[i, col_bool]).upper() == "TRUE")
    if k_pt not in st.session_state:
        st.session_state[k_pt] = clean_float(df.iloc[i, col_pts])

k_app = f"app_{selected_student}"
if k_app not in st.session_state:
    val_app = df.iloc[row_appreciation, col_pts]
    st.session_state[k_app] = str(val_app) if pd.notna(val_app) else ""

# --- 3. FONCTIONS DE LOGIQUE ---
def update_logic(i, max_q, mode):
    k_ch, k_pt = f"ch_{selected_student}_{i}", f"pts_{selected_student}_{i}"
    if mode == "check":
        st.session_state[k_pt] = float(max_q) if st.session_state[k_ch] else 0.0
    else:
        st.session_state[k_ch] = st.session_state[k_pt] > 0

def mark_absent():
    for i in range(2, len(df)):
        if pd.notna(df.iloc[i, 1]):
            st.session_state[f"ch_{selected_student}_{i}"] = False
            st.session_state[f"pts_{selected_student}_{i}"] = 0.0
    st.session_state[f"app_{selected_student}"] = "ABSENT"
    st.warning(f"{selected_student} marqué absent.")

# --- 4. TABLEAU DE BORD & GRAPHIQUES ---
@st.dialog("Tableau de bord de la classe", width="large")
def show_class_summary(dataframe):
    tab1, tab2 = st.tabs(["📝 Édition & Moyennes", "📊 Statistiques"])
    indices_exos = [i for i in range(len(dataframe)) if pd.notna(dataframe.iloc[i, 2]) and "Exercice" in str(dataframe.iloc[i, 2])]
    names = dataframe.iloc[0, 4::2].tolist()
    
    # Barème total réel
    bareme_total_reel = sum([clean_float(dataframe.iloc[idx, 3]) for idx in indices_exos])-3
    
    summary_data = []
    scores_presents = {dataframe.iloc[idx, 2]: [] for idx in indices_exos}
    totals_presents = []

    for i, name in enumerate(names):
        p_idx = 5 + (i * 2)
        apprec = st.session_state.get(f"app_{name}", dataframe.iloc[row_appreciation, p_idx])
        is_abs = "ABSENT" in str(apprec).upper()
        row_data = {"Élève": name}
        score_total_eleve = 0.0
        
        for idx_row in indices_exos:
            exo_name = dataframe.iloc[idx_row, 2]
            score = clean_float(dataframe.iloc[idx_row, p_idx])
            row_data[exo_name] = "ABS" if is_abs else score
            if not is_abs:
                scores_presents[exo_name].append(score)
                score_total_eleve += score
        
        row_data["TOTAL"] = "ABS" if is_abs else score_total_eleve
        if not is_abs: totals_presents.append(score_total_eleve)
        row_data["Appréciation"] = apprec if pd.notna(apprec) else ""
        summary_data.append(row_data)

    with tab1:
        # Ligne de moyenne (Présents uniquement)
        mean_row = {"Élève": "📊 MOYENNE (PRÉSENTS)", "Appréciation": f"Sur {len(totals_presents)} présent(s)"}
        for exo, scs in scores_presents.items():
            mean_row[exo] = round(np.mean(scs), 2) if scs else 0.0
        mean_row["TOTAL"] = round(np.mean(totals_presents), 2) if totals_presents else 0.0
        
        df_display = pd.concat([pd.DataFrame(summary_data), pd.DataFrame([mean_row])], ignore_index=True)
        edited_df = st.data_editor(df_display, use_container_width=True, hide_index=True)
        
        if st.button("💾 Enregistrer les modifications"):
            for i, name in enumerate(names):
                st.session_state[f"app_{name}"] = edited_df.iloc[i]["Appréciation"]
                st.session_state.df.iloc[row_appreciation, 5+(i*2)] = edited_df.iloc[i]["Appréciation"]
            st.session_state.df.to_csv(file_path, index=False, header=False, sep=';', decimal=',', encoding='utf-8-sig')
            st.success("Enregistré !"); st.rerun()
    with tab2:
        st.subheader(f"Analyses sur {bareme_total_reel} points")
        
        # --- Ligne 1 : Histogramme et Réussite par Exercice ---
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Répartition des notes**")
            fig = px.histogram(x=totals_presents, nbins=int(bareme_total_reel), labels={'x':'Points', 'y':'Effectif'}, range_x=[0, bareme_total_reel+2])
            fig.update_xaxes(tickmode='linear', tick0=0, dtick=2)
            fig.update_layout(bargap=0.1, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.write("**Réussite par Exercice (%)**")
            exos = list(scores_presents.keys())
            succ = [ (np.mean(scores_presents[e])/clean_float(dataframe.iloc[indices_exos[exos.index(e)], 3]))*100 for e in exos if scores_presents[e]]
            fig2 = px.bar(x=exos, y=succ, range_y=[0,100], color=succ, color_continuous_scale='RdYlGn', text=[f"{round(v,1)}%" for v in succ])
            fig2.update_traces(textposition='outside')
            st.plotly_chart(fig2, use_container_width=True)

        st.divider()

      # --- Ligne 2 : Diagrammes Camemberts (Répartition sur 20) ---
        st.write("📊 **Répartition des notes ramenées sur 20**")
        
        if totals_presents and bareme_total_reel > 0:
            # Conversion des notes sur 20 pour la cohérence des tranches
            notes_sur_20 = [(score / bareme_total_reel) * 20 for score in totals_presents]
            df_notes = pd.DataFrame({"Note": notes_sur_20})
            
            # Définition des tranches et labels pour le premier camembert
            bins_1 = [0, 5, 10, 15, 20.01]
            labels_1 = ["[0, 5[", "[5, 10[", "[10, 15[", "[15, 20]"]
            df_notes['Tranche_1'] = pd.cut(df_notes['Note'], bins=bins_1, labels=labels_1, right=False, include_lowest=True)
            counts_1 = df_notes['Tranche_1'].value_counts().reset_index()
            
            # Définition des tranches et labels pour le second camembert
            bins_2 = [-0.01, 8, 12, 20.01]
            labels_2 = ["[0, 8]", "]8, 12]", "]12, 20]"]
            df_notes['Tranche_2'] = pd.cut(df_notes['Note'], bins=bins_2, labels=labels_2, right=True)
            counts_2 = df_notes['Tranche_2'].value_counts().reset_index()
            
            c3, c4 = st.columns(2)
            
            # --- Ajustement du dark_layout (Légendes et arrière-plan clairs et nets) ---
            dark_layout = dict(
                template="plotly_dark",
                paper_bgcolor="#0e1117",  
                plot_bgcolor="#0e1117",
                font=dict(color="#ffffff", size=14), # Titres et légendes extérieurs restent en blanc
                legend=dict(
                    bgcolor="rgba(0,0,0,0)",    
                    font=dict(color="#ffffff", size=12)
                ),
                hoverlabel=dict(
                    bgcolor="rgba(0,0,0,0)", 
                    font=dict(color="#ffffff", size=14)
                )
            )
            
            with c3:
                st.write("**Répartition [0;5[ - [5;10[ - [10;15[ - [15;20]**")
                fig_pie1 = px.pie(counts_1, values='count', names='Tranche_1', 
                                  color='Tranche_1',
                                  color_discrete_map={"[0, 5[":"#ef553b", "[5, 10[":"#ef963b", "[10, 15[":"#636efa", "[15, 20]":"#00cc96"},
                                  category_orders={"Tranche_1": labels_1})
                
                # ON FORCE LE NOIR ICI
                fig_pie1.update_traces(
                    textinfo='percent+value',
                    textposition='inside',
                    textfont=dict(color='#000000', size=14, family="Arial Black") # Noir pur + police grasse pour un contraste maximal
                )
                fig_pie1.update_layout(**dark_layout)
                st.plotly_chart(fig_pie1, use_container_width=True, theme=None)
                
            with c4:
                st.write("**Découpage Profil (Fragile / Moyen / Solide)**")
                fig_pie2 = px.pie(counts_2, values='count', names='Tranche_2', 
                                  color='Tranche_2',
                                  color_discrete_map={"[0, 8]":"#dc3545", "]8, 12]":"#ffc107", "]12, 20]":"#28a745"},
                                  category_orders={"Tranche_2": labels_2})
                
                # ON FORCE LE NOIR ICI
                fig_pie2.update_traces(
                    textinfo='percent+value',
                    textposition='inside',
                    textfont=dict(color='#000000', size=14, family="Arial Black") # Noir pur + police grasse pour un contraste maximal
                )
                fig_pie2.update_layout(**dark_layout)
                st.plotly_chart(fig_pie2, use_container_width=True, theme=None)
        else:
            st.info("Aucune note disponible pour générer les camemberts.")

# --- 5. INTERFACE PRINCIPALE ---
col_t, col_b = st.columns([4, 1])
with col_t: st.title(f"Notation : {selected_student}")
with col_b: 
    st.write("##")
    if st.button("🚫 ABSENT", use_container_width=True): mark_absent()

indices_exos = [i for i in range(len(df)) if pd.notna(df.iloc[i, 2]) and "Exercice" in str(df.iloc[i, 2])]
scores_recap, total_global = {}, 0.0

for idx_exo, start_row in enumerate(indices_exos):
    end_row = indices_exos[idx_exo+1] if idx_exo+1 < len(indices_exos) else len(df)
    nom_exo = df.iloc[start_row, 2]
    bareme_exo, score_exo = 0.0, 0.0
    for i in range(start_row + 1, end_row):
        if pd.notna(df.iloc[i, 1]):
            bareme_exo += clean_float(df.iloc[i, 3]); score_exo += st.session_state[f"pts_{selected_student}_{i}"]
    
    scores_recap[nom_exo] = (score_exo, bareme_exo)
    total_global += score_exo

    with st.expander(f"📘 {nom_exo} : {round(score_exo, 2)} / {bareme_exo}", expanded=True):
        for i in range(start_row + 1, end_row):
            if pd.notna(df.iloc[i, 1]):
                q_n, q_m = format_q_num(df.iloc[i, 1]), clean_float(df.iloc[i, 3])
                p = st.session_state[f"pts_{selected_student}_{i}"]
                bul = "🟢" if p == q_m and q_m > 0 else "🟡" if p > 0 else "🔴"
                cols = st.columns([0.6, 6, 1, 1.5])
                cols[0].checkbox(f"{bul}", key=f"ch_{selected_student}_{i}", on_change=update_logic, args=(i, q_m, "check"))
                cols[1].write(f"**Q{q_n}** - {df.iloc[i, 2]}")
                cols[2].caption(f"max {q_m}")
                cols[3].number_input("Pts", min_value=0.0, max_value=float(q_m), step=0.25, key=f"pts_{selected_student}_{i}", on_change=update_logic, args=(i, q_m, "pts"), label_visibility="collapsed")
                df.iloc[i, col_bool] = "TRUE" if st.session_state[f"ch_{selected_student}_{i}"] else "FALSE"
                df.iloc[i, col_pts] = format_excel(st.session_state[f"pts_{selected_student}_{i}"])

st.divider()
st.session_state[k_app] = st.text_area(f"💬 Appréciation", value=st.session_state[k_app], height=100)
df.iloc[row_appreciation, col_pts] = st.session_state[k_app]

# --- 6. LATEX ---
def generate_full_pdf_tex(dataframe, students_to_print):
    latex = r"""\documentclass[9pt,a4paper]{article}
\usepackage[utf8]{inputenc} \usepackage[T1]{fontenc} \usepackage[french]{babel}
\usepackage{geometry} \usepackage[most]{tcolorbox} \usepackage{tabularx} \usepackage{pifont} \usepackage{xcolor} \usepackage{amsmath}
\geometry{margin=0.8cm, top=0.6cm, bottom=0.6cm}
\begin{document}
\renewcommand{\arraystretch}{1.1}"""
    for name in students_to_print:
        try:
            p_idx = dataframe.iloc[0].tolist().index(name) + 1
            total_pts = dataframe.iloc[1, p_idx]
            app = st.session_state.get(f"app_{name}", dataframe.iloc[row_appreciation, p_idx])
            is_abs = "ABSENT" in str(app).upper()
            bareme_total = sum([clean_float(dataframe.iloc[idx, 3]) for idx in indices_exos])
            
            note_label = "ABSENT" if is_abs else f"{total_pts} / {bareme_total}"
            
            latex += f"\n\\begin{{tcolorbox}}[colback=gray!5, colframe=black, sharp corners, boxrule=0.5pt, left=2mm, right=2mm, top=1mm, bottom=1mm]\n\\textbf{{BILAN : {clean_latex(name)}}} \\hfill \\large \\textbf{{Note : {note_label}}}\\end{{tcolorbox}}\n"

            if app: latex += f"\\vspace{{5pt}}\\begin{{tcolorbox}}[colback=white, colframe=black!50, title=Appréciation, sharp corners, boxrule=0.5pt]{clean_latex(app)}\\end{{tcolorbox}}\n"

            if not is_abs:
                for idx_e, s_row in enumerate(indices_exos):
                    e_row = indices_exos[idx_e+1] if idx_e+1 < len(indices_exos) else len(dataframe)
                    latex += f"\\vspace{{2pt}}\\noindent\\colorbox{{gray!20}}{{\\makebox[\\textwidth][l]{{\\small\\textbf{{{clean_latex(dataframe.iloc[s_row, 2])}}} --- Score : {dataframe.iloc[s_row, p_idx]} / {dataframe.iloc[s_row, 3]}}}}}\n\\begin{{tabularx}}{{\\textwidth}}{{|l|X|c|c|c|}}\\hline \\textbf{{N°}} & \\textbf{{Description}} & \\textbf{{Etat}} & \\textbf{{Note}} & \\textbf{{Max}} \\\\ \\hline\n"
                    for i in range(s_row + 1, e_row):
                        if pd.notna(dataframe.iloc[i, 1]):
                            q_s, q_m = clean_float(dataframe.iloc[i, p_idx]), clean_float(dataframe.iloc[i, 3])
                            # SYMBOLIQUE DIFFÉRENCIÉE
                            symb = r"\textcolor{green!60!black}{\ding{52}}" if q_s == q_m and q_m > 0 else r"\textcolor{orange}{\ding{46}}" if q_s > 0 else r"\textcolor{red!70!black}{\ding{56}}"
                            latex += f"{format_q_num(dataframe.iloc[i,1])} & {clean_latex(dataframe.iloc[i,2])[:90]} & {symb} & {format_excel(q_s)} & {format_excel(q_m)} \\\\ \\hline\n"
                    latex += "\\end{tabularx}\n"
            
            latex += "\\clearpage\n"
        except: continue
    return latex + "\\end{document}"

# --- 7. SIDEBAR ---
bareme_reel_total = sum([v[1] for v in scores_recap.values()])
st.sidebar.header("📊 RÉCAPITULATIF")
for e, v in scores_recap.items(): st.sidebar.write(f"**{e}** : {round(v[0],2)} / {v[1]}")
st.sidebar.divider()
st.sidebar.metric("SCORE TOTAL", f"{round(total_global, 2)} / {bareme_reel_total}")

if st.sidebar.button("💾 ENREGISTRER (CSV)", use_container_width=True):
    df.iloc[1, col_pts] = format_excel(total_global)
    for idx_e, s_row in enumerate(indices_exos): df.iloc[s_row, col_pts] = format_excel(scores_recap[df.iloc[s_row, 2]][0])
    df.to_csv(file_path, index=False, header=False, sep=';', decimal=',', encoding='utf-8-sig')
    st.sidebar.success("Fichier enregistré !")

if st.sidebar.button("👁️ Tableau de bord", use_container_width=True): show_class_summary(st.session_state.df)
st.sidebar.divider()
if st.sidebar.button(f"📄 Fiche {selected_student}"): st.sidebar.download_button("📥 .tex", generate_full_pdf_tex(df, [selected_student]), f"Bilan_{selected_student}.tex")
if st.sidebar.button("📚 Toute la classe"): st.sidebar.download_button("📥 .tex", generate_full_pdf_tex(df, student_names), "Fiches_NSI.tex")
