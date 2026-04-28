# analise_semantica.py
import logging
import sys
from antlr4 import ParseTreeWalker, ParserRuleContext
from miniportugolParser import miniportugolParser
from miniportugolListener import miniportugolListener
from erro import Erro

class miniportugolSemanticoListenerImpl(miniportugolListener):

    def __init__(self, erro_handler: Erro):
        self.erro_handler = erro_handler
        self.logger = logging.getLogger(self.__class__.__name__)
        self.escopo_atual = {}
        self.variaveis_declaradas_globalmente = set()
        self.ast_anotada = None

    def _registrar_variavel_declarada(self, nome_var: str, tipo_var: str, rule_node_ctx):
        id_node_symbol = None
        if hasattr(rule_node_ctx, 'ID') and callable(rule_node_ctx.ID) and rule_node_ctx.ID():
            id_node_symbol = rule_node_ctx.ID().getSymbol()

        line = id_node_symbol.line if id_node_symbol else rule_node_ctx.start.line
        column = (id_node_symbol.column + 1) if id_node_symbol else (rule_node_ctx.start.column + 1)

        self.logger.info(f"Variável '{nome_var}' (tipo: {tipo_var}) declarada na linha {line}, coluna {column}.")
        self.variaveis_declaradas_globalmente.add(nome_var)
        self.escopo_atual[nome_var] = {
            "linha": line,
            "coluna": column,
            "usada": False,
            "type_name": tipo_var
        }
        if id_node_symbol:
            id_node_symbol.type_name = tipo_var

    def _verificar_uso_variavel(self, nome_var: str, id_symbol):
        line = id_symbol.line
        column = id_symbol.column + 1
        if nome_var not in self.escopo_atual:
            msg = f"Variável '{nome_var}' usada antes de ser definida/declarada."
            self.erro_handler.registrar_erro("Analisador Semântico", line, column, msg, tipo_erro="SEMANTICO")
            return None

        var_info = self.escopo_atual[nome_var]
        var_info["usada"] = True
        self.logger.info(f"Variável '{nome_var}' (tipo: {var_info['type_name']}) usada na linha {line}, coluna {column}.")
        return var_info["type_name"]

    # --- Alternativas de fator ---

    def exitNUMERO(self, ctx: miniportugolParser.NUMEROContext):
        ctx.type_name = "NUMERO"
        self.logger.info(f"EXIT_NUMERO: '{ctx.getText()}' → NUMERO")

    def exitSTRING(self, ctx: miniportugolParser.STRINGContext):
        ctx.type_name = "STRING"
        self.logger.info(f"EXIT_STRING: '{ctx.getText()}' → STRING")

    def exitVARIAVEL(self, ctx: miniportugolParser.VARIAVELContext):
        nome_var = ctx.ID().getText()
        id_symbol = ctx.ID().getSymbol()
        tipo_var = self._verificar_uso_variavel(nome_var, id_symbol)
        ctx.type_name = tipo_var if tipo_var else "ERRO_TIPO"
        self.logger.info(f"EXIT_VARIAVEL: '{nome_var}' → {ctx.type_name}")

    def exitPARENTESES(self, ctx: miniportugolParser.PARENTESESContext):
        inner = ctx.expr()
        ctx.type_name = inner.type_name if hasattr(inner, 'type_name') else "ERRO_TIPO"
        self.logger.info(f"EXIT_PARENTESES: '{ctx.getText()}' → {ctx.type_name}")

    # --- fator (regra base, propaga do filho rotulado) ---

    def exitFator(self, ctx: miniportugolParser.FatorContext):
        # As alternativas rotuladas já definiram type_name; aqui só verificamos
        if not hasattr(ctx, 'type_name'):
            self.logger.error(f"EXIT_FATOR: '{ctx.getText()}' sem type_name!")
            ctx.type_name = "ERRO_TIPO"

    # --- termo ---

    def exitTermo(self, ctx: miniportugolParser.TermoContext):
        current_type = "ERRO_TIPO"
        primeiro_fator = ctx.fator(0)          # ← nome correto: fator
        if primeiro_fator and hasattr(primeiro_fator, 'type_name'):
            current_type = primeiro_fator.type_name
        else:
            self.logger.error(f"EXIT_TERMO: fator(0) de '{ctx.getText()}' sem type_name.")

        num_fatores = len(ctx.fator())
        if num_fatores > 1 and not current_type.startswith("ERRO_"):
            for i in range(num_fatores - 1):
                op_node = ctx.getChild(i * 2 + 1)
                op_text = op_node.getText()
                right_ctx = ctx.fator(i + 1)
                right_type = right_ctx.type_name if hasattr(right_ctx, 'type_name') else "ERRO_TIPO"
                if right_type.startswith("ERRO_"):
                    current_type = "ERRO_TIPO"
                    break
                if op_text in ['*', '/']:
                    if current_type == "NUMERO" and right_type == "NUMERO":
                        current_type = "NUMERO"
                    else:
                        msg = f"Operador '{op_text}' requer operandos numéricos. Obtidos: {current_type} e {right_type}."
                        self.erro_handler.registrar_erro("Analisador Semântico", op_node.symbol.line, op_node.symbol.column + 1, msg, "SEMANTICO")
                        current_type = "ERRO_TIPO"
                        break

        ctx.type_name = current_type
        self.logger.info(f"EXIT_TERMO: '{ctx.getText()}' → {ctx.type_name}")

    # --- expr ---

    def exitExpr(self, ctx: miniportugolParser.ExprContext):
        current_type = "ERRO_TIPO"
        primeiro_termo = ctx.termo(0)
        if primeiro_termo and hasattr(primeiro_termo, 'type_name'):
            current_type = primeiro_termo.type_name
        else:
            self.logger.error(f"EXIT_EXPR: termo(0) de '{ctx.getText()}' sem type_name.")

        num_termos = len(ctx.termo())
        if num_termos > 1 and not current_type.startswith("ERRO_"):
            for i in range(num_termos - 1):
                op_node = ctx.getChild(i * 2 + 1)
                op_text = op_node.getText()
                right_ctx = ctx.termo(i + 1)
                right_type = right_ctx.type_name if hasattr(right_ctx, 'type_name') else "ERRO_TIPO"
                if right_type.startswith("ERRO_"):
                    current_type = "ERRO_TIPO"
                    break
                if op_text in ['+', '-']:
                    if current_type == "NUMERO" and right_type == "NUMERO":
                        current_type = "NUMERO"
                    else:
                        msg = f"Operador '{op_text}' requer operandos numéricos. Obtidos: {current_type} e {right_type}."
                        self.erro_handler.registrar_erro("Analisador Semântico", op_node.symbol.line, op_node.symbol.column + 1, msg, "SEMANTICO")
                        current_type = "ERRO_TIPO"
                        break

        ctx.type_name = current_type
        self.logger.info(f"EXIT_EXPR: '{ctx.getText()}' → {ctx.type_name}")

    # --- Comandos ---

    def exitComando_definir(self, ctx: miniportugolParser.Comando_definirContext):
        nome_var = ctx.ID().getText()
        expr_node = ctx.expr(0)
        tipo_expr = expr_node.type_name if hasattr(expr_node, 'type_name') else "ERRO_TIPO"
        self.logger.info(f"EXIT_COMANDO_DEFINIR: {nome_var} = {tipo_expr}")

        if tipo_expr.startswith("ERRO_"):
            self.erro_handler.registrar_erro("Analisador Semântico", expr_node.start.line, expr_node.start.column + 1,
                f"Expressão para '{nome_var}' contém erro de tipo.", "SEMANTICO")
            self._registrar_variavel_declarada(nome_var, "ERRO_TIPO", ctx)
            return

        if nome_var in self.escopo_atual:
            self.escopo_atual[nome_var]['type_name'] = tipo_expr
        else:
            self._registrar_variavel_declarada(nome_var, tipo_expr, ctx)

        if nome_var in self.escopo_atual:
            self.escopo_atual[nome_var]["usada_como_alvo"] = True

    def exitComando_ler(self, ctx: miniportugolParser.Comando_lerContext):
        nome_var = ctx.ID().getText()
        tipo_input = "NUMERO"
        self.logger.info(f"EXIT_COMANDO_LER: {nome_var} → {tipo_input}")

        if nome_var in self.escopo_atual:
            self.escopo_atual[nome_var]['type_name'] = tipo_input
        else:
            self._registrar_variavel_declarada(nome_var, tipo_input, ctx)

        if nome_var in self.escopo_atual:
            self.escopo_atual[nome_var]["usada_como_alvo"] = True

    def exitComando_escreva(self, ctx: miniportugolParser.Comando_escrevaContext):
        expr_node = ctx.expr()
        tipo_expr = expr_node.type_name if hasattr(expr_node, 'type_name') else "ERRO_TIPO"
        self.logger.info(f"EXIT_COMANDO_ESCREVA: expr='{ctx.getText()}' tipo={tipo_expr}")

        if tipo_expr.startswith("ERRO_"):
            self.erro_handler.registrar_erro("Analisador Semântico", expr_node.start.line, expr_node.start.column + 1,
                f"Expressão no ESCREVA contém erro de tipo ({tipo_expr}).", "SEMANTICO")

    def exitProgram(self, ctx: miniportugolParser.ProgramContext):
        self.logger.info("--- Verificação Final Semântica ---")
        for nome_var, info_var in self.escopo_atual.items():
            if not info_var["usada"] and not info_var.get("usada_como_alvo", False):
                msg = f"Variável '{nome_var}' declarada na linha {info_var['linha']} mas nunca utilizada."
                self.erro_handler.registrar_erro("Analisador Semântico", info_var['linha'], info_var['coluna'], msg, tipo_erro="AVISO_SEMANTICO")
            elif not info_var["usada"] and info_var.get("usada_como_alvo", False):
                msg = f"Valor da variável '{nome_var}' (linha {info_var['linha']}) nunca é lido."
                self.erro_handler.registrar_erro("Analisador Semântico", info_var['linha'], info_var['coluna'], msg, tipo_erro="AVISO_SEMANTICO")
        self.logger.info("Análise semântica concluída.")
        self.ast_anotada = ctx


# --- Wrapper ---
class AnaliseSemantica:
    def __init__(self, erro_handler: Erro):
        self.erro_handler = erro_handler
        self.logger = logging.getLogger(self.__class__.__name__)
        self.ast_anotada = None

    def executarAnaliseSemantica(self, ast_parser):
        self.logger.info("Iniciando análise semântica...")
        if not ast_parser:
            self.logger.error("AST não fornecida.")
            return None
        if self.erro_handler.houve_erro_fatal():
            self.logger.warning("Erros fatais anteriores. Semântica pulada.")
            return ast_parser
        try:
            listener_semantico = miniportugolSemanticoListenerImpl(self.erro_handler)
            walker = ParseTreeWalker()
            walker.walk(listener_semantico, ast_parser)
            self.ast_anotada = listener_semantico.ast_anotada
            if not self.erro_handler.tem_erros_semanticos:
                self.logger.info("Análise semântica concluída sem erros.")
            else:
                self.logger.error("Análise semântica encontrou ERROS.")
            return self.ast_anotada
        except Exception as e:
            self.erro_handler.registrar_erro("Analisador Semântico", 0, 0,
                f"Erro crítico na análise semântica: {e}", tipo_erro="SEMANTICO")
            self.logger.exception("Detalhes:")
            return ast_parser