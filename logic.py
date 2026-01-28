import math

class CalculadoraPreco:
    def __init__(self, db):
        self.db = db

    def calcular_hora_tecnica(self):
        cfg = self.db.get_config()
        custo_mensal = self.db.get_total_custos_operacionais()
        # cfg: id, custo, horas, imposto, lucro, meta, nome
        horas_mensais = cfg[2] if cfg else 160
        return custo_mensal / horas_mensais if horas_mensais > 0 else 0

    def calcular_dias_uteis(self, horas_totais):
        # 6 horas produtivas por dia
        if horas_totais <= 0: return 0
        return math.ceil(horas_totais / 6)

    def calcular_orcamento(self, horas_totais, custos_extras, discount_str=None):
        cfg = self.db.get_config()
        # cfg: id, custo, horas, imposto, lucro, meta, nome
        imposto_pct = (cfg[3] / 100) if cfg else 0
        lucro_ideal_pct = (cfg[4] / 100) if cfg else 0.3

        valor_hora = self.calcular_hora_tecnica()

        # 1. Custo Base
        custo_producao = (horas_totais * valor_hora) + custos_extras

        # 2. Preço Sugerido (Lógica Original Mantida para referência base)
        # Nota: A lógica original aplica imposto sobre o custo (markup), não sobre o total.
        valor_impostos_base = custo_producao * imposto_pct
        base_com_imposto = custo_producao + valor_impostos_base
        preco_sugerido = base_com_imposto * (1 + lucro_ideal_pct)

        # 3. Aplicar Desconto/Acréscimo
        preco_final = preco_sugerido

        if discount_str:
            discount_str = discount_str.strip()
            if discount_str:
                try:
                    # Tenta limpar string
                    clean_str = discount_str.lower().replace("r$", "").replace(" ", "").replace(",", ".")

                    val_adjustment = 0.0

                    if "%" in clean_str:
                        # Porcentagem
                        pct_val = float(clean_str.replace("%", ""))
                        # Se digitar "-10%", pct_val é -10.
                        # Aplicamos sobre o preço sugerido
                        val_adjustment = preco_sugerido * (pct_val / 100)
                    else:
                        # Valor absoluto
                        val_adjustment = float(clean_str)

                    preco_final = preco_sugerido + val_adjustment
                except ValueError:
                    pass # Ignora input inválido

        # 4. Calcular Margem Real (Effective Margin)
        # Margem Real = (Preço Final - Custos - Impostos Reais) / Preço Final
        # Assumindo Imposto Real sobre Faturamento (Regime Simples/MEI/etc)
        impostos_reais = preco_final * imposto_pct
        lucro_liquido_real = preco_final - custo_producao - impostos_reais

        margem_real_pct = (lucro_liquido_real / preco_final * 100) if preco_final > 0 else 0

        return {
            "valor_hora": valor_hora,
            "custo_producao": custo_producao,
            "preco_sugerido": preco_sugerido,
            "preco_final": preco_final,
            "lucro_liquido_real": lucro_liquido_real,
            "margem_real_pct": margem_real_pct,
            "impostos_reais": impostos_reais,
            "dias_uteis": self.calcular_dias_uteis(horas_totais)
        }
