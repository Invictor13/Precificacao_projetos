import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import customtkinter as ctk
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

from database import Database
from logic import CalculadoraPreco

# --- INTERFACE GRÁFICA (GUI) ---

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Okami Project Manager 2.0 - Local")
        self.geometry("1000x650")

        # --- DEFINIÇÃO DE FONTES (DESIGN SYSTEM) ---
        self.font_title = ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        self.font_label = ctk.CTkFont(family="Segoe UI", size=14)
        self.font_metric_value = ctk.CTkFont(family="Segoe UI", size=22, weight="bold")
        self.font_default = ctk.CTkFont(family="Segoe UI", size=12)

        self.db = Database()
        self.calc = CalculadoraPreco(self.db)

        # Estilo Treeview (Dark Mode Compat)
        style = ttk.Style()
        style.theme_use("clam")

        # Estilo do Corpo da Tabela
        style.configure("Treeview",
                        background="#2b2b2b",
                        foreground="white",
                        rowheight=30,
                        fieldbackground="#2b2b2b",
                        borderwidth=0)
        style.map('Treeview', background=[('selected', '#1f6aa5')])

        # Estilo do Cabeçalho
        style.configure("Treeview.Heading",
                        background="#1f2630",
                        foreground="white",
                        relief="flat",
                        font=('Segoe UI', 10, 'bold'))
        style.map("Treeview.Heading",
                    background=[('active', '#10141a')])

        # Container Principal (Tabview)
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

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
        tab = self.tabview.tab("Home")

        # Título
        ctk.CTkLabel(tab, text="Visão Geral do Negócio", font=self.font_title).pack(pady=20)

        # Container de Métricas
        metrics_frame = ctk.CTkFrame(tab, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=20)

        # Dados
        metrics = self.db.get_dashboard_metrics()

        # Cards
        self.create_metric_card(metrics_frame, "Total Orçado", f"R$ {metrics['total_orcado']:.2f}", "#1F6AA5", 0)
        self.create_metric_card(metrics_frame, "Projetos na Base", f"{metrics['total_projetos']}", "#2CC985", 1)
        self.create_metric_card(metrics_frame, "Ticket Médio", f"R$ {metrics['ticket_medio']:.2f}", "#E67E22", 2)

    def create_metric_card(self, parent, title, value, color, col_idx):
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=15)
        card.grid(row=0, column=col_idx, padx=10, pady=10, sticky="ew")
        parent.grid_columnconfigure(col_idx, weight=1)

        ctk.CTkLabel(card, text=title, text_color="white", font=self.font_label).pack(pady=(15, 0))
        ctk.CTkLabel(card, text=value, text_color="white", font=self.font_metric_value).pack(pady=(5, 20))

    # --- ABA 1: MEUS PROJETOS ---
    def create_tab_projetos(self):
        frame = self.tabview.tab("Meus Projetos")

        columns = ("id", "cliente", "status", "preco")
        self.tree_proj = ttk.Treeview(frame, columns=columns, show='headings')
        self.tree_proj.heading("id", text="#")
        self.tree_proj.heading("cliente", text="Cliente")
        self.tree_proj.heading("status", text="Status")
        self.tree_proj.heading("preco", text="Preço Final")

        self.tree_proj.column("id", width=50)
        self.tree_proj.pack(fill='both', expand=True, padx=10, pady=10)

        frame_btns = ctk.CTkFrame(frame, fg_color="transparent")
        frame_btns.pack(pady=10)

        # Atualizar Lista -> Neutro
        ctk.CTkButton(frame_btns, text="🔄 Atualizar Lista", command=self.refresh_projetos,
                      fg_color="#34495E", hover_color="#2C3E50").pack(side="left", padx=10)

        # Alterar Status -> Neutro
        ctk.CTkButton(frame_btns, text="✏️ Alterar Status", command=self.alterar_status,
                      fg_color="#34495E", hover_color="#2C3E50").pack(side="left", padx=10)

        # Gerar PDF -> Positivo
        ctk.CTkButton(frame_btns, text="📄 Gerar Proposta PDF", command=self.gerar_pdf,
                      fg_color="#2CC985", hover_color="#25A970").pack(side="left", padx=10)

        self.refresh_projetos()

    # --- ABA 2: NOVO ORÇAMENTO ---
    def create_tab_novo_orcamento(self):
        tab = self.tabview.tab("Novo Orçamento")

        # Topo: Dados do Cliente
        frame_top = ctk.CTkFrame(tab, fg_color="transparent")
        frame_top.pack(fill='x', padx=20, pady=10)

        ctk.CTkLabel(frame_top, text="Cliente:", font=self.font_label).pack(side='left')
        self.entry_cliente = ctk.CTkEntry(frame_top, width=300, height=35, placeholder_text="Nome do Cliente ou Empresa")
        self.entry_cliente.pack(side='left', padx=10)

        ctk.CTkLabel(frame_top, text="Custos Extras (R$):", font=self.font_label).pack(side='left', padx=10)
        self.entry_extras = ctk.CTkEntry(frame_top, width=150, height=35, placeholder_text="0.00")
        self.entry_extras.pack(side='left')

        # Área de Scroll para Checkboxes
        ctk.CTkLabel(tab, text="Selecione os Serviços do Escopo:", font=self.font_title).pack(padx=20, pady=(10, 5), anchor='w')

        self.scrollable_frame = ctk.CTkScrollableFrame(tab, label_text="Lista de Serviços")
        self.scrollable_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Botões de Ação
        frame_btns = ctk.CTkFrame(tab, fg_color="transparent")
        frame_btns.pack(fill='x', padx=20, pady=20)

        # Recarregar Lista -> Neutro
        ctk.CTkButton(frame_btns, text="🔄 Recarregar Lista", command=self.carregar_checkboxes_tarefas,
                      fg_color="#34495E", hover_color="#2C3E50").pack(side='left', padx=10)

        # CALCULAR ORÇAMENTO -> Positivo
        ctk.CTkButton(frame_btns, text="💰 CALCULAR ORÇAMENTO", command=self.mostrar_previa,
                      fg_color="#2CC985", hover_color="#25A970", text_color="white").pack(side='right', padx=10)

        # Inicializa a lista
        self.check_vars = []
        self.carregar_checkboxes_tarefas()

    def carregar_checkboxes_tarefas(self):
        # Limpa área antiga
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Puxa do Banco de Dados
        servicos = self.db.get_servicos()
        self.check_vars = []

        for sid, nome, horas in servicos:
            var = ctk.BooleanVar(value=False)
            chk = ctk.CTkCheckBox(self.scrollable_frame, text=f"{nome} ({horas}h)", variable=var, font=self.font_label)
            chk.pack(anchor='w', pady=5, padx=10)
            self.check_vars.append((var, horas, nome))

    # --- ABA 3: CATÁLOGO DE SERVIÇOS (NOVA) ---
    def create_tab_catalogo(self):
        tab = self.tabview.tab("Catálogo")

        # Container principal
        container = ctk.CTkFrame(tab, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Lado Esquerdo: Formulário
        frame_form = ctk.CTkFrame(container)
        frame_form.pack(side='left', fill='y', padx=10, pady=10)

        ctk.CTkLabel(frame_form, text="Adicionar Novo Serviço", font=self.font_title).pack(pady=10)

        ctk.CTkLabel(frame_form, text="Nome da Tarefa:", font=self.font_label).pack(anchor='w', padx=10, pady=(10, 2))
        self.entry_novo_servico = ctk.CTkEntry(frame_form, width=200, height=35, placeholder_text="Ex: Modelagem 3D")
        self.entry_novo_servico.pack(padx=10, pady=5)

        ctk.CTkLabel(frame_form, text="Horas Padrão:", font=self.font_label).pack(anchor='w', padx=10, pady=(10, 2))
        self.entry_novas_horas = ctk.CTkEntry(frame_form, width=200, height=35, placeholder_text="Ex: 4.5")
        self.entry_novas_horas.pack(padx=10, pady=5)

        # Adicionar -> Positivo
        ctk.CTkButton(frame_form, text="➕ Adicionar ao Catálogo", command=self.adicionar_servico_db,
                      fg_color="#2CC985", hover_color="#25A970").pack(pady=20, padx=10)

        # Excluir -> Destrutivo
        ctk.CTkButton(frame_form, text="🗑️ Excluir Selecionado", command=self.excluir_servico_db,
                      fg_color="#C0392B", hover_color="#E74C3C").pack(pady=10, padx=10)

        # Lado Direito: Lista
        frame_list = ctk.CTkFrame(container, fg_color="transparent")
        frame_list.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        colunas = ("id", "nome", "horas")
        self.tree_cat = ttk.Treeview(frame_list, columns=colunas, show='headings')
        self.tree_cat.heading("id", text="ID")
        self.tree_cat.heading("nome", text="Serviço")
        self.tree_cat.heading("horas", text="Horas Padrão")
        self.tree_cat.column("id", width=30)
        self.tree_cat.column("horas", width=80)

        self.tree_cat.pack(fill='both', expand=True)

        self.refresh_catalogo()

    # --- ABA 4: CONFIGURAÇÕES FINANCEIRAS ---
    def create_tab_config(self):
        tab = self.tabview.tab("Config. Financeira")

        # Two columns: Left (Costs), Right (Params)
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(0, weight=1)

        # --- LEFT: Costs Table ---
        frame_costs = ctk.CTkFrame(tab)
        frame_costs.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(frame_costs, text="Custos Operacionais", font=self.font_title).pack(pady=10)

        # Table
        cols = ("id", "desc", "val")
        self.tree_custos = ttk.Treeview(frame_costs, columns=cols, show="headings", height=15)
        self.tree_custos.heading("desc", text="Descrição")
        self.tree_custos.heading("val", text="Valor (R$)")
        self.tree_custos.column("id", width=0, stretch=False) # Hide ID
        self.tree_custos.pack(fill="both", expand=True, padx=10, pady=5)

        # Total Label
        self.lbl_total_custos = ctk.CTkLabel(frame_costs, text="Total: R$ 0.00", font=self.font_label)
        self.lbl_total_custos.pack(pady=5)

        # Inputs
        frame_input_costs = ctk.CTkFrame(frame_costs, fg_color="transparent")
        frame_input_costs.pack(fill="x", padx=10, pady=10)

        self.entry_desc_custo = ctk.CTkEntry(frame_input_costs, height=35, placeholder_text="Descrição")
        self.entry_desc_custo.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.entry_valor_custo = ctk.CTkEntry(frame_input_costs, width=100, height=35, placeholder_text="0.00")
        self.entry_valor_custo.pack(side="left", padx=5)

        # + -> Positivo
        ctk.CTkButton(frame_input_costs, text="+", width=40, command=self.add_custo_ui,
                      fg_color="#2CC985", hover_color="#25A970").pack(side="left")

        # Trash -> Destrutivo
        ctk.CTkButton(frame_input_costs, text="🗑️", width=40, command=self.del_custo_ui,
                      fg_color="#C0392B", hover_color="#E74C3C").pack(side="left", padx=5)

        self.refresh_custos_ui()

        # --- RIGHT: Params ---
        frame_params = ctk.CTkFrame(tab)
        frame_params.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(frame_params, text="Parâmetros Gerais", font=self.font_title).pack(pady=10)

        cfg = self.db.get_config()

        ctk.CTkLabel(frame_params, text="Horas Produtivas/Mês:", font=self.font_label).pack(anchor="w", padx=20, pady=(10, 2))
        self.entry_horas = ctk.CTkEntry(frame_params, height=35)
        self.entry_horas.insert(0, cfg[2])
        self.entry_horas.pack(padx=20, fill="x")

        ctk.CTkLabel(frame_params, text="Impostos (%):", font=self.font_label).pack(anchor="w", padx=20, pady=(10, 2))
        self.entry_imposto = ctk.CTkEntry(frame_params, height=35)
        self.entry_imposto.insert(0, cfg[3])
        self.entry_imposto.pack(padx=20, fill="x")

        ctk.CTkLabel(frame_params, text="Margem de Lucro (%):", font=self.font_label).pack(anchor="w", padx=20, pady=(10, 2))
        self.entry_lucro = ctk.CTkEntry(frame_params, height=35)
        self.entry_lucro.insert(0, cfg[4])
        self.entry_lucro.pack(padx=20, fill="x")

        # Salvar -> Positivo
        ctk.CTkButton(frame_params, text="💾 Salvar Parâmetros", command=self.save_config,
                      fg_color="#2CC985", hover_color="#25A970").pack(pady=30, padx=20, fill="x")

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

    def refresh_projetos(self):
        for row in self.tree_proj.get_children():
            self.tree_proj.delete(row)

        # Tags de Cores para Status
        self.tree_proj.tag_configure("Orçamento", foreground="#F39C12") # Laranja
        self.tree_proj.tag_configure("Aprovado", foreground="#2ECC71") # Verde
        self.tree_proj.tag_configure("Em Execução", foreground="#3498DB") # Azul
        self.tree_proj.tag_configure("Concluído", foreground="#95A5A6") # Cinza

        self.db.cursor.execute("SELECT id, cliente, status, preco_final FROM projetos ORDER BY id DESC")
        for row in self.db.cursor.fetchall():
            self.tree_proj.insert("", "end", values=(row[0], row[1], row[2], f"R$ {row[3]:.2f}"), tags=(row[2],))

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
        servicos = self.db.get_servicos()
        for s in servicos:
            self.tree_cat.insert("", "end", values=s)

    def adicionar_servico_db(self):
        nome = self.entry_novo_servico.get()
        horas = self.entry_novas_horas.get()
        if nome and horas:
            try:
                self.db.add_servico(nome, float(horas))
                self.refresh_catalogo()
                self.entry_novo_servico.delete(0, 'end')
                self.entry_novas_horas.delete(0, 'end')
                messagebox.showinfo("Sucesso", "Serviço adicionado! Vá em 'Novo Orçamento' e clique em Recarregar Lista.")
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
            # We calculate current total cost to save as snapshot/cache if needed by update_config
            c = self.db.get_total_custos_operacionais()
            h = float(self.entry_horas.get())
            i = float(self.entry_imposto.get())
            l = float(self.entry_lucro.get())
            self.db.update_config(c, h, i, l)
            messagebox.showinfo("Sucesso", "Dados Financeiros Atualizados!")
        except ValueError:
            messagebox.showerror("Erro", "Verifique os números digitados.")

    def mostrar_previa(self):
        # Coleta horas selecionadas
        horas_totais = 0
        escopo_desc = []
        for var, horas, nome in self.check_vars:
            if var.get():
                horas_totais += horas
                escopo_desc.append(f"{nome} ({horas}h)")

        if horas_totais == 0:
            messagebox.showwarning("Atenção", "Selecione pelo menos uma tarefa.")
            return

        try:
            extras = float(self.entry_extras.get())
            if self.entry_extras.get() == "": # Handle empty string
                extras = 0
        except:
            extras = 0

        res = self.calc.calcular_orcamento(horas_totais, extras)

        msg = f"""
        CLIENTE: {self.entry_cliente.get()}
        ----------------------------------
        Itens Selecionados: {len(escopo_desc)}
        Total de Horas: {horas_totais}h

        CUSTOS:
        - Mão de obra: R$ {horas_totais * res['valor_hora']:.2f}
        - Extras: R$ {extras:.2f}
        - Impostos: R$ {res['impostos']:.2f}

        LUCRO LÍQUIDO: R$ {res['lucro']:.2f}
        ----------------------------------
        PREÇO FINAL: R$ {res['preco_final']:.2f}
        """

        if messagebox.askyesno("Orçamento Gerado", msg + "\n\nSalvar este projeto?"):
            self.salvar_projeto(res['preco_final'], extras)

    def salvar_projeto(self, preco_final, extras):
        cliente = self.entry_cliente.get()
        if not cliente:
            cliente = "Cliente Sem Nome"

        self.db.cursor.execute("""
            INSERT INTO projetos (cliente, data_criacao, status, custo_extras, preco_final)
            VALUES (?, ?, ?, ?, ?)
        """, (cliente, datetime.now().strftime("%Y-%m-%d"), "Orçamento", extras, preco_final))

        proj_id = self.db.cursor.lastrowid

        for var, horas, nome in self.check_vars:
            if var.get():
                self.db.cursor.execute("INSERT INTO tarefas_projeto (projeto_id, descricao, horas_estimadas) VALUES (?, ?, ?)",
                                       (proj_id, nome, horas))

        self.db.conn.commit()
        messagebox.showinfo("Sucesso", "Projeto Salvo!")
        self.refresh_projetos()
        self.tabview.set("Meus Projetos")
