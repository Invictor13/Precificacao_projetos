class CalculadoraPreco:
    def __init__(self, db):
        self.db = db

    def calcular_hora_tecnica(self):
        cfg = self.db.get_config()
        custo_mensal = self.db.get_total_custos_operacionais()
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
