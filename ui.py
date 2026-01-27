import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import customtkinter as ctk
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import DateEntry
import json
import os
import csv
import shutil

from database import Database
from logic import CalculadoraPreco

# --- INTERFACE GRÁFICA (GUI) ---

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Protótipo de Gestão de Projetos - Por Victor")
        self.geometry("1100x700")

        # --- DESIGN SYSTEM (CORES) ---
        self.col_bg = "#0f172a"       # Dark Blue/Black
        self.col_card = "#1e293b"     # Lighter Dark
        self.col_accent = "#8b5cf6"   # Neon Purple
        self.col_success = "#10b981"  # Cyber Green
        self.col_text = "#f1f5f9"     # White-ish
        self.col_text_muted = "#94a3b8" # Gray

        self.configure(fg_color=self.col_bg)

        # --- DEFINIÇÃO DE FONTES (DESIGN SYSTEM) ---
        self.font_title = ctk.CTkFont(family="Segoe UI", size=24, weight="bold")
        self.font_subtitle = ctk.CTkFont(family="Segoe UI", size=18, weight="bold")
        self.font_label = ctk.CTkFont(family="Segoe UI", size=14)
        self.font_metric_value = ctk.CTkFont(family="Segoe UI", size=28, weight="bold")
        self.font_default = ctk.CTkFont(family="Segoe UI", size=12)

        self.db = Database()
        self.calc = CalculadoraPreco(self.db)

        self.editing_project_id = None # Control flag for Edit Mode

        # Estilo Treeview (Dark Mode Compat)
        style = ttk.Style()
        style.theme_use("clam")

        # Estilo do Corpo da Tabela
        style.configure("Treeview",
                        background=self.col_card,
                        foreground=self.col_text,
                        rowheight=45,
                        fieldbackground=self.col_card,
                        borderwidth=0,
                        font=self.font_label)
        style.map('Treeview', background=[('selected', self.col_accent)], foreground=[('selected', 'white')])

        # Estilo do Cabeçalho
        style.configure("Treeview.Heading",
                        background=self.col_bg,
                        foreground=self.col_text,
                        relief="flat",
                        font=('Segoe UI', 12, 'bold'))
        style.map("Treeview.Heading",
                    background=[('active', self.col_card)])

        # Container Principal (Tabview)
        # Customizing Tabview to fit the dark theme better if possible,
        # but mostly relying on the content frames to carry the design.
        self.tabview = ctk.CTkTabview(self, fg_color=self.col_bg,
                                      segmented_button_fg_color=self.col_card,
                                      segmented_button_selected_color=self.col_accent,
                                      segmented_button_selected_hover_color=self.col_accent,
                                      segmented_button_unselected_hover_color=self.col_card)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        self.tabview.add("Home")
        self.tabview.add("Meus Projetos")
        self.tabview.add("Novo Orçamento")
        self.tabview.add("Catálogo")
        self.tabview.add("Config. Financeira")

        # Inicialização das Telas
        self.create_tab_home()
        self.create_tab_projetos()
        self.create_tab_novo_orcamento()
        self.create_tab_catalogo()
        self.create_tab_config()

    def create_tab_home(self):
        self.tab_home = self.tabview.tab("Home")

        # Header: Greeting & Filter (Banner Style)
        self.frame_header = ctk.CTkFrame(self.tab_home, fg_color=self.col_card, corner_radius=10)
        self.frame_header.pack(fill="x", padx=20, pady=15)

        self.lbl_greeting = ctk.CTkLabel(self.frame_header, text="", font=self.font_title)
        self.lbl_greeting.pack(side="left", padx=20, pady=15)

        self.combo_filter = ctk.CTkComboBox(self.frame_header,
                                            values=["Todos", "Este Mês", "Este Ano"],
                                            command=self.update_dashboard,
                                            width=150,
                                            fg_color=self.col_bg,
                                            button_color=self.col_accent,
                                            button_hover_color=self.col_accent,
                                            border_color=self.col_card)
        self.combo_filter.set("Todos")
        self.combo_filter.pack(side="right", padx=20)

        # Container de Métricas
        self.metrics_frame = ctk.CTkFrame(self.tab_home, fg_color="transparent")
        self.metrics_frame.pack(fill="x", padx=10, pady=5)

        # Container de Meta
        self.frame_meta = ctk.CTkFrame(self.tab_home, fg_color="transparent")
        self.frame_meta.pack(fill="x", padx=30, pady=10)

        self.lbl_meta_title = ctk.CTkLabel(self.frame_meta, text="Meta Mensal", font=self.font_label, text_color=self.col_text_muted)
        self.lbl_meta_title.pack(anchor="w")

        self.progress_meta = ctk.CTkProgressBar(self.frame_meta, progress_color=self.col_success, fg_color=self.col_card)
        self.progress_meta.pack(fill="x", pady=5)
        self.progress_meta.set(0)

        self.lbl_meta_val = ctk.CTkLabel(self.frame_meta, text="R$ 0 / R$ 0", font=self.font_default)
        self.lbl_meta_val.pack(anchor="e")

        # Container de Gráficos
        self.frame_charts = ctk.CTkFrame(self.tab_home, fg_color="transparent")
        self.frame_charts.pack(fill="both", expand=True, padx=20, pady=10)

        # Initial Load
        self.update_dashboard()

    def update_dashboard(self, _=None):
        # 1. Update Greeting
        now = datetime.now()
        hour = now.hour
        greeting = "Bom dia" if 5 <= hour < 12 else "Boa tarde" if 12 <= hour < 18 else "Boa noite"

        cfg = self.db.get_config()
        user_name = cfg[6] if len(cfg) > 6 else "Usuário"
        meta_mensal = cfg[5] if len(cfg) > 5 else 10000.0

        self.lbl_greeting.configure(text=f"{greeting}, {user_name}!")

        # 2. Get Data based on Filter
        filtro = self.combo_filter.get()
        f_mes, f_ano = None, None

        if filtro == "Este Mês":
            f_mes = now.strftime("%m")
            f_ano = now.strftime("%Y")
        elif filtro == "Este Ano":
            f_ano = now.strftime("%Y")

        metrics = self.db.get_dashboard_metrics(filtro_mes=f_mes, filtro_ano=f_ano)

        # 3. Update Metrics Cards (Clear & Recreate)
        for widget in self.metrics_frame.winfo_children():
            widget.destroy()

        self.create_metric_card(self.metrics_frame, "Total Orçado", f"R$ {metrics['total_orcado']:.2f}", self.col_accent, 0, icon="💰")
        self.create_metric_card(self.metrics_frame, "Projetos na Base", f"{metrics['total_projetos']}", self.col_success, 1, icon="📂")
        self.create_metric_card(self.metrics_frame, "Ticket Médio", f"R$ {metrics['ticket_medio']:.2f}", "#F59E0B", 2, icon="📈")

        # 4. Update Meta Progress
        metrics_month = self.db.get_dashboard_metrics(filtro_mes=now.strftime("%m"), filtro_ano=now.strftime("%Y"))
        val_month = metrics_month['total_orcado']

        progress = val_month / meta_mensal if meta_mensal > 0 else 0
        if progress > 1: progress = 1

        self.progress_meta.set(progress)
        self.lbl_meta_val.configure(text=f"R$ {val_month:.2f} / R$ {meta_mensal:.2f}")

        # 5. Charts
        for widget in self.frame_charts.winfo_children():
            widget.destroy()

        # Matplotlib Pie Chart (Status Distribution)
        status_data = metrics['status_dist'] # List of tuples (status, count)

        if status_data:
            labels = [x[0] for x in status_data]
            sizes = [x[1] for x in status_data]
            colors_map = {
                "Orçamento": "#F59E0B",
                "Aprovado": self.col_success,
                "Em Execução": "#3B82F6",
                "Concluído": "#64748B"
            }
            colors_list = [colors_map.get(l, "#94A3B8") for l in labels]

            fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
            fig.patch.set_facecolor(self.col_card)
            ax.set_facecolor(self.col_card)

            wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                              startangle=90, colors=colors_list,
                                              textprops=dict(color=self.col_text))

            # Make text/autotext visible on dark
            plt.setp(texts, color=self.col_text)
            plt.setp(autotexts, color="white", weight="bold")

            ax.axis('equal')
            ax.set_title(f"Status dos Projetos ({filtro})", color=self.col_text, fontsize=12, weight="bold")

            canvas = FigureCanvasTkAgg(fig, master=self.frame_charts)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(self.frame_charts, text="Sem dados para exibir gráfico", font=self.font_label, text_color=self.col_text_muted).pack(pady=20)

    def create_metric_card(self, parent, title, value, color, col_idx, icon="📊"):
        # Main Card Frame
        card = ctk.CTkFrame(parent, fg_color=self.col_card, corner_radius=15)
        card.grid(row=0, column=col_idx, padx=10, pady=10, sticky="ew")
        parent.grid_columnconfigure(col_idx, weight=1)

        # Colored Strip (Left)
        strip = ctk.CTkFrame(card, fg_color=color, width=5, corner_radius=5)
        strip.pack(side="left", fill="y", padx=(0, 10))

        # Content Frame
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(content, text=title, text_color=self.col_text_muted, font=self.font_label).pack(anchor="w", pady=(10, 0))
        ctk.CTkLabel(content, text=value, text_color="white", font=self.font_metric_value).pack(anchor="w", pady=(5, 15))

        # Icon (Right/Background) - Simulated Watermark
        lbl_icon = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=40), text_color="#334155")
        lbl_icon.place(relx=1.0, rely=0.5, anchor="e", x=-15)

    # --- ABA 1: MEUS PROJETOS ---
    def create_tab_projetos(self):
        frame = self.tabview.tab("Meus Projetos")

        # Search Bar
        frame_search = ctk.CTkFrame(frame, fg_color="transparent")
        frame_search.pack(fill="x", padx=10, pady=(10, 5))

        self.entry_search = ctk.CTkEntry(frame_search, placeholder_text="🔍 Pesquisar Cliente...",
                                         height=40, border_width=0, fg_color=self.col_card)
        self.entry_search.pack(fill="x")
        self.entry_search.bind("<KeyRelease>", lambda e: self.refresh_projetos(self.entry_search.get()))

        # Treeview
        columns = ("id", "cliente", "data", "status", "preco")
        self.tree_proj = ttk.Treeview(frame, columns=columns, show='headings')

        # Sortable Headers
        for col in columns:
            self.tree_proj.heading(col, text=col.capitalize(),
                                   command=lambda c=col: self.sort_treeview(self.tree_proj, c, False))

        self.tree_proj.heading("id", text="#")
        self.tree_proj.heading("data", text="Data Entrega")
        self.tree_proj.heading("preco", text="Preço")

        self.tree_proj.column("id", width=40)
        self.tree_proj.column("status", width=120)
        self.tree_proj.column("data", width=100)

        self.tree_proj.pack(fill='both', expand=True, padx=10, pady=10)

        # Bind Double Click
        self.tree_proj.bind("<Double-1>", self.on_double_click_project)

        frame_btns = ctk.CTkFrame(frame, fg_color="transparent")
        frame_btns.pack(pady=10)

        # Row 1 Buttons
        # Atualizar
        ctk.CTkButton(frame_btns, text="🔄", width=40, command=lambda: self.refresh_projetos(),
                      fg_color=self.col_card, hover_color=self.col_bg).grid(row=0, column=0, padx=5)

        # Editar
        ctk.CTkButton(frame_btns, text="✏️ Editar", command=self.editar_projeto,
                      fg_color=self.col_accent, hover_color="#7c3aed").grid(row=0, column=1, padx=5)

        # Duplicar
        ctk.CTkButton(frame_btns, text="🐑 Duplicar", command=self.duplicar_projeto,
                      fg_color="#8E44AD", hover_color="#9B59B6").grid(row=0, column=2, padx=5)

        # Status
        ctk.CTkButton(frame_btns, text="🏷️ Status", command=self.alterar_status,
                      fg_color="#E67E22", hover_color="#D35400").grid(row=0, column=3, padx=5)

        # PDF
        ctk.CTkButton(frame_btns, text="📄 PDF", command=self.gerar_pdf,
                      fg_color=self.col_success, hover_color="#059669").grid(row=0, column=4, padx=5)

        # Excluir
        ctk.CTkButton(frame_btns, text="🗑️", width=40, command=self.excluir_projeto,
                      fg_color="#EF4444", hover_color="#DC2626").grid(row=0, column=5, padx=5)

        self.refresh_projetos()

    def sort_treeview(self, tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        try:
            l.sort(key=lambda t: float(t[0].replace('R$','').replace(',','')))
        except ValueError:
            l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)

        tv.heading(col, command=lambda: self.sort_treeview(tv, col, not reverse))

    # --- ABA 2: NOVO ORÇAMENTO ---
    def create_tab_novo_orcamento(self):
        tab = self.tabview.tab("Novo Orçamento")

        # Grid Layout
        tab.columnconfigure(0, weight=3) # Form
        tab.columnconfigure(1, weight=1) # Preview
        tab.rowconfigure(0, weight=1)

        # Left: Form
        self.frame_orc_form = ctk.CTkFrame(tab, fg_color="transparent")
        self.frame_orc_form.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Right: Preview (Sidebar style)
        self.frame_orc_preview = ctk.CTkFrame(tab, fg_color=self.col_card, corner_radius=15, border_width=1, border_color="#334155")
        self.frame_orc_preview.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # --- FORM BUILD ---
        # 1. Client & Date
        f_client = ctk.CTkFrame(self.frame_orc_form, fg_color="transparent")
        f_client.pack(fill="x", pady=5)

        ctk.CTkLabel(f_client, text="Cliente:", font=self.font_label).pack(anchor="w")
        self.entry_cliente = ctk.CTkEntry(f_client, height=40, placeholder_text="Nome do Cliente",
                                          fg_color=self.col_card, border_width=0)
        self.entry_cliente.pack(fill="x", pady=(2, 10))
        self.entry_cliente.bind("<KeyRelease>", self.update_live_preview) # Live Update

        ctk.CTkLabel(f_client, text="Previsão de Entrega:", font=self.font_label).pack(anchor="w")
        try:
            self.entry_data = DateEntry(f_client, width=12, background=self.col_accent,
                                        foreground='white', borderwidth=0, headersbackground=self.col_card,
                                        normalbackground=self.col_card, normalforeground='white')
        except:
             # Fallback if tkcalendar fails or locale issue
             self.entry_data = ctk.CTkEntry(f_client, placeholder_text="dd/mm/aaaa", height=40, fg_color=self.col_card, border_width=0)

        self.entry_data.pack(anchor="w", pady=(2, 10))
        # Bind for DateEntry
        if hasattr(self.entry_data, 'bind'):
             self.entry_data.bind("<<DateEntrySelected>>", self.update_live_preview)
             self.entry_data.bind("<KeyRelease>", self.update_live_preview)

        # 2. Extras
        f_costs = ctk.CTkFrame(self.frame_orc_form, fg_color="transparent")
        f_costs.pack(fill="x", pady=5)

        ctk.CTkLabel(f_costs, text="Custos Extras (R$):", font=self.font_label).pack(anchor="w")
        self.entry_extras = ctk.CTkEntry(f_costs, height=40, placeholder_text="0.00",
                                         fg_color=self.col_card, border_width=0)
        self.entry_extras.pack(fill="x", pady=(2, 10))
        self.entry_extras.bind("<KeyRelease>", self.update_live_preview)

        # 3. Services List (Scrollable)
        header_frame = ctk.CTkFrame(self.frame_orc_form, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 5))
        ctk.CTkLabel(header_frame, text="Escopo do Projeto:", font=self.font_title).pack(side="left")
        ctk.CTkButton(header_frame, text="🔄", width=30, command=self.carregar_checkboxes_tarefas,
                      fg_color=self.col_card, hover_color=self.col_bg).pack(side="right")

        self.scrollable_frame = ctk.CTkScrollableFrame(self.frame_orc_form, label_text="Selecione os Serviços",
                                                       fg_color=self.col_card, label_fg_color=self.col_bg)
        self.scrollable_frame.pack(fill="both", expand=True, pady=5)

        # --- PREVIEW BUILD ---
        ctk.CTkLabel(self.frame_orc_preview, text="Resumo do Orçamento", font=self.font_title, text_color="white").pack(pady=20)

        self.lbl_prev_horas = ctk.CTkLabel(self.frame_orc_preview, text="Horas: 0h", font=self.font_label, text_color=self.col_text_muted)
        self.lbl_prev_horas.pack(pady=5)

        self.lbl_prev_custo = ctk.CTkLabel(self.frame_orc_preview, text="Custo Prod: R$ 0.00", font=self.font_label, text_color=self.col_text_muted)
        self.lbl_prev_custo.pack(pady=5)

        self.lbl_prev_lucro = ctk.CTkLabel(self.frame_orc_preview, text="Lucro Líq: R$ 0.00", font=self.font_label, text_color=self.col_text_muted)
        self.lbl_prev_lucro.pack(pady=5)

        ctk.CTkFrame(self.frame_orc_preview, height=2, fg_color="#334155").pack(fill="x", padx=20, pady=10) # Divider

        self.lbl_prev_total = ctk.CTkLabel(self.frame_orc_preview, text="R$ 0.00", font=ctk.CTkFont(size=36, weight="bold"), text_color=self.col_success)
        self.lbl_prev_total.pack(pady=10)

        # Save Button
        ctk.CTkButton(self.frame_orc_preview, text="💾 Salvar/Gerar Projeto", command=self.finalizar_orcamento,
                      fg_color=self.col_success, hover_color="#059669", height=50, font=ctk.CTkFont(weight="bold")).pack(side="bottom", padx=20, pady=20, fill="x")

        # Cancel/Clear Button
        ctk.CTkButton(self.frame_orc_preview, text="❌ Limpar / Cancelar", command=self.cancelar_edicao,
                      fg_color="#EF4444", hover_color="#DC2626").pack(side="bottom", padx=20, pady=(0, 5), fill="x")

        # Load Data
        self.check_vars = []
        self.carregar_checkboxes_tarefas()

        # Restore Draft
        self.after(500, self.load_draft) # Slight delay to ensure widgets ready

    def carregar_checkboxes_tarefas(self):
        # Limpa área antiga
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Puxa do Banco de Dados
        servicos = self.db.get_servicos() # id, nome, horas, categoria

        # Group by Category
        grouped = {}
        for s in servicos:
            cat = s[3] if s[3] else "Geral"
            if cat not in grouped: grouped[cat] = []
            grouped[cat].append(s)

        self.check_vars = []

        for cat in sorted(grouped.keys()):
            # Category Header
            ctk.CTkLabel(self.scrollable_frame, text=cat, font=ctk.CTkFont(weight="bold", size=13)).pack(anchor="w", pady=(10, 2))
            for sid, nome, horas, _ in grouped[cat]:
                var = ctk.BooleanVar(value=False)
                # Bind command to update preview
                chk = ctk.CTkCheckBox(self.scrollable_frame, text=f"{nome} ({horas}h)", variable=var,
                                      command=self.update_live_preview)
                chk.pack(anchor="w", padx=10, pady=2)
                self.check_vars.append((var, horas, nome, sid))

    # --- ABA 3: CATÁLOGO DE SERVIÇOS (NOVA) ---
    def create_tab_catalogo(self):
        tab = self.tabview.tab("Catálogo")

        # Container principal
        container = ctk.CTkFrame(tab, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Lado Esquerdo: Formulário
        frame_form = ctk.CTkFrame(container, fg_color=self.col_card)
        frame_form.pack(side='left', fill='y', padx=10, pady=10)

        ctk.CTkLabel(frame_form, text="Adicionar Serviço", font=self.font_title).pack(pady=10)

        ctk.CTkLabel(frame_form, text="Nome da Tarefa:", font=self.font_label).pack(anchor='w', padx=10, pady=(5, 2))
        self.entry_novo_servico = ctk.CTkEntry(frame_form, width=200, height=40, placeholder_text="Ex: Modelagem 3D",
                                               fg_color=self.col_bg, border_width=0)
        self.entry_novo_servico.pack(padx=10, pady=5)

        ctk.CTkLabel(frame_form, text="Categoria:", font=self.font_label).pack(anchor='w', padx=10, pady=(5, 2))
        self.combo_nova_cat = ctk.CTkComboBox(frame_form, values=["Pré-Projeto", "Execução", "Pós-Produção", "Geral"],
                                              fg_color=self.col_bg, button_color=self.col_accent)
        self.combo_nova_cat.pack(padx=10, pady=5)

        ctk.CTkLabel(frame_form, text="Horas Padrão:", font=self.font_label).pack(anchor='w', padx=10, pady=(5, 2))
        self.entry_novas_horas = ctk.CTkEntry(frame_form, width=200, height=40, placeholder_text="Ex: 4.5",
                                              fg_color=self.col_bg, border_width=0)
        self.entry_novas_horas.pack(padx=10, pady=5)

        # Adicionar -> Positivo
        ctk.CTkButton(frame_form, text="➕ Adicionar", command=self.adicionar_servico_db,
                      fg_color=self.col_success, hover_color="#059669").pack(pady=15, padx=10, fill="x")

        ctk.CTkLabel(frame_form, text="Ferramentas CSV", font=self.font_title).pack(pady=(20, 10))

        ctk.CTkButton(frame_form, text="📂 Importar CSV", command=self.importar_csv,
                      fg_color=self.col_bg, hover_color="#334155").pack(pady=5, padx=10, fill="x")

        ctk.CTkButton(frame_form, text="💾 Exportar CSV", command=self.exportar_csv,
                      fg_color=self.col_bg, hover_color="#334155").pack(pady=5, padx=10, fill="x")

        # Excluir -> Destrutivo
        ctk.CTkButton(frame_form, text="🗑️ Excluir Selecionado", command=self.excluir_servico_db,
                      fg_color="#EF4444", hover_color="#DC2626").pack(side="bottom", pady=20, padx=10, fill="x")

        # Lado Direito: Lista
        frame_list = ctk.CTkFrame(container, fg_color="transparent")
        frame_list.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        # Filter
        self.combo_cat_filter = ctk.CTkComboBox(frame_list, values=["Todas", "Pré-Projeto", "Execução", "Pós-Produção", "Geral"],
                                                command=lambda x: self.refresh_catalogo(),
                                                fg_color=self.col_card, button_color=self.col_accent)
        self.combo_cat_filter.set("Todas")
        self.combo_cat_filter.pack(anchor="ne", pady=5)

        colunas = ("id", "nome", "horas", "categoria")
        self.tree_cat = ttk.Treeview(frame_list, columns=colunas, show='headings')
        self.tree_cat.heading("id", text="ID")
        self.tree_cat.heading("nome", text="Serviço")
        self.tree_cat.heading("horas", text="Horas")
        self.tree_cat.heading("categoria", text="Categoria")

        self.tree_cat.column("id", width=30)
        self.tree_cat.column("horas", width=60)
        self.tree_cat.column("categoria", width=100)

        self.tree_cat.pack(fill='both', expand=True)
        self.tree_cat.bind("<Double-1>", self.editar_servico_modal)

        self.refresh_catalogo()

    # --- ABA 4: CONFIGURAÇÕES FINANCEIRAS ---
    def create_tab_config(self):
        tab = self.tabview.tab("Config. Financeira")

        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(0, weight=1)

        # --- LEFT: Costs Table ---
        frame_costs = ctk.CTkFrame(tab)
        frame_costs.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(frame_costs, text="Custos Operacionais", font=self.font_title).pack(pady=10)

        cols = ("id", "desc", "val")
        self.tree_custos = ttk.Treeview(frame_costs, columns=cols, show="headings", height=15)
        self.tree_custos.heading("desc", text="Descrição")
        self.tree_custos.heading("val", text="Valor (R$)")
        self.tree_custos.column("id", width=0, stretch=False)
        self.tree_custos.pack(fill="both", expand=True, padx=10, pady=5)

        self.lbl_total_custos = ctk.CTkLabel(frame_costs, text="Total: R$ 0.00", font=self.font_label)
        self.lbl_total_custos.pack(pady=5)

        frame_input_costs = ctk.CTkFrame(frame_costs, fg_color="transparent")
        frame_input_costs.pack(fill="x", padx=10, pady=10)

        self.entry_desc_custo = ctk.CTkEntry(frame_input_costs, height=40, placeholder_text="Descrição",
                                             fg_color=self.col_card, border_width=0)
        self.entry_desc_custo.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.entry_valor_custo = ctk.CTkEntry(frame_input_costs, width=100, height=40, placeholder_text="0.00",
                                              fg_color=self.col_card, border_width=0)
        self.entry_valor_custo.pack(side="left", padx=5)

        ctk.CTkButton(frame_input_costs, text="+", width=40, command=self.add_custo_ui,
                      fg_color=self.col_success, hover_color="#059669").pack(side="left")

        ctk.CTkButton(frame_input_costs, text="🗑️", width=40, command=self.del_custo_ui,
                      fg_color="#EF4444", hover_color="#DC2626").pack(side="left", padx=5)

        self.refresh_custos_ui()

        # --- RIGHT: Params ---
        frame_params = ctk.CTkFrame(tab)
        frame_params.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(frame_params, text="Parâmetros Gerais", font=self.font_title).pack(pady=10)

        cfg = self.db.get_config()
        # cfg: id, custo, horas, imposto, lucro, meta, nome

        # Usuario
        ctk.CTkLabel(frame_params, text="Nome de Usuário:", font=self.font_label).pack(anchor="w", padx=20)
        self.entry_usuario = ctk.CTkEntry(frame_params, height=35, fg_color=self.col_card, border_width=0)
        self.entry_usuario.insert(0, cfg[6] if len(cfg)>6 else "Usuário")
        self.entry_usuario.pack(padx=20, fill="x", pady=(0,10))

        # Horas
        ctk.CTkLabel(frame_params, text="Horas Produtivas/Mês:", font=self.font_label).pack(anchor="w", padx=20)
        self.entry_horas = ctk.CTkEntry(frame_params, height=35, fg_color=self.col_card, border_width=0)
        self.entry_horas.insert(0, cfg[2])
        self.entry_horas.pack(padx=20, fill="x", pady=(0,10))

        # Meta
        ctk.CTkLabel(frame_params, text="Meta de Faturamento Mensal (R$):", font=self.font_label).pack(anchor="w", padx=20)
        self.entry_meta = ctk.CTkEntry(frame_params, height=35, fg_color=self.col_card, border_width=0)
        self.entry_meta.insert(0, cfg[5] if len(cfg)>5 else 10000.0)
        self.entry_meta.pack(padx=20, fill="x", pady=(0,10))

        # Tax Profile
        ctk.CTkLabel(frame_params, text="Perfil Tributário:", font=self.font_label).pack(anchor="w", padx=20)
        self.combo_tax = ctk.CTkComboBox(frame_params, values=["Personalizado", "MEI (0%)", "Simples (6%)", "Lucro Presumido (16.33%)"],
                                         command=self.update_tax_profile, fg_color=self.col_card, button_color=self.col_accent)
        self.combo_tax.pack(padx=20, fill="x", pady=(0,10))
        self.combo_tax.set("Personalizado")

        # Sliders
        # Impostos
        ctk.CTkLabel(frame_params, text="Impostos (%):", font=self.font_label).pack(anchor="w", padx=20)

        frame_imp = ctk.CTkFrame(frame_params, fg_color="transparent")
        frame_imp.pack(fill="x", padx=20, pady=(0, 10))

        self.slider_imposto = ctk.CTkSlider(frame_imp, from_=0, to=40, command=self.update_slider_labels,
                                            button_color=self.col_accent, progress_color=self.col_accent)
        self.slider_imposto.set(cfg[3])
        self.slider_imposto.pack(side="left", fill="x", expand=True)

        self.lbl_imposto_val = ctk.CTkLabel(frame_imp, text=f"{cfg[3]}%", width=50, font=ctk.CTkFont(weight="bold"))
        self.lbl_imposto_val.pack(side="right", padx=(10,0))

        # Lucro
        ctk.CTkLabel(frame_params, text="Margem de Lucro (%):", font=self.font_label).pack(anchor="w", padx=20)

        frame_lucro = ctk.CTkFrame(frame_params, fg_color="transparent")
        frame_lucro.pack(fill="x", padx=20, pady=(0, 10))

        self.slider_lucro = ctk.CTkSlider(frame_lucro, from_=0, to=100, command=self.update_slider_labels,
                                          button_color=self.col_accent, progress_color=self.col_accent)
        self.slider_lucro.set(cfg[4])
        self.slider_lucro.pack(side="left", fill="x", expand=True)

        self.lbl_lucro_val = ctk.CTkLabel(frame_lucro, text=f"{cfg[4]}%", width=50, font=ctk.CTkFont(weight="bold"))
        self.lbl_lucro_val.pack(side="right", padx=(10,0))

        # Salvar -> Positivo
        ctk.CTkButton(frame_params, text="💾 Salvar Configurações", command=self.save_config,
                      fg_color=self.col_success, hover_color="#059669").pack(pady=20, padx=20, fill="x")

        # Backup/Restore
        frame_bkp = ctk.CTkFrame(frame_params, fg_color="transparent")
        frame_bkp.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(frame_bkp, text="☁️ Backup", command=self.backup_db, width=100,
                      fg_color=self.col_card, hover_color=self.col_bg).pack(side="left", padx=5, expand=True)
        ctk.CTkButton(frame_bkp, text="🔄 Restore", command=self.restore_db, width=100,
                      fg_color="#EF4444", hover_color="#DC2626").pack(side="right", padx=5, expand=True)

    def update_slider_labels(self, _=None):
        self.lbl_imposto_val.configure(text=f"{int(self.slider_imposto.get())}%")
        self.lbl_lucro_val.configure(text=f"{int(self.slider_lucro.get())}%")

    def update_tax_profile(self, choice):
        if choice == "MEI (0%)":
            self.slider_imposto.set(0)
        elif choice == "Simples (6%)":
            self.slider_imposto.set(6)
        elif choice == "Lucro Presumido (16.33%)":
            self.slider_imposto.set(16.33)
        self.update_slider_labels()

    def backup_db(self):
        filename = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite DB", "*.db")])
        if filename:
            try:
                shutil.copy("meus_projetos.db", filename)
                messagebox.showinfo("Sucesso", "Backup realizado!")
            except Exception as e:
                messagebox.showerror("Erro", str(e))

    def restore_db(self):
        filename = filedialog.askopenfilename(filetypes=[("SQLite DB", "*.db")])
        if filename:
            if messagebox.askyesno("Cuidado", "Isso irá substituir todos os seus dados atuais. Continuar?"):
                try:
                    self.db.conn.close() # Close connection before overwrite
                    shutil.copy(filename, "meus_projetos.db")
                    # Reconnect
                    self.db = Database()
                    self.calc = CalculadoraPreco(self.db)
                    messagebox.showinfo("Sucesso", "Backup restaurado! O sistema será atualizado.")
                    self.update_dashboard()
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao restaurar: {e}")

    def importar_csv(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not filename: return

        try:
            with open(filename, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                count = 0
                for row in reader:
                    # Expect headers: Nome, Horas, Categoria
                    nome = row.get("Nome", row.get("nome"))
                    horas = row.get("Horas", row.get("horas"))
                    cat = row.get("Categoria", row.get("categoria", "Geral"))
                    if nome and horas:
                        self.db.add_servico(nome, float(horas), cat)
                        count += 1
            messagebox.showinfo("Sucesso", f"{count} serviços importados!")
            self.refresh_catalogo()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao importar: {e}")

    def exportar_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not filename: return

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["ID", "Nome", "Horas", "Categoria"])
                for s in self.db.get_servicos():
                    writer.writerow(s)
            messagebox.showinfo("Sucesso", "Catálogo exportado!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {e}")

    def editar_servico_modal(self, event):
        selected = self.tree_cat.selection()
        if not selected: return

        item = self.tree_cat.item(selected[0])
        vals = item['values'] # id, nome, horas, categoria

        win = ctk.CTkToplevel(self)
        win.title("Editar Serviço")
        win.geometry("300x300")

        ctk.CTkLabel(win, text="Nome:").pack(pady=5)
        e_nome = ctk.CTkEntry(win)
        e_nome.insert(0, vals[1])
        e_nome.pack(pady=5)

        ctk.CTkLabel(win, text="Horas:").pack(pady=5)
        e_horas = ctk.CTkEntry(win)
        e_horas.insert(0, vals[2])
        e_horas.pack(pady=5)

        ctk.CTkLabel(win, text="Categoria:").pack(pady=5)
        e_cat = ctk.CTkComboBox(win, values=["Pré-Projeto", "Execução", "Pós-Produção", "Geral"])
        e_cat.set(vals[3])
        e_cat.pack(pady=5)

        def save_edit():
            self.db.cursor.execute("UPDATE catalogo_servicos SET nome=?, horas_padrao=?, categoria=? WHERE id=?",
                                   (e_nome.get(), float(e_horas.get()), e_cat.get(), vals[0]))
            self.db.conn.commit()
            self.refresh_catalogo()
            win.destroy()

        ctk.CTkButton(win, text="Salvar", command=save_edit).pack(pady=20)

    # --- FUNÇÕES DE AÇÃO ---

    def refresh_custos_ui(self):
        for row in self.tree_custos.get_children():
            self.tree_custos.delete(row)
        custos = self.db.get_custos_operacionais()
        total = 0
        for c in custos:
            self.tree_custos.insert("", "end", values=(c[0], c[1], f"R$ {c[2]:.2f}"))
            total += c[2]
        self.lbl_total_custos.configure(text=f"Total Calculado: R$ {total:.2f}")

    def add_custo_ui(self):
        desc = self.entry_desc_custo.get()
        val = self.entry_valor_custo.get()
        if desc and val:
            try:
                self.db.add_custo_operacional(desc, float(val))
                self.refresh_custos_ui()
                self.entry_desc_custo.delete(0, 'end')
                self.entry_valor_custo.delete(0, 'end')
            except ValueError:
                messagebox.showerror("Erro", "Valor deve ser numérico.")
        else:
            messagebox.showwarning("Erro", "Preencha descrição e valor.")

    def del_custo_ui(self):
        selected = self.tree_custos.selection()
        if selected:
            item = self.tree_custos.item(selected[0])
            if messagebox.askyesno("Confirmar", "Excluir custo selecionado?"):
                self.db.delete_custo_operacional(item['values'][0])
                self.refresh_custos_ui()

    def refresh_projetos(self, query=None):
        for row in self.tree_proj.get_children():
            self.tree_proj.delete(row)

        sql = "SELECT id, cliente, data_entrega, status, preco_final FROM projetos"
        params = []
        if query:
            sql += " WHERE cliente LIKE ?"
            params.append(f"%{query}%")
        sql += " ORDER BY id DESC"

        self.db.cursor.execute(sql, params)

        status_emojis = {
            "Orçamento": "🟡 Orçamento",
            "Aprovado": "🟢 Aprovado",
            "Em Execução": "🔵 Em Execução",
            "Concluído": "⚪ Concluído"
        }

        for row in self.db.cursor.fetchall():
            # row: id, cliente, data_entrega, status, preco
            st_txt = status_emojis.get(row[3], row[3])
            price = f"R$ {row[4]:.2f}"
            self.tree_proj.insert("", "end", values=(row[0], row[1], row[2], st_txt, price))

    def alterar_status(self):
        selected = self.tree_proj.selection()
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um projeto na lista.")
            return

        item = self.tree_proj.item(selected[0])
        proj_id = item['values'][0]
        current_status = item['values'][2]

        # Janela Modal Simples
        dialog = ctk.CTkToplevel(self)
        dialog.title("Alterar Status")
        dialog.geometry("300x150")
        dialog.transient(self) # Mantém sobre a janela principal
        dialog.grab_set()      # Bloqueia interação com a janela principal

        ctk.CTkLabel(dialog, text="Selecione o Novo Status:", font=self.font_label).pack(pady=15)

        status_options = ["Orçamento", "Aprovado", "Em Execução", "Concluído"]
        combo = ctk.CTkComboBox(dialog, values=status_options)
        combo.set(current_status)
        combo.pack(pady=5)

        def confirm():
            new_status = combo.get()
            self.db.cursor.execute("UPDATE projetos SET status=? WHERE id=?", (new_status, proj_id))
            self.db.conn.commit()
            self.refresh_projetos()
            dialog.destroy()
            messagebox.showinfo("Sucesso", "Status atualizado!")

        # Salvar -> Positivo
        ctk.CTkButton(dialog, text="Salvar", command=confirm,
                      fg_color="#2CC985", hover_color="#25A970").pack(pady=15)

    def gerar_pdf(self):
        selected = self.tree_proj.selection()
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um projeto.")
            return

        item = self.tree_proj.item(selected[0])
        proj_id = item['values'][0]

        # Fetch Data
        self.db.cursor.execute("SELECT * FROM projetos WHERE id=?", (proj_id,))
        proj = self.db.cursor.fetchone() # id, cliente, data, status, extras, preco

        cliente = proj[1]
        # data_criacao = proj[2] # Not used currently
        extras = proj[4]
        preco_final = proj[5]

        self.db.cursor.execute("SELECT descricao, horas_estimadas FROM tarefas_projeto WHERE projeto_id=?", (proj_id,))
        tarefas = self.db.cursor.fetchall()

        # File Dialog
        filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if not filename:
            return

        # PDF Generation
        try:
            c = canvas.Canvas(filename, pagesize=A4)
            width, height = A4

            # Header
            c.setFont("Helvetica-Bold", 20)
            c.drawString(50, height - 50, "Okami Project Manager")
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 70, f"Data da Proposta: {datetime.now().strftime('%d/%m/%Y')}")

            # Client
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, height - 110, f"Cliente: {cliente}")
            c.drawString(50, height - 130, f"Projeto ID: #{proj_id}")

            # Scope Table
            y = height - 170
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y, "Escopo do Projeto")
            y -= 30

            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y, "Descrição da Tarefa")
            c.drawString(400, y, "Horas Estimadas")
            y -= 10
            c.line(50, y, 500, y)
            y -= 20

            c.setFont("Helvetica", 10)
            for desc, horas in tarefas:
                c.drawString(50, y, desc)
                c.drawString(400, y, f"{horas}h")
                y -= 20
                if y < 100: # New Page if low
                    c.showPage()
                    y = height - 50

            # Financial Summary
            y -= 30
            c.line(50, y, 500, y)
            y -= 30

            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y, "Resumo Financeiro")
            y -= 30

            c.setFont("Helvetica", 12)

            # Calculate Service Total
            total_servicos = preco_final - extras

            c.drawString(50, y, f"Total dos Serviços:")
            c.drawRightString(500, y, f"R$ {total_servicos:.2f}")
            y -= 20

            if extras > 0:
                c.drawString(50, y, f"Custos Extras:")
                c.drawRightString(500, y, f"R$ {extras:.2f}")
                y -= 20

            y -= 10
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y, f"PREÇO TOTAL DO PROJETO:")
            c.drawRightString(500, y, f"R$ {preco_final:.2f}")

            c.save()
            messagebox.showinfo("Sucesso", "PDF Gerado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar PDF: {e}")

    def refresh_catalogo(self):
        for row in self.tree_cat.get_children():
            self.tree_cat.delete(row)

        filter_cat = self.combo_cat_filter.get()
        servicos = self.db.get_servicos()

        for s in servicos:
            # s = (id, nome, horas, categoria)
            if filter_cat == "Todas" or s[3] == filter_cat:
                self.tree_cat.insert("", "end", values=s)

    def adicionar_servico_db(self):
        nome = self.entry_novo_servico.get()
        horas = self.entry_novas_horas.get()
        cat = self.combo_nova_cat.get()
        if nome and horas:
            try:
                self.db.add_servico(nome, float(horas), cat)
                self.refresh_catalogo()
                self.entry_novo_servico.delete(0, 'end')
                self.entry_novas_horas.delete(0, 'end')
                messagebox.showinfo("Sucesso", "Serviço adicionado!")
            except ValueError:
                messagebox.showerror("Erro", "Horas deve ser um número.")
        else:
            messagebox.showwarning("Erro", "Preencha nome e horas.")

    def excluir_servico_db(self):
        selected = self.tree_cat.selection()
        if selected:
            item = self.tree_cat.item(selected[0])
            id_servico = item['values'][0]
            confirm = messagebox.askyesno("Confirmar", f"Excluir '{item['values'][1]}' do catálogo?")
            if confirm:
                self.db.delete_servico(id_servico)
                self.refresh_catalogo()

    def save_config(self):
        try:
            c = self.db.get_total_custos_operacionais()
            h = float(self.entry_horas.get())
            i = float(self.slider_imposto.get())
            l = float(self.slider_lucro.get())
            meta = float(self.entry_meta.get())
            nome = self.entry_usuario.get()

            self.db.update_config(c, h, i, l, meta, nome)
            messagebox.showinfo("Sucesso", "Dados Financeiros Atualizados!")
        except ValueError:
            messagebox.showerror("Erro", "Verifique os números digitados.")

    def update_live_preview(self, _=None):
        # Coleta dados
        horas_totais = 0
        ids_selecionados = []

        for var, horas, nome, sid in self.check_vars:
            if var.get():
                horas_totais += horas
                ids_selecionados.append(sid)

        try:
            extras = float(self.entry_extras.get())
        except:
            extras = 0.0

        res = self.calc.calcular_orcamento(horas_totais, extras)

        # Update UI Labels
        self.lbl_prev_horas.configure(text=f"Horas: {horas_totais}h")
        self.lbl_prev_custo.configure(text=f"Custo Prod: R$ {res['custo_producao']:.2f}")
        self.lbl_prev_lucro.configure(text=f"Lucro Líq: R$ {res['lucro']:.2f}")
        self.lbl_prev_total.configure(text=f"R$ {res['preco_final']:.2f}")

        # Auto-save Draft
        self.save_draft(ids_selecionados)

    def save_draft(self, ids):
        data = {
            "cliente": self.entry_cliente.get(),
            "extras": self.entry_extras.get(),
            "data": self.entry_data.get(),
            "servicos": ids
        }
        try:
            with open("draft.json", "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Erro ao salvar rascunho: {e}")

    def load_draft(self):
        if not os.path.exists("draft.json"):
            return

        try:
            with open("draft.json", "r") as f:
                data = json.load(f)

            self.entry_cliente.delete(0, 'end')
            self.entry_cliente.insert(0, data.get("cliente", ""))

            self.entry_extras.delete(0, 'end')
            self.entry_extras.insert(0, data.get("extras", ""))

            if hasattr(self.entry_data, 'set_date'):
                # Try to parse date, if fail ignore
                try:
                    self.entry_data.set_date(data.get("data", datetime.now()))
                except: pass

            saved_ids = data.get("servicos", [])
            for var, _, _, sid in self.check_vars:
                if sid in saved_ids:
                    var.set(True)
                else:
                    var.set(False)

            self.update_live_preview()
        except Exception as e:
            print(f"Erro ao carregar rascunho: {e}")

    def cancelar_edicao(self):
        if messagebox.askyesno("Confirmar", "Limpar todos os campos e cancelar a edição atual?"):
            self.editing_project_id = None
            self.entry_cliente.delete(0, 'end')
            self.entry_extras.delete(0, 'end')
            try:
                self.entry_data.set_date(datetime.now())
            except: pass
            for var, _, _, _ in self.check_vars: var.set(False)
            self.update_live_preview()

            if os.path.exists("draft.json"):
                os.remove("draft.json")

    def finalizar_orcamento(self):
        horas_totais = 0
        ids_selected = []
        for var, horas, nome, sid in self.check_vars:
            if var.get():
                horas_totais += horas
                ids_selected.append(sid)

        if horas_totais == 0:
            messagebox.showwarning("Atenção", "Selecione pelo menos uma tarefa.")
            return

        try:
            extras = float(self.entry_extras.get())
        except:
            extras = 0.0

        res = self.calc.calcular_orcamento(horas_totais, extras)

        action = "Atualizar Projeto" if self.editing_project_id else "Criar Projeto"
        msg = f"Valor Final: R$ {res['preco_final']:.2f}\nLucro Estimado: R$ {res['lucro']:.2f}\n\nConfirmar {action}?"

        if messagebox.askyesno("Confirmar", msg):
            if self.editing_project_id:
                self.atualizar_projeto_db(res['preco_final'], extras)
            else:
                self.salvar_projeto(res['preco_final'], extras)

    def salvar_projeto(self, preco_final, extras):
        cliente = self.entry_cliente.get()
        if not cliente:
            cliente = "Cliente Sem Nome"

        try:
            data_entrega = self.entry_data.get_date().strftime("%d/%m/%Y")
        except:
            data_entrega = ""

        self.db.cursor.execute("""
            INSERT INTO projetos (cliente, data_criacao, data_entrega, status, custo_extras, preco_final)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cliente, datetime.now().strftime("%Y-%m-%d"), data_entrega, "Orçamento", extras, preco_final))

        proj_id = self.db.cursor.lastrowid

        for var, horas, nome, sid in self.check_vars:
            if var.get():
                self.db.cursor.execute("INSERT INTO tarefas_projeto (projeto_id, descricao, horas_estimadas) VALUES (?, ?, ?)",
                                       (proj_id, nome, horas))

        self.db.conn.commit()
        self._post_save_actions("Projeto Criado!")

    def atualizar_projeto_db(self, preco_final, extras):
        cliente = self.entry_cliente.get()
        try:
            data_entrega = self.entry_data.get_date().strftime("%d/%m/%Y")
        except:
            data_entrega = ""

        self.db.cursor.execute("""
            UPDATE projetos SET cliente=?, data_entrega=?, custo_extras=?, preco_final=?
            WHERE id=?
        """, (cliente, data_entrega, extras, preco_final, self.editing_project_id))

        # Recreate tasks
        self.db.cursor.execute("DELETE FROM tarefas_projeto WHERE projeto_id=?", (self.editing_project_id,))
        for var, horas, nome, sid in self.check_vars:
            if var.get():
                self.db.cursor.execute("INSERT INTO tarefas_projeto (projeto_id, descricao, horas_estimadas) VALUES (?, ?, ?)",
                                       (self.editing_project_id, nome, horas))

        self.db.conn.commit()
        self._post_save_actions("Projeto Atualizado!")

    def _post_save_actions(self, msg):
        # Clear Draft
        if os.path.exists("draft.json"):
            os.remove("draft.json")

        messagebox.showinfo("Sucesso", msg)

        # Reset Form and Mode
        self.editing_project_id = None
        self.entry_cliente.delete(0, 'end')
        self.entry_extras.delete(0, 'end')
        try:
            self.entry_data.set_date(datetime.now())
        except: pass

        for var, _, _, _ in self.check_vars: var.set(False)
        self.update_live_preview()

        # Switch Back
        self.refresh_projetos()
        self.tabview.set("Meus Projetos")

    def editar_projeto(self):
        selected = self.tree_proj.selection()
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um projeto.")
            return

        item = self.tree_proj.item(selected[0])
        pid = item['values'][0]

        self.db.cursor.execute("SELECT * FROM projetos WHERE id=?", (pid,))
        proj = self.db.cursor.fetchone() # id, cliente, data_criacao, data_entrega, status, extras, preco

        # Switch to Tab 3
        self.tabview.set("Novo Orçamento")
        self.editing_project_id = pid

        # Populate
        self.entry_cliente.delete(0, 'end')
        self.entry_cliente.insert(0, proj[1])

        self.entry_extras.delete(0, 'end')
        self.entry_extras.insert(0, proj[5])

        if proj[3] and hasattr(self.entry_data, 'set_date'):
            try:
                dt = datetime.strptime(proj[3], "%d/%m/%Y")
                self.entry_data.set_date(dt)
            except: pass

        # Select Tasks
        self.db.cursor.execute("SELECT descricao FROM tarefas_projeto WHERE projeto_id=?", (pid,))
        tarefas = [t[0] for t in self.db.cursor.fetchall()]

        for var, horas, nome, sid in self.check_vars:
            # We match by name/description since we didn't store service_id in tarefas_projeto originally.
            # Ideally we should match by name.
            if nome in tarefas:
                var.set(True)
            else:
                var.set(False)

        self.update_live_preview()
        messagebox.showinfo("Modo Edição", f"Editando Projeto #{pid}")

    def duplicar_projeto(self):
        selected = self.tree_proj.selection()
        if not selected: return

        pid = self.tree_proj.item(selected[0])['values'][0]

        self.db.cursor.execute("SELECT cliente, data_entrega, status, custo_extras, preco_final FROM projetos WHERE id=?", (pid,))
        orig = self.db.cursor.fetchone()

        cliente_novo = orig[0] + " (Cópia)"

        self.db.cursor.execute("""
            INSERT INTO projetos (cliente, data_criacao, data_entrega, status, custo_extras, preco_final)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cliente_novo, datetime.now().strftime("%Y-%m-%d"), orig[1], "Orçamento", orig[3], orig[4]))

        new_pid = self.db.cursor.lastrowid

        self.db.cursor.execute("SELECT descricao, horas_estimadas FROM tarefas_projeto WHERE projeto_id=?", (pid,))
        tarefas = self.db.cursor.fetchall()

        for t in tarefas:
            self.db.cursor.execute("INSERT INTO tarefas_projeto (projeto_id, descricao, horas_estimadas) VALUES (?, ?, ?)",
                                   (new_pid, t[0], t[1]))

        self.db.conn.commit()
        self.refresh_projetos()
        messagebox.showinfo("Sucesso", "Projeto Duplicado!")

    def excluir_projeto(self):
        selected = self.tree_proj.selection()
        if not selected: return

        pid = self.tree_proj.item(selected[0])['values'][0]

        if messagebox.askyesno("Confirmar", "Excluir permanentemente este projeto?"):
            self.db.cursor.execute("DELETE FROM tarefas_projeto WHERE projeto_id=?", (pid,))
            self.db.cursor.execute("DELETE FROM projetos WHERE id=?", (pid,))
            self.db.conn.commit()
            self.refresh_projetos()
            # Update Dashboard if needed
            self.update_dashboard()

    def on_double_click_project(self, event):
        selected = self.tree_proj.selection()
        if not selected: return
        item = self.tree_proj.item(selected[0])
        pid = item['values'][0]

        # Modal View
        self.db.cursor.execute("SELECT * FROM projetos WHERE id=?", (pid,))
        proj = self.db.cursor.fetchone()

        self.db.cursor.execute("SELECT descricao, horas_estimadas FROM tarefas_projeto WHERE projeto_id=?", (pid,))
        tarefas = self.db.cursor.fetchall()

        win = ctk.CTkToplevel(self)
        win.title(f"Detalhes do Projeto #{pid}")
        win.geometry("400x500")
        win.grab_set()

        ctk.CTkLabel(win, text=proj[1], font=self.font_title).pack(pady=10)
        ctk.CTkLabel(win, text=f"Status: {proj[4]}", font=self.font_label).pack()
        ctk.CTkLabel(win, text=f"Preço: R$ {proj[6]:.2f}", font=self.font_metric_value, text_color="#2CC985").pack(pady=10)

        scroll = ctk.CTkScrollableFrame(win, label_text="Tarefas")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        for t in tarefas:
            ctk.CTkLabel(scroll, text=f"• {t[0]} ({t[1]}h)").pack(anchor="w")
