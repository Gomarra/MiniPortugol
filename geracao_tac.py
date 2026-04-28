# geracao_tac.py
import logging
from erro import Erro
from miniportugolParser import miniportugolParser

class GeracaoTAC:
    def __init__(self, erro_handler: Erro):
        self.erro_handler = erro_handler
        self.logger = logging.getLogger(self.__class__.__name__)
        self.codigo_tac = []
        self.contador_temporarias = 0
        self.contador_labels = 0

    def _nova_temporaria(self) -> str:
        temp_nome = f"t{self.contador_temporarias}"
        self.contador_temporarias += 1
        return temp_nome

    def _nova_label(self) -> str:
        label = f"L{self.contador_labels}"
        self.contador_labels += 1
        return label

    def _gerar_tac_expr(self, ctx) -> str:
        # Alternativas de fator
        if isinstance(ctx, miniportugolParser.NUMEROContext):
            return ctx.INT().getText()

        if isinstance(ctx, miniportugolParser.STRINGContext):
            return ctx.STRING().getText()

        if isinstance(ctx, miniportugolParser.VARIAVELContext):
            return ctx.ID().getText()

        if isinstance(ctx, miniportugolParser.PARENTESESContext):
            return self._gerar_tac_expr(ctx.expr())

        # FatorContext base (não deve acontecer se as alternativas acima cobrem tudo)
        if isinstance(ctx, miniportugolParser.FatorContext):
            if ctx.getChildCount() == 1:
                return self._gerar_tac_expr(ctx.getChild(0))

        # TermoContext e ExprContext têm a mesma estrutura: operando (op operando)*
        if isinstance(ctx, (miniportugolParser.TermoContext, miniportugolParser.ExprContext)):
            children = ctx.children
            resultado = self._gerar_tac_expr(children[0])
            num_ops = (len(children) - 1) // 2
            for i in range(num_ops):
                operador = children[i * 2 + 1].getText()
                direito = self._gerar_tac_expr(children[i * 2 + 2])
                temp = self._nova_temporaria()
                self.codigo_tac.append(f"{temp} := {resultado} {operador} {direito}")
                resultado = temp
            return resultado

        self.logger.error(f"GER_TAC_EXPR: tipo não suportado: {type(ctx)} → '{ctx.getText()}'")
        return "ERRO_TAC"

    def _gerar_tac_condicao(self, ctx: miniportugolParser.CondicaoContext) -> str:
        """Gera TAC para uma condição e retorna o nome da temporária com o resultado."""
        esq = self._gerar_tac_expr(ctx.expr(0))
        op  = ctx.expr_condicionais().getText()  # ==, !=, >, <, &&, ||
        dir = self._gerar_tac_expr(ctx.expr(1))
        temp = self._nova_temporaria()
        # Se o operador for vazio (alternativa 1 da gramática), trata como expressão simples
        if op == "":
            return esq
        self.codigo_tac.append(f"{temp} := {esq} {op} {dir}")
        return temp

    def _gerar_tac_bloco(self, ctx: miniportugolParser.BlocoContext):
        for lista_cmd in ctx.lista_comandos():
            self._gerar_tac_lista_comandos(lista_cmd)

    def _gerar_tac_lista_comandos(self, ctx: miniportugolParser.Lista_comandosContext):
        filho = ctx.getChild(0)

        if isinstance(filho, miniportugolParser.Comando_escrevaContext):
            val = self._gerar_tac_expr(filho.expr())
            self.codigo_tac.append(f"PRINT {val}")
            self.logger.info(f"TAC: PRINT {val}")

        elif isinstance(filho, miniportugolParser.Comando_lerContext):
            var = filho.ID().getText()
            self.codigo_tac.append(f"INPUT {var}")
            self.logger.info(f"TAC: INPUT {var}")

        elif isinstance(filho, miniportugolParser.Comando_definirContext):
            var = filho.ID().getText()
            val = self._gerar_tac_expr(filho.expr(0))
            self.codigo_tac.append(f"{var} := {val}")
            self.logger.info(f"TAC: {var} := {val}")

        elif isinstance(filho, miniportugolParser.Comando_seContext):
            cond = self._gerar_tac_condicao(filho.condicao())
            label_falso = self._nova_label()
            label_fim   = self._nova_label()

            self.codigo_tac.append(f"IF_FALSE {cond} GOTO {label_falso}")
            self._gerar_tac_bloco(filho.bloco(0))

            if filho.SENAO():
                self.codigo_tac.append(f"GOTO {label_fim}")
                self.codigo_tac.append(f"{label_falso}:")
                self._gerar_tac_bloco(filho.bloco(1))
                self.codigo_tac.append(f"{label_fim}:")
            else:
                self.codigo_tac.append(f"{label_falso}:")

        elif isinstance(filho, miniportugolParser.Comando_enquantoContext):
            label_inicio = self._nova_label()
            label_fim    = self._nova_label()

            self.codigo_tac.append(f"{label_inicio}:")
            cond = self._gerar_tac_condicao(filho.condicao())
            self.codigo_tac.append(f"IF_FALSE {cond} GOTO {label_fim}")
            self._gerar_tac_bloco(filho.bloco())
            self.codigo_tac.append(f"GOTO {label_inicio}")
            self.codigo_tac.append(f"{label_fim}:")

        else:
            self.logger.warning(f"TAC: comando não suportado: {type(filho)}")

    def gerarCodigoTAC(self, ast_validada):
        self.logger.info("Iniciando geração de TAC...")
        if not ast_validada or self.erro_handler.houve_erro_fatal():
            return None

        self.codigo_tac = []
        self.contador_temporarias = 0
        self.contador_labels = 0

        try:
            # declaracoes de variável não geram TAC (só reservam espaço)
            for lista_cmd in ast_validada.lista_comandos():
                self._gerar_tac_lista_comandos(lista_cmd)

        except Exception as e:
            self.erro_handler.registrar_erro("Gerador TAC", 0, 0, f"Erro inesperado na geração TAC: {e}", "TAC")
            self.logger.exception("Detalhes:")
            return None

        self.logger.info("--- Código TAC Gerado ---")
        for i, instrucao in enumerate(self.codigo_tac):
            self.logger.info(f"  {i}: {instrucao}")
        self.logger.info("-------------------------")

        return self.codigo_tac