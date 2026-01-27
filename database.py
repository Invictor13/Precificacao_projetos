import sqlite3

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

        # Tabela de Custos Operacionais
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS custos_operacionais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT,
                valor REAL
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

        # Seed Custos Operacionais
        self.cursor.execute("SELECT count(*) FROM custos_operacionais")
        if self.cursor.fetchone()[0] == 0:
            custos_iniciais = [
                ("Água", 35.0), ("Luz", 500.0), ("Telefone", 300.0), ("Internet", 50.0),
                ("IPTU", 200.0), ("Condomínio", 100.0), ("Aluguel", 100.0), ("Faxina", 100.0),
                ("Gás", 100.0), ("Alvará", 100.0), ("Material de limpeza", 100.0),
                ("Papelaria/Escritório", 100.0), ("Software", 100.0), ("Pro labore", 3000.0),
                ("Estagiário", 100.0), ("Associações", 100.0), ("Contabilidade", 100.0),
                ("Marketing", 100.0), ("Conselho Profissional", 100.0), ("Cursos", 100.0),
                ("Terceirizados", 10.0)
            ]
            self.cursor.executemany("INSERT INTO custos_operacionais (descricao, valor) VALUES (?, ?)", custos_iniciais)
            self.conn.commit()
            print("Custos operacionais iniciais criados.")

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

    # Métodos de Custos Operacionais
    def get_custos_operacionais(self):
        self.cursor.execute("SELECT id, descricao, valor FROM custos_operacionais ORDER BY descricao")
        return self.cursor.fetchall()

    def add_custo_operacional(self, descricao, valor):
        self.cursor.execute("INSERT INTO custos_operacionais (descricao, valor) VALUES (?, ?)", (descricao, valor))
        self.conn.commit()

    def delete_custo_operacional(self, id_custo):
        self.cursor.execute("DELETE FROM custos_operacionais WHERE id=?", (id_custo,))
        self.conn.commit()

    def get_total_custos_operacionais(self):
        self.cursor.execute("SELECT SUM(valor) FROM custos_operacionais")
        result = self.cursor.fetchone()[0]
        return result if result else 0.0

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
