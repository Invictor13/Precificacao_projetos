import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

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

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Okami Project Manager 2.0 - Local")
        self.geometry("1000x650")
        self.db = Database()
        self.calc = CalculadoraPreco(self.db)
        
        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TButton", padding=6)
        style.configure("Treeview", rowheight=25)

        # Abas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.create_tab_projetos()
        self.create_tab_novo_orcamento()
        self.create_tab_catalogo() # Nova Aba
        self.create_tab_config()

    # --- ABA 1: MEUS PROJETOS ---
    def create_tab_projetos(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Meus Projetos")
        
        columns = ("id", "cliente", "status", "preco")
        self.tree_proj = ttk.Treeview(frame, columns=columns, show='headings')
        self.tree_proj.heading("id", text="#")
        self.tree_proj.heading("cliente", text="Cliente")
        self.tree_proj.heading("status", text="Status")
        self.tree_proj.heading("preco", text="Preço Final")
        
        self.tree_proj.column("id", width=50)
        self.tree_proj.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Button(frame, text="Atualizar Lista", command=self.refresh_projetos).pack(pady=5)
        self.refresh_projetos()

    # --- ABA 2: NOVO ORÇAMENTO ---
    def create_tab_novo_orcamento(self):
        self.frame_orc = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_orc, text="Novo Orçamento")

        # Topo: Dados do Cliente
        frame_top = ttk.Frame(self.frame_orc)
        frame_top.pack(fill='x', padx=20, pady=10)

        ttk.Label(frame_top, text="Cliente:").pack(side='left')
        self.entry_cliente = ttk.Entry(frame_top, width=30)
        self.entry_cliente.pack(side='left', padx=5)

        ttk.Label(frame_top, text="Custos Extras (R$):").pack(side='left', padx=10)
        self.entry_extras = ttk.Entry(frame_top, width=15)
        self.entry_extras.insert(0, "0")
        self.entry_extras.pack(side='left')
        
        # Área de Scroll para Checkboxes
        lbl_escopo = ttk.Label(self.frame_orc, text="Selecione os Serviços do Escopo:", font=('Arial', 10, 'bold'))
        lbl_escopo.pack(padx=20, pady=(10, 5), anchor='w')
        
        self.frame_tarefas_container = ttk.Frame(self.frame_orc)
        self.frame_tarefas_container.pack(fill='both', expand=True, padx=20, pady=5)
        
        # Botões de Ação
        frame_btns = ttk.Frame(self.frame_orc)
        frame_btns.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(frame_btns, text="Recarregar Lista de Serviços", command=self.carregar_checkboxes_tarefas).pack(side='left')
        ttk.Button(frame_btns, text="CALCULAR ORÇAMENTO", command=self.mostrar_previa).pack(side='right')

        # Inicializa a lista
        self.check_vars = []
        self.carregar_checkboxes_tarefas()

    def carregar_checkboxes_tarefas(self):
        # Limpa área antiga
        for widget in self.frame_tarefas_container.winfo_children():
            widget.destroy()

        # Canvas + Scrollbar setup
        canvas = tk.Canvas(self.frame_tarefas_container)
        scrollbar = ttk.Scrollbar(self.frame_tarefas_container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Puxa do Banco de Dados
        servicos = self.db.get_servicos()
        self.check_vars = []

        for sid, nome, horas in servicos:
            var = tk.BooleanVar(value=False) # Desmarcado por padrão para forçar escolha
            # Texto do checkbox mostra o nome e as horas padrão
            chk = ttk.Checkbutton(self.scrollable_frame, text=f"{nome} ({horas}h)", variable=var)
            chk.pack(anchor='w', pady=2)
            # Guardamos a referência: variavel, horas, nome
            self.check_vars.append((var, horas, nome))

    # --- ABA 3: CATÁLOGO DE SERVIÇOS (NOVA) ---
    def create_tab_catalogo(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Catálogo de Serviços")

        # Lado Esquerdo: Formulário
        frame_form = ttk.LabelFrame(frame, text="Adicionar Novo Serviço")
        frame_form.pack(side='left', fill='y', padx=10, pady=10)

        ttk.Label(frame_form, text="Nome da Tarefa:").pack(anchor='w', padx=5, pady=2)
        self.entry_novo_servico = ttk.Entry(frame_form, width=30)
        self.entry_novo_servico.pack(padx=5, pady=5)

        ttk.Label(frame_form, text="Horas Padrão:").pack(anchor='w', padx=5, pady=2)
        self.entry_novas_horas = ttk.Entry(frame_form, width=10)
        self.entry_novas_horas.pack(padx=5, pady=5)

        ttk.Button(frame_form, text="Adicionar ao Catálogo", command=self.adicionar_servico_db).pack(pady=10)
        ttk.Button(frame_form, text="Excluir Selecionado", command=self.excluir_servico_db).pack(pady=20)

        # Lado Direito: Lista
        frame_list = ttk.Frame(frame)
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
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Config. Financeira")

        cfg = self.db.get_config()
        
        # Grid layout simples
        ttk.Label(frame, text="Custos Fixos Mensais (R$):").grid(row=0, column=0, padx=10, pady=10)
        self.entry_custo = ttk.Entry(frame)
        self.entry_custo.insert(0, cfg[1])
        self.entry_custo.grid(row=0, column=1)

        ttk.Label(frame, text="Horas Produtivas/Mês:").grid(row=1, column=0, padx=10, pady=10)
        self.entry_horas = ttk.Entry(frame)
        self.entry_horas.insert(0, cfg[2])
        self.entry_horas.grid(row=1, column=1)

        ttk.Label(frame, text="Impostos (%):").grid(row=2, column=0, padx=10, pady=10)
        self.entry_imposto = ttk.Entry(frame)
        self.entry_imposto.insert(0, cfg[3])
        self.entry_imposto.grid(row=2, column=1)

        ttk.Label(frame, text="Margem de Lucro (%):").grid(row=3, column=0, padx=10, pady=10)
        self.entry_lucro = ttk.Entry(frame)
        self.entry_lucro.insert(0, cfg[4])
        self.entry_lucro.grid(row=3, column=1)

        ttk.Button(frame, text="Salvar Alterações", command=self.save_config).grid(row=4, column=0, columnspan=2, pady=20)

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
        self.notebook.select(0) 

if __name__ == "__main__":
    app = App()
    app.mainloop()