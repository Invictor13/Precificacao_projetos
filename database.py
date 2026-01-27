import sqlite3

class Database:
    def __init__(self, db_name="meus_projetos.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.check_and_migrate()
        self.seed_data()

    def create_tables(self):
        # Tabela de Configurações Financeiras
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                custo_mensal REAL,
                horas_mensais REAL,
                imposto_padrao REAL,
                lucro_padrao REAL,
                meta_mensal REAL DEFAULT 10000.0,
                nome_usuario TEXT DEFAULT 'Visitante'
            )
        """)

        # Tabela de Catálogo de Serviços
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS catalogo_servicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                horas_padrao REAL,
                categoria TEXT DEFAULT 'Geral'
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
                data_entrega TEXT,
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

    def check_and_migrate(self):
        # Verifica colunas em 'catalogo_servicos'
        self.cursor.execute("PRAGMA table_info(catalogo_servicos)")
        cols = [info[1] for info in self.cursor.fetchall()]
        if "categoria" not in cols:
            print("Migrando DB: Adicionando coluna 'categoria' em catalogo_servicos...")
            self.cursor.execute("ALTER TABLE catalogo_servicos ADD COLUMN categoria TEXT DEFAULT 'Geral'")

            # Atualiza categorias padrão para dados existentes (tentativa heurística)
            mapping = {
                "Pré-Projeto": ["Fechamento", "Pesquisa", "Pré-projeto", "Reuniões (Pré"],
                "Execução": ["Projeto", "Modelagem", "Reuniões (Exe", "Correções"],
                "Pós-Produção": ["Render", "Detalhamento", "Entrega"]
            }
            for cat, keywords in mapping.items():
                for kw in keywords:
                    self.cursor.execute(f"UPDATE catalogo_servicos SET categoria = ? WHERE nome LIKE ?", (cat, f"%{kw}%"))
            self.conn.commit()

        # Verifica colunas em 'configuracoes'
        self.cursor.execute("PRAGMA table_info(configuracoes)")
        cols = [info[1] for info in self.cursor.fetchall()]
        if "meta_mensal" not in cols:
            print("Migrando DB: Adicionando coluna 'meta_mensal' em configuracoes...")
            self.cursor.execute("ALTER TABLE configuracoes ADD COLUMN meta_mensal REAL DEFAULT 10000.0")
        if "nome_usuario" not in cols:
            print("Migrando DB: Adicionando coluna 'nome_usuario' em configuracoes...")
            self.cursor.execute("ALTER TABLE configuracoes ADD COLUMN nome_usuario TEXT DEFAULT 'Visitante'")

        # Verifica colunas em 'projetos'
        self.cursor.execute("PRAGMA table_info(projetos)")
        cols = [info[1] for info in self.cursor.fetchall()]
        if "data_entrega" not in cols:
            print("Migrando DB: Adicionando coluna 'data_entrega' em projetos...")
            self.cursor.execute("ALTER TABLE projetos ADD COLUMN data_entrega TEXT")

        self.conn.commit()

    def seed_data(self):
        # Seed Configurações
        self.cursor.execute("SELECT count(*) FROM configuracoes")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("""
                INSERT INTO configuracoes (custo_mensal, horas_mensais, imposto_padrao, lucro_padrao, meta_mensal, nome_usuario)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (5495.0, 180.0, 32.0, 30.0, 15000.0, "Okami"))
            self.conn.commit()

        # Seed Catálogo de Serviços
        self.cursor.execute("SELECT count(*) FROM catalogo_servicos")
        if self.cursor.fetchone()[0] == 0:
            tarefas_iniciais = [
                ("Fechamento Orçamentário", 4, "Pré-Projeto"),
                ("Pesquisa de referencias", 4, "Pré-Projeto"),
                ("Pesquisa a campo", 10, "Pré-Projeto"),
                ("Pré-projeto", 1, "Pré-Projeto"),
                ("Projeto pré executivo", 1, "Execução"),
                ("Reuniões (Pré-executivo)", 12, "Pré-Projeto"),
                ("Modelagem 3D", 1, "Execução"),
                ("Projeto executivo", 1, "Execução"),
                ("Reuniões (Executivo)", 5, "Execução"),
                ("Correções 3D", 4, "Execução"),
                ("Renderização", 7, "Pós-Produção"),
                ("Detalhamentos finais", 2, "Pós-Produção"),
                ("Entrega", 3, "Pós-Produção")
            ]
            self.cursor.executemany("INSERT INTO catalogo_servicos (nome, horas_padrao, categoria) VALUES (?, ?, ?)", tarefas_iniciais)
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

    def update_config(self, custo, horas, imposto, lucro, meta, nome):
        # Verifica se já existe config
        if self.get_config():
            self.cursor.execute("""
                UPDATE configuracoes SET custo_mensal=?, horas_mensais=?, imposto_padrao=?, lucro_padrao=?, meta_mensal=?, nome_usuario=?
                WHERE id = (SELECT MAX(id) FROM configuracoes)
            """, (custo, horas, imposto, lucro, meta, nome))
        else:
             self.cursor.execute("""
                INSERT INTO configuracoes (custo_mensal, horas_mensais, imposto_padrao, lucro_padrao, meta_mensal, nome_usuario)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (custo, horas, imposto, lucro, meta, nome))
        self.conn.commit()

    # Métodos do Catálogo
    def get_servicos(self):
        self.cursor.execute("SELECT id, nome, horas_padrao, categoria FROM catalogo_servicos ORDER BY categoria, nome")
        return self.cursor.fetchall()

    def get_categorias(self):
        self.cursor.execute("SELECT DISTINCT categoria FROM catalogo_servicos ORDER BY categoria")
        return [row[0] for row in self.cursor.fetchall()]

    def add_servico(self, nome, horas, categoria="Geral"):
        self.cursor.execute("INSERT INTO catalogo_servicos (nome, horas_padrao, categoria) VALUES (?, ?, ?)", (nome, horas, categoria))
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

    def get_dashboard_metrics(self, filtro_mes=None, filtro_ano=None):
        query = "SELECT COUNT(*), SUM(preco_final) FROM projetos"
        params = []

        where_clauses = []
        if filtro_mes and filtro_mes != "Todos":
             # Assuming data_criacao is YYYY-MM-DD
             where_clauses.append("strftime('%m', data_criacao) = ?")
             params.append(filtro_mes)

        if filtro_ano and filtro_ano != "Todos":
             where_clauses.append("strftime('%Y', data_criacao) = ?")
             params.append(filtro_ano)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        self.cursor.execute(query, params)
        data = self.cursor.fetchone()

        total_projetos = data[0] if data[0] else 0
        total_orcado = data[1] if data[1] else 0.0

        ticket_medio = total_orcado / total_projetos if total_projetos > 0 else 0.0

        # Get Status Distribution for Pie Chart
        query_status = "SELECT status, COUNT(*) FROM projetos"
        if where_clauses:
            query_status += " WHERE " + " AND ".join(where_clauses)
        query_status += " GROUP BY status"

        self.cursor.execute(query_status, params)
        status_dist = self.cursor.fetchall()

        return {
            "total_projetos": total_projetos,
            "total_orcado": total_orcado,
            "ticket_medio": ticket_medio,
            "status_dist": status_dist
        }
