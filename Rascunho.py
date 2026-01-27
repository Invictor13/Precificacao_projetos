import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import customtkinter as ctk

# --- CONFIGURAÇÃO INICIAL E BANCO DE DADOS ---

class Database:
    def __init__(self, db_name="meus_projetos.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.seed_data()

    def create_tables(self):
        # Tabela de Configurações Financeiras
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                custo_mensal REAL,
                horas_mensais REAL,
                imposto_padrao REAL,
                lucro_padrao REAL
            )
        """)

        # Tabela de Catálogo de Serviços (NOVIDADE)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS catalogo_servicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                horas_padrao REAL
            )
        """)

        # Tabela de Projetos
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS projetos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT,
                data_criacao TEXT,
                status TEXT,
                custo_extras REAL,
                preco_final REAL
            )
        """)

        # Tabela de Tarefas salvas em cada Projeto
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tarefas_projeto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                projeto_id INTEGER,
                descricao TEXT,
                horas_estimadas REAL,
                FOREIGN KEY(projeto_id) REFERENCES projetos(id)
            )
        """)
        self.conn.commit()

    def seed_data(self):
        # Seed Configurações
        self.cursor.execute("SELECT count(*) FROM configuracoes")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("""
                INSERT INTO configuracoes (custo_mensal, horas_mensais, imposto_padrao, lucro_padrao)
                VALUES (?, ?, ?, ?)
            """, (5495.0, 180.0, 32.0, 30.0))
            self.conn.commit()

        # Seed Catálogo de Serviços (Se estiver vazio, preenche com o padrão do CSV)
        self.cursor.execute("SELECT count(*) FROM catalogo_servicos")
        if self.cursor.fetchone()[0] == 0:
            tarefas_iniciais = [
                ("Fechamento Orçamentário", 4),
                ("Pesquisa de referencias", 4),
                ("Pesquisa a campo", 10),
                ("Pré-projeto", 1),
                ("Projeto pré executivo", 1),
                ("Reuniões (Pré-executivo)", 12),
                ("Modelagem 3D", 1),
                ("Projeto executivo", 1),
                ("Reuniões (Executivo)", 5),
                ("Correções 3D", 4),
                ("Renderização", 7),
                ("Detalhamentos finais", 2),
                ("Entrega", 3)
            ]
            self.cursor.executemany("INSERT INTO catalogo_servicos (nome, horas_padrao) VALUES (?, ?)", tarefas_iniciais)
            self.conn.commit()
            print("Catálogo de serviços inicial criado.")

    # Métodos de Configuração
    def get_config(self):
        self.cursor.execute("SELECT * FROM configuracoes ORDER BY id DESC LIMIT 1")
        return self.cursor.fetchone()

    def update_config(self, custo, horas, imposto, lucro):
        self.cursor.execute("""
            UPDATE configuracoes SET custo_mensal=?, horas_mensais=?, imposto_padrao=?, lucro_padrao=?
            WHERE id = (SELECT MAX(id) FROM configuracoes)
        """, (custo, horas, imposto, lucro))
        self.conn.commit()

    # Métodos do Catálogo
    def get_servicos(self):
        self.cursor.execute("SELECT id, nome, horas_padrao FROM catalogo_servicos ORDER BY nome")
        return self.cursor.fetchall()

    def add_servico(self, nome, horas):
        self.cursor.execute("INSERT INTO catalogo_servicos (nome, horas_padrao) VALUES (?, ?)", (nome, horas))
        self.conn.commit()

    def delete_servico(self, id_servico):
        self.cursor.execute("DELETE FROM catalogo_servicos WHERE id=?", (id_servico,))
        self.conn.commit()

    def get_dashboard_metrics(self):
        self.cursor.execute("SELECT COUNT(*), SUM(preco_final) FROM projetos")
        data = self.cursor.fetchone()

        total_projetos = data[0] if data[0] else 0
        total_orcado = data[1] if data[1] else 0.0

        ticket_medio = total_orcado / total_projetos if total_projetos > 0 else 0.0

        return {
            "total_projetos": total_projetos,
            "total_orcado": total_orcado,
            "ticket_medio": ticket_medio
        }

# --- LÓGICA DE NEGÓCIO ---

class CalculadoraPreco:
    def __init__(self, db):
        self.db = db

    def calcular_hora_tecnica(self):
        cfg = self.db.get_config()
        custo_mensal = cfg[1]
        horas_mensais = cfg[2]
        return custo_mensal / horas_mensais if horas_mensais > 0 else 0

    def calcular_orcamento(self, horas_totais, custos_extras):
        cfg = self.db.get_config()
        imposto_pct = cfg[3] / 100
        lucro_pct = cfg[4] / 100
        valor_hora = self.calcular_hora_tecnica()

        custo_producao = (horas_totais * valor_hora) + custos_extras
        valor_impostos = custo_producao * imposto_pct
        base_com_imposto = custo_producao + valor_impostos
        preco_final = base_com_imposto * (1 + lucro_pct)

        lucro_valor = preco_final - base_com_imposto

        return {
            "valor_hora": valor_hora,
            "custo_producao": custo_producao,
            "impostos": valor_impostos,
            "lucro": lucro_valor,
            "preco_final": preco_final
        }

# --- INTERFACE GRÁFICA (GUI) ---

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Okami Project Manager 2.0 - Local")
        self.geometry("1000x650")
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
        ctk.CTkLabel(tab, text="Visão Geral do Negócio", font=("Segoe UI", 24, "bold")).pack(pady=20)

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

        ctk.CTkLabel(card, text=title, text_color="white", font=("Segoe UI", 14)).pack(pady=(15, 0))
        ctk.CTkLabel(card, text=value, text_color="white", font=("Segoe UI", 22, "bold")).pack(pady=(5, 20))

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

        ctk.CTkButton(frame, text="🔄 Atualizar Lista", command=self.refresh_projetos,
                      fg_color="#34495E").pack(pady=10)
        self.refresh_projetos()

    # --- ABA 2: NOVO ORÇAMENTO ---
    def create_tab_novo_orcamento(self):
        tab = self.tabview.tab("Novo Orçamento")

        # Topo: Dados do Cliente
        frame_top = ctk.CTkFrame(tab, fg_color="transparent")
        frame_top.pack(fill='x', padx=20, pady=10)

        ctk.CTkLabel(frame_top, text="Cliente:").pack(side='left')
        self.entry_cliente = ctk.CTkEntry(frame_top, width=300, placeholder_text="Nome do Cliente ou Empresa")
        self.entry_cliente.pack(side='left', padx=10)

        ctk.CTkLabel(frame_top, text="Custos Extras (R$):").pack(side='left', padx=10)
        self.entry_extras = ctk.CTkEntry(frame_top, width=150, placeholder_text="0.00")
        self.entry_extras.pack(side='left')

        # Área de Scroll para Checkboxes (Modernizado)
        ctk.CTkLabel(tab, text="Selecione os Serviços do Escopo:", font=('Segoe UI', 16, 'bold')).pack(padx=20, pady=(10, 5), anchor='w')

        self.scrollable_frame = ctk.CTkScrollableFrame(tab, label_text="Lista de Serviços")
        self.scrollable_frame.pack(fill='both', expand=True, padx=20, pady=5)

        # Botões de Ação
        frame_btns = ctk.CTkFrame(tab, fg_color="transparent")
        frame_btns.pack(fill='x', padx=20, pady=20)

        ctk.CTkButton(frame_btns, text="🔄 Recarregar Lista", command=self.carregar_checkboxes_tarefas,
                      fg_color="#34495E").pack(side='left')

        ctk.CTkButton(frame_btns, text="💰 CALCULAR ORÇAMENTO", command=self.mostrar_previa,
                      fg_color="#2CC985", text_color="white").pack(side='right')

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
            chk = ctk.CTkCheckBox(self.scrollable_frame, text=f"{nome} ({horas}h)", variable=var)
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

        ctk.CTkLabel(frame_form, text="Adicionar Novo Serviço", font=("Segoe UI", 16, "bold")).pack(pady=10)

        ctk.CTkLabel(frame_form, text="Nome da Tarefa:").pack(anchor='w', padx=10, pady=(10, 2))
        self.entry_novo_servico = ctk.CTkEntry(frame_form, width=200, placeholder_text="Ex: Modelagem 3D")
        self.entry_novo_servico.pack(padx=10, pady=5)

        ctk.CTkLabel(frame_form, text="Horas Padrão:").pack(anchor='w', padx=10, pady=(10, 2))
        self.entry_novas_horas = ctk.CTkEntry(frame_form, width=200, placeholder_text="Ex: 4.5")
        self.entry_novas_horas.pack(padx=10, pady=5)

        ctk.CTkButton(frame_form, text="➕ Adicionar ao Catálogo", command=self.adicionar_servico_db,
                      fg_color="#2CC985").pack(pady=20, padx=10)

        ctk.CTkButton(frame_form, text="🗑️ Excluir Selecionado", command=self.excluir_servico_db,
                      fg_color="#C0392B").pack(pady=10, padx=10)

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

        # Center content
        frame_center = ctk.CTkFrame(tab)
        frame_center.pack(pady=40, padx=40)

        ctk.CTkLabel(frame_center, text="Parâmetros Financeiros", font=("Segoe UI", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=20)

        cfg = self.db.get_config()

        ctk.CTkLabel(frame_center, text="Custos Fixos Mensais (R$):").grid(row=1, column=0, padx=20, pady=10, sticky="e")
        self.entry_custo = ctk.CTkEntry(frame_center, width=150)
        self.entry_custo.insert(0, cfg[1])
        self.entry_custo.grid(row=1, column=1, padx=20, pady=10, sticky="w")

        ctk.CTkLabel(frame_center, text="Horas Produtivas/Mês:").grid(row=2, column=0, padx=20, pady=10, sticky="e")
        self.entry_horas = ctk.CTkEntry(frame_center, width=150)
        self.entry_horas.insert(0, cfg[2])
        self.entry_horas.grid(row=2, column=1, padx=20, pady=10, sticky="w")

        ctk.CTkLabel(frame_center, text="Impostos (%):").grid(row=3, column=0, padx=20, pady=10, sticky="e")
        self.entry_imposto = ctk.CTkEntry(frame_center, width=150)
        self.entry_imposto.insert(0, cfg[3])
        self.entry_imposto.grid(row=3, column=1, padx=20, pady=10, sticky="w")

        ctk.CTkLabel(frame_center, text="Margem de Lucro (%):").grid(row=4, column=0, padx=20, pady=10, sticky="e")
        self.entry_lucro = ctk.CTkEntry(frame_center, width=150)
        self.entry_lucro.insert(0, cfg[4])
        self.entry_lucro.grid(row=4, column=1, padx=20, pady=10, sticky="w")

        ctk.CTkButton(frame_center, text="💾 Salvar Alterações", command=self.save_config,
                      fg_color="#2CC985").grid(row=5, column=0, columnspan=2, pady=30)

    # --- FUNÇÕES DE AÇÃO ---

    def refresh_projetos(self):
        for row in self.tree_proj.get_children():
            self.tree_proj.delete(row)
        self.db.cursor.execute("SELECT id, cliente, status, preco_final FROM projetos ORDER BY id DESC")
        for row in self.db.cursor.fetchall():
            self.tree_proj.insert("", "end", values=(row[0], row[1], row[2], f"R$ {row[3]:.2f}"))

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
            c = float(self.entry_custo.get())
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

if __name__ == "__main__":
    app = App()
    app.mainloop()